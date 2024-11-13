from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

from enum import Enum


class QuestionnaireFields(Enum):
    ONE = "one"
    TWO = "two"
    THREE = "three"
    FOUR = "four"
    FIVE = "five"
    SIX = "six"
    SEVEN = "seven"
    EIGHT = "eight"
    NINE = "nine"
    TEN = "ten"
    ELEVEN = "eleven"
    TWELVE = "twelve"
    THIRTEEN = "thirteen"
    FOURTEEN = "fourteen"
    FIFTEEN = "fifteen"
    SIXTEEN = "sixteen"
    SEVENTEEN = "seventeen"
    EIGHTEEN = "eighteen"


class QuestionnaireEnum(str, Enum):
    ONE = "How many people live in the home?"
    TWO = "How many people under 18 live in the home?"
    THREE = "How many bedrooms are there in your home?"
    FOUR = "Are you using air conditioning?"
    FIVE = "Are you using a geyser?"
    SIX = "Are you using an electric iron?"
    SEVEN = "Are you using a washing machine?"
    EIGHT = "Are you using a dishwasher?"
    NINE = "Are you using an induction oven, hot plate, etc.?"
    TEN = "Are you using a microwave oven, grill, etc.?"
    ELEVEN = "Are you using a water heater kettle?"
    TWELVE = "Are you using a vacuum cleaner?"
    THIRTEEN = "Are you using a room heater?"
    FOURTEEN = "Can you estimate the surface area of your home?"
    FIFTEEN = "If you are living in a villa, do you have a swimming pool?"
    SIXTEEN = "If you are living in a villa, do you have a garden?"
    SEVENTEEN = "During which month do you generally go for vacations?"
    EIGHTEEN = "How long is your vacation per trip?"


class QuestionnaireAnswerCreate(BaseModel):
    one: int = Field(ge=0)  # How many people live in the home?
    two: int = Field(ge=0)  # How many people under 18 live in the home?
    three: int = Field(ge=0)  # How many bedrooms are there in your home?
    four: bool  # Are you using air conditioning?
    five: bool  # Are you using a geyser?
    six: bool  # Are you using an electric iron?
    seven: bool  # Are you using a washing machine?
    eight: bool  # Are you using a dishwasher?
    nine: bool  # Are you using an induction oven, hot plate, etc.?
    ten: bool  # Are you using a microwave oven, grill, etc.?
    eleven: bool  # Are you using a water heater kettle?
    twelve: bool  # Are you using a vacuum cleaner?
    thirteen: bool  # Are you using a room heater?
    fourteen: float  # Estimated surface area of your home (in sq units)
    fifteen: bool  # Do you have a swimming pool if living in a villa?
    sixteen: bool  # Do you have a garden if living in a villa?
    seventeen: str  # Month(s) generally taken for vacation
    eighteen: int  # Duration of vacation per trip (in days)


class QuestionnaireAnswerUpdate(BaseModel):
    one: Optional[int] = Field(ge=0)  # How many people live in the home?
    two: Optional[int] = Field(ge=0)  # How many people under 18 live in the home?
    three: Optional[int] = Field(ge=0)  # How many bedrooms are there in your home?
    four: Optional[bool]  # Are you using air conditioning?
    five: Optional[bool]  # Are you using a geyser?
    six: Optional[bool]  # Are you using an electric iron?
    seven: Optional[bool]  # Are you using a washing machine?
    eight: Optional[bool]  # Are you using a dishwasher?
    nine: Optional[bool]  # Are you using an induction oven, hot plate, etc.?
    ten: Optional[bool]  # Are you using a microwave oven, grill, etc.?
    eleven: Optional[bool]  # Are you using a water heater kettle?
    twelve: Optional[bool]  # Are you using a vacuum cleaner?
    thirteen: Optional[bool]  # Are you using a room heater?
    fourteen: Optional[bool]  # Estimated surface area of your home (in sq units)
    fifteen: Optional[bool]  # Do you have a swimming pool if living in a villa?
    sixteen: Optional[bool]  # Do you have a garden if living in a villa?
    seventeen: Optional[bool]  # Month(s) generally taken for vacation
    eighteen: Optional[int]  # Duration of vacation per trip (in days)
