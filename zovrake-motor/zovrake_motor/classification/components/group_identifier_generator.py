"""Group Identifier Generator — estructura preparatoria."""

from zovrake_motor.classification.components.base import ClassificationComponentPort


class GroupIdentifierGenerator(ClassificationComponentPort):
    """Responsabilidad futura: generar identificadores únicos para grupos comparables."""

    @property
    def component_name(self) -> str:
        return "group_identifier_generator"

    @property
    def component_label(self) -> str:
        return "Group Identifier Generator"

    def is_ready(self) -> bool:
        return False
