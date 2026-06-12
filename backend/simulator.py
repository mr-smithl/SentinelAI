"""Standalone sensor event simulator when Arduino is not connected."""

from __future__ import annotations

import argparse
import json
import time
import urllib.request


def post_event(base_url: str, payload: dict) -> None:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/events",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        print(resp.read().decode())


def main() -> None:
    parser = argparse.ArgumentParser(description="SentinelAI sensor simulator")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--scenario", choices=["door_open", "light_intrusion", "overheat", "flame_ir", "telemetry"], default="telemetry")
    parser.add_argument("--interval", type=float, default=2.0)
    args = parser.parse_args()

    scenarios = {
        "door_open": {"event": "door_open", "severity": "high", "message": "Door opened", "door_open": True, "temp_c": 40, "light_level": 120},
        "light_intrusion": {"event": "light_intrusion", "severity": "high", "message": "Torch detected", "light_level": 900, "temp_c": 35},
        "overheat": {"event": "overheat", "severity": "critical", "message": "Overheat", "temp_c": 88, "light_level": 100},
        "flame_ir": {"event": "flame_ir", "severity": "medium", "message": "IR spike", "flame_detected": True, "light_level": 500, "temp_c": 50},
        "telemetry": {"event": "telemetry", "severity": "info", "message": "Normal reading", "temp_c": 38, "light_level": 110, "door_open": False},
    }

    print(f"Posting {args.scenario} to {args.url} every {args.interval}s (Ctrl+C to stop)")
    while True:
        payload = {"asset_id": "TRANSFORMER-001", **scenarios[args.scenario]}
        try:
            post_event(args.url, payload)
            print("OK", payload["event"])
        except Exception as exc:
            print("Error:", exc)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
