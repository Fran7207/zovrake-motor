"""PDF Adapter — estructura preparatoria."""

from zovrake_motor.comprehension.adapters.enums import DocumentFormatType
from zovrake_motor.comprehension.adapters.port import DocumentAdapterPort


class PdfDocumentAdapter(DocumentAdapterPort):
    """Responsabilidad futura: adaptar documentos PDF al flujo interno uniforme."""

    @property
    def format_type(self) -> DocumentFormatType:
        return DocumentFormatType.PDF

    @property
    def adapter_name(self) -> str:
        return "pdf_adapter"

    @property
    def adapter_label(self) -> str:
        return "PDF Adapter"

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        return (".pdf",)

    def is_ready(self) -> bool:
        return True
