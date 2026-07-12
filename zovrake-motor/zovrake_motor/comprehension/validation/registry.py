"""Registro centralizado de reglas de validación documental."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.validation.exceptions import ValidationRuleNotFoundError
from zovrake_motor.comprehension.validation.port import ValidationRulePort
from zovrake_motor.comprehension.validation.rules import (
    CorruptFileRule,
    EmptyFileRule,
    IllegibleDocumentRule,
    InaccessibleFileRule,
    IncompleteDocumentRule,
    InconsistentStructureRule,
    InvalidSizeRule,
    UnsupportedFormatRule,
)
from zovrake_motor.config.categories.comprehension import DocumentValidationSettings


class ValidationRuleRegistry:
    """
    Registro único de reglas de validación documental.

    Toda regla debe registrarse exclusivamente desde este punto.
    """

    def __init__(self) -> None:
        self._rules_by_name: dict[str, ValidationRulePort] = {}
        self._rules_ordered: list[ValidationRulePort] = []

    def register(self, rule: ValidationRulePort) -> None:
        if rule.rule_name in self._rules_by_name:
            raise ValueError(f"Regla ya registrada: {rule.rule_name}")
        self._rules_by_name[rule.rule_name] = rule
        self._rules_ordered.append(rule)

    def register_defaults(self, *, settings: DocumentValidationSettings | None = None) -> None:
        defaults: tuple[ValidationRulePort, ...] = (
            EmptyFileRule(),
            CorruptFileRule(),
            UnsupportedFormatRule(settings=settings),
            InaccessibleFileRule(),
            IncompleteDocumentRule(),
            IllegibleDocumentRule(),
            InvalidSizeRule(settings=settings),
            InconsistentStructureRule(),
        )
        for rule in defaults:
            self.register(rule)

    def get(self, name: str) -> ValidationRulePort | None:
        return self._rules_by_name.get(name)

    def require(self, name: str) -> ValidationRulePort:
        rule = self.get(name)
        if rule is None:
            raise ValidationRuleNotFoundError(f"Regla no registrada: {name}")
        return rule

    def all_rules(self) -> tuple[ValidationRulePort, ...]:
        return tuple(self._rules_ordered)

    def count(self) -> int:
        return len(self._rules_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [rule.snapshot() for rule in self._rules_ordered]
