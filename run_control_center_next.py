from __future__ import annotations

import os

import uvicorn

from backend.app.main import app


def main() -> None:
    host = os.environ.get("CONTROL_CENTER_NEXT_HOST", "127.0.0.1")
    port = int(os.environ.get("CONTROL_CENTER_NEXT_UI_PORT", "3210"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
