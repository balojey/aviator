from typing import Literal
from pydantic import BaseModel

from bot.data_source.round_result import RoundResult
from bot.data_source.decided_multiplier import DecidedMultiplier

class CommonBetHistory(BaseModel):
    date: str
    time: str
    bet_amount_for_box_one: float
    bet_amount_for_box_two: float
    multiplier: float
    decided_multiplier: DecidedMultiplier
    result_one: RoundResult
    result_two: RoundResult
    initial_balance: float
    current_balance: float
    multiplier_category: Literal['B', 'P', 'Pk']
    decided_multiplier_one_category: Literal['B', 'P', 'Pk']
    decided_multiplier_two_category: Literal['B', 'P', 'Pk']
    
    @property
    def datetime_timestamp(self) -> str:
        return f"{self.date} {self.time}"