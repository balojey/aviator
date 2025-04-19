from typing import Literal
from pydantic import BaseModel

from bot.data_source.round_result import RoundResult
from bot.data_source.decided_multiplier import DecidedMultiplier
from bot.data_source.common_bet_history import CommonBetHistory

class BetHistory(CommonBetHistory):
    round_number: int
    