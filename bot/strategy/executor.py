import os
import random
import logging
from time import sleep
from datetime import datetime
import queue
import threading
import json

from pydantic import BaseModel, ConfigDict
import polars as pl
from dotenv import load_dotenv

from bot.data_source import DataSource, LiveBetHistory, IterationHistory, RoundResult, DecidedMultiplier
from bot.strategy.betting_strategy import BettingStrategy
from bot.strategy.risk_manager import RiskManager
from bot.casino import Casino

load_dotenv()


logging.basicConfig(
    filename=f'logs/live/run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class Executor(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    strategy: BettingStrategy
    risk_manager: RiskManager
    casino: Casino
    data_source: DataSource
    look_back: int = 2
    start_time: str = '00:00:00'
    end_time: str = '23:59:59'
    live_bet_history: list[LiveBetHistory] = []
    consistent: bool = True
    continuous: bool = True
    iteration_history: list[IterationHistory] = []
    iteration_wait_time: int = 0
    live_bet_history_storage: str = f'live_bet_history/live_bet_history_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

    def execute(self):
        logging.info('Logging in to casino')
        self.casino.login()
        logging.info('Logged in!')
        logging.info('Launching aviator')
        self.casino.launch_aviator()
        logging.info('Launched aviator!')
        initial_balance = self.casino.get_balance()
        current_balance = initial_balance
        self.risk_manager.balance_for_stop_loss = initial_balance
        iteration = 1
        restart_strategy = False
        self.strategy.is_backtest = False
        self.strategy.log = logging
        self.casino.log = logging
        self.risk_manager.log = logging
        self.strategy.introduce_strategy()
        while True:
            try:
                if self.casino.is_ready():
                    box_one_result_queue = queue.Queue()
                    box_two_result_queue = queue.Queue()
                    logging.info('Starting New Round!')
                    self.data_source.load_data()
                    if not self.risk_manager.check_risk(initial_balance, current_balance) and self.continuous:
                        logging.info('Restarting strategy')
                        profit = (current_balance - initial_balance) if current_balance > initial_balance else 0.0
                        loss = (initial_balance - current_balance) if initial_balance > current_balance else 0.0
                        profit_percentage = (profit / initial_balance) * 100 if profit > 0 else 0.0
                        loss_percentage = (loss / initial_balance) * 100 if loss > 0 else 0.0
                        self.iteration_history.append(ih := IterationHistory(
                            profit=profit,
                            loss=loss,
                            iteration=iteration,
                            profit_percentage=profit_percentage,
                            loss_percentage=loss_percentage
                        ))
                        logging.info(ih)
                        restart_strategy = True
                        initial_balance = current_balance
                        self.risk_manager.balance_for_stop_loss = initial_balance
                        iteration += 1
                        sleep(self.iteration_wait_time)
                    elif not self.risk_manager.check_risk(initial_balance, current_balance) and not self.continuous:
                            profit = (current_balance - initial_balance) if current_balance > initial_balance else 0.0
                            loss = (initial_balance - current_balance) if initial_balance > current_balance else 0.0
                            profit_percentage = (profit / initial_balance) * 100 if profit > 0 else 0.0
                            loss_percentage = (loss / initial_balance) * 100 if loss > 0 else 0.0
                            self.iteration_history.append(ih := IterationHistory(
                                profit=profit,
                                loss=loss,
                                iteration=iteration,
                                profit_percentage=profit_percentage,
                                loss_percentage=loss_percentage
                            ))
                            logging.info(ih)
                    date = datetime.now().strftime('%Y-%m-%d')
                    time = datetime.now().strftime('%H:%M:%S')
                    historical_data = self.data_source.get_data_before_date_and_time(
                        start_date=date,
                        look_back=self.look_back,
                    )
                    if self.risk_manager.check_risk(initial_balance, current_balance):
                        try:
                            decided_multiplier: DecidedMultiplier = self.strategy.decide_multiplier(
                                game_data=historical_data,
                                bet_history=self.live_bet_history,
                                restart_strategy=restart_strategy
                            )
                        except Exception as e:
                            print(e)
                            decided_multiplier = DecidedMultiplier(
                                multiplier_for_box_one=1.00,
                                multiplier_for_box_two=1.00
                            )
                        adjusted_multiplier_for_box_one = self.adjust_for_latency(decided_multiplier.multiplier_for_box_one)
                        adjusted_multiplier_for_box_two = self.adjust_for_latency(decided_multiplier.multiplier_for_box_two)
                        bet_amount = self.strategy.calculate_bet_amount(balance=initial_balance if self.consistent else current_balance)
                        cash_out_amount_1 = round(bet_amount * adjusted_multiplier_for_box_one, 2)
                        cash_out_amount_2 = round(bet_amount * adjusted_multiplier_for_box_two, 2)
                        result_one: RoundResult = RoundResult.DRAW
                        result_two: RoundResult = RoundResult.DRAW

                        if decided_multiplier.multiplier_for_box_one > 1.0:
                            self.casino.place_bet_in_box_one(bet_amount)
                        if decided_multiplier.multiplier_for_box_two > 1.0:
                            self.casino.place_bet_in_box_two(bet_amount)

                        def cash_out_box_one():
                            result = self.casino.cash_out_box_one(cash_out_amount_1)
                            box_one_result_queue.put(result)
                        def cash_out_box_two():
                            result = self.casino.cash_out_box_two(cash_out_amount_2)
                            box_two_result_queue.put(result)
                        threads = []
                        if decided_multiplier.multiplier_for_box_one > 1.0:
                            threads.append(threading.Thread(target=cash_out_box_one))
                        if decided_multiplier.multiplier_for_box_two > 1.0:
                            threads.append(threading.Thread(target=cash_out_box_two))
                        for thread in threads:
                            thread.start()
                        for thread in threads:
                            thread.join()
                        if decided_multiplier.multiplier_for_box_one > 1.0:
                            result_one = box_one_result_queue.get()
                        if decided_multiplier.multiplier_for_box_two > 1.0:
                            result_two = box_two_result_queue.get()

                        while True:
                            if self.casino.latest_game_round_multiplier != self.casino.get_latest_multiplier():
                                current_balance = self.casino.get_balance()
                                self.live_bet_history.append(lvb := LiveBetHistory(
                                    date=date,
                                    time=time,
                                    bet_amount=bet_amount,
                                    multiplier=(m := self.casino.get_latest_multiplier()),
                                    decided_multiplier=decided_multiplier,
                                    result_one=result_one,
                                    result_two=result_two,
                                    initial_balance=initial_balance,
                                    current_balance=current_balance,
                                    multiplier_category='B' if 1.00 <= m <= 1.99 else 'P' if 2.00 <= m <= 9.99 else 'Pk',
                                    decided_multiplier_one_category='B' if 1.00 <= decided_multiplier.multiplier_for_box_one <= 1.99 else 'P' if 2.00 <= decided_multiplier.multiplier_for_box_one <= 9.99 else 'Pk',
                                    decided_multiplier_two_category='B' if 1.00 <= decided_multiplier.multiplier_for_box_two <= 1.99 else 'P' if 2.00 <= decided_multiplier.multiplier_for_box_two <= 9.99 else 'Pk',
                                ))
                                logging.info(lvb)
                                self.save_live_bet_history()
                                break
            except Exception as e:
                self.casino.refresh()

    def save_live_bet_history(self) -> None:
        try:
            with open(self.live_bet_history_storage, 'w') as file:
                json.dump(
                    [history.model_dump() | {"result_one": str(history.result_one.value), "result_two": str(history.result_two.value)} for history in self.live_bet_history],
                    file,
                    indent=4
                )
                logging.info(f'Live bet history saved to {self.live_bet_history_storage}')
        except Exception as e:
            print(f'Failed to save live bet history: {e}')

    def adjust_for_latency(self, multiplier: float) -> float:
        latency = 0.00
        if 1.0 <= multiplier < 1.5:
            latency = 0.05
        if 1.50 <= multiplier < 2.0:
            latency = 0.07
        if 2.0 <= multiplier < 2.5:
            latency = 0.09
        if 2.5 <= multiplier < 3.0:
            latency = 0.11
        if 3.0 <= multiplier < 4.0:
            latency = 0.13
        if 4.0 <= multiplier < 5.0:
            latency = 0.15
        if 5.0 <= multiplier < 6.0:
            latency = 0.17
        if 6.0 <= multiplier < 7.0:
            latency = 0.19
        if 7.0 <= multiplier < 8.0:
            latency = 0.21
        if 8.0 <= multiplier < 9.0:
            latency = 0.23
        if 9.0 <= multiplier < 10.0:
            latency = 0.25
        if 10.0 <= multiplier < 11.0:
            latency = 0.27
        if 11.0 <= multiplier < 12.0:
            latency = 0.29
        if 12.0 <= multiplier < 13.0:
            latency = 0.31
        if 13.0 <= multiplier < 14.0:
            latency = 0.33
        if 14.0 <= multiplier < 15.0:
            latency = 0.35
        if 15.0 <= multiplier < 16.0:
            latency = 0.37
        if 16.0 <= multiplier < 17.0:
            latency = 0.39
        if 17.0 <= multiplier < 18.0:
            latency = 0.41
        if 18.0 <= multiplier < 19.0:
            latency = 0.43
        if 19.0 <= multiplier < 20.0:
            latency = 0.45
        if 20.0 <= multiplier < 21.0:
            latency = 0.47
        if 21.0 <= multiplier < 22.0:
            latency = 0.49
        if 22.0 <= multiplier < 23.0:
            latency = 0.51
        if 23.0 <= multiplier < 24.0:
            latency = 0.53
        if 24.0 <= multiplier < 25.0:
            latency = 0.55
        if 25.0 <= multiplier < 26.0:
            latency = 0.57
        if 26.0 <= multiplier < 27.0:
            latency = 0.59
        if 27.0 <= multiplier < 28.0:
            latency = 0.61
        if 28.0 <= multiplier < 29.0:
            latency = 0.63
        if 29.0 <= multiplier < 30.0:
            latency = 0.65
        if 30.0 <= multiplier < 31.0:
            latency = 0.67
        if 31.0 <= multiplier < 32.0:
            latency = 0.69
        if 32.0 <= multiplier < 33.0:
            latency = 0.71
        if 33.0 <= multiplier < 34.0:
            latency = 0.73
        if 34.0 <= multiplier < 35.0:
            latency = 0.75
        if 35.0 <= multiplier < 36.0:
            latency = 0.77
        if 36.0 <= multiplier < 37.0:   
            latency = 0.79
        if 37.0 <= multiplier < 38.0:
            latency = 0.81
        if 38.0 <= multiplier < 39.0:
            latency = 0.83
        if 39.0 <= multiplier < 40.0:
            latency = 0.85
        if 40.0 <= multiplier < 41.0:
            latency = 0.87
        if 41.0 <= multiplier < 42.0:
            latency = 0.89
        if 42.0 <= multiplier < 43.0:
            latency = 0.91
        if 43.0 <= multiplier < 44.0:
            latency = 0.93
        if 44.0 <= multiplier < 45.0:
            latency = 0.95
        if 45.0 <= multiplier < 46.0:
            latency = 0.97
        if 46.0 <= multiplier < 47.0:
            latency = 0.99
        if 47.0 <= multiplier < 48.0:
            latency = 1.01
        if 48.0 <= multiplier < 49.0:
            latency = 1.03
        if 49.0 <= multiplier < 50.0:
            latency = 1.05
        adjusted_multiplier = round(multiplier - latency, 2)
        return adjusted_multiplier
