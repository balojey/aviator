from pydantic import BaseModel


class DecidedMultiplier(BaseModel):
    multiplier_for_box_one: float
    multiplier_for_box_two: float