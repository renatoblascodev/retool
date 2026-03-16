"""Invite service: email sending via SMTP or console fallback."""
from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def send_invite_email(
    *,
    to_email: str,
    app_name: str,
    role: str,
    inviter_name: str | None,
    accept_link: str,
) -> None:
    """Send invite email. Falls back to console log if SMTP_HOST is not set."""
    if not settings.smtp_host:
        logger.info(
            "[DEV MODE] Invite link for %s (role=%s): %s",
            to_email,
            role,
            accept_link,
        )
        return

    inviter = inviter_name or "A teammate"
    subject = f"{inviter} invited you to '{app_name}'"
    html = f"""
    <html><body>
      <h2>You've been invited to <em>{app_name}</em></h2>
      <p>{inviter} invited you as <strong>{role}</strong>.</p>
      <p><a href="{accept_link}" style="padding:10px 20px;background:#6366f1;color:#fff;
      border-radius:6px;text-decoration:none">Accept invitation</a></p>
      <p style="color:#888;font-size:12px">This link expires in 7 days.</p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        if settings.smtp_user and settings.smtp_pass:
            smtp.login(settings.smtp_user, settings.smtp_pass)
        smtp.sendmail(settings.smtp_from, [to_email], msg.as_string())
