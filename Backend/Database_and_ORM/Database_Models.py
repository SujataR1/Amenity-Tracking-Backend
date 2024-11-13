from tortoise import fields
from tortoise.models import Model
from Users.Data_Schemas import RoleEnum, MartialStatusEnum, OTPTypeEnum

# from Methods import validate_pan


class User(Model):
    id = fields.UUIDField(pk=True)  # Primary key field
    name = fields.CharField(max_length=100)
    email = fields.CharField(max_length=100, unique=True)
    email_verified = fields.BooleanField(default=False)
    address = fields.CharField(max_length=500)
    pin_code = fields.BigIntField(max_length=6)
    phone_number = fields.BigIntField
    phone_number_verified = fields.BooleanField(default=False)
    aadhar_card_number = fields.BigIntField(length=12, unique=True)
    pan = fields.CharField(max_length=10)
    occupation = fields.CharField(max_length=30)
    martial_status = fields.CharEnumField(
        MartialStatusEnum, default=MartialStatusEnum.unmarried
    )
    annual_income_bar = fields.BigIntField()
    password = fields.CharField(max_length=128)
    two_fa_status = fields.BooleanField(default=False)
    role = fields.CharEnumField(RoleEnum, default=RoleEnum.user)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "User"


class Blacklisted_Tokens(Model):
    Blacklisted_Tokens = fields.CharField(pk=True, max_length=255)

    class Meta:
        table = "Blacklisted_Tokens"


class OTP(Model):
    otp_code = fields.CharField(max_length=8, pk=True)  # Primary key for uniqueness
    user = fields.ForeignKeyField(
        "models.User", related_name="otps", on_delete="CASCADE"
    )
    purpose = fields.CharEnumField(OTPTypeEnum, description="Purpose of the OTP")
    expiration = fields.DatetimeField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "otp"


class QuestionnaireAnswers(Model):
    id = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField(
        "models.User",
        related_name="questionnaire_answers",
        on_delete=fields.CASCADE,
    )
    one = fields.IntField()  # "How many people live in the home?"
    two = fields.IntField()  # "How many people under 18 live in the home?"
    three = fields.IntField()  # "How many bedrooms are there in your home?"
    four = fields.BooleanField()  # "Are you using air conditioning?"
    five = fields.BooleanField()  # "Are you using a geyser?"
    six = fields.BooleanField()  # "Are you using an electric iron?"
    seven = fields.BooleanField()  # "Are you using a washing machine?"
    eight = fields.BooleanField()  # "Are you using a dishwasher?"
    nine = fields.BooleanField()  # "Are you using an induction oven, hot plate, etc.?"
    ten = fields.BooleanField()  # "Are you using a microwave oven, grill, etc.?"
    eleven = fields.BooleanField()  # "Are you using a water heater kettle?"
    twelve = fields.BooleanField()  # "Are you using a vacuum cleaner?"
    thirteen = fields.BooleanField()  # "Are you using a room heater?"
    fourteen = fields.FloatField()  # "Can you estimate the surface area of your home?"
    fifteen = (
        fields.BooleanField()
    )  # "If you are living in a villa, do you have a swimming pool?"
    sixteen = (
        fields.BooleanField()
    )  # "If you are living in a villa, do you have a garden?"
    seventeen = fields.CharField(
        max_length=50
    )  # "During which month do you generally go for vacations?"
    eighteen = fields.IntField()  # "How long is your vacation per trip?"

    class Meta:
        table = "questionnaire_answers"
