# Arduino Setup

## Libraries

Install via Arduino IDE → **Sketch → Include Library → Manage Libraries**:

1. **Adafruit MLX90614** (by Adafruit)
2. **Adafruit BusIO** (dependency, auto-installed)

## Upload

1. Connect Arduino Uno via USB
2. Board: **Arduino Uno**
3. Port: your COM port (e.g. COM3 on Windows)
4. Open `sentinel_node/sentinel_node.ino`
5. Upload

## Serial Monitor

- Baud: **115200**
- You should see JSON lines like:

```json
{"asset_id":"TRANSFORMER-001","event":"telemetry","severity":"info",...}
```

## Wiring

See `TEAM.md` pin map. All modules use 5V and GND from breadboard rails.

**Reed switch:** use INPUT_PULLUP on D2 — magnet near = LOW (door closed), away = HIGH (open).

**Buzzer:** active buzzer module — signal pin to D8.

**LDR module:** AO to A0, DO optional (we use analog).

**MLX90614:** VCC, GND, SDA (A4), SCL (A5).

If MLX90614 is not connected, firmware falls back to simulated temperature from A1.
