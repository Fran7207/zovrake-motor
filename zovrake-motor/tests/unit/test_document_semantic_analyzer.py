"""Pruebas del análisis semántico inicial de DocumentKnowledge."""

from __future__ import annotations

from zovrake_motor.comprehension.document_semantic_analyzer import (
    DocumentSemanticAnalyzer,
)
from zovrake_motor.comprehension.models import (
    DocumentEvidence,
    DocumentKnowledge,
    DocumentRegion,
)


def build_knowledge(
    regions: tuple[DocumentRegion, ...],
) -> DocumentKnowledge:
    evidence = tuple(
        DocumentEvidence(
            evidence_id=f"evidence-{region.region_id}",
            source_kind=region.source_kind,
            source_id=region.region_id,
            page_number=region.page_number,
            text=region.content,
            bbox=region.bbox,
            confidence=region.confidence,
        )
        for region in regions
    )

    return DocumentKnowledge(
        document_id="DOC-SEMANTIC-001",
        file_name="documento.pdf",
        content_type="application/pdf",
        page_count=2,
        regions=regions,
        text="\n".join(
            region.content
            for region in regions
        ),
        evidence=evidence,
        metadata={
            "fixture": "unit",
        },
    )


def test_analyzer_classifies_independent_document_contexts() -> None:
    knowledge = build_knowledge(
        (
            DocumentRegion(
                region_id="r-provider",
                page_number=1,
                region_type="text_block",
                content="DATOS DEL PROVEEDOR",
                source_kind="native_text",
                confidence=1.0,
            ),
            DocumentRegion(
                region_id="r-customer",
                page_number=1,
                region_type="text_block",
                content="DATOS DEL CLIENTE",
                source_kind="native_text",
                confidence=1.0,
            ),
            DocumentRegion(
                region_id="r-conditions",
                page_number=1,
                region_type="text_block",
                content="CONDICIONES DE PAGO: 30 días",
                source_kind="native_text",
                confidence=1.0,
            ),
            DocumentRegion(
                region_id="r-financial",
                page_number=2,
                region_type="text_block",
                content="SUBTOTAL 1000 IGV 180 TOTAL 1180",
                source_kind="native_text",
                confidence=1.0,
            ),
            DocumentRegion(
                region_id="r-technical",
                page_number=2,
                region_type="text_block",
                content="ESPECIFICACIONES TÉCNICAS Y MATERIAL",
                source_kind="native_text",
                confidence=1.0,
            ),
        )
    )

    result = DocumentSemanticAnalyzer().analyze(
        knowledge
    )

    sections_by_region = {
        section["region_id"]: section["section_type"]
        for section in result.sections
    }

    assert sections_by_region["r-provider"] == "provider_identity"
    assert sections_by_region["r-customer"] == "customer_identity"
    assert sections_by_region["r-conditions"] == "conditions"
    assert sections_by_region["r-financial"] == "financial"
    assert sections_by_region["r-technical"] == "technical"


def test_analyzer_preserves_document_content_and_evidence() -> None:
    regions = (
        DocumentRegion(
            region_id="r-001",
            page_number=1,
            region_type="text_block",
            content="Texto original que no debe modificarse.",
            source_kind="native_text",
            confidence=1.0,
            metadata={
                "custom_field": "preservar",
            },
        ),
        DocumentRegion(
            region_id="r-002",
            page_number=2,
            region_type="image",
            content="",
            source_kind="pdf_image",
            confidence=1.0,
            metadata={
                "image_id": "img-002",
            },
        ),
    )

    knowledge = build_knowledge(regions)

    result = DocumentSemanticAnalyzer().analyze(
        knowledge
    )

    assert result.text == knowledge.text
    assert result.evidence == knowledge.evidence
    assert result.tables == knowledge.tables
    assert result.images == knowledge.images
    assert result.ocr_blocks == knowledge.ocr_blocks
    assert result.unresolved == knowledge.unresolved

    assert len(result.regions) == len(knowledge.regions)

    original = knowledge.regions[0]
    analyzed = result.regions[0]

    assert analyzed.region_id == original.region_id
    assert analyzed.page_number == original.page_number
    assert analyzed.content == original.content
    assert analyzed.bbox == original.bbox
    assert analyzed.source_kind == original.source_kind
    assert analyzed.metadata["custom_field"] == "preservar"

    assert (
        analyzed.metadata["semantic_model_version"]
        == DocumentSemanticAnalyzer.MODEL_VERSION
    )
    assert (
        analyzed.metadata["document_section"]
        == "unknown"
    )


def test_analyzer_uses_semantic_table_role_when_text_is_not_descriptive() -> None:
    knowledge = build_knowledge(
        (
            DocumentRegion(
                region_id="r-table-001",
                page_number=1,
                region_type="semantic_table",
                content="A B C",
                source_kind="semantic_table",
                confidence=0.9,
                metadata={
                    "table_role": "financial",
                },
            ),
        )
    )

    result = DocumentSemanticAnalyzer().analyze(
        knowledge
    )

    region = result.regions[0]

    assert (
        region.metadata["document_section"]
        == "financial"
    )
    assert (
        region.metadata["semantic_context_confidence"]
        == 0.85
    )
    assert "table_role:financial" in (
        region.metadata["semantic_hints"]
    )


def test_analyzer_marks_competing_contexts_as_unknown() -> None:
    knowledge = build_knowledge(
        (
            DocumentRegion(
                region_id="r-ambiguous",
                page_number=1,
                region_type="text_block",
                content=(
                    "DATOS DEL CLIENTE "
                    "DATOS DEL PROVEEDOR"
                ),
                source_kind="native_text",
                confidence=1.0,
            ),
        )
    )

    result = DocumentSemanticAnalyzer().analyze(
        knowledge
    )

    region = result.regions[0]

    assert (
        region.metadata["document_section"]
        == "unknown"
    )
    assert (
        region.metadata["semantic_context_confidence"]
        < 0.5
    )
    assert (
        "ambiguous_semantic_context"
        in region.metadata["semantic_hints"]
    )
    assert result.sections == ()


def test_analyzer_rejects_invalid_input() -> None:
    analyzer = DocumentSemanticAnalyzer()

    try:
        analyzer.analyze(None)  # type: ignore[arg-type]
    except TypeError as exc:
        assert "DocumentKnowledge" in str(exc)
    else:
        raise AssertionError(
            "Se esperaba TypeError para entrada inválida."
        )