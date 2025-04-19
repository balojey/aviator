from typing_extensions import Any
import logging

from pydantic import BaseModel, field_validator, ConfigDict


class RiskManager(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    stop_loss: float
    take_profit: float
    balance_for_stop_loss: float = None
    log: logging.Logger = None

    @field_validator('stop_loss', 'take_profit')
    def check_limits(cls, value):
        if not 0.0 <= value <= 1.0:
            raise ValueError('stop_loss and take_profit must be between 0.0 and 1.0 inclusive')
        return value

    def check_risk(self, initial_balance: float, current_balance: float) -> bool:
        """Check if the risk limits have been reached."""
        self.balance_for_stop_loss = self.balance_for_stop_loss if self.balance_for_stop_loss > current_balance else current_balance
        stop_loss_amount = self.balance_for_stop_loss - (self.balance_for_stop_loss * self.stop_loss)
        take_profit_amount = initial_balance + (initial_balance * self.take_profit)
        if current_balance <= stop_loss_amount:
            self.log.info("Stopping: Reached stop-loss limit.")
            return False
        if current_balance >= take_profit_amount:
            self.log.info("Stopping: Reached take-profit target.")
            return False
        return True