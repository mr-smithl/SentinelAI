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
