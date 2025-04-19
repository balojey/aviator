from typing_extensions import Any
import logging

from pydantic import BaseModel, field_validator, ConfigDict
import polars as pl

from bot.data_source import BetHistory, LiveBetHistory, DecidedMultiplier


class BettingStrategy(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    percentage_to_bet_per_round: float
    is_backtest: bool = None
    log: logging.Logger = None

    @field_validator('percentage_to_bet_per_round')
    def check_limits(cls, value):
        if not 0.0 <= value <= 1.0:
            raise ValueError('stop_loss and take_profit must be between 0.0 and 1.0 inclusive')
        return value
    
    def introduce_strategy(self) -> None:
        """Override this method in specific strategy classes"""
        pass

    def decide_multiplier(self, game_data: pl.DataFrame, bet_history: list[BetHistory | LiveBetHistory] = [], restart_strategy: bool = False) -> DecidedMultiplier:
        """Override this method in specific strategy classes"""
        raise NotImplementedError
    
    def calculate_bet_amount(self, balance: float) -> float:
        return round(balance * self.percentage_to_bet_per_round, 2)
    
    def send_quit_signal(self):
        """Send a signal to quit the game"""
        return 1
    
    def after_game_round_during_backtesting(self):
        pass