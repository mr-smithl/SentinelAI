/*
 ═══════════════════════════════════════════════════════════════
   SentinelAI — Arduino sketch (4-pin KY-026 version)

   YOUR EXACT KIT:
     KY-026 Flame sensor (4 pins: VCC · GND · DO · AO)
       DO  → D2  (digital interrupt — instant fire alert)
       AO  → A1  (analog 0–1023 — flame intensity for score)
     Reed switch module (3 pins: VCC · GND · S)
       S   → D3  (tamper: magnet removed = HIGH)
     KY-018 LDR (3 pins: VCC · GND · S)
       S   → A0  (cover disc = darkness = intruder)
     KY-012 Buzzer (3 pins: VCC · GND · S)
       S   → D7
     Yellow LED alert   → D8  (+ 220Ω to GND)
     Yellow LED status  → D9  (+ 220Ω to GND)
     Arduino Uno        → USB to laptop

   HOW TO TRIGGER EACH ALERT FOR DEMO:
     Fire/heat  → Wave hand near KY-026 IR eye (or lighter)
     Door tamper→ Pull magnet away from reed switch module
     Intruder   → Cover the LDR disc fully with your thumb

   Output: JSON on Serial 9600 baud → serial_bridge.py
 ═══════════════════════════════════════════════════════════════
*/

// ── PINS ─────────────────────────────────────────────────────────
#define PIN_FLAME_DO   2    // KY-026 digital out  (LOW = flame!)
#define PIN_REED       3    // Reed switch          (HIGH = tamper)
#define PIN_FLAME_AO   A1   // KY-026 analog out    (0=bright flame, 1023=none)
#define PIN_LDR        A0   // KY-018 LDR           (low = dark = intruder)
#define PIN_BUZZER     7    // KY-012 active buzzer
#define PIN_LED_ALERT  8    // Yellow LED — alert flash
#define PIN_LED_STATUS 9    // Yellow LED — status on = online

// ── NODE IDENTITY ─────────────────────────────────────────────────
#define NODE_ID    "NODE-01"
#define LOCATION   "Transformer-001, Solland Substation, Vereeniging, Gauteng"

// ── THRESHOLDS ────────────────────────────────────────────────────
// LDR: lower reading = darker = suspicious
// Open Serial Monitor and read A0 value in normal light, then set
// threshold at ~60% of that value. Typical: 600-700 in normal light.
#define LDR_DARK_THRESHOLD  700

// Cooldown: min milliseconds between alerts of same type
#define COOLDOWN_MS  15000UL

// ── STATE ─────────────────────────────────────────────────────────
volatile bool flameFired = false;   // set by interrupt
unsigned long lastFlame  = 0;
unsigned long lastReed   = 0;
unsigned long lastLDR    = 0;
unsigned long lastHB     = 0;
bool prevReed = LOW;   // tracks reed state change

// ── ISR: flame DO fires LOW when flame detected ───────────────────
void onFlame() {
  flameFired = true;
}

// ═════════════════════════════════════════════════════════════════
void setup() {
  Serial.begin(9600);

  pinMode(PIN_FLAME_DO, INPUT);
  pinMode(PIN_REED,     INPUT_PULLUP);
  pinMode(PIN_BUZZER,   OUTPUT);
  pinMode(PIN_LED_ALERT,  OUTPUT);
  pinMode(PIN_LED_STATUS, OUTPUT);

  // KY-026 DO goes LOW when flame detected → FALLING trigger
  attachInterrupt(digitalPinToInterrupt(PIN_FLAME_DO), onFlame, FALLING);

  bootSequence();
  sendJSON("boot", "1", "0", "System online");
  digitalWrite(PIN_LED_STATUS, HIGH);  // steady on = ready
}

