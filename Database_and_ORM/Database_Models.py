from tortoise import fields
from tortoise.models import Model
from Users.Data_Schemas import RoleEnum, OTPTypeEnum
from Questionnaire.Data_Schemas import MonthEnum


class User(Model):
    id = fields.UUIDField(pk=True)  # Primary key field
    name = fields.CharField(max_length=100)
    email = fields.CharField(max_length=100, unique=True)
    email_verified = fields.BooleanField(default=False)
    address = fields.CharField(max_length=500)
    pin_code = fields.BigIntField(max_length=6)
    phone_number = fields.BigIntField
    phone_number_verified = fields.BooleanField(default=False)
    password = fields.CharField(max_length=128)
    two_fa_status = fields.BooleanField(default=False)
    role = fields.CharEnumField(RoleEnum, default=RoleEnum.user)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    profile_picture_path = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "User"


class Blacklisted_Tokens(Model):
    Blacklisted_Tokens = fields.CharField(pk=True, max_length=255)

    class Meta:
        table = "Blacklisted_Tokens"


class OTP(Model):
    otp_code = fields.CharField(
        max_length=8, pk=True
    )  # Primary key for uniqueness
    user = fields.ForeignKeyField(
        "models.User", related_name="otps", on_delete="CASCADE"
    )
    purpose = fields.CharEnumField(
        OTPTypeEnum, description="Purpose of the OTP"
    )
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
    nine = (
        fields.BooleanField()
    )  # "Are you using an induction oven, hot plate, etc.?"
    ten = (
        fields.BooleanField()
    )  # "Are you using a microwave oven, grill, etc.?"
    eleven = fields.BooleanField()  # "Are you using a water heater kettle?"
    twelve = fields.BooleanField()  # "Are you using a vacuum cleaner?"
    thirteen = fields.BooleanField()  # "Are you using a room heater?"
    fourteen = (
        fields.FloatField()
    )  # "Can you estimate the surface area of your home?"
    fifteen = (
        fields.BooleanField()
    )  # "If you are living in a villa, do you have a swimming pool?"
    sixteen = (
        fields.BooleanField()
    )  # "If you are living in a villa, do you have a garden?"
    seventeen = fields.CharEnumField(
        MonthEnum
    )  # "During which month do you generally go for vacations?"
    eighteen = fields.IntField()  # "How long is your vacation per trip?"

    class Meta:
        table = "questionnaire_answers"


class APIActivityLog(Model):
    """
    Model to track API activity details such as IP address, request, response,
    endpoint, timings, and errors.
    """

    id = fields.UUIDField(pk=True)
    requesting_ip = fields.CharField(
        max_length=45
    )  # Supports both IPv4 and IPv6
    request = fields.JSONField()  # Stores request data in JSON format
    response = fields.JSONField(
        null=True
    )  # Stores response data in JSON format, can be null if there's an error
    endpoint_hit = fields.CharField(
        max_length=255
    )  # The endpoint that was accessed
    time_taken = (
        fields.FloatField()
    )  # Time taken to process the request, in seconds
    time_requested = fields.DatetimeField(
        auto_now_add=True
    )  # Time the request was received
    time_responded = fields.DatetimeField(
        null=True
    )  # Time the response was sent, can be null if an error occurs
    error = fields.TextField(null=True)  # Error message, if any
    error_location = fields.CharField(
        max_length=255, null=True
    )  # Location of the error, e.g., filename and line number

    class Meta:
        table = "api_activity_log"
        ordering = ["-time_requested"]


class Admin(Model):
    id = fields.UUIDField(pk=True, max_length=6)
    role = fields.CharEnumField(
        RoleEnum,
        max_length=5,
        default=RoleEnum.admin,
        description="Role of the admin",
    )
    name = fields.CharField(max_length=255, description="Name of the admin")
    number_of_users = fields.IntField(
        default=0, description="Automatically updates"
    )
    email = fields.CharField(max_length=100, unique=True)
    email_verified = fields.BooleanField(default=False)
    password = fields.CharField(
        max_length=255, description="Hashed password for admin login"
    )
    two_fa_status = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(
        auto_now_add=True, description="Timestamp when the admin was created"
    )
    updated_at = fields.DatetimeField(
        auto_now=True, description="Timestamp when the admin was last updated"
    )

    class Meta:
        table = "admin"
        ordering = ["created_at"]


