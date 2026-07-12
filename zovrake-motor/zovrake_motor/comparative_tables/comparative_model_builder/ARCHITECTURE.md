# Comparative Model Builder — Implementación 4.8

## Responsabilidad

El **Comparative Model Builder (CMB)** es el único componente responsable de construir el **Modelo Comparativo Definitivo**, contrato oficial de salida del Prompt Maestro 6.

**No genera** HTML, tablas visuales, PDF, recomendaciones ni resultados de análisis.

## Contrato oficial PM6

| Campo catálogo | Descripción |
|----------------|-------------|
| `pm6_definitive_output_contract` | Declara el contrato oficial de salida |
| `pm7_input_contract_prepared` | Preparado para consumo del PM7 |
| `models` | Un `DefinitiveComparativeModel` por Grupo Comparable |

## Estructura del modelo definitivo

Cada modelo incluye: identificador único, grupo, columnas dinámicas, filas dinámicas, organización de proveedores, información comercial y técnica, contexto, nivel de confianza, metadatos, trazabilidad y referencias internas.

## Reglas de inmutabilidad

- Los catálogos CSE, DCB, DRB, POE, GIE y TME permanecen intactos
- El CMB solo produce una representación consolidada inmutable
- Sin acceso a documentos originales ni modelos intermedios prohibidos

## Integración

| Componente | Relación |
|------------|----------|
| Pipeline PM6 | Etapa 9 — `MODELO_COMPARATIVO` |
| CVF (4.9) | `ComparativeValidationFrameworkIntegrationPoint` preparado |

## Próximo paso

**Implementación 4.9** — Comparative Validation Framework (CVF).
