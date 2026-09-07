from zovrake_motor.comprehension.deep_document_comprehension import DeepDocumentComprehensionEngine
from zovrake_motor.comprehension.models import DocumentEvidence, DocumentKnowledge, DocumentRegion


def test_universal_comprehension_uses_multilayer_evidence_without_quote_template():
    knowledge = DocumentKnowledge(
        document_id="generic-doc",
        file_name="manual.pdf",
        page_count=2,
        text="Technical specification\nSerial Number: AB-9001\nTemperature: 25 °C",
        visual_text="Diagram\nRevision: B",
        regions=(
            DocumentRegion(
                region_id="r1", page_number=1, region_type="text_block",
                bbox=(10, 10, 120, 22), content="Technical specification",
                source_kind="native_text", confidence=1.0,
            ),
            DocumentRegion(
                region_id="r2", page_number=1, region_type="text_block",
                bbox=(10, 30, 220, 42), content="Serial Number: AB-9001",
                source_kind="native_text", confidence=1.0,
            ),
            DocumentRegion(
                region_id="r3", page_number=1, region_type="text_block",
                bbox=(10, 50, 220, 62), content="Temperature: 25 °C",
                source_kind="native_text", confidence=1.0,
            ),
            DocumentRegion(
                region_id="r4", page_number=2, region_type="page_visual",
                bbox=(0, 0, 300, 400), content="Diagram",
                source_kind="visual_understanding", confidence=0.8,
                metadata={"object_type": "diagram_or_chart", "semantic_hints": ["technical"]},
            ),
        ),
        evidence=(
            DocumentEvidence("e1", "native_text", "r1", 1, "Technical specification", (10,10,120,22), 1.0, {"region_id":"r1"}),
            DocumentEvidence("e2", "native_text", "r2", 1, "Serial Number: AB-9001", (10,30,220,42), 1.0, {"region_id":"r2"}),
            DocumentEvidence("e3", "native_text", "r3", 1, "Temperature: 25 °C", (10,50,220,62), 1.0, {"region_id":"r3"}),
            DocumentEvidence("e4", "visual_understanding", "r4", 2, "Diagram", (0,0,300,400), 0.8, {"region_id":"r4"}),
        ),
        facts=(
            {"fact_id":"f1","label":"Serial Number","normalized_label":"serial number","raw_value":"AB-9001","page_number":1,"region_id":"r2","evidence_id":"e2","confidence":0.98},
        ),
        attributes=(
            {"attribute_id":"a1","name":"Revision","raw_label":"Revision","value":"B","page_number":2,"region_id":"r4","evidence_id":"e4","confidence":0.9},
        ),
    )

    result = DeepDocumentComprehensionEngine().comprehend(knowledge)
    names = {concept["name"] for concept in result.metadata["deep_semantic_concepts"]}

    assert "serial_number" in names
    assert "temperature" in names
    assert result.metadata["deep_comprehension_profile"]["document_kind"] in {"technical_specification", "structured_document", "general"}
    assert result.metadata["deep_comprehension_coverage"]["page_coverage"] == 1.0
    assert result.metadata["deep_comprehension_schema_version"] == "deep-comprehension-schema-v2"


def test_table_math_is_scoped_to_the_same_row_and_supports_thousands_separator():
    knowledge = DocumentKnowledge(
        document_id="table-doc",
        page_count=1,
        regions=(
            DocumentRegion(
                region_id="table-region",
                page_number=1,
                region_type="semantic_table",
                content=(
                    "quantity=2370 | unit=MT2 | description=TRACK | "
                    "unit_price=$58.82 | total=$139,403.40\n"
                    "quantity=2 | unit=EA | description=OTHER | "
                    "unit_price=$10.00 | total=$25.00"
                ),
                source_kind="semantic_table",
                confidence=0.95,
                metadata={"table_id":"table-1","source_page_number":1,"table_role":"unknown"},
            ),
        ),
    )

    result = DeepDocumentComprehensionEngine().comprehend(knowledge)
    rows = result.metadata["deep_table_findings"][0]["rows"]

    assert rows[0]["status"] == "consistent"
    assert rows[0]["expected_total"] == "139403.40"
    assert rows[1]["status"] == "inconsistent"
    assert result.metadata["deep_consistency"]["numeric_inconsistency_count"] == 1
