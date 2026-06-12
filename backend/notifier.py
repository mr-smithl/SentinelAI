"""Role-based notifications: security company vs utility operations."""

from __future__ import annotations

import logging
import os
import smtplib
from email.mime.text import MIMEText
from typing import Dict, List

logger = logging.getLogger("sentinel.notify")

# Security company receives intrusion / theft alerts
SECURITY_EVENTS = {"door_open", "light_intrusion", "flame_ir", "motion_detected"}
# Utility department receives asset health + maintenance
OPERATIONS_EVENTS = {"overheat", "overheat_warn", "maintenance"}


def _send_email(to_addrs: List[str], subject: str, body: str) -> None:
    smtp_host = os.getenv("SENTINEL_SMTP_HOST")
    smtp_user = os.getenv("SENTINEL_SMTP_USER")
    smtp_pass = os.getenv("SENTINEL_SMTP_PASS")
    if not all([smtp_host, smtp_user, smtp_pass]) or not to_addrs:
        return
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = ", ".join(to_addrs)
        with smtplib.SMTP(smtp_host, int(os.getenv("SENTINEL_SMTP_PORT", "587"))) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        logger.info("Email sent to %s", to_addrs)
    except Exception as exc:
        logger.error("Email failed: %s", exc)


def notify_security(summary: str, risk: Dict, ai: Dict) -> None:
    """Alert private security / response company."""
    line = (
        f"[SECURITY DISPATCH] {summary} | "
        f"AI Intrusion: {ai.get('intrusion_probability', 0)}% | "
        f"Action: {ai.get('recommended_action', 'Investigate')}"
    )
    logger.warning(line)

    recipients = [
        e.strip()
        for e in os.getenv("SENTINEL_SECURITY_EMAIL", os.getenv("SENTINEL_ALERT_EMAIL", "")).split(",")
        if e.strip()
    ]
    body = (
        "SentinelAI — Security Operations Alert\n\n"
        f"{summary}\n\n"
        f"AI Assessment:\n"
        f"  Intrusion Probability: {ai.get('intrusion_probability')}%\n"
        f"  Classification: {ai.get('break_in_likelihood')}\n"
        f"  Confidence: {ai.get('confidence')}\n"
        f"  Recommended Action: {ai.get('recommended_action')}\n\n"
        f"Active Signals: {', '.join(ai.get('active_signals', []))}\n"
    )
    _send_email(recipients, f"[SentinelAI Security] {risk.get('status', 'ALERT')}", body)


def notify_operations(summary: str, risk: Dict, ai: Dict) -> None:
    """Alert municipal / Eskom operations & maintenance team."""
    line = (
        f"[OPERATIONS] {summary} | "
        f"Asset status: {risk.get('status')} | "
        f"AI: {ai.get('ai_summary', '')}"
    )
    logger.info(line)

    recipients = [
        e.strip()
        for e in os.getenv("SENTINEL_OPERATIONS_EMAIL", "").split(",")
        if e.strip()
    ]
    if not recipients:
        return
    body = (
        "SentinelAI — Utility Operations Notice\n\n"
        f"{summary}\n\n"
        f"AI Summary: {ai.get('ai_summary')}\n"
        f"Recommended Action: {ai.get('recommended_action')}\n"
    )
    _send_email(recipients, f"[SentinelAI Operations] {risk.get('status', 'NOTICE')}", body)


def dispatch_notifications(event: str, summary: str, risk: Dict, ai: Dict) -> Dict[str, bool]:
    """Route notifications to the correct stakeholder interface."""
    sent = {"security": False, "operations": False}

    if event in SECURITY_EVENTS and risk.get("risk_score", 0) >= 35:
        notify_security(summary, risk, ai)
        sent["security"] = True

    if event in OPERATIONS_EVENTS or risk.get("status") == "MAINTENANCE":
        notify_operations(summary, risk, ai)
        sent["operations"] = True

    # High compound intrusion goes to both
    if ai.get("intrusion_probability", 0) >= 65 and event in SECURITY_EVENTS:
        notify_operations(summary, risk, ai)
        sent["operations"] = True

    return sent
