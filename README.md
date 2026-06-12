# SentinelAI

> Predict. Protect. Prevent.

An AI-powered infrastructure protection system that helps government departments detect, predict, and prevent theft and vandalism of critical public infrastructure using Arduino-based sensor nodes, real-time monitoring, and predictive analytics.

---

## Problem Statement

Infrastructure theft and vandalism continue to impact service delivery across South Africa.

Critical infrastructure such as:

- Electrical transformers
- Substations
- Traffic light control boxes
- Water pump stations
- Clinics
- Schools
- Government facilities

are frequently targeted, resulting in:

- Power outages
- Water disruptions
- Increased maintenance costs
- Delayed service delivery
- Financial losses

Current security systems are largely reactive.

SentinelAI aims to shift from reactive response to proactive prevention.

---

## Project Goals

### Early Threat Detection
Detect suspicious activity around government infrastructure in real time.

### Predictive Prevention
Use Artificial Intelligence to identify infrastructure at risk before incidents occur.

### Rapid Response
Automatically notify the appropriate response teams.

### Infrastructure Visibility
Provide centralized monitoring and reporting capabilities.

### Data-Driven Decisions
Generate insights to improve security planning and resource allocation.

---

## Key Features

### Smart Sensor Monitoring

Arduino-based sensor nodes monitor infrastructure using:

- PIR Motion Sensors
- Vibration Sensors
- Tamper Detection Sensors
- GPS Modules (Optional)
- Temperature Sensors (Future)

---

### Real-Time Alerts

Receive alerts via:

- Web Dashboard
- SMS
- WhatsApp
- Email

---

### AI Risk Scoring

The system analyzes:

- Motion activity
- Vibration activity
- Time of day
- Historical incidents
- Infrastructure location

to calculate a threat score.

Example:

```text
Asset: Transformer-001

Motion Detected: Yes
Vibration Detected: High
Time: 02:13 AM

Risk Score: 94%
Status: HIGH RISK
```

### Infrastructure Risk Map

Visualize:

- High-risk zones
- Infrastructure locations
- Active incidents
- Historical theft patterns

---

### Incident Management

Track incidents from detection to resolution.

Statuses:

- Open
- Assigned
- In Progress
- Resolved

---

### Predictive Analytics

The AI engine predicts:

- Theft hotspots
- High-risk infrastructure
- Repeat offender patterns
- Recommended patrol locations

---

### Asset Health Monitoring

Monitor infrastructure condition and detect:

- Excessive vibration
- Repeated tampering
- Environmental anomalies

---

### AI Assistant

Generate:

- Risk assessments
- Monthly reports
- Incident summaries
- Security recommendations

---

## System Architecture

```text
PIR Motion Sensor
        |
Vibration Sensor
        |
     Arduino
        |
 WiFi / GSM Module
        |
    Backend API
        |
    PostgreSQL
        |
   AI Engine
        |
 Dashboard & Alerts
        |
 Security Teams
```

---

## Hardware Components

### Prototype Hardware

- Arduino Uno / Nano
- PIR Motion Sensor
- SW-420 Vibration Sensor
- GSM Module (SIM800L)
- ESP8266 WiFi Module
- LEDs
- Buzzer
- Breadboard
- Jumper Wires

---

## Software Stack

### Frontend

- React.js
- Tailwind CSS
- Leaflet Maps

### Backend

- FastAPI (Python)

### Database

- PostgreSQL

### AI & Analytics

- Python
- Pandas
- NumPy
- Scikit-learn

### Notifications

- SMS Gateway
- WhatsApp API
- Email Service

---

## AI Integration

### Threat Classification

Classifies activity as:

- Normal
- Suspicious
- High Risk

---

### Predictive Risk Analysis

Predicts:

- Infrastructure likely to be targeted
- High-risk locations
- Time-based attack patterns

---

### Response Recommendations

Suggests:

- Closest response team
- Priority level
- Recommended action

---

## User Roles

### Security Officer

- View alerts
- Update incidents
- Monitor infrastructure status

### Infrastructure Manager

- View reports
- Monitor assets
- Analyze trends

### Government Administrator

- Monitor all assets
- Review analytics
- Generate reports

---

## Example Workflow

1. Motion detected near a transformer.
2. Vibration sensor detects tampering.
3. Arduino sends sensor data to the backend.
4. AI calculates a risk score.
5. Alert is generated.
6. Security team is notified.
7. Incident is tracked until resolution.

---

## Future Enhancements

- Computer Vision Detection
- LoRaWAN Connectivity
- Drone Surveillance Integration
- Predictive Maintenance
- Multi-Department Infrastructure Monitoring
- Smart City Integration

---

## Expected Impact

- Reduced infrastructure theft
- Faster response times
- Improved service delivery
- Lower maintenance costs
- Better resource allocation
- Increased public safety

---

## Team

Developed for the Gauteng G13 Hackathon.

### SentinelAI
**Intelligent Infrastructure Protection System**

---

## Quick Start (Hackathon Demo)

### Who does what?

See **[TEAM.md](TEAM.md)** for the full 5-person split (3 hardware + 2 software) and the 5-minute demo script.

Open **[component_map.html](component_map.html)** in a browser for the component inventory and pin map.

### Run the full stack (one laptop)

```bash
# 1. Backend dependencies
pip install -r requirements.txt

# 2. Build dashboard
cd frontend
npm install
npm run build
cd ..

# 3. Start server (serves API + dashboard on port 8000)
python run.py
```

Open **http://127.0.0.1:8000** — use the demo buttons if Arduino is not connected.

### With Arduino connected

1. Upload `arduino/sentinel_node/sentinel_node.ino` (see `arduino/README.md`)
2. Plug Arduino into the same laptop via USB
3. Start with serial enabled (default):

```bash
python run.py
```

The backend auto-detects the COM port and ingests JSON from the serial monitor.

### Dev mode (hot reload dashboard)

```bash
# Terminal 1
python run.py

# Terminal 2
cd frontend && npm run dev
```

Dashboard: http://localhost:5173 · API docs: http://127.0.0.1:8000/docs

### Sensor → alert mapping

| Sensor | Threat | Buzzer |
|--------|--------|--------|
| Reed switch | Cabinet door opened | 1 beep |
| LDR light | Torch / headlights at night | 2 beeps |
| MLX90614 | Transformer overheating (>80°C) | 3 beeps |
| Flame/IR module | Bright IR / heat source | 4 beeps |
