from pathlib import Path

from zovrake_motor.comprehension.document_knowledge_builder import DocumentKnowledgeBuilder
from zovrake_motor.comprehension.document_semantic_analyzer import DocumentSemanticAnalyzer
from zovrake_motor.comprehension.document_entity_resolver import DocumentEntityResolver
from zovrake_motor.comprehension.document_fact_extractor import DocumentFactExtractor
from zovrake_motor.comprehension.document_fact_entity_linker import DocumentFactEntityLinker
from zovrake_motor.comprehension.deep_document_comprehension import DeepDocumentComprehensionEngine
from zovrake_motor.comprehension.pdf_processing.processor import PDFDocumentProcessor


def _knowledge():
    p=Path('tests/fixtures/COTIZACION-02.pdf')
    d=PDFDocumentProcessor(ocr_all_pages=True, ocr_embedded_images=True).process(
        document_id='deep-test', file_name=p.name, pdf_bytes=p.read_bytes())
    k=DocumentKnowledgeBuilder().build(d)
    k=DocumentSemanticAnalyzer().analyze(k)
    k=DocumentEntityResolver().resolve(k)
    k=DocumentFactExtractor().extract(k)
    k=DocumentFactEntityLinker().link(k)
    return k


def test_deep_comprehension_creates_profile_and_semantic_index():
    k=_knowledge()
    result=DeepDocumentComprehensionEngine().comprehend(k)
    assert result.metadata['deep_comprehension_stage'] == 'unified_semantic_reasoning'
    assert result.metadata['deep_comprehension_profile']['page_count'] == 1
    assert result.metadata['deep_semantic_concepts']
    assert result.metadata['deep_semantic_index']
    assert 'document_kind' in result.metadata['deep_comprehension_profile']


def test_deep_comprehension_is_deterministic_for_same_knowledge():
    k=_knowledge()
    engine=DeepDocumentComprehensionEngine()
    first=engine.comprehend(k)
    second=engine.comprehend(k)
    assert first.metadata['deep_semantic_concepts'] == second.metadata['deep_semantic_concepts']
    assert first.metadata['deep_semantic_index'] == second.metadata['deep_semantic_index']
