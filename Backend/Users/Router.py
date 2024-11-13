from fastapi import APIRouter, HTTPException, status, Response, Header, Depends
from Utility_Methods.Utility_Methods import verify_jwt
from Users.Data_Schemas import UserCreate, LoginData, UserUpdate, OTPTypeEnum
from Users.Methods import (
    create_user,
    authenticate_user,
    logout_user,
    update_user,
    delete_user,
    verify_2fa_and_login,
    generate_and_send_otp,
    verify_email_otp,
    request_password_reset_by_email,
    reset_password,
)

User_Router = APIRouter()


@User_Router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(user: UserCreate):
    """
    Endpoint to create a new user. Expects JSON body with name, email, password, and other details.
    """
    new_user = await create_user(user)
    if "error" in new_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=new_user["error"]
        )
    return new_user


@User_Router.post("/login", status_code=status.HTTP_200_OK)
async def login_user(
    response: Response, login_data: LoginData, otp_code: int = None
):
    """
    Login endpoint that validates user credentials. If 2FA is enabled, requires OTP.
    """
    try:
        user, token_or_message = await authenticate_user(
            login_data.email, login_data.password, otp_code=otp_code
        )
        if isinstance(token_or_message, dict):  # If OTP generation message
            return token_or_message
        response.headers["Authorization"] = f"Bearer {token_or_message}"
        return {"message": f"User {user.name} has successfully logged in"}
    except HTTPException as e:
        raise e


@User_Router.post("/logout")
async def logout_user_endpoint(
    authorization: str = Header(None), payload=Depends(verify_jwt)
):
    """
    Logs out the user by blacklisting the JWT token.
    """
    if not authorization:
        raise HTTPException(status_code=400, detail="Cannot verify user")
    return await logout_user(authorization, payload)


@User_Router.patch("/update")
async def update_user_endpoint(
    update_data: UserUpdate, payload=Depends(verify_jwt)
):
    """
    Updates user details based on the user ID extracted from JWT.
    """
    return await update_user(
        update_data.model_dump(exclude_unset=True), payload
    )


@User_Router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    authorization: str = Header(None), payload=Depends(verify_jwt)
):
    """
    Endpoint to delete a user and blacklist the token.
    """
    return await delete_user(payload, authorization)


@User_Router.post("/2fa/verify", status_code=status.HTTP_200_OK)
async def verify_2fa_login_endpoint(
    response: Response, email: str, otp_code: int
):
    """
    Verifies the OTP for 2FA and, if valid, logs the user in by returning a JWT token.
    """
    token, user = await verify_2fa_and_login(email, otp_code)
    response.headers["Authorization"] = f"Bearer {token}"
    return {
        "message": f"2FA verification successful. User {user.name} is now logged in."
    }


@User_Router.post("/otp/generate", status_code=status.HTTP_200_OK)
async def generate_otp_endpoint(email: str, purpose: OTPTypeEnum):
    """
    Generates an OTP for a specified purpose (2FA, email verification, password reset).
    """
    otp = await generate_and_send_otp(email, purpose)
    return {
        "message": f"OTP for {purpose.value} generated successfully.",
        "otp_code": otp,
    }


@User_Router.post("/otp/verify/email", status_code=status.HTTP_200_OK)
async def verify_email_otp_endpoint(
    otp_code: int, payload=Depends(verify_jwt)
):
    """
    Verifies the OTP for email verification and updates the user's email_verified status.
    """
    verified = await verify_email_otp(payload, otp_code)
    if verified:
        return {"message": "Email verification successful"}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired OTP for email verification",
    )


@User_Router.post("/password-reset/request", status_code=status.HTTP_200_OK)
async def request_password_reset(email: str):
    """
    Requests a password reset. Sends a reset token to the user's email.
    """
    reset_token = await request_password_reset_by_email(email)
    return {
        "message": "Password reset token generated",
        "reset_token": reset_token,
    }


@User_Router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
async def reset_password_endpoint(token: str, new_password: str):
    """
    Confirms the password reset by validating the reset token and updating the user's password.
    """
    return await reset_password(token, new_password)
