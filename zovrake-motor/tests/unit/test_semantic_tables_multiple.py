"""Pruebas unitarias de reconstrucción semántica de tablas PDF."""

from __future__ import annotations

from zovrake_motor.comprehension.pdf_processing.models import (
    PdfTextBlock,
)
from zovrake_motor.comprehension.pdf_processing.semantic_tables import (
    PdfSemanticTableAnalyzer,
)


def _block(
    index: int,
    text: str,
    x: float,
    y: float,
    width: float = 60.0,
) -> PdfTextBlock:
    return PdfTextBlock(
        block_id=f"block-{index}",
        page_number=1,
        text=text,
        bbox=(x, y, x + width, y + 12.0),
    )


def _table_blocks(
    start_index: int,
    header_y: float,
    code: str,
    description: str,
    quantity: str,
    total: str,
) -> list[PdfTextBlock]:
    values = (
        ("CODIGO", 40.0, 60.0),
        ("DESCRIPCION", 140.0, 100.0),
        ("CANTIDAD", 300.0, 70.0),
        ("TOTAL", 410.0, 60.0),
        (code, 40.0, 60.0),
        (description, 140.0, 100.0),
        (quantity, 300.0, 70.0),
        (total, 410.0, 60.0),
    )

    blocks: list[PdfTextBlock] = []

    for offset, (text, x, width) in enumerate(values):
        y = (
            header_y
            if offset < 4
            else header_y + 26.0
        )
        blocks.append(
            _block(
                start_index + offset,
                text,
                x,
                y,
                width,
            )
        )

    return blocks


def test_layout_analysis_reconstructs_multiple_tables_on_one_page() -> None:
    blocks = (
        _table_blocks(
            1,
            80.0,
            "A-001",
            "CEMENTO",
            "10",
            "255.00",
        )
        + _table_blocks(
            20,
            260.0,
            "B-002",
            "ARENA",
            "5",
            "125.00",
        )
    )

    tables = PdfSemanticTableAnalyzer().analyze_page(
        page_number=1,
        text_blocks=blocks,
        page_width=500.0,
        page_height=500.0,
    )

    assert len(tables) == 2

    assert tables[0].table_id == (
        "page-1-semantic-table-1"
    )
    assert tables[1].table_id == (
        "page-1-semantic-table-2"
    )

    assert tables[0].rows == (
        {
            "code": "A-001",
            "description": "CEMENTO",
            "quantity": "10",
            "total": "255.00",
        },
    )
    assert tables[1].rows == (
        {
            "code": "B-002",
            "description": "ARENA",
            "quantity": "5",
            "total": "125.00",
        },
    )


def test_layout_analysis_keeps_single_table_behavior() -> None:
    blocks = _table_blocks(
        1,
        80.0,
        "A-001",
        "CEMENTO",
        "10",
        "255.00",
    )

    tables = PdfSemanticTableAnalyzer().analyze_page(
        page_number=1,
        text_blocks=blocks,
        page_width=500.0,
        page_height=500.0,
    )

    assert len(tables) == 1
    assert len(tables[0].columns) == 4
    assert len(tables[0].rows) == 1


def test_header_semantics_prioritize_specific_price_phrases() -> None:
    analyzer = PdfSemanticTableAnalyzer()

    assert analyzer._classify_header("PRECIO TOTAL") == ("total", 0.98)
    assert analyzer._classify_header("S/.TOTAL") == ("total", 0.98)
    assert analyzer._classify_header("S/P.U.") == ("unit_price", 0.98)
    assert analyzer._classify_header("PRECIO UNITARIO") == ("unit_price", 0.98)


def test_physical_analysis_filters_administrative_rows_after_table_role_classification() -> None:
    analyzer = PdfSemanticTableAnalyzer()

    table = type(
        "PdfTableStub",
        (),
        {
            "table_id": "quote-mixed",
            "page_number": 1,
            "rows": (
                ("ITEM", "DESCRIPCIÓN", "UNID.", "CANT.", "S/P.U.", "S/.TOTAL"),
                ("", "Razón Social", "", "INVERSIONES EVZA S.R.L.", "", ""),
                ("1", "Tubería PVC-U UF 110MM PN5", "UND", "1", "160.00", "160.00"),
                ("", "Subtotal", "", "", "", "160.00"),
            ),
        },
    )()

    semantic = analyzer.analyze(table)

    assert semantic is not None
    assert semantic.table_role == "commercial_items"
    assert semantic.rows == (
        {
            "code": "1",
            "description": "Tubería PVC-U UF 110MM PN5",
            "unit": "UND",
            "quantity": "1",
            "unit_price": "160.00",
            "total": "160.00",
        },
    )
