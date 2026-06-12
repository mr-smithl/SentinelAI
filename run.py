#!/usr/bin/env python3
"""Start SentinelAI backend server."""

import os
import sys

# Ensure project root is on path when run directly
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import uvicorn

if __name__ == "__main__":
    host = os.getenv("SENTINEL_HOST", "127.0.0.1")
    port = int(os.getenv("SENTINEL_PORT", "8000"))
    print(f"Starting SentinelAI on http://{host}:{port}")
    print("API docs: http://127.0.0.1:8000/docs")
    dist = os.path.join(ROOT, "frontend", "dist", "index.html")
    if os.path.isfile(dist):
        print("Dashboard: http://127.0.0.1:8000")
    else:
        print("Dashboard dev: cd frontend && npm run dev  →  http://localhost:5173")
    uvicorn.run("backend.main:app", host=host, port=port, reload=False)
