from tortoise import fields
from tortoise.models import Model

from Users.Data_Schemas import RoleEnum, OTPTypeEnum
from Questionnaire.Data_Schemas import MonthEnum, ClimateEnum
from enum import Enum
from Database_and_ORM.Enums import ConsumptionType




class ConsumptionType(str, Enum):
    ELECTRICITY = "electricity"
    WATER = "water"
    GAS = "gas"
    FUEL = "fuel"
# =========================================================
# USER MODEL
# =========================================================
class User(Model):
    id = fields.UUIDField(pk=True)

    name = fields.CharField(max_length=100)

    email = fields.CharField(
        max_length=100,
        unique=True,
    )

    email_verified = fields.BooleanField(default=False)

    address = fields.CharField(max_length=500)

    # BigIntField does not support max_length
    pin_code = fields.CharField(max_length=10)

    phone_number = fields.BigIntField()

    phone_number_verified = fields.BooleanField(default=False)

    password = fields.CharField(max_length=128)

    two_fa_status = fields.BooleanField(default=False)

    role = fields.CharEnumField(
        RoleEnum,
        default=RoleEnum.user,
    )

    profile_picture_path = fields.CharField(
        max_length=255,
        null=True,
    )

    created_at = fields.DatetimeField(auto_now_add=True)

    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "user"


# =========================================================
# BLACKLISTED TOKENS
# =========================================================
class Blacklisted_Tokens(Model):
    token = fields.CharField(
        pk=True,
        max_length=500,
    )

    class Meta:
        table = "blacklisted_tokens"


# =========================================================
# OTP MODEL
# =========================================================
class OTP(Model):
    id = fields.UUIDField(pk=True)

    otp_code = fields.CharField(max_length=8)

    user = fields.ForeignKeyField(
        "models.User",
        related_name="otps",
        on_delete=fields.CASCADE,
    )

    purpose = fields.CharEnumField(OTPTypeEnum)

    expiration = fields.DatetimeField()

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "otp"


# =========================================================
# QUESTIONNAIRE ANSWERS
# =========================================================
class QuestionnaireAnswers(Model):
    id = fields.UUIDField(pk=True)

    user = fields.ForeignKeyField(
        "models.User",
        related_name="questionnaire_answers",
        on_delete=fields.CASCADE,
        unique=True,  # one questionnaire per user
    )

    # =====================================================
    # HOUSEHOLD INFORMATION
    # =====================================================
    num_people = fields.IntField()

    num_children = fields.IntField()

    bedrooms = fields.IntField()

    # =====================================================
    # APPLIANCES
    # =====================================================
    has_ac = fields.BooleanField()

    has_geyser = fields.BooleanField()

    has_iron = fields.BooleanField()

    has_washing_machine = fields.BooleanField()

    has_dishwasher = fields.BooleanField()

    has_induction = fields.BooleanField()

    has_microwave = fields.BooleanField()

    has_kettle = fields.BooleanField()

    has_vacuum = fields.BooleanField()

    has_room_heater = fields.BooleanField()

    # =====================================================
    # PROPERTY DETAILS
    # =====================================================
    home_area = fields.FloatField()

    has_pool = fields.BooleanField()

    has_garden = fields.BooleanField()

    # =====================================================
    # VACATION DETAILS
    # =====================================================
    vacation_month = fields.CharEnumField(MonthEnum)

    vacation_days = fields.IntField()

    climate = fields.CharEnumField(ClimateEnum)

    created_at = fields.DatetimeField(auto_now_add=True)

    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "questionnaire_answers"


# =========================================================
# API ACTIVITY LOGGING
# =========================================================
class APIActivityLog(Model):
    id = fields.UUIDField(pk=True)

    requesting_ip = fields.CharField(max_length=45)

    request = fields.JSONField()

    response = fields.JSONField(null=True)

    endpoint_hit = fields.CharField(max_length=255)

    time_taken = fields.FloatField()

    time_requested = fields.DatetimeField(auto_now_add=True)

    time_responded = fields.DatetimeField(null=True)

    error = fields.TextField(null=True)

    error_location = fields.TextField(
        null=True,
    )

    class Meta:
        table = "api_activity_log"
        ordering = ["-time_requested"]


