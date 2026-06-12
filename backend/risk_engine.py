"""Sensor-aware threat scoring for SentinelAI infrastructure nodes."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

# Event weights for infrastructure theft / vandalism scenarios
EVENT_WEIGHTS: Dict[str, float] = {
    "door_open": 0.35,
    "light_intrusion": 0.30,
    "flame_ir": 0.20,
    "overheat": 0.25,
    "overheat_warn": 0.10,
    "door_closed": 0.0,
    "telemetry": 0.0,
    "startup": 0.0,
    "heartbeat": 0.0,
    "maintenance": 0.0,
    "calibration": 0.0,
}

SEVERITY_BASE: Dict[str, float] = {
    "critical": 0.95,
    "high": 0.80,
    "medium": 0.55,
    "low": 0.30,
    "info": 0.05,
}

NIGHT_HOURS = range(0, 6)  # 00:00–05:59 — highest cable theft window


def _time_multiplier(ts: datetime) -> float:
    hour = ts.hour
    if hour in NIGHT_HOURS or hour >= 22:
        return 1.0
    if 6 <= hour < 18:
        return 0.5
    return 0.75


def _temp_bonus(temp_c: float) -> float:
    if temp_c >= 80:
        return 0.25
    if temp_c >= 65:
        return 0.10
    return 0.0


def calculate_sensor_risk(
    event: str,
    severity: str,
    *,
    temp_c: float = 25.0,
    light_level: int = 0,
    door_open: bool = False,
    flame_detected: bool = False,
    maintenance_mode: bool = False,
    timestamp: Optional[datetime] = None,
    recent_events: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Compute a 0–100 risk score from a single sensor event."""
    if timestamp is None:
        timestamp = datetime.now()

    if maintenance_mode:
        return {
            "risk_score": 0,
            "risk_level": "MAINTENANCE",
            "status": "MAINTENANCE",
            "factors": ["Maintenance mode — alerts suppressed"],
        }

    base = SEVERITY_BASE.get(severity.lower(), 0.4)
    event_weight = EVENT_WEIGHTS.get(event, 0.15)
    time_mult = _time_multiplier(timestamp)

    score = (base * 0.45 + event_weight * 0.35 + _temp_bonus(temp_c) * 0.20) * time_mult

    factors: List[str] = []
    if event == "door_open":
        factors.append("Cabinet door opened outside maintenance window")
    if event == "light_intrusion":
        factors.append(f"Light spike detected (level {light_level}) during sensitive hours")
    if flame_detected or event == "flame_ir":
        factors.append("IR/flame sensor triggered — torch or heat source")
    if temp_c >= 80:
        factors.append(f"Transformer surface at {temp_c:.1f}°C — overheating")
    elif temp_c >= 65:
        factors.append(f"Elevated temperature {temp_c:.1f}°C")
    if door_open:
        factors.append("Door currently open")
    if time_mult >= 1.0:
        factors.append("Night-time window — elevated cable theft risk")

    # Compound threat: multiple signals in short succession
    if recent_events:
        unique_threats = {e for e in recent_events if e in EVENT_WEIGHTS and EVENT_WEIGHTS[e] > 0}
        if len(unique_threats) >= 2:
            score = min(score + 0.15, 1.0)
            factors.append("Multiple threat signals detected — compound risk")

    # Demo-realistic floors for primary infrastructure threat events
    event_floors = {
        "overheat": 0.90,
        "door_open": 0.78,
        "light_intrusion": 0.72,
        "flame_ir": 0.58,
    }
    if event in event_floors and time_mult >= 0.75:
        score = max(score, event_floors[event])

    score_pct = round(min(max(score, 0.0), 1.0) * 100)

    if score_pct >= 85:
        risk_level = "CRITICAL"
        status = "HIGH RISK"
    elif score_pct >= 65:
        risk_level = "HIGH"
        status = "ALERT"
    elif score_pct >= 35:
        risk_level = "MODERATE"
        status = "SUSPICIOUS"
    else:
        risk_level = "LOW"
        status = "NORMAL"

    return {
        "risk_score": score_pct,
        "risk_level": risk_level,
        "status": status,
        "factors": factors or [f"Event: {event}"],
        "time_multiplier": round(time_mult, 2),
    }


def format_alert_summary(asset_id: str, event: str, risk: Dict[str, Any]) -> str:
    """Human-readable alert line for dashboard and notifications."""
    return (
        f"Asset: {asset_id}\n"
        f"Event: {event.replace('_', ' ').title()}\n"
        f"Risk Score: {risk['risk_score']}%\n"
        f"Status: {risk['status']}\n"
        f"Factors: {', '.join(risk['factors'][:3])}"
    )
