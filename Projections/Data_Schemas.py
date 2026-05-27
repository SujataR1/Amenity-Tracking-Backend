# Projections/Data_Schemas.py

from pydantic import BaseModel
from typing import Literal

from Machine_Learning.Data_Schemas import ResourceTypeEnum


# =========================================================
# QUESTIONNAIRE SCHEMA
# =========================================================
class QuestionnaireInput(BaseModel):

    num_people: int
    num_children: int
    bedrooms: int

    has_ac: bool
    has_geyser: bool
    has_iron: bool
    has_washing_machine: bool
    has_dishwasher: bool
    has_induction: bool
    has_microwave: bool
    has_kettle: bool
    has_vacuum: bool
    has_room_heater: bool

    home_area: float

    has_pool: bool
    has_garden: bool

    vacation_month: str
    vacation_days: int

    climate: str


# =========================================================
# NORMAL PREDICTION REQUEST
# =========================================================
class ProjectionRequest(BaseModel):

    resource_type: ResourceTypeEnum
    month: str
    year: int


# =========================================================
# TEST PREDICTION REQUEST
# =========================================================
class ProjectionTestRequest(BaseModel):

    resource_type: ResourceTypeEnum
    month: str
    year: int

    questionnaire: QuestionnaireInput