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
    iteration_wait_rounds: int = 0
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
        iteration_wait_rounds_count = 0
        box_one_result_queue = queue.Queue()
        box_two_result_queue = queue.Queue()
        date = datetime.now().strftime('%Y-%m-%d')
        time = datetime.now().strftime('%H:%M:%S')
        bet_amount_for_box_one = self.strategy.calculate_bet_amount_for_box_one(current_balance)
        bet_amount_for_box_two = self.strategy.calculate_bet_amount_for_box_two(current_balance)
        decided_multiplier = DecidedMultiplier(multiplier_for_box_one=1.0, multiplier_for_box_two=1.0)
        result_one = RoundResult.DRAW
        result_two = RoundResult.DRAW
        while True:
            try:
                if len(self.casino.previous_multiplier_history) <= 0:
                    self.casino.previous_multiplier_history = self.casino.get_latest_multipliers()
                if self.casino.previous_multiplier_history != self.casino.get_latest_multipliers():

                    if self.casino.previous_multiplier_history[:14] == self.casino.get_latest_multipliers()[1:]:
                        latest_multiplier = self.casino.get_latest_multipliers()[0]
                        if decided_multiplier.multiplier_for_box_one > 1.00 and result_one == RoundResult.LOSS and latest_multiplier >= decided_multiplier.multiplier_for_box_one:
                            result_one = RoundResult.MISS
                            decided_multiplier.multiplier_for_box_one = 1.00
                        if decided_multiplier.multiplier_for_box_two > 1.00 and result_two == RoundResult.LOSS and latest_multiplier >= decided_multiplier.multiplier_for_box_two:
                            result_two = RoundResult.MISS
                            decided_multiplier.multiplier_for_box_two = 1.00
                            
                    if self.casino.previous_multiplier_history[:14] != self.casino.get_latest_multipliers()[1:]:
                        previous_multiplier = self.casino.previous_multiplier_history[0]
                        index_of_previous_multiplier_in_latest_multipliers = self.casino.get_latest_multipliers().index(previous_multiplier)
                        if decided_multiplier.multiplier_for_box_one > 1.00 and result_one == RoundResult.LOSS:
                            for multiplier in self.casino.get_latest_multipliers()[:index_of_previous_multiplier_in_latest_multipliers + 1]:
                                if multiplier >= decided_multiplier.multiplier_for_box_one:
                                    result_one = RoundResult.MISS
                                    decided_multiplier.multiplier_for_box_one = 1.00
                                    break
                        if decided_multiplier.multiplier_for_box_two > 1.00 and result_two == RoundResult.LOSS:
                            for multiplier in self.casino.get_latest_multipliers()[:index_of_previous_multiplier_in_latest_multipliers + 1]:
                                if multiplier >= decided_multiplier.multiplier_for_box_two:
                                    result_two = RoundResult.MISS
                                    decided_multiplier.multiplier_for_box_two = 1.00
                                    break

                    self.casino.previous_multiplier_history = self.casino.get_latest_multipliers()
                    current_balance = self.casino.get_balance()
                    self.live_bet_history.append(lvb := LiveBetHistory(
                        date=date,
                        time=time,
                        bet_amount_for_box_one=bet_amount_for_box_one,
                        bet_amount_for_box_two=bet_amount_for_box_two,
                        multiplier=(m := self.casino.get_latest_multipliers()[0]),
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

                    winnings_1 = [history for history in self.live_bet_history if history.result_one == RoundResult.WIN]
                    winnings_2 = [history for history in self.live_bet_history if history.result_two == RoundResult.WIN]
                    total_winnings = len(winnings_1) + len(winnings_2)
                    logging.info(f'Total Number of Winnings: {total_winnings}')

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
                        iteration_wait_rounds_count = self.iteration_wait_rounds
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
                    if self.risk_manager.check_risk(initial_balance, current_balance) and iteration_wait_rounds_count <= 0:
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

                        logging.info(f'Box One Multiplier: {decided_multiplier.multiplier_for_box_one}')
                        logging.info(f'Box Two Multiplier: {decided_multiplier.multiplier_for_box_two}')

                        adjusted_multiplier_for_box_one = self.adjust_for_latency(decided_multiplier.multiplier_for_box_one)
                        adjusted_multiplier_for_box_two = self.adjust_for_latency(decided_multiplier.multiplier_for_box_two)
                        bet_amount_for_box_one = self.strategy.calculate_bet_amount_for_box_one(balance=initial_balance if self.consistent else current_balance)
                        bet_amount_for_box_two = self.strategy.calculate_bet_amount_for_box_two(balance=initial_balance if self.consistent else current_balance)

                        if self.casino.__repr_name__() == 'Spribe' and bet_amount_for_box_one < 1.0:
                            bet_amount_for_box_one = 1.0
                        if self.casino.__repr_name__() == 'Spribe' and bet_amount_for_box_two < 1.0:
                            bet_amount_for_box_two = 1.0
                        if (self.casino.__repr_name__() == 'Sporty' or self.casino.__repr_name__() == 'MSport') and bet_amount_for_box_one < 10.0:
                            bet_amount_for_box_one = 10.0
                        if (self.casino.__repr_name__() == 'Sporty' or self.casino.__repr_name__() == 'MSport') and bet_amount_for_box_two < 10.0:
                            bet_amount_for_box_two = 10.0
                        cash_out_amount_1 = round(bet_amount_for_box_one * adjusted_multiplier_for_box_one, 2)
                        cash_out_amount_2 = round(bet_amount_for_box_two * adjusted_multiplier_for_box_two, 2)
                        result_one: RoundResult = RoundResult.DRAW
                        result_two: RoundResult = RoundResult.DRAW

                        if decided_multiplier.multiplier_for_box_one > 1.0:
                            self.casino.place_bet_in_box_one(bet_amount_for_box_one)
                        if decided_multiplier.multiplier_for_box_two > 1.0:
                            self.casino.place_bet_in_box_two(bet_amount_for_box_two)

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

                        # while True:
                        #     if self.casino.previous_multiplier_history != self.casino.get_latest_multipliers():
                        #         current_balance = self.casino.get_balance()
                        #         self.live_bet_history.append(lvb := LiveBetHistory(
                        #             date=date,
                        #             time=time,
                        #             bet_amount_for_box_one=bet_amount_for_box_one,
                        #             bet_amount_for_box_two=bet_amount_for_box_two,
                        #             multiplier=(m := self.casino.get_latest_multipliers()[0]),
                        #             decided_multiplier=decided_multiplier,
                        #             result_one=result_one,
                        #             result_two=result_two,
                        #             initial_balance=initial_balance,
                        #             current_balance=current_balance,
                        #             multiplier_category='B' if 1.00 <= m <= 1.99 else 'P' if 2.00 <= m <= 9.99 else 'Pk',
                        #             decided_multiplier_one_category='B' if 1.00 <= decided_multiplier.multiplier_for_box_one <= 1.99 else 'P' if 2.00 <= decided_multiplier.multiplier_for_box_one <= 9.99 else 'Pk',
                        #             decided_multiplier_two_category='B' if 1.00 <= decided_multiplier.multiplier_for_box_two <= 1.99 else 'P' if 2.00 <= decided_multiplier.multiplier_for_box_two <= 9.99 else 'Pk',
                        #         ))
                        #         logging.info(lvb)
                        #         self.save_live_bet_history()

                        #         winnings_1 = [history for history in self.live_bet_history if history.result_one == RoundResult.WIN]
                        #         winnings_2 = [history for history in self.live_bet_history if history.result_two == RoundResult.WIN]
                        #         total_winnings = len(winnings_1) + len(winnings_2)
                        #         logging.info(f'Total Number of Winnings: {total_winnings}')

                        #         break
                        restart_strategy = False
                    else:
                        iteration_wait_rounds_count -= 1
                        self.live_bet_history.append(lvb := LiveBetHistory(
                            date=date,
                            time=time,
                            bet_amount_for_box_one=bet_amount_for_box_one,
                            bet_amount_for_box_two=bet_amount_for_box_two,
                            multiplier=(m := self.casino.get_latest_multipliers()[0]),
                            decided_multiplier=DecidedMultiplier(multiplier_for_box_one=1.00, multiplier_for_box_two=1.0),
                            result_one=RoundResult.DRAW,
                            result_two=RoundResult.DRAW,
                            initial_balance=initial_balance,
                            current_balance=current_balance,
                            multiplier_category='B' if 1.00 <= m <= 1.99 else 'P' if 2.00 <= m <= 9.99 else 'Pk',
                            decided_multiplier_one_category='B' if 1.00 <= decided_multiplier.multiplier_for_box_one <= 1.99 else 'P' if 2.00 <= decided_multiplier.multiplier_for_box_one <= 9.99 else 'Pk',
                            decided_multiplier_two_category='B' if 1.00 <= decided_multiplier.multiplier_for_box_two <= 1.99 else 'P' if 2.00 <= decided_multiplier.multiplier_for_box_two <= 9.99 else 'Pk',
                        ))
                        logging.info(lvb)
                        self.save_live_bet_history()
                        logging.info(f'Waiting for {iteration_wait_rounds_count} of {self.iteration_wait_rounds} rounds to place a bet')
            except Exception as e:
                print(f'Error during execution: {e}')
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
        return round(0.05 + (multiplier - 1.0) * 0.05, 2)

    def adjust_for_latency(self, multiplier: float) -> float:
        latency = self.calculate_latency(multiplier)
        adjusted_multiplier = round(multiplier - latency, 2)
        return adjusted_multiplier
