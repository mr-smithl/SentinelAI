"""
SentinelAI FastAPI backend — dual-audience alerts, AI fusion, live infrastructure map.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Set

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.ai_analyzer import analyze_intrusion
from backend.database import (
    get_latest_telemetry,
    get_site,
    init_db,
    insert_alert,
    insert_notification,
    insert_telemetry,
    list_alerts,
    list_assets,
    list_notifications,
    list_sites,
    resolve_site_id,
    update_incident,
)
from backend.notifier import dispatch_notifications
from backend.risk_engine import calculate_sensor_risk, format_alert_summary
from backend.serial_bridge import SerialBridge, list_serial_ports
from backend.stations import flatten_stations

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger("sentinel.api")

app = FastAPI(
    title="SentinelAI",
    version="2.0.0",
    description="AI-powered infrastructure protection — security & operations portals",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

THREAT_EVENTS = {
    "door_open", "light_intrusion", "flame_ir", "overheat",
    "overheat_warn", "motion_detected",
}
recent_event_buffer: Deque[str] = deque(maxlen=12)
site_maintenance: Dict[str, bool] = {}
ws_clients: Set[WebSocket] = set()
serial_bridge: Optional[SerialBridge] = None

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
LOCATION_CONTEXT = "Industrial District"


class SensorEvent(BaseModel):
    asset_id: str = "TRANSFORMER-001"
    event: str
    severity: str = "info"
    message: str = ""
    temp_c: float = 25.0
    light_level: int = 0
    flame_detected: bool = False
    door_open: bool = False
    motion_detected: bool = False
    maintenance_mode: bool = False
    alert_active: bool = False


class IncidentUpdate(BaseModel):
    incident_status: str = Field(..., pattern="^(Open|Assigned|In Progress|Resolved)$")


class MaintenanceCommand(BaseModel):
    enabled: bool
    site_id: str = "john-ware-substation"


class SimulateRequest(BaseModel):
    scenario: str = Field(
        ...,
        description="door_open | light_intrusion | overheat | flame_ir | motion_detected",
    )
    site_id: Optional[str] = None


async def broadcast(message: Dict[str, Any]) -> None:
    dead: List[WebSocket] = []
    payload = json.dumps(message)
    for ws in list(ws_clients):
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        ws_clients.discard(ws)


def process_sensor_event(data: Dict[str, Any]) -> Dict[str, Any]:
    event = data.get("event", "telemetry")
    severity = data.get("severity", "info")
    asset_id = data.get("asset_id", "TRANSFORMER-001")
    site_id = data.get("site_id") or resolve_site_id(asset_id)
    maintenance = bool(data.get("maintenance_mode")) or site_maintenance.get(site_id, False)

    site = get_site(site_id)
    location_name = site["name"] if site else LOCATION_CONTEXT

    ai = analyze_intrusion(
        event=event,
        temp_c=float(data.get("temp_c", 25)),
        light_level=int(data.get("light_level", 0)),
        door_open=bool(data.get("door_open")),
        flame_detected=bool(data.get("flame_detected")),
        motion_detected=bool(data.get("motion_detected")),
        maintenance_mode=maintenance,
        recent_events=list(recent_event_buffer),
        location_name=location_name,
    )

    risk = calculate_sensor_risk(
        event,
        severity,
        temp_c=float(data.get("temp_c", 25)),
        light_level=int(data.get("light_level", 0)),
        door_open=bool(data.get("door_open")),
        flame_detected=bool(data.get("flame_detected")),
        maintenance_mode=maintenance,
        recent_events=list(recent_event_buffer),
    )

    # AI fusion can elevate status for compound intrusions
    if ai["intrusion_probability"] >= 85:
        risk["status"] = "HIGH RISK"
        risk["risk_level"] = "CRITICAL"
        risk["risk_score"] = max(risk["risk_score"], int(ai["intrusion_probability"]))
    elif ai["intrusion_probability"] >= 65:
        risk["status"] = "ALERT"
        risk["risk_level"] = "HIGH"
        risk["risk_score"] = max(risk["risk_score"], int(ai["intrusion_probability"]))

    if maintenance:
        risk["status"] = "MAINTENANCE"
        risk["risk_level"] = "MAINTENANCE"

    audience = "all"
    if event in {"door_open", "light_intrusion", "flame_ir", "motion_detected"}:
        audience = "security"
    elif event in {"overheat", "overheat_warn", "maintenance"}:
        audience = "operations"

    record: Dict[str, Any] = {
        "asset_id": asset_id,
        "site_id": site_id,
        "event": event,
        "severity": severity,
        "message": data.get("message", ""),
        "risk_score": risk["risk_score"],
        "risk_level": risk["risk_level"],
        "status": risk["status"],
        "intrusion_probability": ai["intrusion_probability"],
        "temp_c": data.get("temp_c"),
        "light_level": data.get("light_level"),
        "door_open": data.get("door_open"),
        "flame_detected": data.get("flame_detected"),
        "motion_detected": data.get("motion_detected"),
        "audience": audience,
        "payload": {"factors": risk["factors"], "ai": ai, "raw": data},
        "created_at": datetime.now().isoformat(),
    }

    insert_telemetry({
        **record,
        "maintenance_mode": maintenance,
    })

    alert_id: Optional[int] = None
    if event in THREAT_EVENTS and risk["risk_score"] >= 35 and not maintenance:
        recent_event_buffer.append(event)
        alert_id = insert_alert(record)
        summary = format_alert_summary(asset_id, event, risk)
        summary += f"\nAI Intrusion Probability: {ai['intrusion_probability']}%"
        summary += f"\nAI Action: {ai['recommended_action']}"

        sent = dispatch_notifications(event, summary, risk, ai)
        if sent.get("security"):
            insert_notification(
                "security",
                f"{risk['status']} — {event.replace('_', ' ').title()}",
                summary,
                alert_id,
            )
        if sent.get("operations"):
            insert_notification(
                "operations",
                f"{risk['status']} — {event.replace('_', ' ').title()}",
                summary,
                alert_id,
            )

    return {**record, "id": alert_id, "risk": risk, "ai": ai}


def on_serial_event(data: Dict[str, Any]) -> None:
    result = process_sensor_event(data)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                broadcast({"type": "sensor_event", "data": result}), loop
            )
    except RuntimeError:
        pass


@app.on_event("startup")
async def startup() -> None:
    init_db()
    global serial_bridge
    use_serial = os.getenv("SENTINEL_USE_SERIAL", "1") == "1"
    port = os.getenv("SENTINEL_SERIAL_PORT")
    if use_serial:
        serial_bridge = SerialBridge(on_event=on_serial_event, port=port)
        if not serial_bridge.start():
            logger.info("Serial bridge not started — use /api/simulate for demo")
            serial_bridge = None


@app.on_event("shutdown")
async def shutdown() -> None:
    if serial_bridge:
        serial_bridge.stop()


# ── API ───────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "version": "2.0.0",
        "serial_ports": list_serial_ports(),
        "serial_active": serial_bridge is not None,
        "ws_clients": len(ws_clients),
        "sites_loaded": len(flatten_stations()),
    }


@app.get("/api/stations")
def get_stations() -> List[Dict[str, Any]]:
    """All power stations & substations with live status for map coloring."""
    sites = list_sites()
    for site in sites:
        if site.get("sensor_node_id"):
            tel = get_latest_telemetry(site["sensor_node_id"])
            site["telemetry"] = tel
    return sites


@app.get("/api/stations/{site_id}")
def get_station_detail(site_id: str) -> Dict[str, Any]:
    site = get_site(site_id)
    if not site:
        raise HTTPException(404, "Site not found")
    if site.get("sensor_node_id"):
        site["telemetry"] = get_latest_telemetry(site["sensor_node_id"])
    return site


@app.get("/api/assets")
def get_assets() -> List[Dict[str, Any]]:
    assets = list_assets()
    for asset in assets:
        asset["telemetry"] = get_latest_telemetry(asset["id"])
    return assets


@app.get("/api/alerts")
def get_alerts(
    limit: int = 50,
    audience: Optional[str] = Query(None, description="security | operations"),
) -> List[Dict[str, Any]]:
    return list_alerts(limit, audience)


@app.get("/api/notifications/{audience}")
def get_notifications(audience: str, limit: int = 20) -> List[Dict[str, Any]]:
    if audience not in ("security", "operations"):
        raise HTTPException(400, "audience must be security or operations")
    return list_notifications(audience, limit)


@app.post("/api/ai/analyze")
def ai_analyze(event: SensorEvent) -> Dict[str, Any]:
    """Run AI fusion on current sensor snapshot without persisting."""
    site_id = resolve_site_id(event.asset_id)
    site = get_site(site_id)
    return analyze_intrusion(
        event=event.event,
        temp_c=event.temp_c,
        light_level=event.light_level,
        door_open=event.door_open,
        flame_detected=event.flame_detected,
        motion_detected=event.motion_detected,
        maintenance_mode=event.maintenance_mode or site_maintenance.get(site_id, False),
        recent_events=list(recent_event_buffer),
        location_name=site["name"] if site else LOCATION_CONTEXT,
    )


@app.get("/api/location-risk/{area_name}")
def location_risk(area_name: str) -> Dict[str, Any]:
    try:
        from Agent import CrimeRiskAgent
        return CrimeRiskAgent().analyze_location(area_name)
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc


@app.post("/api/events")
async def ingest_event(event: SensorEvent) -> Dict[str, Any]:
    result = process_sensor_event(event.model_dump())
    await broadcast({"type": "sensor_event", "data": result})
    return result


@app.patch("/api/alerts/{alert_id}/incident")
def patch_incident(alert_id: int, body: IncidentUpdate) -> Dict[str, str]:
    if not update_incident(alert_id, body.incident_status):
        raise HTTPException(404, "Alert not found")
    return {"status": "updated", "incident_status": body.incident_status}


@app.post("/api/maintenance")
async def set_maintenance(cmd: MaintenanceCommand) -> Dict[str, Any]:
    site_maintenance[cmd.site_id] = cmd.enabled
    command = "MAINTENANCE_ON" if cmd.enabled else "MAINTENANCE_OFF"
    sent = serial_bridge.send_command(command) if serial_bridge else False
    result = process_sensor_event({
        "asset_id": "TRANSFORMER-001",
        "site_id": cmd.site_id,
        "event": "maintenance",
        "severity": "info",
        "message": f"Maintenance mode {'enabled' if cmd.enabled else 'disabled'}",
        "maintenance_mode": cmd.enabled,
    })
    await broadcast({"type": "maintenance", "data": result})
    return {"serial_sent": sent, "maintenance_mode": cmd.enabled, "site_id": cmd.site_id}


@app.post("/api/simulate")
async def simulate_scenario(body: SimulateRequest) -> Dict[str, Any]:
    scenarios = {
        "door_open": {
            "event": "door_open", "severity": "high",
            "message": "Cabinet door opened unexpectedly",
            "door_open": True, "temp_c": 42, "light_level": 130,
        },
        "light_intrusion": {
            "event": "light_intrusion", "severity": "high",
            "message": "Unexpected light — possible intruder torch",
            "light_level": 850, "temp_c": 38,
        },
        "motion_detected": {
            "event": "motion_detected", "severity": "high",
            "message": "PIR motion detected in secured perimeter",
            "motion_detected": True, "light_level": 200, "temp_c": 36,
        },
        "overheat": {
            "event": "overheat", "severity": "critical",
            "message": "Transformer surface temperature critical",
            "temp_c": 87.5, "light_level": 90,
        },
        "flame_ir": {
            "event": "flame_ir", "severity": "medium",
            "message": "IR/flame sensor triggered",
            "flame_detected": True, "light_level": 400, "temp_c": 55,
        },
    }
    if body.scenario not in scenarios:
        raise HTTPException(400, f"Choose: {list(scenarios)}")

    payload = {
        "asset_id": "TRANSFORMER-001",
        "site_id": body.site_id or "john-ware-substation",
        **scenarios[body.scenario],
    }
    result = process_sensor_event(payload)
    await broadcast({"type": "sensor_event", "data": result})
    return result


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    ws_clients.add(ws)
    try:
        await ws.send_json({"type": "connected", "message": "SentinelAI live feed"})
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_clients.discard(ws)


if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/")
    async def serve_dashboard():
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/{path:path}")
    async def spa_fallback(path: str):
        if path.startswith("api/"):
            raise HTTPException(404)
        file_path = FRONTEND_DIST / path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
