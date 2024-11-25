from enum import Enum
from pydantic import BaseModel
from typing import Optional


class MonthEnum(str, Enum):
    january = "January"
    february = "February"
    march = "March"
    april = "April"
    may = "May"
    june = "June"
    july = "July"
    august = "August"
    september = "September"
    october = "October"
    november = "November"
    december = "December"


class ConsumptionBase(BaseModel):
    month: Optional[MonthEnum] = None
    year: Optional[int] = None


class CreateConsumption(ConsumptionBase):
    consumption: float


class UpdateConsumption(CreateConsumption):
    pass


class GetConsumption(ConsumptionBase):
    limit: Optional[str] = None
