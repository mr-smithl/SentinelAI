"""
Multi-sensor AI fusion for intrusion and break-in probability.

Combines motion, light, door/tamper, temperature, and time-of-day signals
with optional geographic crime context from Agent.py.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

SENSOR_WEIGHTS = {
    "door_open": 0.28,
    "motion_detected": 0.26,
    "light_intrusion": 0.22,
    "flame_ir": 0.12,
    "overheat": 0.08,
    "overheat_warn": 0.04,
}

NIGHT_HOURS = set(range(0, 6)) | set(range(22, 24))


def _time_risk(hour: int) -> float:
    if hour in NIGHT_HOURS:
        return 1.0
    if 6 <= hour < 18:
        return 0.45
    return 0.72


def _classify_intrusion(score: float, signals: List[str]) -> str:
    if score >= 0.82:
        return "High Risk — Likely Break-in"
    if score >= 0.62:
        return "Suspicious — Probable Intrusion"
    if score >= 0.38:
        return "Elevated — Monitor Closely"
    if signals:
        return "Low — Anomaly Detected"
    return "Normal — No Threat Indicators"


def _recommended_action(score: float, signals: List[str], maintenance: bool) -> str:
    if maintenance:
        return "Maintenance window active — verify work order on site."
    if score >= 0.82:
        return "Dispatch armed response unit immediately. Lock down adjacent feeders."
    if score >= 0.62:
        return "Alert security patrol. Activate perimeter cameras and two-factor site check."
    if score >= 0.38:
        return "Increase monitoring frequency. Log incident for trend analysis."
    if signals:
        return "Continue observation. No dispatch required yet."
    return "Routine monitoring. All sensor channels nominal."


def analyze_intrusion(
    *,
    event: str = "telemetry",
    temp_c: float = 25.0,
    light_level: int = 0,
    door_open: bool = False,
    flame_detected: bool = False,
    motion_detected: bool = False,
    maintenance_mode: bool = False,
    recent_events: Optional[List[str]] = None,
    location_name: Optional[str] = None,
    timestamp: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Fuse all sensor channels into a single AI intrusion assessment.
    Returns probability, classification, contributing factors, and actions.
    """
    if timestamp is None:
        timestamp = datetime.now()

    if maintenance_mode:
        return {
            "intrusion_probability": 0.0,
            "break_in_likelihood": "None — Maintenance Mode",
            "threat_class": "MAINTENANCE",
            "confidence": 1.0,
            "active_signals": [],
            "sensor_scores": {},
            "factors": ["Scheduled maintenance — intrusion detection suppressed"],
            "recommended_action": _recommended_action(0, [], True),
            "ai_summary": "Site is in authorized maintenance. Sensor alerts are logged but not escalated.",
        }

    recent = recent_events or []
    active_signals: List[str] = []
    sensor_scores: Dict[str, float] = {}

    # Live sensor state (not just the triggering event)
    if door_open or event == "door_open":
        active_signals.append("door_tamper")
        sensor_scores["door_tamper"] = SENSOR_WEIGHTS["door_open"]
    if motion_detected or event == "motion_detected":
        active_signals.append("motion")
        sensor_scores["motion"] = SENSOR_WEIGHTS["motion_detected"]
    if light_level > 400 or event == "light_intrusion":
        active_signals.append("light")
        sensor_scores["light"] = SENSOR_WEIGHTS["light_intrusion"] * min(light_level / 900, 1.0)
    if flame_detected or event == "flame_ir":
        active_signals.append("ir_flame")
        sensor_scores["ir_flame"] = SENSOR_WEIGHTS["flame_ir"]
    if temp_c >= 80 or event == "overheat":
        active_signals.append("overheat")
        sensor_scores["overheat"] = SENSOR_WEIGHTS["overheat"]
    elif temp_c >= 65 or event == "overheat_warn":
        sensor_scores["thermal"] = SENSOR_WEIGHTS["overheat_warn"]

    # Recent event memory boosts correlated intrusion patterns
    threat_recent = [e for e in recent if e in SENSOR_WEIGHTS]
    if len(set(threat_recent)) >= 2:
        sensor_scores["correlation"] = 0.18
        active_signals.append("multi_sensor_correlation")

    # Cable theft signature: night + door + light/motion
    hour = timestamp.hour
    time_factor = _time_risk(hour)
    cable_theft_pattern = (
        time_factor >= 1.0
        and ("door_tamper" in active_signals or door_open)
        and ("light" in active_signals or "motion" in active_signals)
    )
    if cable_theft_pattern:
        sensor_scores["cable_theft_pattern"] = 0.22
        active_signals.append("cable_theft_signature")

    base = sum(sensor_scores.values())
    base = min(base * time_factor, 1.0)

    # Geographic context from Agent.py (optional, lightweight)
    geo_boost = 0.0
    geo_note = None
    if location_name:
        try:
            from Agent import CrimeRiskAgent

            agent = CrimeRiskAgent()
            area = agent.calculate_risk_score(location_name, timestamp)
            geo_boost = (area["risk_score"] / 100) * 0.12
            geo_note = f"Area baseline risk {area['risk_score']}% ({area['matched_area']})"
        except Exception:
            pass

    probability = round(min(base + geo_boost, 1.0) * 100, 1)

    factors: List[str] = []
    if "door_tamper" in active_signals:
        factors.append("Tamper/door sensor indicates unauthorized cabinet access")
    if "motion" in active_signals:
        factors.append("PIR motion detected in secured perimeter")
    if "light" in active_signals:
        factors.append(f"Abnormal light level ({light_level}) — possible torch or vehicle headlights")
    if "ir_flame" in active_signals:
        factors.append("IR sensor spike — heat source or high-intensity light nearby")
    if "overheat" in active_signals:
        factors.append(f"Thermal anomaly: {temp_c:.1f}°C surface reading")
    if "multi_sensor_correlation" in active_signals:
        factors.append("AI correlation: multiple sensors triggered within short window")
    if "cable_theft_signature" in active_signals:
        factors.append("Pattern match: night-time door + light/motion — typical cable theft MO")
    if time_factor >= 1.0:
        factors.append("High-risk time window (22:00–06:00)")
    if geo_note:
        factors.append(geo_note)

    threat_class = _classify_intrusion(probability / 100, active_signals)
    confidence = round(min(0.55 + len(active_signals) * 0.12 + len(threat_recent) * 0.05, 0.98), 2)

    return {
        "intrusion_probability": probability,
        "break_in_likelihood": threat_class,
        "threat_class": (
            "CRITICAL" if probability >= 85 else
            "HIGH" if probability >= 65 else
            "MODERATE" if probability >= 38 else
            "LOW"
        ),
        "confidence": confidence,
        "active_signals": active_signals,
        "sensor_scores": {k: round(v, 3) for k, v in sensor_scores.items()},
        "factors": factors or ["All sensor channels within normal parameters"],
        "recommended_action": _recommended_action(probability / 100, active_signals, False),
        "ai_summary": (
            f"AI fusion analysis: {probability}% intrusion probability based on "
            f"{len(active_signals)} active signal(s) at {timestamp.strftime('%H:%M')}."
        ),
        "time_risk_factor": round(time_factor, 2),
    }
