from collections import Counter, defaultdict
import random
import sys
import polars as pl

from bot.backtesting.backtest import Backtester
from bot.casino.sporty import Sporty
from bot.casino.spribe import Spribe
from bot.data_source import DataSource, DecidedMultiplier
from bot.strategy import BettingStrategy
from bot.data_source import BetHistory, RoundResult, LiveBetHistory
from bot.strategy.executor import Executor
from bot.strategy.risk_manager import RiskManager


class MarkovModelStrategy(BettingStrategy):
    lookback_window: int = 8
    base_multiplier_for_box_one: float = 5.00
    base_multiplier_for_box_two: float = 3.00

    def introduce_strategy(self):
        self.log.info(f"""
        Strategy: {self.__repr_name__()}
        Description: A strategy using Markov chains for game prediction.
        Is Backtest? {self.is_backtest}
        Percentage to bet per round: {self.percentage_to_bet_per_round}
        Lookback window: {self.lookback_window}
        Base multiplier for box one: {self.base_multiplier_for_box_one}
        Base multiplier for box two: {self.base_multiplier_for_box_two}
        """)

    def build_markov_model(self, history: list[str]) -> dict[str, dict[str, float]]:
        transitions = defaultdict(Counter)
        for i in range(len(history) - 1):
            current_state = history[i]
            next_state = history[i + 1]
            transitions[current_state][next_state] += 1

        # Normalize probabilities
        markov_model = {}
        for state, next_counts in transitions.items():
            total = sum(next_counts.values())
            markov_model[state] = {k: v / total for k, v in next_counts.items()}
        
        return markov_model


    def markov_predict_next(self, markov_model: dict[str, dict[str, float]], current_state: str) -> dict[str, float]:
        if current_state not in markov_model:
            return {'B': 0, 'P': 0, 'Pk': 0}
        
        return markov_model[current_state]

    def predict(self, history: list[str]) -> dict[str, float]:
        markov_model = self.build_markov_model(history)
        current_state = history[-1]
        markov_probs = self.markov_predict_next(markov_model, current_state)
        return markov_probs
    
    def is_suspicious_p(self, number_of_ps: int, number_of_bs: int, number_of_pks: int) -> bool:
        if (number_of_bs < 23 or number_of_bs >= 26) and (number_of_ps < 20):
            return False
        return True

    def decide_multiplier(self, game_data: pl.DataFrame, bet_history: list[BetHistory | LiveBetHistory] = [], restart_strategy: bool = False) -> DecidedMultiplier:
        decided_multiplier = DecidedMultiplier(
            multiplier_for_box_one=1.0,
            multiplier_for_box_two=1.0,
        )
        # last_failed_rounds = []
        # for history in reversed(bet_history):
        #     if history.result_one == history.result_two == RoundResult.LOSS:
        #         last_failed_rounds.append(history)
        #         if len(last_failed_rounds) == 2:
        #             break
        #     elif history.result_one != RoundResult.WIN:
        #         break
        # if len(last_failed_rounds) >= 2 and self.previous_failed_rounds != last_failed_rounds:
        #     self.previous_failed_rounds = last_failed_rounds
        #     self.base_multiplier_for_box_one = round(self.base_multiplier_for_box_one - (self.base_multiplier_for_box_one * 0.25), 2) if self.base_multiplier_for_box_one > 1.95 else 1.95
        #     self.base_multiplier_for_box_two = round(self.base_multiplier_for_box_two - (self.base_multiplier_for_box_two * 0.25), 2) if self.base_multiplier_for_box_two > 1.5 else 1.5

        # last_successful_rounds = []
        # for history in reversed(bet_history):
        #     if history.result_one == history.result_two == RoundResult.WIN:
        #         last_successful_rounds.append(history)
        #         if len(last_successful_rounds) == 3:
        #             break
        #     elif history.result_one != RoundResult.LOSS:
        #         break
        # if len(last_successful_rounds) >= 3 and self.previous_successful_rounds != last_successful_rounds:
        #     self.previous_successful_rounds = last_successful_rounds
        #     self.base_multiplier_for_box_one = round(self.base_multiplier_for_box_one + (self.base_multiplier_for_box_one * 0.25), 2) if self.base_multiplier_for_box_one <= 2.5 else 2.5
        #     self.base_multiplier_for_box_two = round(self.base_multiplier_for_box_two + (self.base_multiplier_for_box_two * 0.25), 2) if self.base_multiplier_for_box_two <= 2.0 else 2.0
        
        if self.base_multiplier_for_box_two <= 1.0:
            self.base_multiplier_for_box_two = 1.5

        categories = [history.multiplier_category for history in bet_history[-self.lookback_window:]]
        # multipliers_in_lookback_window = [history.multiplier for history in bet_history[:]]
        multipliers_in_lookback_window = [history.multiplier for history in bet_history[-self.lookback_window:]]
        sum_of_multipliers_in_lookback_window = sum(multipliers_in_lookback_window)
        self.log.info(f'Sum of multipliers in lookback window: {sum_of_multipliers_in_lookback_window}')
        number_of_bs = categories.count('B')
        self.log.info(f'Number of Bs in lookback window: {number_of_bs}')
        number_of_ps = categories.count('P')
        self.log.info(f'Number of Ps in lookback window: {number_of_ps}')
        number_of_pks = categories.count('Pk')
        self.log.info(f'Number of Pks in lookback window: {number_of_pks}')

        markov_probs = self.predict(categories)
        self.log.info(f'Markov Probabilities: {markov_probs}')
        
        max_category = max(markov_probs, key=markov_probs.get)
        self.log.info(f'Maximum Category: {max_category}')

        # calculated_b = (markov_probs.get('B', 0.000001) / (number_of_ps + number_of_pks)) * self.lookback_window
        # self.log.info(f'Calculated B: {calculated_b}')
        # calculated_p = (markov_probs.get('P', 0.000001) / (number_of_bs + number_of_pks)) * self.lookback_window
        # self.log.info(f'Calculated P: {calculated_p}')
        # difference_b_p = abs(calculated_b - calculated_p)
        # self.log.info(f'Difference B-P: {difference_b_p}')

        if len(bet_history) >= self.lookback_window:  # and bet_history[-1].result_one != RoundResult.WIN and bet_history[-1].result_two != RoundResult.WIN:
            # if not self.is_suspicious_p(number_of_ps, number_of_bs, number_of_pks):
            div = sum_of_multipliers_in_lookback_window / sum([history.multiplier for history in bet_history[-self.lookback_window:]])
            self.log.info(f'Division: {div}')
            decided_multiplier.multiplier_for_box_one = self.base_multiplier_for_box_one
            decided_multiplier.multiplier_for_box_two = self.base_multiplier_for_box_two
            # pass
        return decided_multiplier
    