// ═════════════════════════════════════════════════════════════════
void loop() {
  unsigned long now = millis();

  // ── 1. FLAME DETECTION (KY-026 DO interrupt) ─────────────────
  if (flameFired && canAlert(lastFlame, now)) {
    flameFired = false;
    lastFlame  = now;

    // Read AO for intensity → convert to risk score
    int aoVal    = analogRead(PIN_FLAME_AO);
    // AO: 0 = strong flame, 1023 = no flame
    // Map inverted: low AO = high score
    int score    = map(aoVal, 1023, 0, 50, 99);
    score        = constrain(score, 50, 99);

    String msg = "Flame/heat detected. AO=" + String(aoVal) + " intensity=" + String(100 - (aoVal * 100 / 1023)) + "%";
    sendJSON("flame", "1", String(score), msg);
    buzzerAlert(3, true);   // 3 loud bursts
  }
  flameFired = false;  // clear any stray ISR calls

  // ── 2. DOOR TAMPER (Reed switch) ─────────────────────────────
  // With INPUT_PULLUP: magnet ON = pulled LOW, magnet OFF = HIGH
  bool reedNow = digitalRead(PIN_REED);
  if (reedNow == HIGH && prevReed == LOW && canAlert(lastReed, now)) {
    // Transition LOW→HIGH = magnet just removed = tamper!
    lastReed = now;
    sendJSON("tamper", "1", "94", "Cabinet door opened — magnet removed");
    buzzerAlert(5, true);   // 5 loud bursts = highest priority
  }
  prevReed = reedNow;

  // ── 3. INTRUDER (LDR — cover = dark = person present) ────────
  int ldrVal = analogRead(PIN_LDR);
  if (ldrVal < LDR_DARK_THRESHOLD && canAlert(lastLDR, now)) {
    lastLDR = now;
    // Darker = higher score
    int score = map(ldrVal, LDR_DARK_THRESHOLD, 0, 55, 85);
    score = constrain(score, 55, 85);
    String msg = "Motion/obstruction detected. LDR=" + String(ldrVal);
    sendJSON("motion", "1", String(score), msg);
    buzzerAlert(2, false);  // 2 short bursts = medium priority
  }

  // ── 4. HEARTBEAT every 30 sec ────────────────────────────────
  if (now - lastHB > 30000UL) {
    lastHB = now;
    int ldr   = analogRead(PIN_LDR);
    int flame = analogRead(PIN_FLAME_AO);
    Serial.print("{\"type\":\"heartbeat\",\"node\":\"" NODE_ID "\",");
    Serial.print("\"value\":\"1\",\"score\":0,");
    Serial.print("\"ldr\":");   Serial.print(ldr);
    Serial.print(",\"flame\":"); Serial.print(flame);
    Serial.println("}");
  }

  delay(150);
}

// ═══════════════ HELPERS ═════════════════════════════════════════

bool canAlert(unsigned long lastTime, unsigned long now) {
  return (now - lastTime) > COOLDOWN_MS;
}

void sendJSON(String type, String value, String score, String msg) {
  digitalWrite(PIN_LED_ALERT, HIGH);
  Serial.print("{\"type\":\"");    Serial.print(type);
  Serial.print("\",\"node\":\"");  Serial.print(NODE_ID);
  Serial.print("\",\"location\":\""); Serial.print(LOCATION);
  Serial.print("\",\"value\":\""); Serial.print(value);
  Serial.print("\",\"score\":");   Serial.print(score);
  Serial.print(",\"msg\":\"");     Serial.print(msg);
  Serial.println("\"}");
  delay(300);
  digitalWrite(PIN_LED_ALERT, LOW);
}

void buzzerAlert(int bursts, bool loud) {
  for (int i = 0; i < bursts; i++) {
    digitalWrite(PIN_LED_ALERT, HIGH);
    digitalWrite(PIN_BUZZER, HIGH);
    delay(loud ? 180 : 80);
    digitalWrite(PIN_BUZZER, LOW);
    digitalWrite(PIN_LED_ALERT, LOW);
    delay(100);
  }
}

void bootSequence() {
  for (int i = 0; i < 3; i++) {
    digitalWrite(PIN_LED_ALERT,  HIGH);
    digitalWrite(PIN_LED_STATUS, LOW);
    delay(180);
    digitalWrite(PIN_LED_ALERT,  LOW);
    digitalWrite(PIN_LED_STATUS, HIGH);
    delay(180);
  }
  digitalWrite(PIN_LED_STATUS, LOW);
}
