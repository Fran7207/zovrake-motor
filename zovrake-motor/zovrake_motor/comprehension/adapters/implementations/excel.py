"""Excel Adapter — estructura preparatoria."""

from zovrake_motor.comprehension.adapters.enums import DocumentFormatType
from zovrake_motor.comprehension.adapters.port import DocumentAdapterPort


class ExcelDocumentAdapter(DocumentAdapterPort):
    """Responsabilidad futura: adaptar documentos Excel al flujo interno uniforme."""

    @property
    def format_type(self) -> DocumentFormatType:
        return DocumentFormatType.EXCEL

    @property
    def adapter_name(self) -> str:
        return "excel_adapter"

    @property
    def adapter_label(self) -> str:
        return "Excel Adapter"

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        return (".xlsx", ".xls")

    def is_ready(self) -> bool:
        return True
