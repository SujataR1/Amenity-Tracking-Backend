from enum import Enum


class ConsumptionType(str, Enum):
    ELECTRICITY = "electricity"
    WATER = "water"
    GAS = "gas"
    FUEL = "fuel"