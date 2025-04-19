from pydantic import BaseModel


class IterationHistory(BaseModel):
    profit: float
    loss: float
    iteration: float
    profit_percentage: float
    loss_percentage: float
    