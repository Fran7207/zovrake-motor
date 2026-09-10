"""Adaptador server-side de OpenAI Responses API para ZOVRAKE."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from typing import Any

from .cache import LocalAIComprehensionCache
from .models import AIComprehensionResult, ComprehensionRoute
from .prompt_policy import SCHEMA, SYSTEM_INSTRUCTIONS, build_user_prompt
from .response_validator import validate_understanding


class OpenAIComprehensionProvider:
    """
    Única capa que conoce el SDK de OpenAI.

    La clave nunca se recibe del frontend ni se guarda en el código.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        cache: LocalAIComprehensionCache | None = None,
    ) -> None:
        self.api_key = (
            api_key
            or os.getenv("ZOVRAKE_OPENAI_API_KEY", "")
            or os.getenv("OPENAI_API_KEY", "")
        ).strip()
        self.model = (
            model
            or os.getenv("ZOVRAKE_OPENAI_MODEL", "gpt-5.6-luna")
        ).strip()
        self.cache = cache or LocalAIComprehensionCache()
        self._client = None

    @property
    def configured(self) -> bool:
        enabled = os.getenv("ZOVRAKE_OPENAI_ENABLED", "auto").strip().lower()
        if enabled in {"0", "false", "no", "off", "disabled"}:
            return False
        return bool(self.api_key)

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not self.api_key:
            raise RuntimeError(
                "No hay API key configurada. Define ZOVRAKE_OPENAI_API_KEY "
                "o OPENAI_API_KEY en el servidor."
            )
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "Falta la dependencia 'openai'. Ejecuta la instalación de "
                "dependencias del proyecto ZOVRAKE."
            ) from exc
        self._client = OpenAI(api_key=self.api_key)
        return self._client

    def comprehend(
        self,
        *,
        knowledge,
        route: ComprehensionRoute,
        selected_context: dict[str, Any],
        pdf_bytes: bytes | None = None,
    ) -> AIComprehensionResult:
        route = ComprehensionRoute(route)
        if route is ComprehensionRoute.LOCAL_ONLY:
            return AIComprehensionResult(
                success=False,
                route=route,
                model=self.model,
                error="route_local_only",
            )

        raw_pdf = bytes(pdf_bytes or b"")
        document_hash = (
            hashlib.sha256(raw_pdf).hexdigest()
            if raw_pdf
            else hashlib.sha256(
                (
                    str(getattr(knowledge, "document_id", ""))
                    + "\n"
                    + str(getattr(knowledge, "file_name", ""))
                ).encode("utf-8")
            ).hexdigest()
        )
        cache_key = self.cache.key(
            document_hash=document_hash,
            route=route.value,
            model=self.model,
            selected_context=selected_context,
        )

        cached = self.cache.get(cache_key)
        if cached:
            return AIComprehensionResult(
                success=True,
                route=route,
                model=self.model,
                output=cached.get("output", {}),
                cache_hit=True,
                response_id=str(cached.get("response_id", "")),
                input_character_count=int(
                    cached.get("input_character_count", 0)
                ),
            )

        prompt = build_user_prompt(
            knowledge=knowledge,
            route=route.value,
            selected_context=selected_context,
            include_full_pdf=route is ComprehensionRoute.FULL_PDF,
        )

        try:
            client = self._get_client()
            content: list[dict[str, Any]] = [
                {"type": "input_text", "text": prompt}
            ]

            if route is ComprehensionRoute.FULL_PDF:
                if not raw_pdf:
                    # Sin bytes reales, no mentimos diciendo que enviamos el PDF.
                    raise RuntimeError(
                        "La ruta full_pdf requiere los bytes del PDF."
                    )
                content.append(
                    {
                        "type": "input_file",
                        "filename": (
                            str(getattr(knowledge, "file_name", "document.pdf"))
                            or "document.pdf"
                        ),
                        "file_data": (
                            "data:application/pdf;base64,"
                            + base64.b64encode(raw_pdf).decode("ascii")
                        ),
                    }
                )
            else:
                for image in selected_context.get("selected_images", ()) or ():
                    data_url = str(image.get("image_data_url", "")).strip()
                    if data_url:
                        content.append(
                            {
                                "type": "input_image",
                                "image_url": data_url,
                                "detail": str(
                                    image.get("detail", "low")
                                ),
                            }
                        )

            response = client.responses.create(
                model=self.model,
                instructions=SYSTEM_INSTRUCTIONS,
                input=[{"role": "user", "content": content}],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "zovrake_document_understanding",
                        "description": (
                            "Structured universal document understanding "
                            "for ZOVRAKE."
                        ),
                        "schema": SCHEMA,
                        "strict": True,
                    }
                },
                store=False,
            )

            raw_output = str(
                getattr(response, "output_text", "") or ""
            ).strip()
            if not raw_output:
                raise RuntimeError(
                    "OpenAI no devolvió contenido estructurado."
                )

            parsed = validate_understanding(json.loads(raw_output))
            result = AIComprehensionResult(
                success=True,
                route=route,
                model=self.model,
                output=parsed,
                cache_hit=False,
                response_id=str(getattr(response, "id", "") or ""),
                input_character_count=len(prompt),
            )

            self.cache.set(
                cache_key,
                {
                    "output": parsed,
                    "response_id": result.response_id,
                    "input_character_count": result.input_character_count,
                },
            )
            return result

        except Exception as exc:
            return AIComprehensionResult(
                success=False,
                route=route,
                model=self.model,
                error=str(exc),
                input_character_count=len(prompt),
            )
