<p align="center">
  <strong style="font-size:2rem">SentinelAI</strong><br/>
  <em>Predict · Protect · Prevent</em>
</p>

<p align="center">
  An AI-powered infrastructure protection platform for Gauteng's power network — detecting cable theft,
  substation intrusion, and transformer faults through Arduino sensor nodes, multi-signal fusion,
  and role-specific dashboards for security companies and utility operators.
</p>

<p align="center">
  <strong>Gauteng G13 Hackathon</strong> · Intelligent Infrastructure Protection System
</p>

---

## Overview

South Africa's public infrastructure — transformers, substations, cable vaults, and distribution nodes — is a high-value target for theft and vandalism. **SentinelAI** shifts security from reactive response to **proactive, AI-informed prevention**.

The platform combines:

- **Edge sensor nodes** (Arduino Uno) monitoring temperature, light, door/tamper, motion, and IR
- **AI fusion engine** correlating multi-sensor patterns against time-of-day and geographic risk
- **Dual stakeholder portals** — one for private security dispatch, one for municipal/Eskom operations
- **Live Gauteng infrastructure map** with all facilities from `power-stations.json`, color-coded by real-time status

---

## Dual Portal Architecture

| Portal | Audience | Receives |
|--------|----------|----------|
| **Security Operations Center** (`/security`) | Private security & rapid response | Door/tamper, motion, light intrusion, IR alerts · AI break-in probability · dispatch notifications |
| **Utility Operations** (`/operations`) | Municipal / Eskom maintenance teams | Transformer overheating, thermal warnings, maintenance mode, asset health notices |

Notifications route automatically:

- `SENTINEL_SECURITY_EMAIL` — security company inbox
- `SENTINEL_OPERATIONS_EMAIL` — utility operations inbox
- Console logging always active for demo

---

## AI Intrusion Analysis

The **AI Fusion Engine** (`backend/ai_analyzer.py`) ingests all sensor channels simultaneously:

| Signal | Weight | Detects |
|--------|--------|---------|
| Door / tamper | 28% | Unauthorized cabinet access |
| PIR motion | 26% | Movement in secured perimeter |
| Light (LDR) | 22% | Torches, headlights at night |
| IR / flame | 12% | Heat sources near cables |
| Temperature | 8% | Transformer thermal faults |

The engine also detects **compound patterns** — e.g. night + door + light/motion matching typical cable theft MO — and blends **geographic baseline risk** from `Agent.py`.

How AI analyzes each event:
- Inputs are fused from door/tamper, motion, light, flame/IR, and temperature signals.
- Temporal context is considered through the recent event buffer, which highlights repeated patterns over the last 12 events.
- The analyzer combines signal weights, anomaly thresholds, and location-specific risk factors to compute an intrusion probability.
- The resulting score is mapped into status bands such as NORMAL, ALERT, HIGH RISK, and MAINTENANCE.
- Site risk is enriched with geographic context, so critical substations and busy urban areas produce more meaningful actionable alerts.

Output per event:
- Intrusion probability (0–100%)
- Threat classification
- Confidence score
- Active signal breakdown
- Recommended action (dispatch / monitor / maintenance)

---

## Live Infrastructure Map

All Gauteng power stations and substations are loaded from **`power-stations.json`**:

- Kelvin, Rooiwal, Pretoria West power stations
- Eskom transmission substations (Apollo, Minerva, Craighall, Jupiter)
- Municipal distribution nodes (John Ware, Cydna, Delta, Kwagga, Centurion Central)

**Map features:**
- OpenStreetMap & satellite base layers
- Custom SVG icons per facility type (power station / substation / monitored node)
- Status color coding with pulse rings on active threats
- Threat radius circles around alerting sites

| Status | Color | Meaning |
|--------|-------|---------|
| NORMAL | Green | All sensors nominal |
| SUSPICIOUS | Amber | Anomaly detected |
| ALERT | Orange | Active threat signal |
| HIGH RISK | Red | Multi-sensor intrusion pattern |
| MAINTENANCE | Purple | Authorized maintenance window |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Arduino Sensor Node (John Ware Substation)                 │
│  MLX90614 · LDR · Reed Switch · PIR · IR · Buzzer · LEDs   │
└──────────────────────────┬──────────────────────────────────┘
                           │ USB Serial / JSON (115200 baud)
