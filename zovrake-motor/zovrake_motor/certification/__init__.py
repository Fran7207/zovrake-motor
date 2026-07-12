"""Certificación arquitectónica del núcleo del Motor Inteligente."""

from zovrake_motor.certification.checker import CoreCertificationChecker
from zovrake_motor.certification.classification_pipeline import (
    ClassificationPipelineCertificationResult,
    run_full_classification_pipeline,
)
from zovrake_motor.certification.comparative_tables_pipeline import (
    ComparativeTablesPipelineCertificationResult,
    run_full_comparative_tables_pipeline,
)
from zovrake_motor.certification.intelligent_analysis_pipeline import (
    IntelligentAnalysisPipelineCertificationResult,
    run_full_intelligent_analysis_pipeline,
)
from zovrake_motor.certification.comprehension_pipeline import (
    ComprehensionPipelineCertificationResult,
    run_full_comprehension_pipeline,
)
from zovrake_motor.certification.enums import CertificationArea, CertificationStatus
from zovrake_motor.certification.models import CertificationCheck, CertificationReport
from zovrake_motor.certification.stack import build_certified_stack

__all__ = [
    "CertificationArea",
    "CertificationCheck",
    "CertificationReport",
    "CertificationStatus",
    "ClassificationPipelineCertificationResult",
    "ComparativeTablesPipelineCertificationResult",
    "ComprehensionPipelineCertificationResult",
    "IntelligentAnalysisPipelineCertificationResult",
    "CoreCertificationChecker",
    "build_certified_stack",
    "run_full_classification_pipeline",
    "run_full_comparative_tables_pipeline",
    "run_full_comprehension_pipeline",
    "run_full_intelligent_analysis_pipeline",
]


def __getattr__(name: str):
    if name == "ComprehensionModuleCertificationChecker":
        from zovrake_motor.certification.comprehension_checker import ComprehensionModuleCertificationChecker

        return ComprehensionModuleCertificationChecker
    if name == "ClassificationModuleCertificationChecker":
        from zovrake_motor.certification.classification_checker import ClassificationModuleCertificationChecker

        return ClassificationModuleCertificationChecker
    if name == "ClassificationModuleClosureChecker":
        from zovrake_motor.certification.classification_closure_checker import ClassificationModuleClosureChecker

        return ClassificationModuleClosureChecker
    if name == "ComparativeTablesModuleCertificationChecker":
        from zovrake_motor.certification.comparative_tables_checker import (
            ComparativeTablesModuleCertificationChecker,
        )

        return ComparativeTablesModuleCertificationChecker
    if name == "IntelligentAnalysisModuleCertificationChecker":
        from zovrake_motor.certification.intelligent_analysis_checker import (
            IntelligentAnalysisModuleCertificationChecker,
        )

        return IntelligentAnalysisModuleCertificationChecker
    if name == "IntelligentAnalysisModuleClosureChecker":
        from zovrake_motor.certification.intelligent_analysis_closure_checker import (
            IntelligentAnalysisModuleClosureChecker,
        )

        return IntelligentAnalysisModuleClosureChecker
    if name == "EnterpriseIntegrationE2ECertificationChecker":
        from zovrake_motor.certification.enterprise_integration_e2e_checker import (
            EnterpriseIntegrationE2ECertificationChecker,
        )

        return EnterpriseIntegrationE2ECertificationChecker
    if name == "EnterpriseIntegrationPlatformCertificationChecker":
        from zovrake_motor.certification.enterprise_integration_platform_checker import (
            EnterpriseIntegrationPlatformCertificationChecker,
        )

        return EnterpriseIntegrationPlatformCertificationChecker
    if name == "EnterpriseIntegrationModuleClosureChecker":
        from zovrake_motor.certification.enterprise_integration_closure_checker import (
            EnterpriseIntegrationModuleClosureChecker,
        )

        return EnterpriseIntegrationModuleClosureChecker
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
