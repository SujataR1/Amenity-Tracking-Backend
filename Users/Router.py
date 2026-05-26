from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Response,
    Header,
    Depends,
    File,
    UploadFile,
)

from Utility_Methods.Utility_Methods import verify_jwt

from Users.Data_Schemas import (
    UserCreate,
    LoginData,
    UserUpdate,
    Toggle2FARequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    TwoFARequest,
    OTPRequest,
)

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
    toggle_2fa_status,
    get_2fa_status,
    get_user_data,
    upload_profile_picture,
    get_profile_picture,
)

User_Router = APIRouter()


# =========================================================
# SIGNUP
# =========================================================
@User_Router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(user: UserCreate):
    new_user = await create_user(user)
    return new_user


# =========================================================
# LOGIN
# FIXED: removed wrong tuple unpacking
# =========================================================
@User_Router.post("/login", status_code=status.HTTP_200_OK)
async def login_user(response: Response, login_data: LoginData):

    result = await authenticate_user(
        email=login_data.email,
        password=login_data.password
    )

    response.headers["Authorization"] = f"Bearer {result['token']}"

    return {
        "message": result["message"],
        "user": result["user"]
    }


# =========================================================
# LOGOUT
# =========================================================
@User_Router.post("/logout")
async def logout_user_endpoint(
    authorization: str = Header(None),
    payload: dict = Depends(verify_jwt),
):

    if not authorization:
        raise HTTPException(
            status_code=400,
            detail="Authorization header missing"
        )

    return await logout_user(authorization, payload)


# =========================================================
# UPDATE USER
# =========================================================
@User_Router.patch("/update")
async def update_user_endpoint(
    update_data: UserUpdate,
    payload=Depends(verify_jwt)
):

    return await update_user(
        update_data.model_dump(exclude_unset=True),
        payload
    )


# =========================================================
# DELETE USER
# =========================================================
@User_Router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    authorization: str = Header(None),
    payload: dict = Depends(verify_jwt),
):

    return await delete_user(payload, authorization)


# =========================================================
# 2FA STATUS
# FIXED: removed variable shadowing "status"
# =========================================================
@User_Router.get("/2fa/status", status_code=status.HTTP_200_OK)
async def get_2fa_status_endpoint(payload=Depends(verify_jwt)):

    if not payload:
        raise HTTPException(
            status_code=400,
            detail="Login required"
        )

    result = await get_2fa_status(payload)
    return result


# =========================================================
# 2FA TOGGLE
# =========================================================
@User_Router.patch("/2fa/toggle", status_code=status.HTTP_200_OK)
async def toggle_2fa_status_endpoint(
    request: Toggle2FARequest,
    payload=Depends(verify_jwt)
):

    if not payload:
        raise HTTPException(
            status_code=400,
            detail="Login required"
        )

    result = await toggle_2fa_status(
        payload,
        entered_password=request.entered_password
    )

    return result


# =========================================================
# 2FA VERIFY LOGIN
# FIXED: correct return handling
# =========================================================
@User_Router.post("/2fa/verify", status_code=status.HTTP_200_OK)
async def verify_2fa_login_endpoint(
    response: Response,
    two_fa_data: TwoFARequest
):

    result = await verify_2fa_and_login(
        two_fa_data.email,
        two_fa_data.otp_code
    )

    response.headers["Authorization"] = f"Bearer {result['token']}"

    return {
        "message": result["message"],
        "user": result["user"]
    }


# =========================================================
# OTP GENERATE
# FIXED: do NOT assume otp is returned
# =========================================================
@User_Router.post("/otp/generate", status_code=status.HTTP_200_OK)
async def generate_otp_endpoint(otp_request: OTPRequest):

    result = await generate_and_send_otp(
        otp_request.email,
        otp_request.purpose
    )

    return result


# =========================================================
# EMAIL OTP VERIFY
# FIXED: correct field usage
# =========================================================
@User_Router.post("/otp/verify/email", status_code=status.HTTP_200_OK)
async def verify_email_otp_endpoint(
    otp_request: OTPRequest,
    payload=Depends(verify_jwt)
):

    result = await verify_email_otp(
        payload,
        otp_request.otp_code
    )

    if result:
        return {"message": "Email verification successful"}

    raise HTTPException(
        status_code=400,
        detail="Invalid OTP"
    )


# =========================================================
# PASSWORD RESET REQUEST
# =========================================================
@User_Router.post("/password-reset/request", status_code=status.HTTP_200_OK)
async def request_password_reset(request_data: PasswordResetRequest):

    return await request_password_reset_by_email(request_data.email)


# =========================================================
# PASSWORD RESET CONFIRM
# =========================================================
@User_Router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
async def reset_password_endpoint(request_data: PasswordResetConfirm):

    return await reset_password(
        email=request_data.email,
        new_password=request_data.new_password,
        otp_code=request_data.otp_code
    )


# =========================================================
# PROFILE
# =========================================================
@User_Router.get("/profile", status_code=status.HTTP_200_OK)
async def get_user_profile(payload=Depends(verify_jwt)):

    user_data = await get_user_data(payload)

    return user_data


# =========================================================
# PROFILE PICTURE UPLOAD
# FIXED: removed useless file_path check
# =========================================================
@User_Router.post("/profile-picture/upload", status_code=status.HTTP_201_CREATED)
async def create_profile_picture(
    payload: dict = Depends(verify_jwt),
    file: UploadFile = File(...)
):

    result = await upload_profile_picture(
        file=file,
        payload=payload
    )

    return result


# =========================================================
# PROFILE PICTURE GET
# =========================================================
@User_Router.get("/profile-picture", status_code=status.HTTP_200_OK)
async def get_profile_picture_endpoint(payload=Depends(verify_jwt)):

    result = await get_profile_picture(payload)

    return result