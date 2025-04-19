import polars as pl
from talipp.indicators import SMA

from bot.strategy import BettingStrategy
from bot.data_source import BetHistory, RoundResult


class SMACrossOver(BettingStrategy):
    slow_sma: int = 50
    fast_sma: int = 100

    def decide_multiplier(self, game_data: pl.DataFrame, bet_history: list[BetHistory] = [], restart_strategy: bool = False) -> float:
        sma1 = SMA(period=self.slow_sma, input_values=list(game_data['multiplier']))
        sma2 = SMA(period=self.fast_sma, input_values=list(game_data['multiplier']))

        # Check if we have enough data points to calculate SMA crossover
        if len(sma1) < 2 or len(sma2) < 2:
            return 1.0  # Default multiplier if not enough data

        # Determine the crossover
        if sma1[-1] > sma2[-1] and sma1[-2] <= sma2[-2]:
            # Fast SMA crosses above Slow SMA (Bullish signal)
            return 2.0  # Aggressive multiplier
        elif sma1[-1] < sma2[-1] and sma1[-2] >= sma2[-2]:
            # Fast SMA crosses below Slow SMA (Bearish signal)
            return 0.5  # Conservative multiplier
        else:
            # No crossover, maintain a neutral multiplier
            return 1.0