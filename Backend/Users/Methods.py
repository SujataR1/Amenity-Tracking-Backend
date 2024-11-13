from Database_and_ORM.Database_Models import User, Blacklisted_Tokens, OTP
from Users.Data_Schemas import UserCreate, OTPTypeEnum
from Comms.Methods import send_email, get_email_content
from tortoise.exceptions import IntegrityError, DoesNotExist
import uuid
from typing import Union
from datetime import datetime, timedelta, timezone
from decouple import config
from fastapi import HTTPException, status
from typing import Dict
from Utility_Methods.Utility_Methods import (
    get_token_from_authorization_header_value,
    create_jwt,
    verify_otp,
    decode_jwt,
    verify_user_password,
    get_hashed_password,
)


async def create_user(user_data: UserCreate) -> Union[User, dict]:
    """
    Creates a new user in the database with hashed password.
    """
    # Hash the password with a salt
    hashed_password = await get_hashed_password(user_data.password)

    user = User(
        name=user_data.name,
        email=user_data.email,  # Defaults to False if not passed
        password=hashed_password,
        address=user_data.address,
        pin_code=user_data.pin_code,
        phone_number=user_data.phone_number,  # Defaults to False if not passed
        aadhar_card_number=user_data.aadhar_card_number,
        pan=user_data.pan,
        occupation=user_data.occupation,
        martial_status=user_data.martial_status,
        annual_income_bar=user_data.annual_income_bar,
    )

    try:
        await user.save()
        return {"message": "Account succesfully created!"}
    except IntegrityError:
        return {"error": "A user with same details already exists."}


async def authenticate_user(email: str, password: str, otp_code: str = None):
    """
    Authenticates a user by email and password.
    If 2FA is enabled, requires OTP verification before generating JWT.
    """
    user = await User.get_or_none(email=email)
    verified = await verify_user_password(
        entered_password=password, user_password=user.password
    )
    if user is None or not verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Check if 2FA is enabled for the user
    if user and verified and user.two_fa_status:
        await generate_and_send_otp(email, purpose=OTPTypeEnum.TWO_FA)
        raise HTTPException(
            status_code=status.HTTP_308_PERMANENT_REDIRECT,
            detail="2FA is enabled. Please verify with OTP.",
        )

    # Generate JWT token if 2FA is not enabled or OTP verification is successful
    token = await create_jwt(str(user.id), expiration_duration=1440)
    return user, token


async def logout_user(authorization: str, payload: dict):
    """
    Logs out the user by adding the token to the blacklist.
    """
    if payload:
        try:
            token = await get_token_from_authorization_header_value(
                authorization
            )
            await Blacklisted_Tokens.create(Blacklisted_Tokens=token)
            return {"message": "Successfully logged out"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Either you have already logged out, or there's something wrong on our end",
            )
    else:
        return "You have already logged out!"


async def update_user(update_data: dict, payload: dict):
    """
    Updates user details based on user_id extracted from JWT token in authorization header.
    """
    # Manually call verify_jwt with the authorization header

    if payload:
        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Please log in",
            )

        # Retrieve the user from the database
        user = await User.get_or_none(id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        changes = {}

        # Iterate through the update data and apply changes
        for field, new_value in update_data.items():
            if field == "role":  # Exclude updating the role field
                continue
            current_value = getattr(user, field)
            if current_value != new_value:
                setattr(user, field, new_value)
                changes[field] = (
                    f"`{field}` updated from `{current_value}` to `{new_value}`"
                )

        if changes:
            await user.save()
            return changes
        else:
            return {"message": "Nothing was changed!"}

    else:
        return "Please login to update your data!"


async def delete_user(payload: dict, authorization: str):
    """
    Deletes a user based on user ID extracted from JWT token and blacklists the token.
    """
    # Extract user_id from payload
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please log in first to delete your account",
        )

    # Find the user and delete
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    await user.delete()

    # Blacklist the token
    token = await get_token_from_authorization_header_value(
        authorization
    )  # Extract the token part from "Bearer <token>"
    await Blacklisted_Tokens.create(Blacklisted_Tokens=token)

    return {"message": "User deleted successfully and token blacklisted"}


async def verify_2fa_and_login(email: str, otp_code: str):
    """
    Verifies the OTP for 2FA and, if valid, generates a JWT token and sets it in the response headers.
    """
    # Retrieve the OTP entry for the user and 2FA purpose
    user = await User.get_or_none(email=email)
    user_name = user.name
    verified = await verify_otp(
        user_name, otp_code, purpose=OTPTypeEnum.TWO_FA
    )

    if verified:
        # Generate JWT token
        token = await create_jwt(user_name, expiration_duration=1440)
        response = token, user
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="2FA Verification Failed",
        )

    return response


