from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


# =========================================================
# MONTH ENUM
# =========================================================
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


# =========================================================
# CLIMATE ENUM
# =========================================================
class ClimateEnum(str, Enum):
    HOT = "Hot"
    COLD = "Cold"
    HUMID = "Humid"
    DRY = "Dry"
    TEMPERATE = "Temperate"


# =========================================================
# QUESTIONNAIRE FIELD NAMES
# =========================================================
class QuestionnaireFields(Enum):
    NUM_PEOPLE = "num_people"

    NUM_CHILDREN = "num_children"

    BEDROOMS = "bedrooms"

    HAS_AC = "has_ac"

    HAS_GEYSER = "has_geyser"

    HAS_IRON = "has_iron"

    HAS_WASHING_MACHINE = "has_washing_machine"

    HAS_DISHWASHER = "has_dishwasher"

    HAS_INDUCTION = "has_induction"

    HAS_MICROWAVE = "has_microwave"

    HAS_KETTLE = "has_kettle"

    HAS_VACUUM = "has_vacuum"

    HAS_ROOM_HEATER = "has_room_heater"

    HOME_AREA = "home_area"

    HAS_POOL = "has_pool"

    HAS_GARDEN = "has_garden"

    VACATION_MONTH = "vacation_month"

    VACATION_DAYS = "vacation_days"

    CLIMATE = "climate"


# =========================================================
# QUESTIONNAIRE QUESTIONS
# =========================================================
class QuestionnaireEnum(str, Enum):
    NUM_PEOPLE = "How many people live in the home?"

    NUM_CHILDREN = "How many people under 18 live in the home?"

    BEDROOMS = "How many bedrooms are there in your home?"

    HAS_AC = "Are you using air conditioning?"

    HAS_GEYSER = "Are you using a geyser?"

    HAS_IRON = "Are you using an electric iron?"

    HAS_WASHING_MACHINE = "Are you using a washing machine?"

    HAS_DISHWASHER = "Are you using a dishwasher?"

    HAS_INDUCTION = "Are you using an induction oven, hot plate, etc.?"

    HAS_MICROWAVE = "Are you using a microwave oven, grill, etc.?"

    HAS_KETTLE = "Are you using a water heater kettle?"

    HAS_VACUUM = "Are you using a vacuum cleaner?"

    HAS_ROOM_HEATER = "Are you using a room heater?"

    HOME_AREA = "Can you estimate the surface area of your home?"

    HAS_POOL = "If you are living in a villa, do you have a swimming pool?"

    HAS_GARDEN = "If you are living in a villa, do you have a garden?"

    VACATION_MONTH = "During which month do you generally go for vacations?"

    VACATION_DAYS = "How long is your vacation per trip?"

    CLIMATE = "What's the climate there like?"


# =========================================================
# CREATE QUESTIONNAIRE ANSWERS
# =========================================================
class QuestionnaireAnswerCreate(BaseModel):
    # =====================================================
    # HOUSEHOLD INFO
    # =====================================================
    num_people: int = Field(ge=0)

    num_children: int = Field(ge=0)

    bedrooms: int = Field(ge=0)

    # =====================================================
    # APPLIANCES
    # =====================================================
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

    # =====================================================
    # PROPERTY DETAILS
    # =====================================================
    home_area: float = Field(gt=0)

    has_pool: bool

    has_garden: bool

    # =====================================================
    # VACATION DETAILS
    # =====================================================
    vacation_month: MonthEnum

    vacation_days: int = Field(ge=0)

    climate: ClimateEnum


# =========================================================
# UPDATE QUESTIONNAIRE ANSWERS
# =========================================================
class QuestionnaireAnswerUpdate(BaseModel):
    # =====================================================
    # HOUSEHOLD INFO
    # =====================================================
    num_people: Optional[int] = Field(default=None, ge=0)

    num_children: Optional[int] = Field(default=None, ge=0)

    bedrooms: Optional[int] = Field(default=None, ge=0)

    # =====================================================
    # APPLIANCES
    # =====================================================
    has_ac: Optional[bool] = None

    has_geyser: Optional[bool] = None

    has_iron: Optional[bool] = None

    has_washing_machine: Optional[bool] = None

    has_dishwasher: Optional[bool] = None

    has_induction: Optional[bool] = None

    has_microwave: Optional[bool] = None

    has_kettle: Optional[bool] = None

    has_vacuum: Optional[bool] = None

    has_room_heater: Optional[bool] = None

    # =====================================================
    # PROPERTY DETAILS
    # =====================================================
    home_area: Optional[float] = None

    has_pool: Optional[bool] = None

    has_garden: Optional[bool] = None

    # =====================================================
    # VACATION DETAILS
    # =====================================================
    vacation_month: Optional[MonthEnum] = None

    vacation_days: Optional[int] = Field(default=None, ge=0)

    climate: Optional[ClimateEnum] = None