"""
Utilidad de certificación del Pipeline de Razonamiento Inteligente completo.

Ejecuta las etapas 7.2–7.8 en secuencia para validación integral.
No introduce lógica de negocio ni nuevos motores.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.models import (
    ConsistencyEvaluationRequest,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.models import (
    ContextEvaluationRequest,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.models import (
    EvidenceAnalysisRequest,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.models import (
    ExplanationGenerationRequest,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.enums import (
    ReasoningResultBuildStatus,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.governance import (
    PM7_OUTPUT_CATALOG_CONTRACT_NAME,
    PM7_OUTPUT_CONTRACT_NAME,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.models import (
    ReasoningResultBuildRequest,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.models import (
    RecommendationGenerationRequest,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.models import (
    RiskAnalysisRequest,
)
from zovrake_motor.intelligent_analysis.service import IntelligentAnalysisService


@dataclass(frozen=True)
class IntelligentAnalysisPipelineCertificationResult:
    """Resultado de la ejecución certificada del Pipeline PM7."""

    process_id: UUID
    document_id: str
    model_id: str
    evidence_analysis_passed: bool
    consistency_evaluation_passed: bool
    risk_analysis_passed: bool
    context_evaluation_passed: bool
    explanation_generation_passed: bool
    recommendation_generation_passed: bool
    reasoning_result_build_passed: bool
    traceability_intact: bool
    definitive_catalog_preserved: bool
    source_catalogs_preserved: bool
    pm7_output_contract_valid: bool
    integration_certification_framework_prepared: bool
    results_count: int
    stages_executed: int
    technical_observations: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return (
            self.evidence_analysis_passed
            and self.consistency_evaluation_passed
            and self.risk_analysis_passed
            and self.context_evaluation_passed
            and self.explanation_generation_passed
            and self.recommendation_generation_passed
            and self.reasoning_result_build_passed
            and self.traceability_intact
            and self.definitive_catalog_preserved
            and self.source_catalogs_preserved
            and self.pm7_output_contract_valid
            and self.integration_certification_framework_prepared
            and self.results_count >= 1
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "complete": self.complete,
            "evidence_analysis_passed": self.evidence_analysis_passed,
            "consistency_evaluation_passed": self.consistency_evaluation_passed,
            "risk_analysis_passed": self.risk_analysis_passed,
            "context_evaluation_passed": self.context_evaluation_passed,
            "explanation_generation_passed": self.explanation_generation_passed,
            "recommendation_generation_passed": self.recommendation_generation_passed,
            "reasoning_result_build_passed": self.reasoning_result_build_passed,
            "traceability_intact": self.traceability_intact,
            "definitive_catalog_preserved": self.definitive_catalog_preserved,
            "source_catalogs_preserved": self.source_catalogs_preserved,
            "pm7_output_contract_valid": self.pm7_output_contract_valid,
            "integration_certification_framework_prepared": (
                self.integration_certification_framework_prepared
            ),
            "results_count": self.results_count,
            "stages_executed": self.stages_executed,
            "technical_observations": list(self.technical_observations),
        }


def run_full_intelligent_analysis_pipeline(
    service: IntelligentAnalysisService,
    *,
    process_id: UUID,
    definitive_catalog: dict[str, Any],
) -> IntelligentAnalysisPipelineCertificationResult:
    """
    Ejecuta el Pipeline PM7 completo (7.2–7.8) sin interrupciones.

    Flujo: EAE → CEE → RAE → CxEE → EGE → RGE → RRB.
    """
    observations: list[str] = []
    stages = 0

    definitive_snapshot = copy.deepcopy(definitive_catalog)
    document_id = str(definitive_catalog.get("document_id", ""))
    model_id = str(definitive_catalog.get("model_id", ""))
    requirement_context = {}
    if definitive_catalog.get("models"):
        requirement_context = dict(
            definitive_catalog["models"][0].get("inherited_context", {}),
        )

    eae_result = service.analyze_evidence(
        EvidenceAnalysisRequest(
            process_id=process_id,
            definitive_catalog=definitive_catalog,
        ),
    )
    stages += 1
    evidence_catalog = eae_result.catalog
    evidence_analysis_passed = eae_result.definitive_catalog_preserved

    cee_result = service.evaluate_consistency(
        ConsistencyEvaluationRequest(
            process_id=process_id,
            evidence_catalog=evidence_catalog,
        ),
    )
    stages += 1
    consistency_catalog = cee_result.catalog
    consistency_evaluation_passed = (
        cee_result.evidence_catalog_preserved
        and cee_result.catalog.source_evidence_catalog_id == evidence_catalog.catalog_id
    )

    rae_result = service.analyze_risks(
        RiskAnalysisRequest(
            process_id=process_id,
            evidence_catalog=evidence_catalog,
            consistency_catalog=consistency_catalog,
        ),
    )
    stages += 1
    risk_catalog = rae_result.catalog
    risk_analysis_passed = (
        rae_result.evidence_catalog_preserved
        and rae_result.consistency_catalog_preserved
        and rae_result.catalog.source_consistency_catalog_id == consistency_catalog.catalog_id
    )

    cxee_result = service.evaluate_context(
        ContextEvaluationRequest(
            process_id=process_id,
            evidence_catalog=evidence_catalog,
            consistency_catalog=consistency_catalog,
            risk_catalog=risk_catalog,
            definitive_catalog=definitive_catalog,
            requirement_context=requirement_context,
        ),
    )
    stages += 1
    context_catalog = cxee_result.catalog
    context_evaluation_passed = (
        cxee_result.evidence_catalog_preserved
        and cxee_result.consistency_catalog_preserved
        and cxee_result.risk_catalog_preserved
        and cxee_result.definitive_catalog_preserved
    )

    ege_result = service.generate_explanations(
        ExplanationGenerationRequest(
            process_id=process_id,
            evidence_catalog=evidence_catalog,
            consistency_catalog=consistency_catalog,
            risk_catalog=risk_catalog,
            context_catalog=context_catalog,
            definitive_catalog=definitive_catalog,
        ),
    )
    stages += 1
    explanation_catalog = ege_result.catalog
    explanation_generation_passed = (
        ege_result.evidence_catalog_preserved
        and ege_result.consistency_catalog_preserved
        and ege_result.risk_catalog_preserved
        and ege_result.context_catalog_preserved
        and ege_result.definitive_catalog_preserved
    )

    rge_result = service.generate_recommendations(
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
    stages += 1
    recommendation_catalog = rge_result.catalog
    recommendation_generation_passed = (
        rge_result.explanation_catalog_preserved
        and rge_result.definitive_catalog_preserved
        and rge_result.catalog.reasoning_result_builder_prepared
    )

    rrb_result = service.build_intelligent_analysis_results(
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
    stages += 1
    reasoning_result_build_passed = (
        rrb_result.status
        in (ReasoningResultBuildStatus.BUILT, ReasoningResultBuildStatus.PARTIAL)
        and rrb_result.recommendation_catalog_preserved
        and rrb_result.definitive_catalog_preserved
        and rrb_result.source_data_preserved
    )
    integration_certification_framework_prepared = (
        rrb_result.catalog.integration_certification_framework_prepared
    )
    results_count = rrb_result.results_count

    definitive_catalog_preserved = definitive_catalog == definitive_snapshot
    source_catalogs_preserved = (
        eae_result.definitive_catalog_preserved
        and cee_result.evidence_catalog_preserved
        and rae_result.evidence_catalog_preserved
        and cxee_result.definitive_catalog_preserved
        and ege_result.definitive_catalog_preserved
        and rge_result.definitive_catalog_preserved
        and rrb_result.source_data_preserved
    )

    pm7_output_contract_valid = (
        rrb_result.catalog.to_dict()["contract_name"] == PM7_OUTPUT_CATALOG_CONTRACT_NAME
        and bool(rrb_result.catalog.results)
        and rrb_result.catalog.results[0].to_dict()["contract_name"] == PM7_OUTPUT_CONTRACT_NAME
    )

    traceability_intact = (
        eae_result.document_id == document_id
        and cee_result.document_id == document_id
        and rae_result.document_id == document_id
        and cxee_result.document_id == document_id
        and ege_result.document_id == document_id
        and rge_result.document_id == document_id
        and rrb_result.document_id == document_id
        and rrb_result.model_id == model_id
        and rrb_result.catalog.document_id == document_id
        and rrb_result.catalog.model_id == model_id
        and rrb_result.catalog.source_evidence_catalog_id == evidence_catalog.catalog_id
        and rrb_result.catalog.source_consistency_catalog_id == consistency_catalog.catalog_id
        and rrb_result.catalog.source_risk_catalog_id == risk_catalog.catalog_id
        and rrb_result.catalog.source_context_catalog_id == context_catalog.catalog_id
        and rrb_result.catalog.source_explanation_catalog_id == explanation_catalog.catalog_id
        and rrb_result.catalog.source_recommendation_catalog_id == recommendation_catalog.catalog_id
        and rrb_result.catalog.source_definitive_catalog_id == definitive_catalog.get("catalog_id")
    )
    if rrb_result.catalog.results:
        group_result = rrb_result.catalog.results[0]
        traceability_intact = traceability_intact and bool(
            group_result.document_traceability.definitive_model_id
            and group_result.document_traceability.document_id == document_id
        )

    observations.extend(
        (
            f"stages_executed={stages}",
            f"results_count={results_count}",
            f"reasoning_result_status={rrb_result.status.value}",
            "pipeline_certification_complete=True" if stages == 7 else "pipeline_certification_partial=True",
        ),
    )

    return IntelligentAnalysisPipelineCertificationResult(
        process_id=process_id,
        document_id=document_id,
        model_id=model_id,
        evidence_analysis_passed=evidence_analysis_passed,
        consistency_evaluation_passed=consistency_evaluation_passed,
        risk_analysis_passed=risk_analysis_passed,
        context_evaluation_passed=context_evaluation_passed,
        explanation_generation_passed=explanation_generation_passed,
        recommendation_generation_passed=recommendation_generation_passed,
        reasoning_result_build_passed=reasoning_result_build_passed,
        traceability_intact=traceability_intact,
        definitive_catalog_preserved=definitive_catalog_preserved,
        source_catalogs_preserved=source_catalogs_preserved,
        pm7_output_contract_valid=pm7_output_contract_valid,
        integration_certification_framework_prepared=integration_certification_framework_prepared,
        results_count=results_count,
        stages_executed=stages,
        technical_observations=tuple(observations),
    )
