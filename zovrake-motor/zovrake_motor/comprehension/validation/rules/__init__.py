"""Reglas de validación documental del DVF."""

from zovrake_motor.comprehension.validation.rules.corrupt_file import CorruptFileRule
from zovrake_motor.comprehension.validation.rules.empty_file import EmptyFileRule
from zovrake_motor.comprehension.validation.rules.inaccessible_file import InaccessibleFileRule
from zovrake_motor.comprehension.validation.rules.incomplete_document import IncompleteDocumentRule
from zovrake_motor.comprehension.validation.rules.inconsistent_structure import InconsistentStructureRule
from zovrake_motor.comprehension.validation.rules.illegible_document import IllegibleDocumentRule
from zovrake_motor.comprehension.validation.rules.invalid_size import InvalidSizeRule
from zovrake_motor.comprehension.validation.rules.unsupported_format import UnsupportedFormatRule

__all__ = [
    "CorruptFileRule",
    "EmptyFileRule",
    "IllegibleDocumentRule",
    "InaccessibleFileRule",
    "IncompleteDocumentRule",
    "InconsistentStructureRule",
    "InvalidSizeRule",
    "UnsupportedFormatRule",
]
