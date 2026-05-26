import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from decouple import config
from Comms.Templates import email_templates

# Load environment variables
EMAIL_HOST = config("EMAIL_HOST")
EMAIL_PORT = config("EMAIL_PORT", cast=int)
EMAIL_USER = config("EMAIL_USER")
EMAIL_PASSWORD = config("EMAIL_PASSWORD")


# -----------------------------------------------------
# INTERNAL SYNC FUNCTION (REAL SMTP WORK)
# -----------------------------------------------------
def _send_email_sync(to_email: str, subject: str, body: str) -> bool:
    try:
        # Set up SMTP server with timeout
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)

        # Construct email
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain", "utf-8"))

        # Send email
        server.sendmail(EMAIL_USER, to_email, msg.as_string())

        return True

    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

    finally:
        try:
            server.quit()
        except:
            pass


# -----------------------------------------------------
# ASYNC WRAPPER (NON-BLOCKING FASTAPI SAFE)
# -----------------------------------------------------
async def send_email(to_email: str, subject: str, body: str) -> bool:
    return await asyncio.to_thread(
        _send_email_sync,
        to_email,
        subject,
        body
    )


# -----------------------------------------------------
# EMAIL TEMPLATE GENERATOR
# -----------------------------------------------------
async def get_email_content(template_name: str, **kwargs) -> dict:
    """
    Generates email subject and body using templates.
    """

    if template_name not in email_templates:
        raise ValueError(f"Invalid email template: {template_name}")

    template = email_templates[template_name]

    try:
        subject = template["subject"].format(**kwargs)
        body = template["body"].format(**kwargs)

    except KeyError as e:
        raise ValueError(f"Missing template variable: {str(e)}")

    return {
        "subject": subject,
        "body": body
    }