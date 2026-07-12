# Módulo de Razonamiento y Resultado del Análisis Inteligente — Arquitectura Base

**Implementación 7.1 — Prompt Maestro 7 (arquitectura base)**

## Responsabilidad del módulo

Analizar el **Modelo Comparativo Definitivo** (salida certificada del PM6) y producir un **Resultado del Análisis Inteligente** completamente explicable y basado en evidencias.

En esta etapa el módulo **no ejecuta razonamiento** ni genera resultados de análisis.

## Límites del módulo

| Dentro del módulo | Fuera del módulo |
|-------------------|------------------|
| Estructura de componentes preparados | Análisis de evidencias |
| Consumo vía `DefinitiveComparativeModelReference` | Acceso a documentos originales |
| Orquestación interna futura | Acceso a modelos intermedios de PM4/PM5/PM6 |
| Validación estructural del gateway | Representación visual |
| Integración con Coordinator | Integración directa con ERP/Frontend |

## Fronteras arquitectónicas

```
PM6 Cuadros Comparativos → PM7 Razonamiento Inteligente → Resultado del Análisis
```

Sin comunicación directa entre motores. **Coordinator General** como único orquestador.

## Flujo de integración

1. **MotorCoordinator** registra `IntelligentAnalysisService` (order 7 en pipeline).
2. **ComparativeTablesOutputGateway** valida referencias al Modelo Comparativo Definitivo.
3. **IntelligentAnalysisPipeline** define 13 etapas preparadas.
4. **ComponentRegistry** administra 11 componentes (10 motores/stubs + coordinator).
5. **ConfigurationProvider** suministra `IntelligentAnalysisSettings`.
6. **StateManager / EventManager** disponibles vía `IntelligentAnalysisMotorIntegration`.

## Contratos internos

| Contrato | Responsabilidad |
|----------|-----------------|
| `IntelligentAnalysisPort` | Punto de entrada del módulo (`prepare`) |
| `IntelligentAnalysisComponentPort` | Contrato base de cada componente interno |
| `DefinitiveComparativeModelReference` | Referencia inmutable al modelo PM6 |
| `IntelligentAnalysisInputBundle` | Paquete de entrada del proceso |
| `ComparativeTablesOutputGateway` | Consumo desacoplado del modelo definitivo |

## Componentes preparados (Implementación 7.1)

| Componente | Identificador | Estado |
|------------|---------------|--------|
| Evidence Analysis Engine | `evidence_analysis_engine` | **7.2 — Operativo** |
| Consistency Evaluation Engine | `consistency_evaluation_engine` | **7.3 — Operativo** |
| Risk Analysis Engine | `risk_analysis_engine` | **7.4 — Operativo** |
| Context Evaluation Engine | `context_evaluation_engine` | **7.5 — Operativo** |
| Explanation Generation Engine | `explanation_generation_engine` | **7.6 — Operativo** |
| Conclusion Generation Engine | `conclusion_generation_engine` | **7.1 — Preparado** |
| Recommendation Generation Engine | `recommendation_generation_engine` | **7.7 — Operativo** |
| Reasoning Result Builder | `reasoning_result_builder` | **7.8 — Operativo** |
| Confidence Management Engine | `confidence_management_engine` | **7.1 — Preparado** |
| Traceability Management Engine | `traceability_management_engine` | **7.1 — Preparado** |
| Coordinator de Razonamiento | `intelligent_analysis_coordinator` | Operativo |

## Pipeline interno (13 etapas)

1. Preparación
2. Consumo del Modelo Comparativo Definitivo
3. Análisis de Evidencias → `evidence_analysis_engine`
4. Evaluación de Consistencia → `consistency_evaluation_engine`
5. Análisis de Riesgos → `risk_analysis_engine`
6. Evaluación de Contexto → `context_evaluation_engine`
7. Generación de Explicaciones → `explanation_generation_engine`
8. Generación de Conclusiones → `conclusion_generation_engine`
9. Generación de Recomendaciones → `recommendation_generation_engine`
10. Construcción del Resultado del Análisis Inteligente → `reasoning_result_builder`
11. Gestión de Confianza → `confidence_management_engine`
12. Gestión de Trazabilidad → `traceability_management_engine`
13. Finalización

## Contrato oficial de salida (PM7)

El **Resultado del Análisis Inteligente** (`GroupIntelligentAnalysisResult` / `IntelligentAnalysisResultCatalog`) es el único contrato de salida del Prompt Maestro 7. Ningún módulo posterior consumirá directamente explicaciones, recomendaciones, riesgos, evidencias ni el Modelo Comparativo Definitivo.

## Puntos de extensión

- Nuevos motores de razonamiento mediante `ComponentRegistry.register()`.
- Nuevas etapas del pipeline mediante extensión de `DEFAULT_STAGES`.
- Configuración por componente vía `ConfigurationProvider.intelligent_analysis()`.
- Sin modificar el núcleo del módulo ni del Coordinator.

## Próximo paso

**Implementación 7.2** — Evidence Analysis Engine (EAE) operativo.

**Implementación 7.3** — Consistency Evaluation Engine (CEE) operativo.

**Implementación 7.4** — Risk Analysis Engine (RAE) operativo.

**Implementación 7.5** — Context Evaluation Engine (CxEE) operativo.

**Implementación 7.6** — Explanation Generation Engine (EGE) operativo.

**Implementación 7.7** — Recommendation Generation Engine (RGE) operativo.

**Implementación 7.8** — Reasoning Result Builder (RRB) operativo.

**Implementación 7.10** — Prompt Maestro 7 **CERRADO** — ver [CLOSURE.md](./CLOSURE.md).
