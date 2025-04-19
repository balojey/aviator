import polars as pl

from bot.strategy import BettingStrategy
from bot.data_source import BetHistory, RoundResult


class TitForTat(BettingStrategy):
    base_multiplier: float = 1.01
    current_multiplier: float = 1.0

    def decide_multiplier(self, game_data: pl.DataFrame, bet_history: list[BetHistory] = [], restart_strategy: bool = False) -> float:
        if len(bet_history) > 0 and bet_history[-1].result == RoundResult.LOSS:
            self.base_multiplier = round(self.base_multiplier + 0.1, 2)  # Double the bet on loss
        # if len(bet_history) >= 3 and bet_history[-1].result == bet_history[-2].result == bet_history[-3].result == RoundResult.LOSS:
        #     return 1.00
        if restart_strategy:
            self.base_multiplier = 1.01
        self.current_multiplier = self.base_multiplier  # Reset bet on win
        return self.current_multiplier
