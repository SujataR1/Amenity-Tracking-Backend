from tortoise import fields
from tortoise.models import Model
from Backend.Users.Data_Schemas import RoleEnum, MartialStatusEnum
from Methods import validate_pan


class User(Model):
    id = fields.UUIDField(pk=True)  # Primary key field
    name = fields.CharField(max_length=100)
    email = fields.CharField(max_length=100, unique=True)
    phone_number = fields.BigIntField
    aadhar_card_number = fields.BigIntField(length=12, unique=True)
    pan = fields.CharField(length=10, validators=[validate_pan])
    occupation = fields.CharField(max_length=30)
    martial_status = fields.CharEnumField(
        MartialStatusEnum, default=MartialStatusEnum.unmarried
    )
    annual_income_bar = fields.BigIntField()
    password = fields.CharField(max_length=128)
    role = fields.CharEnumField(RoleEnum, default=RoleEnum.user)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "User"


class Blacklisted_Tokens(Model):
    Blacklisted_Tokens = fields.CharField(pk=True, max_length=255)

    class Meta:
        table = "Blacklisted_Tokens"