class ElectricityConsumption(Model):
    id = fields.UUIDField(pk=True)  # Primary key field, auto-generated UUID
    user = fields.ForeignKeyField(
        "models.User",
        related_name="electricity_consumption",
        on_delete=fields.CASCADE,
    )  # Relates to User model
    month = fields.CharEnumField(
        MonthEnum
    )  # Integer field to store the month (1-12)
    year = fields.IntField()  # Integer field to store the year
    electricity_consumption = (
        fields.FloatField()
    )  # Field to store electricity consumption in kWh
    created_at = fields.DatetimeField(
        auto_now_add=True
    )  # Automatically adds timestamp when created
    updated_at = fields.DatetimeField(
        auto_now=True
    )  # Automatically updates timestamp when modified

    class Meta:
        table = "electricity_consumption"
        unique_together = (
            "user",
            "month",
            "year",
        )  # Ensures unique entries for a user for a specific month and year


class WaterConsumption(Model):
    id = fields.UUIDField(pk=True)  # Primary key field, auto-generated UUID
    user = fields.ForeignKeyField(
        "models.User",
        related_name="water_consumption",
        on_delete=fields.CASCADE,
    )  # Relates to User model
    month = fields.CharEnumField(
        MonthEnum
    )  # Integer field to store the month (1-12)
    year = fields.IntField()  # Integer field to store the year
    water_consumption = (
        fields.FloatField()
    )  # Field to store electricity consumption in kWh
    created_at = fields.DatetimeField(
        auto_now_add=True
    )  # Automatically adds timestamp when created
    updated_at = fields.DatetimeField(
        auto_now=True
    )  # Automatically updates timestamp when modified

    class Meta:
        table = "water_consumption"
        unique_together = (
            "user",
            "month",
            "year",
        )  # Ensures unique entries for a user for a specific month and year


class GasConsumption(Model):
    id = fields.UUIDField(pk=True)  # Primary key field, auto-generated UUID
    user = fields.ForeignKeyField(
        "models.User",
        related_name="gas_consumption",
        on_delete=fields.CASCADE,
    )  # Relates to User model
    month = fields.CharEnumField(
        MonthEnum
    )  # Integer field to store the month (1-12)
    year = fields.IntField()  # Integer field to store the year
    gas_consumption = (
        fields.FloatField()
    )  # Field to store electricity consumption in kWh
    created_at = fields.DatetimeField(
        auto_now_add=True
    )  # Automatically adds timestamp when created
    updated_at = fields.DatetimeField(
        auto_now=True
    )  # Automatically updates timestamp when modified

    class Meta:
        table = "gas_consumption"
        unique_together = (
            "user",
            "month",
            "year",
        )  # Ensures unique entries for a user for a specific month and year


class FuelConsumption(Model):
    id = fields.UUIDField(pk=True)  # Primary key field, auto-generated UUID
    user = fields.ForeignKeyField(
        "models.User",
        related_name="fuel_consumption",
        on_delete=fields.CASCADE,
    )  # Relates to User model
    month = fields.CharEnumField(
        MonthEnum
    )  # Integer field to store the month (1-12)
    year = fields.IntField()  # Integer field to store the year
    fuel_consumption = (
        fields.FloatField()
    )  # Field to store electricity consumption in kWh
    created_at = fields.DatetimeField(
        auto_now_add=True
    )  # Automatically adds timestamp when created
    updated_at = fields.DatetimeField(
        auto_now=True
    )  # Automatically updates timestamp when modified

    class Meta:
        table = "fuel_consumption"
        unique_together = (
            "user",
            "month",
            "year",
        )  # Ensures unique entries for a user for a specific month and year
