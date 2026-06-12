# SentinelAI — Team of 5: Who Owns What

> Infrastructure theft & cable theft detection node for the Gauteng G13 Hackathon.

---

## Overview

| Role | Members | Deliverable |
|------|---------|-------------|
| **Hardware** | 3 people | Wired Arduino node, calibrated sensors, demo script |
| **Software** | 2 people | Backend API, dashboard, demo runbook |

Open `component_map.html` in a browser for the full component inventory with pin assignments.

---

## Hardware Team (3 members)

### Member 1 — Wiring lead
**Owns:** Breadboard power rails, all jumper connections, pin map verification

| Task | Details |
|------|---------|
| Wire Arduino Uno to breadboard | 5V and GND on power rails |
| Connect all modules per pin map | See `arduino/sentinel_node/sentinel_node.ino` |
| Install MLX90614 library | Arduino IDE → Library Manager → **Adafruit MLX90614** |
| Upload firmware | Open `arduino/sentinel_node/sentinel_node.ino`, board = Arduino Uno, 115200 baud |
| Verify serial output | Tools → Serial Monitor → JSON lines every second |

**Pin map (final):**

| Component | Pin |
|-----------|-----|
| Reed switch (door) | D2 |
| Flame / IR module | D3 |
| LDR light sensor | A0 |
| MLX90614 (I2C) | SDA=A4, SCL=A5 |
| Buzzer | D8 |
| LED normal (220Ω) | D9 |
| LED alert (220Ω) | D10 |

---

### Member 2 — Sensor calibration
**Owns:** Threshold tuning and physical mounting story for judges

| Sensor | Calibration step |
|--------|------------------|
| **MLX90614** | Point at transformer (or warm object for demo). Alert fires above **80°C**. |
| **LDR** | With compartment closed and dark, send serial command `CALIBRATE` to set night baseline. Shine phone torch → light intrusion alert. |
| **Reed switch** | Glue magnet on door, module on frame. Door closed = circuit closed. Open door → 1 beep + alert. |
| **Flame/IR module** | Point away from lights normally. Flashlight close to sensor → IR alert. |

**Buzzer patterns (for demo narration):**
- 1 beep = door opened
- 2 beeps = unexpected light
- 3 beeps = overheat
- 4 beeps = flame/IR

---

### Member 3 — Connectivity & demo hardware
**Owns:** USB serial bridge to laptop, optional WiFi/GSM stretch goal

| Priority | Task |
|----------|------|
| **Must have** | USB cable from Arduino → laptop running `python run.py` |
| **Nice to have** | ESP8266 on D11/D12 (future) — not required for hackathon |
| **Demo props** | Book/box as “transformer cabinet”, magnet on lid, phone torch |

**Serial commands (115200 baud):**
```
MAINTENANCE_ON   — suppress alerts (scheduled maintenance)
MAINTENANCE_OFF  — resume monitoring
CALIBRATE        — snapshot current light level as baseline
PING             — heartbeat
```

---

## Software Team (2 members)

### Member 4 — Backend & AI scoring
**Owns:** `backend/`, `requirements.txt`, `run.py`

| Task | File |
|------|------|
| FastAPI server + SQLite | `backend/main.py`, `backend/database.py` |
| Risk scoring engine | `backend/risk_engine.py` |
| Serial USB bridge | `backend/serial_bridge.py` (auto-detects COM port) |
| Email alerts (optional) | Set env vars: `SENTINEL_SMTP_*`, `SENTINEL_ALERT_EMAIL` |
| Location crime context (stretch) | `Agent.py` — area risk profiles |

**Run:**
```bash
pip install -r requirements.txt
python run.py
```
API docs: http://127.0.0.1:8000/docs

---

### Member 5 — Dashboard & demo
**Owns:** `frontend/`, presentation flow

| Task | File |
|------|------|
| React + Tailwind + Leaflet map | `frontend/src/App.jsx` |
| Real-time WebSocket feed | connects to `/ws` |
| Demo scenario buttons | door / torch / overheat / IR — works without Arduino |
| Build for single-port demo | `npm run build` then backend serves `frontend/dist` |

**Dev mode (two terminals):**
```bash
# Terminal 1
python run.py

# Terminal 2
cd frontend && npm install && npm run dev
```
Dashboard: http://localhost:5173

**Production demo (one laptop):**
```bash
cd frontend && npm install && npm run build
cd .. && python run.py
```
Open: http://127.0.0.1:8000

---

## Demo Script (5 minutes)

1. **Normal state** — Dashboard shows NORMAL, map pin green, slow LED blink on Arduino.
2. **Cable theft scenario** — Open cabinet door → 1 beep, dashboard ALERT, risk score jumps.
3. **2am torch scenario** — Shine phone light on LDR → 2 beeps, “light intrusion” on dashboard.
4. **Transformer fault** — Warm object near MLX90614 (or press Overheat demo button) → 3 beeps, CRITICAL.
5. **Maintenance** — Click “Enable maintenance mode” → open door again → no alert (shows smart ops).
6. **Resolution** — Show alert log, mention SMS/email when `SENTINEL_SMTP_*` configured.

---

## Still Need Before Demo

| Item | Owner | Priority |
|------|-------|----------|
| Jumper wires (20–40) | Hardware | Critical |
| 220Ω resistors ×4 (LEDs) | Hardware | Critical |
| USB cable (Uno → laptop) | Hardware | Critical |
| ESP8266 or SIM800L | Hardware | Optional (USB serial is fine) |

---

## Repository Map

```
SentinelAI/
├── arduino/sentinel_node/sentinel_node.ino   ← Hardware team
├── backend/                                   ← Backend dev
├── frontend/                                  ← Dashboard dev
├── Agent.py                                   ← Location risk AI (stretch)
├── component_map.html                         ← Component inventory
├── TEAM.md                                    ← This file
├── run.py                                     ← Start everything
└── requirements.txt
```
