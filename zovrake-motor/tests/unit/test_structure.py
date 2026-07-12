"""Pruebas de la estructura del proyecto — Implementación 1.2."""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

from zovrake_motor import MotorSettings, __version__

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGE_ROOT = PROJECT_ROOT / "zovrake_motor"

EXPECTED_MODULES = (
    "certification",
    "config",
    "coordinator",
    "reception",
    "documents",
    "context",
    "states",
    "events",
    "communication",
    "models",
    "processing",
    "comprehension",
    "classification",
    "comparative_tables",
    "intelligent_analysis",
    "enterprise_integration",
    "integration",
    "api",
    "operations",
    "utils",
)


class TestProjectStructure:
    def test_version(self):
        assert __version__ == "8.12.0"

    def test_settings_default(self):
        settings = MotorSettings.default()
        assert settings.service_name == "zovrake-motor"
        assert settings.service_version == "8.12.0"

    def test_all_modules_exist(self):
        for module_name in EXPECTED_MODULES:
            module_path = PACKAGE_ROOT / module_name
            assert module_path.is_dir(), f"Falta módulo: {module_name}"
            init_file = module_path / "__init__.py"
            assert init_file.is_file(), f"Falta __init__.py en: {module_name}"

    def test_all_modules_importable(self):
        for module_name in EXPECTED_MODULES:
            module = importlib.import_module(f"zovrake_motor.{module_name}")
            assert module.__doc__, f"El módulo {module_name} debe tener docstring"

    def test_no_duplicate_module_names(self):
        names = [p.name for p in PACKAGE_ROOT.iterdir() if p.is_dir() and not p.name.startswith("_")]
        assert len(names) == len(set(names))

    def test_test_directories_exist(self):
        tests_root = PROJECT_ROOT / "tests"
        for subdir in ("unit", "integration", "functional"):
            assert (tests_root / subdir).is_dir()

    def test_certification_directory_exists(self):
        assert (PROJECT_ROOT / "tests" / "certification").is_dir()
        assert (PROJECT_ROOT / "certify.py").is_file()

    def test_main_exits_successfully(self):
        result = subprocess.run(
            [sys.executable, "main.py"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert "iniciado correctamente" in result.stdout
