"""Image Adapter — estructura preparatoria."""

from zovrake_motor.comprehension.adapters.enums import DocumentFormatType
from zovrake_motor.comprehension.adapters.port import DocumentAdapterPort


class ImageDocumentAdapter(DocumentAdapterPort):
    """Responsabilidad futura: adaptar imágenes documentales al flujo interno uniforme."""

    @property
    def format_type(self) -> DocumentFormatType:
        return DocumentFormatType.IMAGE

    @property
    def adapter_name(self) -> str:
        return "image_adapter"

    @property
    def adapter_label(self) -> str:
        return "Image Adapter"

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        return (".png", ".jpg", ".jpeg", ".tiff", ".bmp")

    def is_ready(self) -> bool:
        return True
