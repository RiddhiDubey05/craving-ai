"""
Email service using Brevo (formerly Sendinblue) Transactional Email API.
Brevo free tier: 300 emails/day, no domain verification needed.
Sends to ANY email address out-of-the-box.

Setup:
  1. Sign up at https://app.brevo.com (free, no credit card)
  2. Go to: Settings → API Keys → Generate API Key
  3. Set BREVO_API_KEY=xkeysib-... in your .env file
  4. Set BREVO_FROM_EMAIL to the email you used to sign up at Brevo
     (it becomes your verified sender automatically)
"""

import requests
from backend.config import get_settings
from backend.utils.logger import app_logger

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def send_otp_email(recipient_email: str, otp_code: str) -> bool:
    """
    Sends an OTP email via Brevo Transactional API.
    Works for ANY recipient email — no domain verification required.
    Returns True on success, False on any failure.
    """
    settings = get_settings()
    api_key = settings.brevo_api_key
    from_email = settings.brevo_from_email
    from_name = settings.brevo_from_name

    # -- Guard: no API key ---------------------------------------------------
    if not api_key:
        app_logger.error(
            "BREVO_API_KEY is not set in .env. "
            "Sign up free at https://app.brevo.com and create an API key."
        )
        return False

    if not from_email:
        app_logger.error(
            "BREVO_FROM_EMAIL is not set in .env. "
            "Set it to the email address you used when signing up at Brevo."
        )
        return False

    # -- Build HTML email body -----------------------------------------------
    html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#0a0a0a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0a;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="480" cellpadding="0" cellspacing="0"
               style="background:#111;border-radius:16px;border:1px solid #222;overflow:hidden;">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#FF6B35,#FF9A5C);padding:28px 32px;text-align:center;">
              <h1 style="margin:0;font-size:22px;font-weight:800;color:#fff;letter-spacing:-0.5px;">
                CravingAI
              </h1>
              <p style="margin:4px 0 0;font-size:13px;color:rgba(255,255,255,0.85);">
                Your personal food intelligence
              </p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:36px 32px;">
              <p style="margin:0 0 8px;font-size:15px;color:#bbb;">
                Here is your one-time login code:
              </p>

              <!-- OTP Box -->
              <div style="background:#1a1a1a;border:1px solid #FF6B35;border-radius:12px;
                          padding:28px;text-align:center;margin:20px 0;">
                <span style="font-size:44px;font-weight:900;letter-spacing:14px;
                             color:#FF6B35;font-family:monospace;display:block;">
                  {otp_code}
                </span>
              </div>

              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="background:#1a1a1a;border-radius:8px;padding:12px 16px;
                              font-size:13px;color:#888;text-align:center;">
                    Valid for <strong style="color:#ccc;">10 minutes</strong>
                    &nbsp;&middot;&nbsp;
                    Do not share this code with anyone
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="border-top:1px solid #1e1e1e;padding:20px 32px;text-align:center;">
              <p style="margin:0;font-size:12px;color:#444;">
                If you didn&rsquo;t request this, you can safely ignore this email.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    plain_body = (
        f"Your CravingAI login code is: {otp_code}\n\n"
        "Valid for 10 minutes. Do not share this code with anyone.\n\n"
        "If you didn't request this, you can safely ignore this email."
    )

    # -- Build Brevo API payload --------------------------------------------
    payload = {
        "sender": {
            "name": from_name,
            "email": from_email,
        },
        "to": [{"email": recipient_email}],
        "subject": "Your CravingAI Login Code",
        "htmlContent": html_body,
        "textContent": plain_body,
    }

    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # -- Send request -------------------------------------------------------
    try:
        response = requests.post(
            BREVO_API_URL,
            json=payload,
            headers=headers,
            timeout=10,
        )

        if response.status_code in (200, 201):
            resp_data = response.json()
            msg_id = resp_data.get("messageId", "unknown")
            app_logger.info(
                f"[OK] OTP email sent via Brevo to {recipient_email} "
                f"(messageId: {msg_id})"
            )
            return True
        else:
            app_logger.error(
                f"[FAIL] Brevo API error for {recipient_email}: "
                f"HTTP {response.status_code} - {response.text}"
            )
            return False

    except requests.exceptions.Timeout:
        app_logger.error(
            f"[FAIL] Brevo API timeout sending to {recipient_email}. "
            "Check network connectivity."
        )
        return False
    except requests.exceptions.ConnectionError:
        app_logger.error(
            "[FAIL] Cannot reach Brevo API. "
            "Check internet connection or firewall settings."
        )
        return False
    except Exception as e:
        app_logger.error(
            f"[FAIL] Unexpected error sending OTP to {recipient_email}: {e}"
        )
        return False