strategy = MarkovModelStrategy(percentage_to_bet_per_round=0.005)
risk_manager = RiskManager(stop_loss=0.1, take_profit=0.2)
data_source = DataSource(csv_file="sporty_aviator_data.csv")
test_casino = Spribe()
live_casino = Sporty()

if __name__ == '__main__':
    arg = sys.argv[1]
    if arg == 'live':
        executor = Executor(
            strategy=strategy,
            risk_manager=risk_manager,
            data_source=data_source,
            casino=live_casino,
            continuous=False,
            consistent=False
        )
        executor.execute()
    elif arg == 'test':
        executor = Executor(
            strategy=strategy,
            risk_manager=risk_manager,
            data_source=data_source,
            casino=test_casino,
            continuous=False,
            consistent=False,
        )
        executor.execute()
    elif arg == 'backtest':
        backester = Backtester(
            strategy=strategy,
            risk_manager=risk_manager,
            data_source=data_source,
            start_date='2025-03-23',
            initial_balance=3000,
            # continuous=False,
            consistent=False,
            # live_bet_history_file='live_bet_history/live_bet_history_20250415_125629.json', # 2025-04-15 Sporty,
            # live_bet_history_file='live_bet_history/live_bet_history_20250416_072424.json', # 2025-04-16 Sporty
            # live_bet_history_file='live_bet_history/live_bet_history_20250416_090335.json', # 2025-04-16 Sporty
            # live_bet_history_file='live_bet_history/live_bet_history_20250416_132948.json', # 2025-04-16 Sporty
            # live_bet_history_file='live_bet_history/live_bet_history_20250416_141523.json', # 2025-04-16 Sporty
            # live_bet_history_file='live_bet_history/live_bet_history_20250416_163943.json', # 2025-04-16 Sporty
            # live_bet_history_file='live_bet_history/live_bet_history_20250416_201112.json', # 2025-04-16 Sporty Real
            # live_bet_history_file='live_bet_history/live_bet_history_20250416_211412.json', # 2025-04-16 Sporty Real
            # live_bet_history_file='live_bet_history/live_bet_history_20250417_003634.json', # 2025-04-17 Sporty Real
            live_bet_history_file='live_bet_history/live_bet_history_20250417_114034.json', # 2025-04-17 Sporty Real
        )
        backester.run()
