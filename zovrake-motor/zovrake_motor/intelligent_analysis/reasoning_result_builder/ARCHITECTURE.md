# Reasoning Result Builder (RRB) — Implementación 7.8

## Responsabilidad

El **Reasoning Result Builder (RRB)** construye el **Resultado del Análisis Inteligente**,
único contrato oficial de salida del Prompt Maestro 7.

## Contrato oficial PM7

| Artefacto | Nombre |
|-----------|--------|
| Resultado por grupo | `GroupIntelligentAnalysisResult` |
| Catálogo de resultados | `IntelligentAnalysisResultCatalog` |

1 Grupo Comparable → 1 Resultado del Análisis Inteligente.

## Entradas (solo lectura)

EAE, CEE, RAE, CxEE, EGE, RGE y Modelo Comparativo Definitivo.

## Estructura mínima por resultado

- Identificador único, grupo, modelo definitivo
- Resumen ejecutivo, explicación estructurada, recomendación
- Nivel de confianza, fortalezas, debilidades, riesgos, limitaciones
- Contexto considerado, trazabilidad documental, metadatos

## Preservación

El RRB nunca modifica catálogos de origen ni documentos originales.

## Integración

- **Pipeline**: fase `CONSTRUCCION_RESULTADO_ANALISIS_INTELIGENTE`
- **Downstream**: Integration & Certification Framework (7.9)
