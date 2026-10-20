#!/usr/bin/env python3
"""
Punto de entrada para ejecutar el servidor FastAPI TurismoIA San Martín con Uvicorn.
Uso:
    python run.py
O mediante uvicorn:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(PROJECT_ROOT / "ml_engine") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "ml_engine"))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
