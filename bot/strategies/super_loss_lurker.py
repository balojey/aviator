import polars as pl

from bot.strategy import BettingStrategy
from bot.data_source import BetHistory, RoundResult, LiveBetHistory


class SuperLossLurker(BettingStrategy):
    base_multiplier: float = 1.00

    def decide_multiplier(self, game_data: pl.DataFrame, bet_history: list[BetHistory | LiveBetHistory] = [], restart_strategy: bool = False) -> float:
        # if self.base_multiplier >=20:
        #     self.base_multiplier = 1.0
        #     return self.base_multiplier
        if len(bet_history) > 0 and bet_history[-1].result == RoundResult.LOSS:
            self.base_multiplier += 1
            return self.base_multiplier
        if len(bet_history) > 0 and bet_history[-1].multiplier < 2.00:
            self.base_multiplier += 1
            return self.base_multiplier
        if len(bet_history) > 0 and bet_history[-1].result == RoundResult.WIN:
            self.base_multiplier = 1.00
            return self.base_multiplier
        return self.base_multiplier