┌──────────────────────────▼──────────────────────────────────┐
│  FastAPI Backend                                            │
│  ├─ Serial Bridge        ├─ AI Fusion Engine                │
│  ├─ Risk Scoring         ├─ SQLite Persistence              │
│  ├─ Role Notifications   └─ WebSocket Live Feed             │
└────────────┬─────────────────────────────┬──────────────────┘
             │                             │
   ┌─────────▼─────────┐         ┌─────────▼─────────┐
   │ Security Portal   │         │ Operations Portal │
   │ /security         │         │ /operations       │
   └───────────────────┘         └───────────────────┘
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Arduino Uno (optional for live demo)

### Install & run

```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend && npm install && npm run build && cd ..

# Start (API + dashboard on port 8000)
python run.py
```

| URL | Description |
|-----|-------------|
| http://127.0.0.1:8000 | Portal selector |
| http://127.0.0.1:8000/security | Security company dashboard |
| http://127.0.0.1:8000/operations | Utility operations dashboard |
| http://127.0.0.1:8000/docs | API documentation |

### Development mode

```bash
python run.py                          # Terminal 1 — API
cd frontend && npm run dev               # Terminal 2 — hot reload at :5173
```

### Arduino setup

See [`arduino/README.md`](arduino/README.md). Upload `arduino/sentinel_node/sentinel_node.ino`, connect via USB — the backend auto-detects the COM port.

### Environment variables (optional)

```bash
SENTINEL_SECURITY_EMAIL=security@company.co.za
SENTINEL_OPERATIONS_EMAIL=ops@citypower.gov.za
SENTINEL_SMTP_HOST=smtp.gmail.com
SENTINEL_SMTP_USER=your@email.com
SENTINEL_SMTP_PASS=app-password
SENTINEL_USE_SERIAL=1
SENTINEL_SERIAL_PORT=COM3
```

---

## API Highlights

| Endpoint | Description |
|----------|-------------|
| `GET /api/stations` | All facilities with live status for map |
| `GET /api/alerts?audience=security` | Filtered alerts per portal |
| `GET /api/notifications/{audience}` | Dispatch / operations notification feed |
| `POST /api/ai/analyze` | Run AI fusion on sensor snapshot |
| `POST /api/simulate` | Demo scenarios without hardware |
| `POST /api/maintenance` | Toggle maintenance mode per site |
| `WS /ws` | Real-time event stream |

---

## Hardware

| Component | Pin | Role |
|-----------|-----|------|
| Reed switch | D2 | Door / tamper |
| Flame / IR | D3 | IR intrusion |
| LDR | A0 | Light / torch |
| MLX90614 | I2C A4/A5 | Transformer temperature |
| Buzzer | D8 | Local alarm |
| LEDs | D9, D10 | Status indicators |

**Buzzer patterns:** 1× door · 2× light · 3× overheat · 4× IR

Full wiring guide: [`TEAM.md`](TEAM.md) · Component inventory: [`component_map.html`](component_map.html)

---

## Project Structure

```
SentinelAI/
├── arduino/sentinel_node/     # Firmware
├── backend/
│   ├── main.py                # FastAPI application
│   ├── ai_analyzer.py         # Multi-sensor AI fusion
│   ├── risk_engine.py         # Threat scoring
│   ├── stations.py            # power-stations.json loader
│   ├── database.py            # SQLite persistence
│   └── notifier.py            # Role-based notifications
├── frontend/src/
│   ├── pages/                 # Landing, Security, Operations portals
│   └── components/            # Map, AI insights
├── power-stations.json        # Gauteng facility coordinates
├── Agent.py                   # Geographic crime risk context
├── TEAM.md                    # 5-person team roles
└── run.py                     # Entry point
```

---

## Team

| Members | Focus |
|---------|-------|
| 3 × Hardware | Arduino wiring, sensor calibration, demo rig |
| 2 × Software | Backend API, dual dashboards, AI integration |

---

## License & Context

Built for the **Gauteng G13 Hackathon** to demonstrate how IoT edge sensing and AI fusion can protect critical public infrastructure and reduce service delivery disruption from theft and vandalism.

**SentinelAI** — *Intelligent Infrastructure Protection System*
