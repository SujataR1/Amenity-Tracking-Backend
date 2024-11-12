from tortoise import fields
from tortoise.models import Model
from Users.Data_Schemas import RoleEnum, MartialStatusEnum, OTPTypeEnum
# from Methods import validate_pan


class User(Model):
    id = fields.UUIDField(pk=True)  # Primary key field
    name = fields.CharField(max_length=100)
    email = fields.CharField(max_length=100, unique=True)
    email = email_verified = fields.BooleanField(default=False)
    phone_number = fields.BigIntField
    phone_number_verified = fields.BooleanField(default=False)
    aadhar_card_number = fields.BigIntField(length=12, unique=True)
    pan = fields.CharField(length=10)
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
    otp_code = fields.CharField(
        max_length=6, pk=True
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
