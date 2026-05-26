email_templates = {
    "password_reset": {
        "subject": "Password Reset Request for {username}",
        "body": (
            "Hello {username},\n\n"
            "You requested a password reset. Use the OTP below to reset your password:\n"
            "{otp_code}\n\n"
            "This OTP is valid for 10 minutes.\n\n"
            "If you did not request this, please ignore this email."
        ),
    },

    "2fa_verification": {
        "subject": "Your 2FA Verification Code",
        "body": (
            "Hello {username},\n\n"
            "Your 2FA verification code is:\n"
            "{otp_code}\n\n"
            "Please enter this code to complete your login process.\n"
            "This code is valid for 10 minutes.\n\n"
            "If you did not attempt to log in, you can safely ignore this email."
        ),
    },

    "email_verification": {
        "subject": "Verify Your Email Address",
        "body": (
            "Hello {username},\n\n"
            "Thank you for signing up. Please use the OTP below to verify your email address:\n"
            "{otp_code}\n\n"
            "This OTP will expire in 10 minutes.\n\n"
            "If you did not create this account, please ignore this email."
        ),
    },
}