# =========================================================
# ADMIN MODEL
# =========================================================
class Admin(Model):
    id = fields.UUIDField(pk=True)

    role = fields.CharEnumField(
        RoleEnum,
        default=RoleEnum.admin,
    )

    name = fields.CharField(max_length=255)

    number_of_users = fields.IntField(default=0)

    email = fields.CharField(
        max_length=100,
        unique=True,
    )

    email_verified = fields.BooleanField(default=False)

    password = fields.CharField(max_length=255)

    two_fa_status = fields.BooleanField(default=False)

    created_at = fields.DatetimeField(auto_now_add=True)

    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "admin"
        ordering = ["created_at"]


# =========================================================
# ELECTRICITY CONSUMPTION
# =========================================================
class ElectricityConsumption(Model):
    id = fields.UUIDField(pk=True)

    user = fields.ForeignKeyField(
        "models.User",
        related_name="electricity_consumption",
        on_delete=fields.CASCADE,
    )

    month = fields.CharEnumField(MonthEnum)

    year = fields.IntField()

    electricity_consumption = fields.FloatField()

    # =====================================================
    # BILLING
    # =====================================================
    bill_amount = fields.FloatField(null=True)

    billing_days = fields.IntField(default=30)

    # =====================================================
    # ML PREDICTIONS
    # =====================================================
    predicted_consumption = fields.FloatField(null=True)

    predicted_bill = fields.FloatField(null=True)

    created_at = fields.DatetimeField(auto_now_add=True)

    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "electricity_consumption"

        unique_together = (
            "user",
            "month",
            "year",
        )


# =========================================================
# WATER CONSUMPTION
# =========================================================
class WaterConsumption(Model):
    id = fields.UUIDField(pk=True)

    user = fields.ForeignKeyField(
        "models.User",
        related_name="water_consumption",
        on_delete=fields.CASCADE,
    )

    month = fields.CharEnumField(MonthEnum)

    year = fields.IntField()

    water_consumption = fields.FloatField()

    created_at = fields.DatetimeField(auto_now_add=True)

    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "water_consumption"

        unique_together = (
            "user",
            "month",
            "year",
        )


# =========================================================
# GAS CONSUMPTION
# =========================================================
class GasConsumption(Model):
    id = fields.UUIDField(pk=True)

    user = fields.ForeignKeyField(
        "models.User",
        related_name="gas_consumption",
        on_delete=fields.CASCADE,
    )

    month = fields.CharEnumField(MonthEnum)

    year = fields.IntField()

    gas_consumption = fields.FloatField()

    created_at = fields.DatetimeField(auto_now_add=True)

    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "gas_consumption"

        unique_together = (
            "user",
            "month",
            "year",
        )


# =========================================================
# FUEL CONSUMPTION
# =========================================================
class FuelConsumption(Model):
    id = fields.UUIDField(pk=True)

    user = fields.ForeignKeyField(
        "models.User",
        related_name="fuel_consumption",
        on_delete=fields.CASCADE,
    )

    month = fields.CharEnumField(MonthEnum)

    year = fields.IntField()

    fuel_consumption = fields.FloatField()

    created_at = fields.DatetimeField(auto_now_add=True)

    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "fuel_consumption"

        unique_together = (
            "user",
            "month",
            "year",
        )

class ConsumptionRecord(Model):
    id = fields.UUIDField(pk=True)

    user = fields.ForeignKeyField(
        "models.User",
        related_name="consumption_records",
        on_delete=fields.CASCADE,
    )

    type = fields.CharEnumField(ConsumptionType)

    month = fields.CharEnumField(MonthEnum)
    year = fields.IntField()

    consumption_value = fields.FloatField()

    bill_amount = fields.FloatField(null=True)

    predicted_consumption = fields.FloatField(null=True)
    predicted_bill = fields.FloatField(null=True)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "consumption_record"
        unique_together = ("user", "type", "month", "year")