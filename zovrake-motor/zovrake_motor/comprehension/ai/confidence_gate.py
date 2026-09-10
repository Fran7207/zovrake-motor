"""Decisión conservadora sobre cuándo llamar a OpenAI."""

from __future__ import annotations

from .models import ComprehensionRoute, GateDecision


class OpenAIComprehensionGate:
    """
    Decide la mínima intervención remota necesaria.

    No usa el modelo para documentos que el razonador local ya resolvió.
    """

    EXTREME_PAGES = 80
    EXTREME_CHARS = 220_000
    EXTREME_IMAGES = 24
    EXTREME_TABLES = 18
    EXTREME_UNRESOLVED = 35

    COMPLEX_PAGES = 16
    COMPLEX_CHARS = 70_000
    COMPLEX_IMAGES = 8
    COMPLEX_TABLES = 8
    COMPLEX_UNRESOLVED = 10

    NORMAL_UNRESOLVED = 2
    NORMAL_UNKNOWN_RATIO = 0.08
    NORMAL_CONFLICTS = 1

    def decide(self, knowledge) -> GateDecision:
        metadata = getattr(knowledge, "metadata", {}) or {}
        universal = metadata.get("deep_universal_understanding", {}) or {}
        page_count = int(getattr(knowledge, "page_count", 0) or 0)
        chars = len(str(getattr(knowledge, "ordered_text", "") or getattr(knowledge, "text", "") or ""))
        images = len(getattr(knowledge, "images", ()) or ())
        tables = len(getattr(knowledge, "tables", ()) or ())
        structural_objects = len(getattr(knowledge, "structural_objects", ()) or ())
        unresolved = len(getattr(knowledge, "unresolved", ()) or ())
        conflicts = len(universal.get("conflicts", ()) or ())
        closure = universal.get("semantic_closure", ()) or ()
        unknowns = sum(
            1
            for item in closure
            if isinstance(item, dict) and item.get("semantic_key") == "unknown"
        )
        unknown_ratio = (unknowns / len(closure)) if closure else 0.0
        capture_status = str(
            (getattr(knowledge, "capture_audit", {}) or {}).get("status", "")
        ).strip().lower()
        resolved_roles = universal.get("resolved_roles", ()) or metadata.get(
            "deep_resolved_roles", []
        )
        role_conflicts = sum(
            1
            for item in resolved_roles
            if isinstance(item, dict) and str(item.get("decision", "")).lower() == "ambiguous"
        )

        strong_reasons: list[str] = []
        if page_count >= self.EXTREME_PAGES:
            strong_reasons.append("many_pages")
        if chars >= self.EXTREME_CHARS:
            strong_reasons.append("large_text_volume")
        if images >= self.EXTREME_IMAGES:
            strong_reasons.append("many_images")
        if tables >= self.EXTREME_TABLES:
            strong_reasons.append("many_tables")
        if unresolved >= self.EXTREME_UNRESOLVED:
            strong_reasons.append("many_unresolved_elements")
        if role_conflicts >= 4:
            strong_reasons.append("many_role_ambiguities")
        if any(
            isinstance(item, dict)
            and str(item.get("type", "")).startswith("processing_error")
            for item in (getattr(knowledge, "unresolved", ()) or ())
        ):
            strong_reasons.append("capture_errors")

        if strong_reasons:
            return GateDecision(
                ComprehensionRoute.FULL_PDF,
                1.0,
                tuple(dict.fromkeys(strong_reasons)),
            )

        complex_reasons: list[str] = []
        if page_count >= self.COMPLEX_PAGES:
            complex_reasons.append("many_pages")
        if chars >= self.COMPLEX_CHARS:
            complex_reasons.append("large_text_volume")
        if images >= self.COMPLEX_IMAGES:
            complex_reasons.append("visual_density")
        if tables >= self.COMPLEX_TABLES or structural_objects >= 25:
            complex_reasons.append("structural_complexity")
        if unresolved >= self.COMPLEX_UNRESOLVED:
            complex_reasons.append("unresolved_elements")
        if conflicts >= self.NORMAL_CONFLICTS:
            complex_reasons.append("semantic_conflicts")
        if unknown_ratio >= self.NORMAL_UNKNOWN_RATIO:
            complex_reasons.append("unknown_semantic_terms")
        if capture_status and capture_status not in {"complete", "completed"}:
            complex_reasons.append("capture_not_complete")
        if complex_reasons:
            return GateDecision(
                ComprehensionRoute.FULL_PDF if page_count >= 24 or chars >= 120_000
                else ComprehensionRoute.SELECTED_EVIDENCE,
                0.85 if page_count >= 24 or chars >= 120_000 else 0.65,
                tuple(dict.fromkeys(complex_reasons)),
            )

        normal_reasons: list[str] = []
        if unresolved > 0:
            normal_reasons.append("unresolved_elements")
        if conflicts > 0:
            normal_reasons.append("semantic_conflicts")
        if unknown_ratio >= self.NORMAL_UNKNOWN_RATIO:
            normal_reasons.append("unknown_semantic_terms")
        if role_conflicts > 0:
            normal_reasons.append("ambiguous_roles")
        if not resolved_roles:
            normal_reasons.append("roles_not_resolved")

        # Documento pequeño y coherente: cero llamadas.
        if (
            page_count <= 6
            and chars <= 35_000
            and images <= 4
            and tables <= 4
            and structural_objects <= 20
            and unresolved <= self.NORMAL_UNRESOLVED
            and conflicts == 0
            and role_conflicts == 0
            and unknown_ratio < self.NORMAL_UNKNOWN_RATIO
            and resolved_roles
        ):
            return GateDecision(
                ComprehensionRoute.LOCAL_ONLY,
                0.10,
                ("local_confidence_sufficient",),
            )

        return GateDecision(
            ComprehensionRoute.SELECTED_EVIDENCE,
            0.35,
            tuple(dict.fromkeys(normal_reasons or ["additional_semantic_resolution_needed"])),
        )
