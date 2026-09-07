from zovrake_motor.comprehension.deep_document_comprehension import DeepDocumentComprehensionEngine
from zovrake_motor.comprehension.models import DocumentKnowledge


def _knowledge():
    return DocumentKnowledge(
        document_id='deterministic-test',
        page_count=1,
        text='Proveedor: ACME S.A.C.\nPrecio unitario: S/ 10.00\nCantidad: 2\nTotal: S/ 20.00',
        attributes=(
            {'attribute_id':'a1','name':'provider','raw_label':'Proveedor','value':'ACME S.A.C.','normalized_value':'acme s.a.c.','page_number':1,'region_id':'r1','evidence_id':'e1','confidence':0.9},
            {'attribute_id':'a2','name':'unit_price','raw_label':'Precio unitario','value':'S/ 10.00','normalized_value':'10.00','page_number':1,'region_id':'r2','evidence_id':'e2','confidence':0.9},
            {'attribute_id':'a3','name':'quantity','raw_label':'Cantidad','value':'2','normalized_value':'2','page_number':1,'region_id':'r2','evidence_id':'e3','confidence':0.9},
            {'attribute_id':'a4','name':'total','raw_label':'Total','value':'S/ 20.00','normalized_value':'20.00','page_number':1,'region_id':'r2','evidence_id':'e4','confidence':0.9},
        ),
        facts=(),
    )


def test_deep_comprehension_is_deterministic_without_pdf_or_ocr():
    engine=DeepDocumentComprehensionEngine()
    one=engine.comprehend(_knowledge())
    two=engine.comprehend(_knowledge())
    assert one.metadata == two.metadata
    assert one.confidence == two.confidence
