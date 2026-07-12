"""Word Adapter — estructura preparatoria."""

from zovrake_motor.comprehension.adapters.enums import DocumentFormatType
from zovrake_motor.comprehension.adapters.port import DocumentAdapterPort


class WordDocumentAdapter(DocumentAdapterPort):
    """Responsabilidad futura: adaptar documentos Word al flujo interno uniforme."""

    @property
    def format_type(self) -> DocumentFormatType:
        return DocumentFormatType.WORD

    @property
    def adapter_name(self) -> str:
        return "word_adapter"

    @property
    def adapter_label(self) -> str:
        return "Word Adapter"

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        return (".docx", ".doc")

    def is_ready(self) -> bool:
        return True
