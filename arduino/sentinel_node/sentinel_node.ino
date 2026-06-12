/*
 * SentinelAI — Infrastructure Theft Detection Node
 * Gauteng G13 Hackathon
 *
 * Sensors:
 *   - MLX90614 IR temperature (I2C) — transformer overheating
 *   - LDR light module (A0) — unexpected light at night (torch/headlights)
 *   - Flame/IR module (D3) — sudden IR/light spike
 *   - Reed switch (D2) — cabinet door open
 *   - Buzzer (D8) — local alarm with distinct patterns
 *   - Status LEDs (D9 normal, D10 alert)
 *
 * Serial output: one JSON line per reading + immediate event lines.
 * Commands (115200 baud): MAINTENANCE_ON | MAINTENANCE_OFF | CALIBRATE
 */

#include <Wire.h>
#include <Adafruit_MLX90614.h>

// ── Pin map (matches component_map.html) ──────────────────────────────────
#define PIN_REED_SWITCH   2
#define PIN_FLAME_DIGITAL 3
#define PIN_LDR_ANALOG    A0
#define PIN_BUZZER        8
#define PIN_LED_NORMAL    9
#define PIN_LED_ALERT     10

// ── Thresholds (tune on site) ───────────────────────────────────────────────
#define TEMP_ALERT_C        80.0f   // transformer surface overheating
#define TEMP_WARN_C         65.0f
#define LIGHT_NIGHT_BASELINE 120    // ADC 0-1023 — calibrate with CALIBRATE cmd
#define LIGHT_SPIKE_DELTA    180    // sudden increase triggers alert
#define FLAME_TRIGGER_LOW    LOW    // most modules pull LOW when flame/light detected
#define REED_DOOR_OPEN       HIGH   // magnet present = LOW, door open = HIGH

#define READ_INTERVAL_MS    1000
#define DEBOUNCE_MS         800
#define SERIAL_BAUD         115200

Adafruit_MLX90614 mlx = Adafruit_MLX90614();

bool maintenanceMode = false;
bool mlxAvailable = false;

unsigned long lastReadMs = 0;
unsigned long lastReedChangeMs = 0;
unsigned long lastLightSpikeMs = 0;
unsigned long lastTempAlertMs = 0;
unsigned long lastFlameAlertMs = 0;

bool doorOpen = false;
bool alertActive = false;

int lightBaseline = LIGHT_NIGHT_BASELINE;
int lastLightReading = 0;

// ── Buzzer patterns ─────────────────────────────────────────────────────────
// 1 beep = door opened | 2 beeps = light | 3 beeps = overheat | 4 = flame/IR

void beepPattern(int count) {
  for (int i = 0; i < count; i++) {
    digitalWrite(PIN_BUZZER, HIGH);
    delay(120);
    digitalWrite(PIN_BUZZER, LOW);
    delay(100);
  }
}

bool isNightHours() {
  // Approximate night window 18:00–06:00 using millis buckets for demo;
  // backend applies real time-of-day scoring. Optional RTC can replace this.
  return true; // treat as night-sensitive for hackathon demo
}

float readObjectTempC() {
  if (!mlxAvailable) {
    // Simulation fallback when MLX90614 not wired — rises if pin A1 pulled
    int sim = analogRead(A1);
    return 25.0f + (sim / 1023.0f) * 60.0f;
  }
  return mlx.readObjectTempC();
}

void emitJson(const char* eventType, const char* severity, const char* message) {
  float tempC = readObjectTempC();
  int light = analogRead(PIN_LDR_ANALOG);
  int flame = digitalRead(PIN_FLAME_DIGITAL);
  int reed = digitalRead(PIN_REED_SWITCH);

  Serial.print(F("{\"asset_id\":\"TRANSFORMER-001\",\"event\":\""));
  Serial.print(eventType);
  Serial.print(F("\",\"severity\":\""));
  Serial.print(severity);
  Serial.print(F("\",\"message\":\""));
  Serial.print(message);
  Serial.print(F("\",\"temp_c\":"));
  Serial.print(tempC, 1);
  Serial.print(F(",\"light_level\":"));
  Serial.print(light);
  Serial.print(F(",\"flame_detected\":"));
  Serial.print(flame == FLAME_TRIGGER_LOW ? "true" : "false");
  Serial.print(F(",\"door_open\":"));
  Serial.print(reed == REED_DOOR_OPEN ? "true" : "false");
  Serial.print(F(",\"maintenance_mode\":"));
  Serial.print(maintenanceMode ? "true" : "false");
  Serial.print(F(",\"alert_active\":"));
  Serial.print(alertActive ? "true" : "false");
  Serial.println(F("}"));
}

