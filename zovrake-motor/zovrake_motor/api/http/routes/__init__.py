"""Rutas REST agrupadas."""

from zovrake_motor.api.http.routes.analyses import router as analyses_router
from zovrake_motor.api.http.routes.health import router as health_router
from zovrake_motor.api.http.routes.info import router as info_router

__all__ = ["analyses_router", "health_router", "info_router"]
