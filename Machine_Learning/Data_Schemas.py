from enum import Enum


class ResourceTypeEnum(str, Enum):
    Electricity = "Electricity"
    Gas = "Gas"
    Water = "Water"
    Fuel = "Fuel"