void handleSerialCommand() {
  if (!Serial.available()) return;

  String cmd = Serial.readStringUntil('\n');
  cmd.trim();
  cmd.toUpperCase();

  if (cmd == "MAINTENANCE_ON") {
    maintenanceMode = true;
    alertActive = false;
    digitalWrite(PIN_LED_ALERT, LOW);
    emitJson("maintenance", "info", "Maintenance mode enabled — alerts suppressed");
  } else if (cmd == "MAINTENANCE_OFF") {
    maintenanceMode = false;
    emitJson("maintenance", "info", "Maintenance mode disabled — monitoring active");
  } else if (cmd == "CALIBRATE") {
    lightBaseline = analogRead(PIN_LDR_ANALOG);
    emitJson("calibration", "info", "Light baseline calibrated");
  } else if (cmd == "PING") {
    emitJson("heartbeat", "info", "Node online");
  }
}

void setAlertLed(bool on) {
  alertActive = on;
  digitalWrite(PIN_LED_ALERT, on ? HIGH : LOW);
}

void setup() {
  pinMode(PIN_REED_SWITCH, INPUT_PULLUP);
  pinMode(PIN_FLAME_DIGITAL, INPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_LED_NORMAL, OUTPUT);
  pinMode(PIN_LED_ALERT, OUTPUT);

  digitalWrite(PIN_BUZZER, LOW);
  digitalWrite(PIN_LED_ALERT, LOW);

  Serial.begin(SERIAL_BAUD);
  while (!Serial && millis() < 3000) { /* wait for USB serial */ }

  Wire.begin();
  if (mlx.begin()) {
    mlxAvailable = true;
  }

  lightBaseline = analogRead(PIN_LDR_ANALOG);
  lastLightReading = lightBaseline;
  doorOpen = digitalRead(PIN_REED_SWITCH) == REED_DOOR_OPEN;

  // Startup chirp
  beepPattern(1);
  emitJson("startup", "info", "SentinelAI node initialized");
}

void loop() {
  handleSerialCommand();

  // Normal LED slow blink
  static unsigned long lastBlink = 0;
  if (millis() - lastBlink > (alertActive ? 150 : 800)) {
    lastBlink = millis();
    digitalWrite(PIN_LED_NORMAL, !digitalRead(PIN_LED_NORMAL));
  }

  unsigned long now = millis();
  if (now - lastReadMs < READ_INTERVAL_MS) return;
  lastReadMs = now;

  float tempC = readObjectTempC();
  int light = analogRead(PIN_LDR_ANALOG);
  int flame = digitalRead(PIN_FLAME_DIGITAL);
  int reed = digitalRead(PIN_REED_SWITCH);
  bool doorIsOpen = reed == REED_DOOR_OPEN;

  // Periodic telemetry
  emitJson("telemetry", "info", "Sensor reading");

  if (maintenanceMode) {
    lastLightReading = light;
    doorOpen = doorIsOpen;
    return;
  }

  // ── Door / reed switch ──────────────────────────────────────────────────
  if (doorIsOpen != doorOpen && now - lastReedChangeMs > DEBOUNCE_MS) {
    lastReedChangeMs = now;
    doorOpen = doorIsOpen;
    if (doorIsOpen) {
      setAlertLed(true);
      beepPattern(1);
      emitJson("door_open", "high", "Cabinet door opened unexpectedly");
    } else {
      emitJson("door_closed", "info", "Cabinet door closed");
    }
  }

  // ── Light spike (torch at night) ────────────────────────────────────────
  int lightDelta = light - lightBaseline;
  if (isNightHours() && lightDelta > LIGHT_SPIKE_DELTA && now - lastLightSpikeMs > 5000) {
    lastLightSpikeMs = now;
    setAlertLed(true);
    beepPattern(2);
    emitJson("light_intrusion", "high", "Unexpected light detected — possible intruder torch");
  }
  lastLightReading = light;

  // ── Flame / IR module ───────────────────────────────────────────────────
  if (flame == FLAME_TRIGGER_LOW && now - lastFlameAlertMs > 5000) {
    lastFlameAlertMs = now;
    setAlertLed(true);
    beepPattern(4);
    emitJson("flame_ir", "medium", "IR/flame sensor triggered — heat or bright IR source");
  }

  // ── Temperature ─────────────────────────────────────────────────────────
  if (tempC >= TEMP_ALERT_C && now - lastTempAlertMs > 10000) {
    lastTempAlertMs = now;
    setAlertLed(true);
    beepPattern(3);
    emitJson("overheat", "critical", "Transformer surface temperature critical");
  } else if (tempC >= TEMP_WARN_C && now - lastTempAlertMs > 15000) {
    lastTempAlertMs = now;
    emitJson("overheat_warn", "medium", "Transformer temperature elevated");
  }

  // Clear alert LED if all conditions normal
  if (!doorIsOpen && lightDelta <= LIGHT_SPIKE_DELTA && flame != FLAME_TRIGGER_LOW && tempC < TEMP_WARN_C) {
    setAlertLed(false);
  }
}
