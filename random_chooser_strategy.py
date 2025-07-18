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

    def introduce_strategy(self):
        self.log.info(f"""
        Strategy: {self.__repr_name__()}
        Description: A strategy using Markov chains for game prediction.
        Is Backtest? {self.is_backtest}
        Percentage to bet per round: {self.percentage_to_bet_per_round}
        """)

    def decide_multiplier(self, game_data: pl.DataFrame, bet_history: list[BetHistory | LiveBetHistory] = [], restart_strategy: bool = False) -> DecidedMultiplier:
        decided_multiplier = DecidedMultiplier(
            multiplier_for_box_one=1.00,
            multiplier_for_box_two=1.00,
        )
        # Determine the current game number
        game_count = len(bet_history)

        # Check if we are in a block of 3 games where multipliers should be generated
        if (game_count // random.randint(1, 10)) % 2 == 0:
            decided_multiplier.multiplier_for_box_one = round(random.uniform(4.99, 15.00), 2)
            decided_multiplier.multiplier_for_box_two = round(random.uniform(1.01, 9.99), 2)
        return decided_multiplier
    
    def calculate_bet_amount(self, balance):
        return round(random.uniform(10, 30), 2)
    

strategy = MarkovModelStrategy(percentage_to_bet_per_round=0.005)
risk_manager = RiskManager(stop_loss=0.1, take_profit=0.3)
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
            continuous=False,
            consistent=False,
            # live_bet_history_file='live_bet_history/live_bet_history_20250415_125629.json', # 2025-04-15 Sporty,
            # live_bet_history_file='live_bet_history/live_bet_history_20250416_072424.json', # 2025-04-16 Sporty
            # live_bet_history_file='live_bet_history/live_bet_history_20250416_090335.json', # 2025-04-16 Sporty
            # live_bet_history_file='live_bet_history/live_bet_history_20250416_132948.json', # 2025-04-16 Sporty
            live_bet_history_file='live_bet_history/live_bet_history_20250416_141523.json', # 2025-04-16 Sporty
            # live_bet_history_file='live_bet_history/live_bet_history_20250416_163943.json', # 2025-04-16 Sporty
            # live_bet_history_file='live_bet_history/live_bet_history_20250416_201112.json', # 2025-04-16 Sporty Real
            # live_bet_history_file='live_bet_history/live_bet_history_20250416_211412.json', # 2025-04-16 Sporty Real
            # live_bet_history_file='live_bet_history/live_bet_history_20250417_003634.json', # 2025-04-17 Sporty Real
        )
        backester.run()
