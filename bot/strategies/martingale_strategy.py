from pprint import pprint

import polars as pl

from bot.strategy import BettingStrategy
from bot.data_source import BetHistory, RoundResult


class MartingaleStrategy(BettingStrategy):
    base_multiplier: float = 1.0
    current_multiplier: float = 1.0

    def decide_multiplier(self, game_data: pl.DataFrame, bet_history: list[BetHistory] = []) -> float:
        if len(bet_history) > 0 and bet_history[-1].result == RoundResult.LOSS:
            self.current_multiplier *= 2  # Double the bet on loss
        else:
            self.current_multiplier = self.base_multiplier  # Reset bet on win
        return self.current_multiplier
