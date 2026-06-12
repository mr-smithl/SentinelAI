"""Read JSON lines from Arduino serial port and forward to the API."""

from __future__ import annotations

import json
import logging
import threading
import time
from typing import Callable, Optional

logger = logging.getLogger("sentinel.serial")

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    serial = None  # type: ignore
    list_ports = None  # type: ignore


def list_serial_ports() -> list[str]:
    if list_ports is None:
        return []
    return [p.device for p in list_ports.comports()]


class SerialBridge:
    def __init__(self, on_event: Callable[[dict], None], port: Optional[str] = None, baud: int = 115200):
        self.on_event = on_event
        self.port = port
        self.baud = baud
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._ser = None

    def start(self) -> bool:
        if serial is None:
            logger.warning("pyserial not installed — serial bridge disabled")
            return False

        if not self.port:
            ports = list_serial_ports()
            if not ports:
                logger.warning("No serial ports found — connect Arduino via USB")
                return False
            # Prefer COM ports that look like Arduino on Windows
            self.port = ports[0]
            logger.info("Auto-selected serial port: %s", self.port)

        try:
            self._ser = serial.Serial(self.port, self.baud, timeout=1)
        except Exception as exc:
            logger.error("Failed to open %s: %s", self.port, exc)
            return False

        self._stop.clear()
        self._thread = threading.Thread(target=self._read_loop, daemon=True, name="serial-bridge")
        self._thread.start()
        logger.info("Serial bridge listening on %s @ %d", self.port, self.baud)
        return True

    def stop(self) -> None:
        self._stop.set()
        if self._ser and self._ser.is_open:
            self._ser.close()

    def send_command(self, command: str) -> bool:
        if not self._ser or not self._ser.is_open:
            return False
        try:
            self._ser.write(f"{command.strip()}\n".encode())
            return True
        except Exception as exc:
            logger.error("Serial write failed: %s", exc)
            return False

    def _read_loop(self) -> None:
        buffer = ""
        while not self._stop.is_set():
            try:
                if not self._ser or not self._ser.is_open:
                    time.sleep(0.5)
                    continue
                raw = self._ser.readline()
                if not raw:
                    continue
                line = raw.decode("utf-8", errors="ignore").strip()
                if not line.startswith("{"):
                    continue
                payload = json.loads(line)
                self.on_event(payload)
            except json.JSONDecodeError:
                logger.debug("Skipping non-JSON line: %s", line[:80] if line else "")
            except Exception as exc:
                logger.error("Serial read error: %s", exc)
                time.sleep(1)
