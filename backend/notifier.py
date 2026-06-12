"""Optional email / console notifications for high-risk alerts."""

from __future__ import annotations

import logging
import os
import smtplib
from email.mime.text import MIMEText
from typing import Dict

logger = logging.getLogger("sentinel.notify")


def send_alert_notification(summary: str, risk: Dict) -> None:
    """Send alert to console always; email if SMTP env vars are set."""
    logger.warning("ALERT: %s", summary.replace("\n", " | "))

    smtp_host = os.getenv("SENTINEL_SMTP_HOST")
    smtp_user = os.getenv("SENTINEL_SMTP_USER")
    smtp_pass = os.getenv("SENTINEL_SMTP_PASS")
    alert_to = os.getenv("SENTINEL_ALERT_EMAIL")

    if not all([smtp_host, smtp_user, smtp_pass, alert_to]):
        return

    try:
        msg = MIMEText(summary)
        msg["Subject"] = f"[SentinelAI] {risk.get('status', 'ALERT')} — Infrastructure Threat"
        msg["From"] = smtp_user
        msg["To"] = alert_to

        with smtplib.SMTP(smtp_host, int(os.getenv("SENTINEL_SMTP_PORT", "587"))) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        logger.info("Email notification sent to %s", alert_to)
    except Exception as exc:
        logger.error("Email notification failed: %s", exc)
