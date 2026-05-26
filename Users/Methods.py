from Database_and_ORM.Database_Models import (
    User,
    Blacklisted_Tokens,
    OTP,
)
from Users.Data_Schemas import UserCreate, OTPTypeEnum
from Comms.Methods import send_email, get_email_content
from tortoise.exceptions import IntegrityError, DoesNotExist
from typing import Dict
from datetime import datetime, timedelta, timezone
from decouple import config
from fastapi import HTTPException, status, UploadFile
from Utility_Methods.Utility_Methods import (
    create_jwt,
    verify_otp,
    verify_user_password,
    get_hashed_password,
    encode_path_to_base64,
    generate_random_otp,
    get_token_from_authorization_header_value,
)
from Admin.Methods import update_admin_user_count
import os


# =========================================================
# CREATE USER
# =========================================================
async def create_user(user_data: UserCreate):
    hashed_password = await get_hashed_password(user_data.password)

    user = User(
        name=user_data.name,
        email=user_data.email,
        password=hashed_password,
        address=user_data.address,
        pin_code=user_data.pin_code,
        phone_number=user_data.phone_number,
    )

    try:
        await user.save()
        await update_admin_user_count()

        return {
            "message": "Account successfully created",
            "user_id": user.id,
        }

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )


# =========================================================
# AUTHENTICATION
# =========================================================
async def authenticate_user(email: str, password: str):

    user = await User.get_or_none(email=email)

    if not user:
        raise HTTPException(401, "Invalid credentials")

    if not user.password:
        raise HTTPException(401, "Invalid credentials")

    verified = await verify_user_password(
        entered_password=password,
        user_password=user.password,
    )

    if not verified:
        raise HTTPException(401, "Invalid credentials")

    # 2FA FLOW
    if user.two_fa_status:
        await generate_and_send_otp(email, OTPTypeEnum.TWO_FA)

        return {
            "message": "2FA required. OTP sent.",
            "two_fa_required": True,
        }

    token = await create_jwt(
        str(user.id),
        expiration_duration=int(config("JWT_VALIDITY_FOR_NORMAL_SESSIONS")),
    )

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
        },
        "token": token,
        "message": "Login successful",
    }


# =========================================================
# LOGOUT
# =========================================================
async def logout_user(authorization: str, payload: dict):

    if not payload:
        return {"message": "Already logged out"}

    try:
        token = await get_token_from_authorization_header_value(authorization)
        await Blacklisted_Tokens.create(Blacklisted_Tokens=token)

        return {"message": "Successfully logged out"}

    except Exception:
        raise HTTPException(500, "Logout failed")


# =========================================================
# UPDATE USER
# =========================================================
async def update_user(update_data: Dict, payload: dict):

    user_id = payload.get("user_id")

    if not user_id:
        raise HTTPException(401, "Login required")

    user = await User.get_or_none(id=user_id)

    if not user:
        raise HTTPException(404, "User not found")

    changes = {}

    for field, new_value in update_data.items():

        if field == "role":
            continue

        if not hasattr(user, field):
            continue

        old_value = getattr(user, field)

        if old_value != new_value:
            setattr(user, field, new_value)
            changes[field] = {"from": old_value, "to": new_value}

            if field == "email":
                user.email_verified = False
                changes["email_verified"] = {"from": True, "to": False}

    if not changes:
        return {"message": "Nothing was changed"}

    await user.save()

    return {"message": "Updated successfully", "changes": changes}


# =========================================================
# DELETE USER
# =========================================================
async def delete_user(payload: dict, authorization: str):

    user_id = payload.get("user_id")

    if not user_id:
        raise HTTPException(400, "Invalid request")

    user = await User.get_or_none(id=user_id)

    if not user:
        raise HTTPException(404, "User not found")

    token = await get_token_from_authorization_header_value(authorization)

    # blacklist FIRST (safer)
    await Blacklisted_Tokens.create(Blacklisted_Tokens=token)

    await user.delete()
    await update_admin_user_count()

    return {"message": "User deleted successfully"}


# =========================================================
# 2FA LOGIN VERIFY
# =========================================================
async def verify_2fa_and_login(email: str, otp_code: str):

    user = await User.get_or_none(email=email)

    if not user:
        raise HTTPException(404, "User not found")

    verified = await verify_otp(
        user.id,
        otp_code,
        purpose=OTPTypeEnum.TWO_FA,
    )

    if not verified:
        raise HTTPException(401, "Invalid OTP")

    token = await create_jwt(
        str(user.id),
        expiration_duration=int(config("JWT_VALIDITY_FOR_NORMAL_SESSIONS")),
    )

    return {
        "user": {"id": user.id, "email": user.email},
        "token": token,
    }