async def generate_and_send_otp(email: str, purpose: OTPTypeEnum) -> dict:
    """
    Checks for an existing OTP for the user and purpose. If none exists or it's expired,
    generates a new OTP, stores it, and sends it via email.
    """
    # Look up the user_id based on the email
    try:
        user = await User.get(email=email)
        user_id = user.id
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist.",
        )

    # Look for an existing OTP entry
    existing_otp = await OTP.filter(user_id=user_id, purpose=purpose).first()

    # Check if OTP exists and is still valid
    if existing_otp and existing_otp.expiry > datetime.now(timezone.utc):
        otp_code = existing_otp.otp_code  # Use the existing OTP if valid
    else:
        # Generate a new random 6-digit OTP
        otp_code = str(uuid.uuid4().int)[
            :6
        ]  # Example of a 6-digit random OTP using UUID

        # Invalidate any existing OTPs for this user and purpose
        await OTP.filter(user_id=user_id, purpose=purpose).delete()

        # Attempt to create a new OTP entry
        try:
            otp_entry = OTP(
                otp_code=otp_code,
                user_id=user_id,
                purpose=purpose,
                expiration=datetime.now(timezone.utc)
                + timedelta(minutes=10),  # OTP valid for 10 minutes
            )
            await otp_entry.save()
        except IntegrityError as e:
            # Log detailed error and raise a user-friendly exception
            print(f"Integrity error while saving OTP: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while generating the OTP. Please try again.",
            )
        except Exception as e:
            # General error handling for any unexpected issue
            print(f"Unexpected error while saving OTP: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred.",
            )

    # Prepare the email content
    values = {"username": user.name, "otp_code": otp_code}
    if purpose == OTPTypeEnum.TWO_FA:
        content = await get_email_content("2fa_verification", **values)
    elif purpose == OTPTypeEnum.MAIL_VERIFICATION:
        content = await get_email_content("email_verification", **values)

    # Send the email
    email_sent = await send_email(
        to_email=email, subject=content["subject"], body=content["body"]
    )

    if email_sent:
        return {"message": "OTP sent successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OTP could not be sent.",
        )


async def get_user_data(payload: dict):
    """
    Retrieves user data by user_id, excluding the password field.
    """
    user_id = payload.get("user_data")
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Exclude the password field
    user_data = user.to_dict()
    user_data.pop("password", None)  # Remove the password field if it exists

    return user_data


async def verify_email_otp(payload: Dict, otp_code: str) -> bool:
    """
    Verifies the OTP for email verification. If valid, marks the user's email as verified.
    """
    user_id = payload.get("user_id")
    user = await User.get(id=user_id)

    if await verify_otp(
        otp_code, user_id, purpose=OTPTypeEnum.MAIL_VERIFICATION
    ):
        # Update the user's email_verified status
        user.email_verified = True
        await user.save()
        return True
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired OTP for email verification",
    )


async def request_password_reset_by_email(email: str) -> str:
    """
    Checks if a user exists with the provided email and generates a password reset JWT token.
    """
    # Find user by email
    user = await User.get_or_none(email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with the provided email.",
        )

    # Generate reset token if user exists
    reset_token = await create_jwt(user.id, expiration_duration=30)
    reset_link = f"{config("PASSWORD_RESET_LANDING_PAGE_URL")}/{reset_token}"

    user_name = str(user.name)

    values = {"username": f"{user_name}", "reset_link": f"{reset_link}"}

    content = await get_email_content("password_reset", **values)

    # Send the email
    email_sent = await send_email(
        to_email=email, subject=content["subject"], body=content["body"]
    )
    if email_sent:
        return {"message": "Password reset email sent successfully."}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to send the password reset link",
        )


async def reset_password(token: str, new_password: str):
    payload = await decode_jwt(token)
    user_id = payload.get("user_id")
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    # Hash the new password and update the user's password
    user.password = await get_hashed_password(new_password)
    try:
        await user.save()
        await Blacklisted_Tokens.create(Blacklisted_Tokens=token)
        return {"message": "Password has been reset successfully."}
    except Exception as error:
        await Blacklisted_Tokens.create(Blacklisted_Tokens=token)
        return f"Error resetting password \n Details: {error}"


async def get_2fa_status(payload: dict) -> str:
    """
    Retrieves the current 2FA status for a user.
    """
    user_id = payload.get("user_id")
    user = await User.get_or_none(id=user_id)
    if user.two_fa_status:
        return {"message": "You have 2FA enabled!"}
    elif not user.two_fa_status:
        return {"message": "You have 2FA disabled!"}
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Something wrong happened on our end!",
    )


async def toggle_2fa_status(payload: dict, entered_password: str) -> str:
    """
    Toggles the 2FA status for a user and returns the new status.
    """
    user_id = payload.get("user_id")
    user = await User.get_or_none(id=user_id)
    user_password = str(user.password)
    verified = await verify_user_password(
        entered_password=entered_password, user_password=user_password
    )
    if user and verified:
        user.two_fa_status = not user.two_fa_status
        await user.save()
        if user.two_fa_status:
            return {"message": "You have enabled 2FA!"}
        elif not user.two_fa_status:
            return {"message": "You have disabled 2FA !"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please check the entered password",
        )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Something wrong happened on our end!",
    )
