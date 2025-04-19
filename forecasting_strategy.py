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


class ForecastingStrategy(BettingStrategy):
    base_multiplier_for_box_one: float = 2.5
    base_multiplier_for_box_two: float = 2.0

    def introduce_strategy(self):
        self.log.info(f"""
        Strategy: {self.__repr_name__()}
        Description: A strategy using Markov chains for game prediction.
        Is Backtest? {self.is_backtest}
        Percentage to bet per round: {self.percentage_to_bet_per_round}
        """)

    def decide_multiplier(self, game_data: pl.DataFrame, bet_history: list[BetHistory | LiveBetHistory], restart_strategy = False):
        pass
