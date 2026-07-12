# Módulo de Clasificación Inteligente — Arquitectura Definitiva

**Implementación 3.12 — Prompt Maestro 5 CERRADO**

## Estado oficial

| Atributo | Valor |
|----------|-------|
| Prompt Maestro | 5 — **CERRADO** |
| Certificación integral | 3.11 |
| Cierre formal | 3.12 |
| Contrato de salida | `ComparativeDomainModelCatalog` v1.0 |
| Próximo módulo | Prompt Maestro 6 |

Documentación de cierre: [CLOSURE.md](./CLOSURE.md) | Contrato PM6: [OUTPUT_CONTRACT.md](./OUTPUT_CONTRACT.md)

## Responsabilidad del módulo

Transformar la salida de Comprensión Documental en un **Modelo Comparativo de Dominio** consistente, trazable e inmutable, validado por el Classification Quality Framework, como **único contrato oficial** hacia PM6.

## Componentes congelados (estables)

| Componente | Identificador | Impl. |
|------------|---------------|-------|
| Concept Analysis Engine | `concept_analysis_engine` | 3.2 |
| Material Classification Engine | `material_classification_engine` | 3.3 |
| Service Classification Engine | `service_classification_engine` | 3.4 |
| Concept Normalization Engine | `concept_normalization_engine` | 3.5 |
| Equivalence Detection Engine | `equivalence_detection_engine` | 3.6 |
| Comparable Group Builder | `comparable_group_builder` | 3.7 |
| Context Association Engine | `context_association_engine` | 3.8 |
| Comparative Domain Model Builder | `comparative_domain_model_builder` | 3.9 |
| Classification Quality Framework | `classification_quality_framework` | 3.10 |

## Pipeline (14 etapas / 9 funcionales)

1. Preparación
2. Análisis de Conceptos → `concept_analysis_engine`
3. Clasificación de Materiales → `material_classification_engine`
4. Clasificación de Servicios → `service_classification_engine`
5. Normalización Conceptual → `concept_normalization_engine`
6. Detección de Equivalencias → `equivalence_detection_engine`
7. Construcción de Grupos Comparables → `comparable_group_builder`
8. Identificación de Grupos → `group_identifier_generator` (reservado)
9. Asociación de Contexto → `context_association_engine`
10. Trazabilidad → `traceability_manager` (reservado)
11. Evaluación de Confianza → `confidence_evaluation_engine` (reservado)
12. Modelo de Dominio Comparativo → `comparative_domain_model_builder`
13. Validación de Calidad → `classification_quality_framework`
14. Finalización

## Fronteras arquitectónicas

```
PM4 Comprensión → PM5 Clasificación → PM6 Cuadros Comparativos
```

Sin comunicación directa entre motores. Coordinator General como único orquestador.

## Integración arquitectónica

- **ClassificationService** — punto de entrada
- **ClassificationPipeline** — ejecución secuencial
- **ComprehensionOutputGateway** — consumo de IDMB sin acoplamiento
- **ConfigurationProvider** — configuración centralizada
- **StateManager / EventManager** — trazabilidad operativa
- **governance.py** — metadatos de cierre y congelamiento

## Contrato hacia Prompt Maestro 6

`ComparativeDomainModelCatalog` con `pm6_output_contract=True` — sin transformaciones adicionales.

## Puntos de extensión (evolución controlada)

Nuevos clasificadores, detectores, normalizadores, agrupadores, constructores y validadores mediante `registry.register()` en cada motor — sin modificar el núcleo.

## Próximo paso

**Prompt Maestro 6** — Generación Automática de Cuadros Comparativos.
