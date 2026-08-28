"""Ejecutor del análisis de Cotizaciones usando los pipelines oficiales PM4–PM7."""

from __future__ import annotations

import copy
from typing import Any
from uuid import UUID

from zovrake_motor.classification.comparable_group_builder.models import ComparableGroupBuildRequest
from zovrake_motor.classification.comparative_domain_model.models import (
    ComparativeDomainModelBuildRequest,
)
from zovrake_motor.classification.concept_analysis.models import ConceptAnalysisRequest
from zovrake_motor.classification.concept_normalization.models import ConceptNormalizationRequest
from zovrake_motor.classification.context_association.models import ContextAssociationRequest
from zovrake_motor.classification.equivalence_detection.models import EquivalenceDetectionRequest
from zovrake_motor.classification.material_classification.models import MaterialClassificationRequest
from zovrake_motor.classification.service import ClassificationService
from zovrake_motor.classification.service_classification.models import ServiceClassificationRequest
from zovrake_motor.comparative_tables.comparative_model_builder.models import ComparativeModelBuildRequest
from zovrake_motor.comparative_tables.comparative_quality_framework.models import (
    ComparativeQualityValidationRequest,
)
from zovrake_motor.comparative_tables.comparative_structure_engine.models import (
    ComparativeStructureBuildRequest,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.models import (
    ComparativeModelValidationRequest,
)
from zovrake_motor.comparative_tables.dynamic_column_builder.models import ComparativeColumnBuildRequest
from zovrake_motor.comparative_tables.dynamic_row_builder.models import ComparativeRowBuildRequest
from zovrake_motor.comparative_tables.group_integrity_engine.models import GroupIntegrityValidationRequest
from zovrake_motor.comparative_tables.provider_organization_engine.models import (
    ProviderOrganizationBuildRequest,
)
from zovrake_motor.comparative_tables.service import ComparativeTablesService
from zovrake_motor.comparative_tables.traceability_metadata_engine.models import (
    TraceabilityMetadataEnrichmentRequest,
)
from zovrake_motor.comprehension.canonical.models import CanonicalRepresentationRequest
from zovrake_motor.comprehension.context_integration.models import ContextIntegrationRequest
from zovrake_motor.comprehension.extraction.models import AdapterDocumentContext, ContentExtractionRequest
from zovrake_motor.comprehension.internal_model.models import InternalModelBuildRequest
from zovrake_motor.comprehension.knowledge_index.models import DocumentIndexRequest
from zovrake_motor.comprehension.recognition.models import DocumentRecognitionRequest
from zovrake_motor.comprehension.service import ComprehensionService
from zovrake_motor.comprehension.validation.models import DocumentValidationRequest
from zovrake_motor.config.provider import ConfigurationProvider
from zovrake_motor.events.manager import EventManager
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.models import (
    ConsistencyEvaluationRequest,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.models import ContextEvaluationRequest
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.models import EvidenceAnalysisRequest
from zovrake_motor.intelligent_analysis.explanation_generation_engine.models import (
    ExplanationGenerationRequest,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.models import ReasoningResultBuildRequest
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.models import (
    RecommendationGenerationRequest,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.models import RiskAnalysisRequest
from zovrake_motor.intelligent_analysis.service import IntelligentAnalysisService
from zovrake_motor.motor_runtime.document_content import (
    ResolvedDocumentContent,
    resolve_evidence_documents,
)
from zovrake_motor.motor_runtime.result_registry import AnalysisResultRegistry, StoredAnalysisResult
from zovrake_motor.states.manager import StateManager


class CotizacionesAnalysisExecutor:
    """
    Ejecuta el flujo completo Cotizaciones con los módulos oficiales del Motor.

    Comprehension → Classification → Comparative Tables → Intelligent Analysis.
    """

    def __init__(
        self,
        *,
        result_registry: AnalysisResultRegistry,
        config_provider: ConfigurationProvider | None = None,
        state_manager: StateManager | None = None,
        event_manager: EventManager | None = None,
        comprehension: ComprehensionService | None = None,
        classification: ClassificationService | None = None,
        comparative_tables: ComparativeTablesService | None = None,
        intelligent_analysis: IntelligentAnalysisService | None = None,
    ) -> None:
        self._registry = result_registry
        self._config = config_provider or ConfigurationProvider.default()
        self._state_manager = state_manager or StateManager()
        self._event_manager = event_manager or EventManager()
        self._comprehension = comprehension or ComprehensionService(
            config_provider=self._config,
            state_manager=self._state_manager,
            event_manager=self._event_manager,
        )
        self._classification = classification or ClassificationService(
            config_provider=self._config,
            state_manager=self._state_manager,
            event_manager=self._event_manager,
        )
        self._comparative_tables = comparative_tables or ComparativeTablesService(
            config_provider=self._config,
            state_manager=self._state_manager,
            event_manager=self._event_manager,
        )
        self._intelligent_analysis = intelligent_analysis or IntelligentAnalysisService(
            config_provider=self._config,
            state_manager=self._state_manager,
            event_manager=self._event_manager,
        )
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return
        self._comprehension.initialize()
        self._classification.initialize()
        self._comparative_tables.initialize()
        self._intelligent_analysis.initialize()
        self._initialized = True

    def execute(
        self,
        *,
        process_id: UUID,
        codigo_req: str,
        evidence_documents: list[dict[str, Any]] | tuple[dict[str, Any], ...],
        requirement_description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> StoredAnalysisResult:
        self.initialize()
        metadata = dict(metadata or {})
        documents = resolve_evidence_documents(evidence_documents)
        if not documents:
            raise ValueError("No hay documentos de evidencia para analizar")

        internal_models = self._run_comprehension_for_documents(
            process_id=process_id,
            documents=documents,
            codigo_req=codigo_req,
            requirement_description=requirement_description,
        )

        if not internal_models:
            raise ValueError(
                "No se pudo generar ningún modelo documental."
            )

        normalized_catalogs = tuple(
            self._run_document_classification(
                process_id=process_id,
                internal_model=internal_model,
                codigo_req=codigo_req,
                requirement_description=requirement_description,
            )
            for internal_model in internal_models
        )

        if not normalized_catalogs:
            raise ValueError(
                "No se pudo generar ningún catálogo de clasificación documental."
            )

        collective_normalized_catalog = (
            self._build_collective_normalized_catalog(
                process_id=process_id,
                normalized_catalogs=normalized_catalogs,
            )
        )

        collective_equivalence_catalog = (
            self._run_collective_equivalence_detection(
                process_id=process_id,
                collective_normalized_catalog=collective_normalized_catalog,
            )
        )

        collective_comparable_group_catalog = (
            self._run_collective_comparable_groups(
                process_id=process_id,
                collective_equivalence_catalog=collective_equivalence_catalog,
                codigo_req=codigo_req,
            )
        )

        collective_context_association_catalog = self._run_collective_context_association(
            process_id=process_id,
            collective_comparable_group_catalog=collective_comparable_group_catalog,
            codigo_req=codigo_req,
            requirement_description=requirement_description,
        )
        domain_catalog = self._run_collective_comparative_domain_model(
            process_id=process_id,
            collective_context_association_catalog=collective_context_association_catalog,
            codigo_req=codigo_req,
        )
        provider_ids = tuple(
            doc.provider_name or doc.document_id for doc in documents
        )
        provider_source_map = self._build_provider_source_map(
            documents,
        )
        definitive_catalog = self._run_comparative_tables(
            process_id=process_id,
            domain_catalog=domain_catalog,
            provider_ids=provider_ids,
            documents=documents,
            provider_source_map=provider_source_map,
        )
        analysis_catalog = self._run_intelligent_analysis(
            process_id=process_id,
            definitive_catalog=definitive_catalog,
        )

        catalog_id = str(
            analysis_catalog.get("catalog_id")
            or definitive_catalog.get("catalog_id")
            or f"result-{process_id}"
        )
        enriched_tables = self._enrich_comparative_payload(
            definitive_catalog=definitive_catalog,
            documents=documents,
        )
        stored = StoredAnalysisResult(
            process_id=process_id,
            codigo_req=codigo_req,
            catalog_id=catalog_id,
            executed=True,
            message="Análisis documental ejecutado — cuadro comparativo generado con datos reales",
            comparative_tables=enriched_tables,
            intelligent_analysis=analysis_catalog,
            documents_processed=tuple(doc.to_summary() for doc in documents),
            metadata={
                "requirement_description": requirement_description,
                "project_id": metadata.get("project_id", ""),
                "quotation_id": metadata.get("quotation_id", ""),
                "source_data_preserved": True,
                "providers": list(provider_ids),
                "provider_source_map": provider_source_map,
                "pipeline_stages": [
                    "comprehension",
                    "document_classification",
                    "collective_normalization",
                    "collective_equivalence_detection",
                    "collective_comparable_groups",
                    "collective_context_association",
                    "comparative_domain_model",
                    "comparative_tables",
                    "intelligent_analysis",
                ],
                "collective_pipeline": {
                    "normalized_document_count": len(normalized_catalogs),
                    "equivalence_count": int(
                        collective_equivalence_catalog.get(
                            "equivalences_count",
                            0,
                        )
                    ),
                    "comparable_group_count": int(
                        collective_comparable_group_catalog.get(
                            "groups_count",
                            0,
                        )
                    ),
                    "context_association_count": int(
                        collective_context_association_catalog.get(
                            "associations_count",
                            0,
                        )
                    ),
                    "comparative_domain_model_count": int(
                        domain_catalog.get(
                            "models_count",
                            0,
                        )
                    ),
                    "document_ids": list(
                        collective_normalized_catalog.get(
                            "document_ids",
                            [],
                        )
                    ),
                    "comparable_group_document_ids": list(
                        collective_comparable_group_catalog.get(
                            "document_ids",
                            [],
                        )
                    ),
                    "collective_e2e_validated": True,
                },
            },
        )
        self._registry.store(stored)
        return stored

    def _run_comprehension_for_documents(
        self,
        *,
        process_id: UUID,
        documents: tuple[ResolvedDocumentContent, ...],
        codigo_req: str,
        requirement_description: str,
    ) -> tuple[dict[str, Any], ...]:
        """
        Ejecuta la comprensión documental individual para cada documento.

        Regla:
            1 documento = 1 modelo documental.

        Esta etapa mantiene separados los documentos.
        No realiza comparación ni mezcla información entre proveedores.
        """
        internal_models: list[dict[str, Any]] = []

        for document in documents:
            internal_model = self._run_comprehension(
                process_id=process_id,
                document=document,
                codigo_req=codigo_req,
                requirement_description=requirement_description,
            )

            model_copy = dict(internal_model)

            model_copy.setdefault(
                "document_id",
                document.document_id,
            )

            model_copy.setdefault(
                "document_label",
                document.document_label,
            )

            model_copy.setdefault(
                "file_name",
                document.file_name,
            )

            model_copy.setdefault(
                "provider_name",
                document.provider_name,
            )

            model_copy.setdefault(
                "source_document",
                {
                    "document_id": document.document_id,
                    "document_label": document.document_label,
                    "file_name": document.file_name,
                    "provider_name": document.provider_name,
                },
            )

            internal_models.append(model_copy)

        return tuple(internal_models)

    def _run_comprehension(
        self,
        *,
        process_id: UUID,
        document: ResolvedDocumentContent,
        codigo_req: str,
        requirement_description: str,
    ) -> dict[str, Any]:
        fmt = document.to_adapter_metadata().get("format_type", "pdf")
        file_size = 2048
        raw_size = document.metadata.get("file_size")
        if isinstance(raw_size, (int, float)) and raw_size > 0:
            file_size = int(raw_size)

        self._comprehension.validate_document(
            DocumentValidationRequest(
                process_id=process_id,
                document_id=document.document_id,
                format_type=str(fmt),
                file_size_bytes=file_size,
            ),
        )
        recognition = self._comprehension.recognize_document(
            DocumentRecognitionRequest(
                process_id=process_id,
                document_id=document.document_id,
                file_name=document.file_name or f"{document.document_id}.pdf",
            ),
        )
        adapter_name = recognition.suggested_adapter or "pdf_adapter"
        adapter_context = AdapterDocumentContext(
            process_id=process_id,
            document_id=document.document_id,
            adapter_name=adapter_name,
            format_type=str(fmt),
            document_reference=f"adapter://{adapter_name}/{document.document_id}",
            original_preserved=True,
            metadata=document.to_adapter_metadata(),
        )
        extraction = self._comprehension.extract_content(
            ContentExtractionRequest(
                process_id=process_id,
                document_id=document.document_id,
                adapter_context=adapter_context,
            ),
        )
        # Garantiza items/tablas desde contenido resuelto si el extractor no los produjo.
        extraction_dict = extraction.to_dict() if hasattr(extraction, "to_dict") else {}
        if not extraction.tables and document.tables:
            from zovrake_motor.comprehension.extraction.models import (
                ContentExtractionResult,
                ExtractedTable,
            )

            tables = tuple(
                ExtractedTable(
                    table_id=str(table.get("table_id", f"table-{index}")),
                    rows=tuple(tuple(str(cell) for cell in row) for row in table.get("rows", ())),
                )
                for index, table in enumerate(document.tables)
            )
            metadata = dict(extraction.metadata)
            metadata.update(
                {
                    "items": list(document.items),
                    "provider_name": document.provider_name,
                    "commercial_currency": document.commercial_currency,
                    "commercial_total_amount": document.commercial_total_amount,
                    "commercial_payment_terms": document.commercial_payment_terms,
                }
            )
            extraction = ContentExtractionResult(
                process_id=extraction.process_id,
                document_id=extraction.document_id,
                extracted_text=extraction.extracted_text or document.text_content,
                tables=tables,
                metadata=metadata,
                structural_elements=extraction.structural_elements,
                incidents=extraction.incidents,
                original_preserved=extraction.original_preserved,
                ocr_integration_prepared=extraction.ocr_integration_prepared,
                extractors_executed=extraction.extractors_executed,
                adapter_name=extraction.adapter_name,
                technical_observations=extraction.technical_observations,
            )
        elif document.items and "items" not in extraction.metadata:
            metadata = dict(extraction.metadata)
            metadata["items"] = list(document.items)
            metadata.setdefault("provider_name", document.provider_name)
            metadata.setdefault("commercial_currency", document.commercial_currency)
            metadata.setdefault("commercial_total_amount", document.commercial_total_amount)
            metadata.setdefault("commercial_payment_terms", document.commercial_payment_terms)
            from zovrake_motor.comprehension.extraction.models import ContentExtractionResult

            extraction = ContentExtractionResult(
                process_id=extraction.process_id,
                document_id=extraction.document_id,
                extracted_text=extraction.extracted_text or document.text_content,
                tables=extraction.tables,
                metadata=metadata,
                structural_elements=extraction.structural_elements,
                incidents=extraction.incidents,
                original_preserved=extraction.original_preserved,
                ocr_integration_prepared=extraction.ocr_integration_prepared,
                extractors_executed=extraction.extractors_executed,
                adapter_name=extraction.adapter_name,
                technical_observations=extraction.technical_observations,
            )

        del extraction_dict  # solo para claridad de flujo

        canonical = self._comprehension.build_canonical_representation(
            CanonicalRepresentationRequest(
                process_id=process_id,
                extraction_result=extraction,
            ),
        )
        model_result = self._comprehension.build_internal_model(
            InternalModelBuildRequest(
                process_id=process_id,
                canonical_result=canonical,
                requirement_code=codigo_req,
                requirement_context={"description": requirement_description},
            ),
        )
        index_result = self._comprehension.index_document(
            DocumentIndexRequest(
                process_id=process_id,
                model_result=model_result,
                validation_reference=f"dvf://{document.document_id}",
            ),
        )
        self._comprehension.integrate_context(
            ContextIntegrationRequest(
                process_id=process_id,
                detalles_requerimiento=requirement_description or codigo_req,
                index_result=index_result,
                model_result=model_result,
                requirement_code=codigo_req,
            ),
        )
        return model_result.model.to_dict()

    def _run_document_classification(
        self,
        *,
        process_id: UUID,
        internal_model: dict[str, Any],
        codigo_req: str,
        requirement_description: str,
    ) -> dict[str, Any]:
        """
        Clasifica un modelo documental de forma independiente.

        Esta etapa llega hasta la normalización y conserva la identidad
        documental. Las equivalencias y los grupos comparables se
        ejecutarán posteriormente sobre el conjunto consolidado de
        documentos.
        """
        concept_result = self._classification.analyze_concepts(
            ConceptAnalysisRequest(
                process_id=process_id,
                internal_model=internal_model,
            ),
        )

        concept_catalog = concept_result.catalog.to_dict()

        if not concept_catalog.get("concepts"):
            concept_catalog = self._seed_concepts_from_items(
                concept_catalog,
                internal_model,
            )

        material_result = self._classification.classify_materials(
            MaterialClassificationRequest(
                process_id=process_id,
                concept_catalog=concept_catalog,
            ),
        )

        service_result = self._classification.classify_services(
            ServiceClassificationRequest(
                process_id=process_id,
                concept_catalog=concept_catalog,
            ),
        )

        normalization_result = self._classification.normalize_concepts(
            ConceptNormalizationRequest(
                process_id=process_id,
                material_catalog=material_result.catalog.to_dict(),
                service_catalog=service_result.catalog.to_dict(),
            ),
        )

        normalized_catalog = normalization_result.catalog.to_dict()

        source_document = dict(
            internal_model.get(
                "source_document",
                {},
            )
        )

        document_id = str(
            source_document.get(
                "document_id",
                internal_model.get(
                    "document_id",
                    "",
                ),
            )
        )

        document_label = str(
            source_document.get(
                "document_label",
                internal_model.get(
                    "document_label",
                    "",
                ),
            )
        )

        file_name = str(
            source_document.get(
                "file_name",
                internal_model.get(
                    "file_name",
                    "",
                ),
            )
        )

        provider_name = str(
            source_document.get(
                "provider_name",
                internal_model.get(
                    "provider_name",
                    "",
                ),
            )
        )

        normalized_catalog["source_document"] = {
            "document_id": document_id,
            "document_label": document_label,
            "file_name": file_name,
            "provider_name": provider_name,
        }

        normalized_catalog["document_id"] = document_id
        normalized_catalog["document_label"] = document_label
        normalized_catalog["file_name"] = file_name
        normalized_catalog["provider_name"] = provider_name
        normalized_catalog["source_data_preserved"] = True

        return normalized_catalog

    @staticmethod
    def _build_collective_normalized_catalog(
        *,
        process_id: UUID,
        normalized_catalogs: tuple[dict[str, Any], ...],
    ) -> dict[str, Any]:
        """
        Consolida catálogos normalizados por documento sin modificar sus
        conceptos ni su trazabilidad de origen.

        La identidad de cada concepto se conserva mediante la combinación
        de document_id, model_id, concept_id y normalized_concept_id.
        La consolidación no ejecuta equivalencias ni grupos comparables.
        """
        if not normalized_catalogs:
            raise ValueError(
                "No se pueden consolidar catálogos normalizados vacíos."
            )

        collective_concepts: list[dict[str, Any]] = []
        seen_concepts: set[tuple[str, str, str, str]] = set()
        document_ids: list[str] = []
        catalog_ids: list[str] = []
        model_ids: list[str] = []
        source_material_catalog_ids: list[str] = []
        source_service_catalog_ids: list[str] = []

        for catalog in normalized_catalogs:
            if not isinstance(catalog, dict):
                raise TypeError(
                    "Cada catálogo normalizado debe ser un diccionario."
                )

            catalog_process_id = str(catalog.get("process_id", ""))
            if catalog_process_id and catalog_process_id != str(process_id):
                raise ValueError(
                    "Todos los catálogos normalizados deben pertenecer al "
                    "mismo process_id."
                )

            catalog_id = str(catalog.get("catalog_id", ""))
            model_id = str(catalog.get("model_id", ""))
            document_id = str(catalog.get("document_id", ""))

            if catalog_id:
                catalog_ids.append(catalog_id)
            if model_id:
                model_ids.append(model_id)
            if document_id:
                document_ids.append(document_id)

            material_catalog_id = str(
                catalog.get("source_material_catalog_id", "")
            )
            service_catalog_id = str(
                catalog.get("source_service_catalog_id", "")
            )
            if material_catalog_id:
                source_material_catalog_ids.append(material_catalog_id)
            if service_catalog_id:
                source_service_catalog_ids.append(service_catalog_id)

            concepts = catalog.get("concepts", [])
            if not isinstance(concepts, list):
                raise TypeError(
                    "El campo concepts de cada catálogo debe ser una lista."
                )

            for concept in concepts:
                if not isinstance(concept, dict):
                    raise TypeError(
                        "Cada concepto normalizado debe ser un diccionario."
                    )

                model_reference = dict(
                    concept.get("model_reference", {})
                )
                traceability = dict(
                    concept.get("traceability", {})
                )

                concept_document_id = str(
                    traceability.get(
                        "document_id",
                        model_reference.get(
                            "document_id",
                            document_id,
                        ),
                    )
                )
                concept_model_id = str(
                    traceability.get(
                        "model_id",
                        model_reference.get(
                            "model_id",
                            model_id,
                        ),
                    )
                )
                concept_id = str(
                    concept.get(
                        "concept_id",
                        model_reference.get("concept_id", ""),
                    )
                )
                normalized_concept_id = str(
                    concept.get("normalized_concept_id", "")
                )

                identity = (
                    concept_document_id,
                    concept_model_id,
                    concept_id,
                    normalized_concept_id,
                )

                if identity in seen_concepts:
                    continue

                seen_concepts.add(identity)
                collective_concepts.append(copy.deepcopy(concept))

        unique_document_ids = list(dict.fromkeys(document_ids))
        unique_catalog_ids = list(dict.fromkeys(catalog_ids))
        unique_model_ids = list(dict.fromkeys(model_ids))
        unique_material_ids = list(
            dict.fromkeys(source_material_catalog_ids)
        )
        unique_service_ids = list(
            dict.fromkeys(source_service_catalog_ids)
        )

        collective_document_id = (
            f"multi-document://{process_id}"
        )
        collective_model_id = f"collective-model://{process_id}"
        collective_catalog_id = f"cne-collective://{process_id}"

        return {
            "catalog_id": collective_catalog_id,
            "process_id": str(process_id),
            "model_id": collective_model_id,
            "document_id": collective_document_id,
            "document_ids": unique_document_ids,
            "document_count": len(unique_document_ids),
            "source_catalog_ids": unique_catalog_ids,
            "source_model_ids": unique_model_ids,
            "source_material_catalog_ids": unique_material_ids,
            "source_service_catalog_ids": unique_service_ids,
            "concepts": collective_concepts,
            "concepts_count": len(collective_concepts),
            "equivalence_detection_prepared": True,
            "comparable_group_builder_prepared": False,
            "collective_normalization": True,
            "source_data_preserved": True,
        }

    @staticmethod
    def _build_document_classification_snapshot(
        *,
        process_id: UUID,
        normalized_catalogs: tuple[dict[str, Any], ...],
    ) -> dict[str, Any]:
        """
        Construye una representación colectiva de los catálogos
        normalizados, conservando la identidad documental.

        Esta etapa NO ejecuta equivalencias ni grupos comparables.
        """
        documents: list[dict[str, Any]] = []

        for catalog in normalized_catalogs:
            source_document = dict(
                catalog.get(
                    "source_document",
                    {},
                )
            )

            documents.append(
                {
                    "document_id": str(
                        source_document.get(
                            "document_id",
                            catalog.get(
                                "document_id",
                                "",
                            ),
                        )
                    ),
                    "document_label": str(
                        source_document.get(
                            "document_label",
                            catalog.get(
                                "document_label",
                                "",
                            ),
                        )
                    ),
                    "file_name": str(
                        source_document.get(
                            "file_name",
                            catalog.get(
                                "file_name",
                                "",
                            ),
                        )
                    ),
                    "provider_name": str(
                        source_document.get(
                            "provider_name",
                            catalog.get(
                                "provider_name",
                                "",
                            ),
                        )
                    ),
                    "catalog": catalog,
                }
            )

        return {
            "catalog_id": f"classification://{process_id}",
            "process_id": str(process_id),
            "documents": documents,
            "document_count": len(documents),
            "stage": "normalized_document_classification",
            "equivalence_executed": False,
            "comparable_groups_executed": False,
            "source_data_preserved": True,
        }

    def _run_collective_equivalence_detection(
        self,
        *,
        process_id: UUID,
        collective_normalized_catalog: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Ejecuta el EDE sobre el catálogo normalizado colectivo.

        Esta etapa únicamente detecta relaciones entre conceptos de
        documentos distintos. No construye todavía grupos comparables,
        PM6 ni tablas comparativas.
        """
        if not collective_normalized_catalog:
            raise ValueError(
                "El catálogo normalizado colectivo no puede estar vacío."
            )

        catalog_process_id = str(
            collective_normalized_catalog.get("process_id", "")
        )
        if catalog_process_id and catalog_process_id != str(process_id):
            raise ValueError(
                "El catálogo normalizado colectivo pertenece a otro process_id."
            )

        prepared_catalog = copy.deepcopy(collective_normalized_catalog)
        prepared_catalog["equivalence_detection_prepared"] = True
        prepared_catalog["cross_document_only"] = True

        result = self._classification.detect_equivalences(
            EquivalenceDetectionRequest(
                process_id=process_id,
                normalized_catalog=prepared_catalog,
                metadata={
                    "scope": "collective_multi_document",
                    "cross_document_only": True,
                    "source_catalog_ids": list(
                        prepared_catalog.get("source_catalog_ids", [])
                    ),
                    "document_ids": list(
                        prepared_catalog.get("document_ids", [])
                    ),
                },
            ),
        )

        return result.catalog.to_dict()

    def _run_collective_comparable_groups(
        self,
        *,
        process_id: UUID,
        collective_equivalence_catalog: dict[str, Any],
        codigo_req: str,
    ) -> dict[str, Any]:
        """
        Ejecuta el CGB oficial sobre el catálogo colectivo de equivalencias.

        No modifica las equivalencias y valida que la identidad documental
        se conserve en el catálogo y en cada grupo construido.
        """
        if not collective_equivalence_catalog:
            raise ValueError(
                "El catálogo colectivo de equivalencias no puede estar vacío."
            )

        catalog_process_id = str(
            collective_equivalence_catalog.get("process_id", "")
        )
        if catalog_process_id and catalog_process_id != str(process_id):
            raise ValueError(
                "El catálogo colectivo de equivalencias pertenece a otro process_id."
            )

        result = self._classification.build_comparable_groups(
            ComparableGroupBuildRequest(
                process_id=process_id,
                equivalence_catalog=copy.deepcopy(
                    collective_equivalence_catalog,
                ),
                codigo_req=codigo_req,
                metadata={
                    "scope": "collective_multi_document",
                    "cross_document_only": True,
                    "document_ids": list(
                        collective_equivalence_catalog.get("document_ids", [])
                    ),
                },
            ),
        )

        catalog = result.catalog.to_dict()

        expected_document_ids = tuple(
            dict.fromkeys(
                str(document_id)
                for document_id in collective_equivalence_catalog.get(
                    "document_ids",
                    [],
                )
                if str(document_id)
            )
        )
        catalog_document_ids = tuple(
            str(document_id)
            for document_id in catalog.get("document_ids", [])
            if str(document_id)
        )

        if catalog_document_ids != expected_document_ids:
            raise RuntimeError(
                "El CGB no preservó los document_id del catálogo colectivo."
            )

        for group in catalog.get("groups", []):
            group_document_ids = tuple(
                str(document_id)
                for document_id in group.get(
                    "model_reference",
                    {},
                ).get("document_ids", [])
                if str(document_id)
            )
            traceability_document_ids = tuple(
                str(document_id)
                for document_id in group.get(
                    "traceability",
                    {},
                ).get("document_ids", [])
                if str(document_id)
            )
            if group_document_ids != traceability_document_ids:
                raise RuntimeError(
                    "La trazabilidad del grupo comparable no coincide "
                    "con su referencia documental."
                )

        return catalog

    def _run_collective_context_association(
        self,
        *,
        process_id: UUID,
        collective_comparable_group_catalog: dict[str, Any],
        codigo_req: str,
        requirement_description: str,
    ) -> dict[str, Any]:
        if not collective_comparable_group_catalog:
            raise ValueError("El catálogo colectivo de grupos comparables no puede estar vacío.")

        result = self._classification.associate_context(
            ContextAssociationRequest(
                process_id=process_id,
                comparable_group_catalog=copy.deepcopy(collective_comparable_group_catalog),
                integrated_context={
                    "context_id": f"ctx://{process_id}",
                    "description": requirement_description or codigo_req,
                    "process_id": str(process_id),
                    "codigo_req": codigo_req,
                    "immutable": True,
                },
                codigo_req=codigo_req,
                metadata={
                    "scope": "collective_multi_document",
                    "document_ids": list(collective_comparable_group_catalog.get("document_ids", [])),
                },
            ),
        )
        catalog = result.catalog.to_dict()
        expected = tuple(collective_comparable_group_catalog.get("document_ids", []))
        actual = tuple(catalog.get("document_ids", []))
        if actual != expected:
            raise RuntimeError("CAE no preservó document_ids del catálogo colectivo.")
        return catalog

    def _run_collective_comparative_domain_model(
        self,
        *,
        process_id: UUID,
        collective_context_association_catalog: dict[str, Any],
        codigo_req: str,
    ) -> dict[str, Any]:
        result = self._classification.build_comparative_domain_model(
            ComparativeDomainModelBuildRequest(
                process_id=process_id,
                context_association_catalog=copy.deepcopy(collective_context_association_catalog),
                codigo_req=codigo_req,
                metadata={
                    "scope": "collective_multi_document",
                    "document_ids": list(collective_context_association_catalog.get("document_ids", [])),
                },
            ),
        )
        catalog = result.catalog.to_dict()
        expected = tuple(collective_context_association_catalog.get("document_ids", []))
        actual = tuple(catalog.get("document_ids", []))
        if actual != expected:
            raise RuntimeError("CDMB no preservó document_ids del catálogo colectivo.")
        for model in catalog.get("models", []):
            model_doc_ids = tuple(model.get("traceability", {}).get("document_ids", []))
            if model_doc_ids != expected:
                raise RuntimeError("CDMB perdió la trazabilidad documental del modelo.")
        return catalog

    def _run_classification(
        self,
        *,
        process_id: UUID,
        internal_model: dict[str, Any],
        codigo_req: str,
        requirement_description: str,
    ) -> dict[str, Any]:
        concept_result = self._classification.analyze_concepts(
            ConceptAnalysisRequest(process_id=process_id, internal_model=internal_model),
        )
        concept_catalog = concept_result.catalog.to_dict()
        if not concept_catalog.get("concepts"):
            # Asegura al menos un concepto a partir de ítems del modelo interno.
            concept_catalog = self._seed_concepts_from_items(concept_catalog, internal_model)

        material_result = self._classification.classify_materials(
            MaterialClassificationRequest(process_id=process_id, concept_catalog=concept_catalog),
        )
        service_result = self._classification.classify_services(
            ServiceClassificationRequest(process_id=process_id, concept_catalog=concept_catalog),
        )
        normalization_result = self._classification.normalize_concepts(
            ConceptNormalizationRequest(
                process_id=process_id,
                material_catalog=material_result.catalog.to_dict(),
                service_catalog=service_result.catalog.to_dict(),
            ),
        )
        normalized_catalog = normalization_result.catalog.to_dict()
        equivalence_result = self._classification.detect_equivalences(
            EquivalenceDetectionRequest(
                process_id=process_id,
                normalized_catalog=normalized_catalog,
            ),
        )
        group_result = self._classification.build_comparable_groups(
            ComparableGroupBuildRequest(
                process_id=process_id,
                equivalence_catalog=equivalence_result.catalog.to_dict(),
            ),
        )
        context_result = self._classification.associate_context(
            ContextAssociationRequest(
                process_id=process_id,
                comparable_group_catalog=group_result.catalog.to_dict(),
                integrated_context={
                    "context_id": f"ctx://{process_id}",
                    "description": requirement_description or codigo_req,
                    "process_id": str(process_id),
                    "codigo_req": codigo_req,
                    "immutable": True,
                },
            ),
        )
        domain_result = self._classification.build_comparative_domain_model(
            ComparativeDomainModelBuildRequest(
                process_id=process_id,
                context_association_catalog=context_result.catalog.to_dict(),
            ),
        )
        return domain_result.catalog.to_dict()

    def _run_comparative_tables(
        self,
        *,
        process_id: UUID,
        domain_catalog: dict[str, Any],
        provider_ids: tuple[str, ...],
        documents: tuple[ResolvedDocumentContent, ...],
        provider_source_map: list[dict[str, Any]],
    ) -> dict[str, Any]:
        structure_result = self._comparative_tables.build_comparative_structure(
            ComparativeStructureBuildRequest(
                process_id=process_id,
                domain_model_catalog=domain_catalog,
            ),
        )
        structure_catalog = self._inject_group_providers(
            structure_result.catalog.to_dict(),
            provider_source_map=provider_source_map,
        )
        column_result = self._comparative_tables.build_dynamic_columns(
            ComparativeColumnBuildRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
            ),
        )
        column_catalog = column_result.catalog.to_dict()
        row_result = self._comparative_tables.build_dynamic_rows(
            ComparativeRowBuildRequest(
                process_id=process_id,
                column_catalog=column_catalog,
                structure_catalog=structure_catalog,
            ),
        )
        row_catalog = row_result.catalog.to_dict()
        provider_result = self._comparative_tables.organize_providers(
            ProviderOrganizationBuildRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
            ),
        )
        provider_catalog = provider_result.catalog.to_dict()
        integrity_result = self._comparative_tables.validate_group_integrity(
            GroupIntegrityValidationRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
                provider_catalog=provider_catalog,
            ),
        )
        integrity_report = integrity_result.report.to_dict()
        enrichment_result = self._comparative_tables.enrich_traceability_metadata(
            TraceabilityMetadataEnrichmentRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
                provider_catalog=provider_catalog,
                integrity_report=integrity_report,
            ),
        )
        enriched_catalog = enrichment_result.catalog.to_dict()
        model_result = self._comparative_tables.build_comparative_model(
            ComparativeModelBuildRequest(
                process_id=process_id,
                enriched_catalog=enriched_catalog,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
                provider_catalog=provider_catalog,
                integrity_report=integrity_report,
            ),
        )
        definitive_catalog = model_result.catalog.to_dict()

        definitive_catalog = (
            self._inject_provider_source_map_into_definitive_catalog(
                definitive_catalog=definitive_catalog,
                provider_source_map=provider_source_map,
            )
        )

        validation_result = self._comparative_tables.validate_comparative_model(
            ComparativeModelValidationRequest(
                process_id=process_id,
                definitive_catalog=definitive_catalog,
            ),
        )
        self._comparative_tables.audit_comparative_quality(
            ComparativeQualityValidationRequest(
                process_id=process_id,
                definitive_catalog=definitive_catalog,
                validation_report=validation_result.report.to_dict(),
                pipeline_snapshot=self._comparative_tables.get_comparative_tables_pipeline_snapshot(),
            ),
        )
        definitive_catalog = self._fill_cell_values_from_documents(
            definitive_catalog,
            documents,
        )

        return definitive_catalog

    @staticmethod
    def _inject_provider_source_map_into_definitive_catalog(
        *,
        definitive_catalog: dict[str, Any],
        provider_source_map: list[dict[str, Any]],
    ) -> dict[str, Any]:
        catalog = copy.deepcopy(definitive_catalog)

        normalized_map = []
        seen_provider_ids: set[str] = set()

        for entry in provider_source_map:
            provider_id = str(entry.get("provider_id", "")).strip()
            provider_name = str(entry.get("provider_name", "")).strip()

            document_ids = tuple(
                dict.fromkeys(
                    str(document_id).strip()
                    for document_id in entry.get("document_ids", [])
                    if str(document_id).strip()
                )
            )

            if not provider_id or provider_id in seen_provider_ids:
                continue

            seen_provider_ids.add(provider_id)
            normalized_map.append(
                {
                    "provider_id": provider_id,
                    "provider_name": provider_name,
                    "document_ids": list(document_ids),
                    "document_count": len(document_ids),
                    "duplicate_document_source": len(document_ids) > 1,
                }
            )

        catalog["provider_source_map"] = normalized_map
        catalog["provider_source_map_count"] = len(normalized_map)

        for model in catalog.get("models", []):
            metadata = dict(model.get("metadata", {}))
            metadata["provider_source_map"] = copy.deepcopy(normalized_map)
            model["metadata"] = metadata

            for row in model.get("dynamic_rows", []):
                row_metadata = dict(row.get("metadata", {}))
                provider_id = str(
                    row.get("provider_id", "")
                ).strip()

                source_entry = next(
                    (
                        entry
                        for entry in normalized_map
                        if entry["provider_id"] == provider_id
                    ),
                    None,
                )

                if source_entry is not None:
                    row_metadata["provider_source_document_ids"] = list(
                        source_entry["document_ids"]
                    )
                    row_metadata["provider_source_document_count"] = (
                        source_entry["document_count"]
                    )
                    row_metadata["provider_source_ambiguous"] = (
                        source_entry["duplicate_document_source"]
                    )
                    row_metadata["provider_name"] = source_entry[
                        "provider_name"
                    ]

                row["metadata"] = row_metadata

        return catalog

    def _run_intelligent_analysis(
        self,
        *,
        process_id: UUID,
        definitive_catalog: dict[str, Any],
    ) -> dict[str, Any]:
        evidence = self._intelligent_analysis.analyze_evidence(
            EvidenceAnalysisRequest(
                process_id=process_id,
                definitive_catalog=definitive_catalog,
            ),
        )
        evidence_catalog = evidence.catalog
        consistency = self._intelligent_analysis.evaluate_consistency(
            ConsistencyEvaluationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
            ),
        )
        consistency_catalog = consistency.catalog
        risks = self._intelligent_analysis.analyze_risks(
            RiskAnalysisRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
            ),
        )
        risk_catalog = risks.catalog
        context = self._intelligent_analysis.evaluate_context(
            ContextEvaluationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                definitive_catalog=definitive_catalog,
            ),
        )
        context_catalog = context.catalog
        explanations = self._intelligent_analysis.generate_explanations(
            ExplanationGenerationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                context_catalog=context_catalog,
                definitive_catalog=definitive_catalog,
            ),
        )
        explanation_catalog = explanations.catalog
        recommendations = self._intelligent_analysis.generate_recommendations(
            RecommendationGenerationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                context_catalog=context_catalog,
                explanation_catalog=explanation_catalog,
                definitive_catalog=definitive_catalog,
            ),
        )
        recommendation_catalog = recommendations.catalog
        built = self._intelligent_analysis.build_intelligent_analysis_results(
            ReasoningResultBuildRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                context_catalog=context_catalog,
                explanation_catalog=explanation_catalog,
                recommendation_catalog=recommendation_catalog,
                definitive_catalog=definitive_catalog,
            ),
        )
        return built.catalog.to_dict()

    @staticmethod
    def _inject_group_providers(
        structure_catalog: dict[str, Any],
        *,
        provider_source_map: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Resuelve los proveedores de cada estructura a partir de su propio grupo.

        El CSE entrega referencias documentales en la trazabilidad del grupo.
        Esta capa de orquestación conoce la relación documento -> proveedor y
        la adapta para PM6 sin mezclar proveedores de grupos distintos.

        No se crea ningún proveedor artificial ni se usa una lista global como
        fallback: una fila solo puede pertenecer a un proveedor respaldado por
        la fuente documental del grupo.
        """
        catalog = copy.deepcopy(structure_catalog)

        document_to_provider: dict[str, str] = {}
        provider_ids: set[str] = set()

        for entry in provider_source_map:
            provider_id = str(entry.get("provider_id", "")).strip()
            if not provider_id:
                continue

            provider_ids.add(provider_id)
            for document_id in entry.get("document_ids", []):
                normalized_document_id = str(document_id).strip()
                if not normalized_document_id:
                    continue

                existing = document_to_provider.get(normalized_document_id)
                if existing is not None and existing != provider_id:
                    raise RuntimeError(
                        "Un document_id pertenece a más de un provider_id en "
                        "provider_source_map: " + normalized_document_id,
                    )
                document_to_provider[normalized_document_id] = provider_id

        for structure in catalog.get("structures", []):
            metadata_prepared = dict(structure.get("metadata_prepared", {}))
            existing_references = tuple(
                str(reference).strip()
                for reference in metadata_prepared.get("available_providers", [])
                if str(reference).strip()
            )

            traceability = dict(structure.get("traceability", {}) or {})
            lineage = dict(traceability.get("lineage", {}) or {})
            domain_reference = dict(structure.get("domain_reference", {}) or {})

            group_document_ids: list[str] = []
            for raw_document_id in lineage.get("document_ids", []):
                document_id = str(raw_document_id).strip()
                if document_id and document_id not in group_document_ids:
                    group_document_ids.append(document_id)

            for raw_document_id in traceability.get("document_ids", []):
                document_id = str(raw_document_id).strip()
                if document_id and document_id not in group_document_ids:
                    group_document_ids.append(document_id)

            fallback_document_id = str(
                domain_reference.get("document_id", "")
            ).strip()
            if fallback_document_id and fallback_document_id not in group_document_ids:
                group_document_ids.append(fallback_document_id)

            resolved_providers: list[str] = []

            def add_provider(provider_id: str) -> None:
                if provider_id and provider_id not in resolved_providers:
                    resolved_providers.append(provider_id)

            for reference in existing_references:
                if reference in provider_ids:
                    add_provider(reference)
                    continue

                document_id = reference.removeprefix("document://").strip()
                provider_id = document_to_provider.get(document_id)
                if provider_id is not None:
                    add_provider(provider_id)
                    continue

                raise RuntimeError(
                    f"No se pudo resolver la referencia de proveedor '{reference}' "
                    f"del grupo {structure.get('group_id', '')} a un proveedor fuente.",
                )

            for document_id in group_document_ids:
                provider_id = document_to_provider.get(document_id)
                if provider_id is None:
                    raise RuntimeError(
                        f"No se pudo resolver el document_id '{document_id}' "
                        f"del grupo {structure.get('group_id', '')} a un proveedor fuente.",
                    )
                add_provider(provider_id)

            metadata_prepared["available_providers"] = resolved_providers
            metadata_prepared["provider_scope"] = "comparable_group"
            metadata_prepared["provider_source_document_ids"] = list(group_document_ids)
            structure["metadata_prepared"] = metadata_prepared

        return catalog

    @staticmethod
    def _ensure_comparable_duplicate(normalized_catalog: dict[str, Any]) -> dict[str, Any]:
        catalog = copy.deepcopy(normalized_catalog)
        concepts = list(catalog.get("concepts", []))
        if len(concepts) >= 2:
            return catalog
        if not concepts:
            return catalog
        duplicate = copy.deepcopy(concepts[0])
        normalized_id = str(duplicate.get("normalized_concept_id", "concept-1"))
        duplicate["normalized_concept_id"] = f"{normalized_id}-dup"
        concepts.append(duplicate)
        catalog["concepts"] = concepts
        return catalog

    @staticmethod
    def _seed_concepts_from_items(
        concept_catalog: dict[str, Any],
        internal_model: dict[str, Any],
    ) -> dict[str, Any]:
        catalog = copy.deepcopy(concept_catalog)
        concepts = list(catalog.get("concepts", []))
        for index, item in enumerate(internal_model.get("items", [])):
            description = str(item.get("description", "")).strip()
            if not description:
                continue
            concepts.append(
                {
                    "concept_id": f"seed://item-{index + 1}",
                    "normalized_concept_id": f"seed-concept-{index + 1}",
                    "kind": "item",
                    "original_description": description,
                    "classification_pending": False,
                    "metadata": {
                        "quantity": item.get("quantity", ""),
                        "unit_price": item.get("unit_price", ""),
                        "unit": item.get("unit", ""),
                    },
                }
            )
        catalog["concepts"] = concepts
        return catalog

    @staticmethod
    def _build_provider_source_map(
        documents: tuple[ResolvedDocumentContent, ...],
    ) -> list[dict[str, Any]]:
        """
        Construye la relación proveedor ↔ documentos fuente.

        `provider_id` mantiene la identidad del proveedor. `document_id`
        mantiene la identidad individual del documento. Si un proveedor
        tiene más de un documento fuente, todos sus documentos se conservan
        y la entrada queda marcada como ambigua para cualquier resolución
        que no disponga de un document_id explícito.
        """
        providers: dict[str, dict[str, Any]] = {}

        for document in documents:
            provider_name = str(
                document.provider_name
                or document.document_id
                or "",
            ).strip()

            document_id = str(document.document_id).strip()

            if not provider_name or not document_id:
                continue

            provider = providers.setdefault(
                provider_name,
                {
                    "provider_id": provider_name,
                    "provider_name": provider_name,
                    "document_ids": [],
                },
            )

            if document_id not in provider["document_ids"]:
                provider["document_ids"].append(document_id)

        return [
            {
                "provider_id": provider["provider_id"],
                "provider_name": provider["provider_name"],
                "document_ids": list(provider["document_ids"]),
                "document_count": len(provider["document_ids"]),
                "duplicate_document_source": (
                    len(provider["document_ids"]) > 1
                ),
            }
            for provider in providers.values()
        ]

    @staticmethod
    def _fill_cell_values_from_documents(
        definitive_catalog: dict[str, Any],
        documents: tuple[ResolvedDocumentContent, ...],
    ) -> dict[str, Any]:
        catalog = copy.deepcopy(definitive_catalog)

        by_document_id = {
            str(document.document_id): document
            for document in documents
            if str(document.document_id)
        }

        documents_by_provider: dict[
            str,
            list[ResolvedDocumentContent],
        ] = {}

        for document in documents:
            provider_name = str(
                document.provider_name
                or document.document_id
                or "",
            ).strip()

            if provider_name:
                documents_by_provider.setdefault(
                    provider_name,
                    [],
                ).append(document)

        for model in catalog.get("models", []):
            rows = list(model.get("dynamic_rows", []))
            columns = list(model.get("dynamic_columns", []))
            attribute_by_column = {
                str(col.get("column_id")): str(
                    col.get("attribute_name", "")
                ).lower()
                for col in columns
            }

            enriched_rows = []

            for row in rows:
                provider_id = str(
                    row.get("provider_id", "")
                ).strip()

                document = by_document_id.get(provider_id)

                provider_candidates = documents_by_provider.get(
                    provider_id,
                    [],
                )

                if document is None and len(provider_candidates) == 1:
                    document = provider_candidates[0]

                cells = []

                for cell in row.get("cells_reserved", []):
                    cell_copy = dict(cell)

                    attr = attribute_by_column.get(
                        str(cell_copy.get("column_id")),
                        "",
                    )

                    value = CotizacionesAnalysisExecutor._resolve_cell_value(
                        attribute=attr,
                        document=document,
                        provider_id=provider_id,
                    )

                    if value:
                        cell_copy["value"] = value
                        cell_copy["value_prepared"] = True

                    cells.append(cell_copy)

                row_copy = dict(row)
                row_copy["cells_reserved"] = cells

                metadata = dict(
                    row_copy.get("metadata", {})
                )

                metadata["cell_values_prepared"] = True

                metadata["provider_source_document_ids"] = [
                    str(candidate.document_id)
                    for candidate in provider_candidates
                    if str(candidate.document_id)
                ]

                metadata["provider_source_document_count"] = len(
                    provider_candidates
                )

                metadata["provider_source_ambiguous"] = (
                    document is None
                    and len(provider_candidates) > 1
                )

                if document is not None:
                    metadata["provider_name"] = (
                        document.provider_name
                    )
                    metadata["document_id"] = (
                        document.document_id
                    )
                    metadata["commercial_total_amount"] = (
                        document.commercial_total_amount
                    )
                    metadata["commercial_currency"] = (
                        document.commercial_currency
                    )

                row_copy["metadata"] = metadata
                enriched_rows.append(row_copy)

            model["dynamic_rows"] = enriched_rows

            commercial = dict(
                model.get(
                    "commercial_information",
                    {},
                )
            )

            provider_fields = []

            for doc in documents:
                provider_fields.append(
                    {
                        "provider_id": (
                            doc.provider_name
                            or doc.document_id
                        ),
                        "provider_name": doc.provider_name,
                        "document_id": doc.document_id,
                        "currency": doc.commercial_currency,
                        "total_amount": doc.commercial_total_amount,
                        "payment_terms": (
                            doc.commercial_payment_terms
                        ),
                        "items": [
                            dict(item)
                            for item in doc.items
                        ],
                    }
                )

            commercial["provider_fields"] = provider_fields
            model["commercial_information"] = commercial

        return catalog


    @staticmethod
    def _resolve_cell_value(
        *,
        attribute: str,
        document: ResolvedDocumentContent | None,
        provider_id: str,
    ) -> str:
        if attribute in {"provider", "proveedor", "provider_name"}:
            return (document.provider_name if document else provider_id) or provider_id
        if document is None:
            return ""
        if attribute in {"currency", "moneda"}:
            return document.commercial_currency
        if attribute in {"total", "total_amount", "monto", "importe"}:
            return document.commercial_total_amount
        if attribute in {"payment_terms", "pago", "condiciones"}:
            return document.commercial_payment_terms
        if attribute in {"quantity", "cantidad"} and document.items:
            return str(document.items[0].get("quantity", ""))
        if attribute in {"unit_price", "precio", "precio_unitario"} and document.items:
            return str(document.items[0].get("unit_price", ""))
        if attribute in {"description", "descripcion", "item"} and document.items:
            return str(document.items[0].get("description", ""))
        if attribute in {"document", "documento", "file_name"}:
            return document.file_name or document.document_label
        return ""

    @staticmethod
    def _enrich_comparative_payload(
        *,
        definitive_catalog: dict[str, Any],
        documents: tuple[ResolvedDocumentContent, ...],
    ) -> dict[str, Any]:
        matrices = []
        for model in definitive_catalog.get("models", []):
            columns = list(model.get("dynamic_columns", []))
            rows = list(model.get("dynamic_rows", []))
            header = [
                str(col.get("display_name") or col.get("attribute_name") or col.get("column_id") or "")
                for col in columns
            ]
            body = []
            for row in rows:
                cells_by_col = {
                    str(cell.get("column_id")): cell
                    for cell in row.get("cells_reserved", [])
                }
                values = []
                for col in columns:
                    cell = cells_by_col.get(str(col.get("column_id")), {})
                    values.append(str(cell.get("value") or ""))
                body.append(
                    {
                        "provider_id": row.get("provider_id", ""),
                        "row_id": row.get("row_id", ""),
                        "values": values,
                        "metadata": dict(row.get("metadata", {})),
                    }
                )
            matrices.append(
                {
                    "comparative_table_id": model.get("comparative_table_id", ""),
                    "group_id": model.get("group_id", ""),
                    "group_type": model.get("group_type", ""),
                    "header": header,
                    "rows": body,
                    "commercial_information": model.get("commercial_information", {}),
                    "technical_information": model.get("technical_information", {}),
                }
            )
        return {
            "catalog_id": definitive_catalog.get("catalog_id", ""),
            "document_id": definitive_catalog.get("document_id", ""),
            "model_id": definitive_catalog.get("model_id", ""),
            "pm6_definitive_output_contract": definitive_catalog.get(
                "pm6_definitive_output_contract",
                True,
            ),
            "models": definitive_catalog.get("models", []),
            "matrices": matrices,
            "providers": [
                {
                    "provider_name": doc.provider_name,
                    "document_id": doc.document_id,
                    "document_label": doc.document_label,
                    "currency": doc.commercial_currency,
                    "total_amount": doc.commercial_total_amount,
                    "payment_terms": doc.commercial_payment_terms,
                    "items": [dict(item) for item in doc.items],
                }
                for doc in documents
            ],
        }