# =========================================================
# OTP GENERATION
# =========================================================
async def generate_and_send_otp(email: str, purpose: OTPTypeEnum):

    user = await User.get_or_none(email=email)

    if not user:
        raise HTTPException(404, "User not found")

    existing_otp = await OTP.filter(
        user_id=user.id,
        purpose=purpose
    ).first()

    now = datetime.now(timezone.utc)

    if existing_otp and existing_otp.expiration > now:
        otp_code = existing_otp.otp_code
    else:
        otp_code = await generate_random_otp()

        await OTP.filter(user_id=user.id, purpose=purpose).delete()

        await OTP.create(
            otp_code=otp_code,
            user_id=user.id,
            purpose=purpose,
            expiration=now + timedelta(minutes=10),
        )

    if purpose == OTPTypeEnum.TWO_FA:
        content = await get_email_content("2fa_verification", username=user.name, otp_code=otp_code)
    elif purpose == OTPTypeEnum.MAIL_VERIFICATION:
        content = await get_email_content("email_verification", username=user.name, otp_code=otp_code)
    elif purpose == OTPTypeEnum.PASSWORD_RESET:
        content = await get_email_content("password_reset", username=user.name, otp_code=otp_code)
    else:
        raise HTTPException(400, "Invalid OTP purpose")

    sent = await send_email(email, content["subject"], content["body"])

    if not sent:
        raise HTTPException(500, "Failed to send OTP")

    return {"message": "OTP sent successfully"}


# =========================================================
# USER DATA
# =========================================================
async def get_user_data(payload: dict):

    user = await User.get_or_none(id=payload.get("user_id"))

    if not user:
        raise HTTPException(404, "User not found")

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "address": user.address,
        "phone_number": user.phone_number,
        "email_verified": user.email_verified,
    }


# =========================================================
# EMAIL OTP VERIFY
# =========================================================
async def verify_email_otp(payload: dict, otp_code: str):

    user = await User.get_or_none(id=payload.get("user_id"))

    if not user:
        raise HTTPException(404, "User not found")

    verified = await verify_otp(
        user.id,
        otp_code,
        purpose=OTPTypeEnum.MAIL_VERIFICATION,
    )

    if not verified:
        raise HTTPException(400, "Invalid OTP")

    user.email_verified = True
    await user.save()

    return True


# =========================================================
# PASSWORD RESET FLOW
# =========================================================
async def request_password_reset_by_email(email: str):

    user = await User.get_or_none(email=email)

    if not user:
        raise HTTPException(404, "User not found")

    return await generate_and_send_otp(email, OTPTypeEnum.PASSWORD_RESET)


async def reset_password(email: str, otp_code: str, new_password: str):

    user = await User.get_or_none(email=email)

    if not user:
        raise HTTPException(404, "User not found")

    verified = await verify_otp(
        user.id,
        otp_code,
        purpose=OTPTypeEnum.PASSWORD_RESET,
    )

    if not verified:
        raise HTTPException(400, "Invalid OTP")

    user.password = await get_hashed_password(new_password)
    await user.save()

    return {"message": "Password reset successful"}


# =========================================================
# 2FA STATUS
# =========================================================
async def get_2fa_status(payload: dict):

    user = await User.get_or_none(id=payload.get("user_id"))

    if not user:
        raise HTTPException(404, "User not found")

    return {"two_fa_enabled": user.two_fa_status}


# =========================================================
# TOGGLE 2FA
# =========================================================
async def toggle_2fa_status(payload: dict, entered_password: str):

    user = await User.get_or_none(id=payload.get("user_id"))

    if not user:
        raise HTTPException(404, "User not found")

    verified = await verify_user_password(
        entered_password=entered_password,
        user_password=user.password,
    )

    if not verified:
        raise HTTPException(401, "Wrong password")

    if not user.email_verified:
        raise HTTPException(403, "Verify email first")

    user.two_fa_status = not user.two_fa_status
    await user.save()

    return {
        "message": "2FA enabled" if user.two_fa_status else "2FA disabled"
    }


# =========================================================
# PROFILE PICTURE
# =========================================================
async def upload_profile_picture(payload: dict, file: UploadFile):

    user_id = payload.get("user_id")

    directory = os.path.join(
        config("USER_MEDIA_PATH"),
        config("USER_PROFILE_PICTURES_DIRECTORY"),
    )

    os.makedirs(directory, exist_ok=True)

    content = await file.read()

    if len(content) > int(config("MAXIMUM_IMAGE_SIZE")) * 1024 * 1024:
        raise HTTPException(400, "File too large")

    file_path = os.path.join(directory, f"{user_id}_{file.filename}")

    with open(file_path, "wb") as f:
        f.write(content)

    user = await User.get(id=user_id)
    user.profile_picture_path = file_path
    await user.save()

    return {"message": "Uploaded successfully"}


# =========================================================
# GET PROFILE PICTURE
# =========================================================
async def get_profile_picture(payload: dict):

    user = await User.get_or_none(id=payload.get("user_id"))

    if not user:
        raise HTTPException(404, "User not found")

    if not user.profile_picture_path:
        return {"message": "No profile picture"}

    encoded = await encode_path_to_base64(user.profile_picture_path)

    return {"profile_picture": encoded}