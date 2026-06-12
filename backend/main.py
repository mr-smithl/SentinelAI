"""
SentinelAI FastAPI backend — sensor ingestion, risk scoring, WebSocket feed.
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

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.database import (
    get_latest_telemetry,
    init_db,
    insert_alert,
    insert_telemetry,
    list_alerts,
    list_assets,
    update_incident,
)
from backend.notifier import send_alert_notification
from backend.risk_engine import calculate_sensor_risk, format_alert_summary
from backend.serial_bridge import SerialBridge, list_serial_ports

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger("sentinel.api")

# ── App setup ───────────────────────────────────────────────────────────────
app = FastAPI(title="SentinelAI", version="1.0.0", description="Infrastructure theft detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

THREAT_EVENTS = {"door_open", "light_intrusion", "flame_ir", "overheat", "overheat_warn"}
recent_event_buffer: Deque[str] = deque(maxlen=10)
ws_clients: Set[WebSocket] = set()
serial_bridge: Optional[SerialBridge] = None

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


# ── Models ──────────────────────────────────────────────────────────────────
class SensorEvent(BaseModel):
    asset_id: str = "TRANSFORMER-001"
    event: str
    severity: str = "info"
    message: str = ""
    temp_c: float = 25.0
    light_level: int = 0
    flame_detected: bool = False
    door_open: bool = False
    maintenance_mode: bool = False
    alert_active: bool = False


class IncidentUpdate(BaseModel):
    incident_status: str = Field(..., pattern="^(Open|Assigned|In Progress|Resolved)$")


class MaintenanceCommand(BaseModel):
    enabled: bool


class SimulateRequest(BaseModel):
    scenario: str = Field(..., description="door_open | light_intrusion | overheat | flame_ir")


# ── WebSocket broadcast ───────────────────────────────────────────────────────
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
    """Core pipeline: score risk, persist, notify, return enriched record."""
    event = data.get("event", "telemetry")
    severity = data.get("severity", "info")
    asset_id = data.get("asset_id", "TRANSFORMER-001")

    risk = calculate_sensor_risk(
        event,
        severity,
        temp_c=float(data.get("temp_c", 25)),
        light_level=int(data.get("light_level", 0)),
        door_open=bool(data.get("door_open")),
        flame_detected=bool(data.get("flame_detected")),
        maintenance_mode=bool(data.get("maintenance_mode")),
        recent_events=list(recent_event_buffer),
    )

    record: Dict[str, Any] = {
        "asset_id": asset_id,
        "event": event,
        "severity": severity,
        "message": data.get("message", ""),
        "risk_score": risk["risk_score"],
        "risk_level": risk["risk_level"],
        "status": risk["status"],
        "temp_c": data.get("temp_c"),
        "light_level": data.get("light_level"),
        "door_open": data.get("door_open"),
        "flame_detected": data.get("flame_detected"),
        "payload": {"factors": risk["factors"], "raw": data},
        "created_at": datetime.now().isoformat(),
    }

    insert_telemetry({
        "asset_id": asset_id,
        "temp_c": record["temp_c"],
        "light_level": record["light_level"],
        "door_open": record["door_open"],
        "flame_detected": record["flame_detected"],
        "maintenance_mode": data.get("maintenance_mode"),
        "created_at": record["created_at"],
    })

    alert_id: Optional[int] = None
    if event in THREAT_EVENTS and risk["risk_score"] >= 35:
        recent_event_buffer.append(event)
        alert_id = insert_alert(record)
        summary = format_alert_summary(asset_id, event, risk)
        send_alert_notification(summary, risk)

    return {**record, "id": alert_id, "risk": risk}


def on_serial_event(data: Dict[str, Any]) -> None:
    result = process_sensor_event(data)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast({"type": "sensor_event", "data": result}), loop)
    except RuntimeError:
        pass


# ── Lifecycle ───────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup() -> None:
    init_db()
    global serial_bridge

    use_serial = os.getenv("SENTINEL_USE_SERIAL", "1") == "1"
    port = os.getenv("SENTINEL_SERIAL_PORT")

    if use_serial:
        serial_bridge = SerialBridge(on_event=on_serial_event, port=port)
        if not serial_bridge.start():
            logger.info("Serial bridge not started — use /api/simulate for demo events")
            serial_bridge = None


@app.on_event("shutdown")
async def shutdown() -> None:
    if serial_bridge:
        serial_bridge.stop()


# ── REST API ──────────────────────────────────────────────────────────────────
@app.get("/api/location-risk/{area_name}")
def location_risk(area_name: str) -> Dict[str, Any]:
    """Optional: area-level crime context from Agent.py (stretch / judging narrative)."""
    try:
        from Agent import CrimeRiskAgent

        agent = CrimeRiskAgent()
        return agent.analyze_location(area_name)
    except Exception as exc:
        raise HTTPException(500, f"Location risk unavailable: {exc}") from exc


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "serial_ports": list_serial_ports(),
        "serial_active": serial_bridge is not None,
        "ws_clients": len(ws_clients),
    }


@app.get("/api/assets")
def get_assets() -> List[Dict[str, Any]]:
    assets = list_assets()
    for asset in assets:
        tel = get_latest_telemetry(asset["id"])
        asset["telemetry"] = tel
    return assets


@app.get("/api/alerts")
def get_alerts(limit: int = 50) -> List[Dict[str, Any]]:
    return list_alerts(limit)


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
    command = "MAINTENANCE_ON" if cmd.enabled else "MAINTENANCE_OFF"
    sent = serial_bridge.send_command(command) if serial_bridge else False
    result = process_sensor_event({
        "asset_id": "TRANSFORMER-001",
        "event": "maintenance",
        "severity": "info",
        "message": f"Maintenance mode {'enabled' if cmd.enabled else 'disabled'}",
        "maintenance_mode": cmd.enabled,
    })
    await broadcast({"type": "maintenance", "data": result})
    return {"serial_sent": sent, "maintenance_mode": cmd.enabled}


@app.post("/api/simulate")
async def simulate_scenario(body: SimulateRequest) -> Dict[str, Any]:
    """Demo endpoint — fire a threat scenario without physical sensors."""
    scenarios = {
        "door_open": {
            "event": "door_open", "severity": "high",
            "message": "Cabinet door opened unexpectedly",
            "door_open": True, "temp_c": 42, "light_level": 130,
        },
        "light_intrusion": {
            "event": "light_intrusion", "severity": "high",
            "message": "Unexpected light detected — possible intruder torch",
            "light_level": 850, "temp_c": 38,
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
        raise HTTPException(400, f"Unknown scenario. Choose: {list(scenarios)}")

    payload = {"asset_id": "TRANSFORMER-001", **scenarios[body.scenario]}
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


# ── Serve built frontend in production/demo mode ────────────────────────────
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/")
    async def serve_dashboard():
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/{path:path}")
    async def spa_fallback(path: str):
        file_path = FRONTEND_DIST / path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
