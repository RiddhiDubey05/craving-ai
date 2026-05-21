"""
Email service using Resend API.
Resend is a production-grade email provider (https://resend.com).
Free tier: 3,000 emails/month, 100/day — no personal credentials needed.

Setup:
  1. Sign up at https://resend.com (free)
  2. Create an API key in the dashboard
  3. Set RESEND_API_KEY=re_xxxx in your .env file
"""

import requests
from backend.config import get_settings
from backend.utils.logger import app_logger

RESEND_API_URL = "https://api.resend.com/emails"


def send_otp_email(recipient_email: str, otp_code: str) -> bool:
    """
    Sends an OTP email via Resend API.
    Returns True on success, False on any failure.
    Logs detailed error info for debugging.
    """
    settings = get_settings()
    api_key = settings.resend_api_key
    from_email = settings.resend_from_email

    # ── Guard: no API key ──────────────────────────────────────────────────
    if not api_key:
        app_logger.error(
            "RESEND_API_KEY is not set in .env. "
            "Sign up at https://resend.com, create an API key, and add it to .env."
        )
        return False

    # ── Build email payload ────────────────────────────────────────────────
    subject = "Your CravingAI Login Code"
    html_body = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                max-width: 480px; margin: 0 auto; padding: 32px 24px;
                background: #0f0f0f; border-radius: 16px; color: #fff;">

      <div style="text-align: center; margin-bottom: 28px;">
        <h1 style="font-size: 24px; font-weight: 700; margin: 0;
                   background: linear-gradient(135deg, #FF6B35, #FF9A5C);
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
          🍽️ CravingAI
        </h1>
      </div>

      <p style="font-size: 15px; color: #aaa; margin: 0 0 8px;">Your login code is:</p>

      <div style="background: #1a1a1a; border: 1px solid #FF6B35;
                  border-radius: 12px; padding: 24px; text-align: center; margin: 16px 0;">
        <span style="font-size: 42px; font-weight: 800; letter-spacing: 12px;
                     color: #FF6B35; font-family: monospace;">
          {otp_code}
        </span>
      </div>

      <p style="font-size: 13px; color: #666; margin: 16px 0 0; text-align: center;">
        ⏱ Valid for <strong style="color: #aaa;">10 minutes</strong> &nbsp;·&nbsp;
        🔒 Do not share this code with anyone
      </p>

      <hr style="border: none; border-top: 1px solid #222; margin: 28px 0;" />

      <p style="font-size: 12px; color: #444; text-align: center; margin: 0;">
        If you didn't request this, you can safely ignore this email.
      </p>
    </div>
    """

    plain_body = (
        f"Your CravingAI login code is: {otp_code}\n\n"
        f"Valid for 10 minutes. Do not share this code with anyone.\n\n"
        f"If you didn't request this, ignore this email."
    )

    payload = {
        "from": from_email,
        "to": [recipient_email],
        "subject": subject,
        "html": html_body,
        "text": plain_body,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # ── Send via Resend ────────────────────────────────────────────────────
    try:
        response = requests.post(
            RESEND_API_URL,
            json=payload,
            headers=headers,
            timeout=10,
        )

        if response.status_code in (200, 201):
            resp_data = response.json()
            email_id = resp_data.get("id", "unknown")
            app_logger.info(
                f"✅ OTP email sent successfully to {recipient_email} "
                f"(Resend ID: {email_id})"
            )
            return True
        else:
            app_logger.error(
                f"❌ Resend API error for {recipient_email}: "
                f"HTTP {response.status_code} — {response.text}"
            )
            return False

    except requests.exceptions.Timeout:
        app_logger.error(
            f"❌ Resend API timeout sending to {recipient_email}. "
            "Check network connectivity."
        )
        return False
    except requests.exceptions.ConnectionError:
        app_logger.error(
            f"❌ Cannot reach Resend API. "
            "Check internet connection or firewall settings."
        )
        return False
    except Exception as e:
        app_logger.error(
            f"❌ Unexpected error sending OTP email to {recipient_email}: {e}"
        )
        return False
