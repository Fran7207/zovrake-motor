"""Arranque del servidor HTTP con Uvicorn."""

from __future__ import annotations

import argparse

import uvicorn

from zovrake_motor.api.http.app import create_app


def serve(
    *,
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
) -> None:
    uvicorn.run(
        "zovrake_motor.api.http.app:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Servidor REST oficial del Motor Inteligente ZOVRAKE",
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()
    serve(host=args.host, port=args.port, reload=args.reload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
