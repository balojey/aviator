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
                        logging.info('Restarting strategy...')
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
                        if self.casino.__repr_name__() == 'Spribe' and bet_amount < 1.0:
                            bet_amount = 1.0
                        if self.casino.__repr_name__() == 'Sporty' and bet_amount < 10.0:
                            bet_amount = 10.0
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
                        threads: list[threading.Thread] = []
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

    def calculate_latency(self, multiplier: float) -> float:
        if multiplier <= 1.0:
            return 0.0
        return round(0.05 + (multiplier - 1.0) * 0.02, 2)

    def adjust_for_latency(self, multiplier: float) -> float:
        latency = self.calculate_latency(multiplier)
        adjusted_multiplier = round(multiplier - latency, 2)
        return adjusted_multiplier
