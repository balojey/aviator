import random

import polars as pl

from bot.strategy import BettingStrategy
from bot.data_source import BetHistory, RoundResult


class RandomStrategy(BettingStrategy):
    base_multiplier: float = 1.01
    unwanted_multiplier: float = 1.0

    def decide_multiplier(self, game_data: pl.DataFrame, bet_history: list[BetHistory] = [], restart_strategy: bool = False) -> float:
        multiplier = random.choice([self.base_multiplier, self.unwanted_multiplier])
        if len(bet_history) > 0 and bet_history[-1] == RoundResult.LOSS:
            multiplier = 1.50
        if len(bet_history) > 0 and bet_history[-1] == RoundResult.LOSS and bet_history[-2] == RoundResult.LOSS:
            multiplier = 1.75
        return multiplier
