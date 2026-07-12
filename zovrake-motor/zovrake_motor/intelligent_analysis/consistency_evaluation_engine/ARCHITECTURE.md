# Consistency Evaluation Engine — Arquitectura

**Implementación 7.3 — Prompt Maestro 7 (CEE operativo)**

## Responsabilidad

Evaluar la consistencia lógica y estructural de evidencias organizadas por el EAE sin interpretar, concluir ni recomendar.

## Entrada

`EvidenceAnalysisCatalog` (EAE) vía `EvidenceAnalysisCatalogGateway`.

## Salida

`ConsistencyEvaluationCatalog` con perfiles de consistencia, inconsistencias registradas y evaluación de suficiencia.

## Criterios de consistencia

1. Coherencia entre información comercial y técnica
2. Consistencia entre proveedores del mismo Grupo Comparable
3. Integridad de la información disponible
4. Relaciones válidas entre atributos comparables
5. Ausencia de contradicciones evidentes

## Tipos de inconsistencias

- Información contradictoria
- Datos incompatibles
- Atributos inconsistentes
- Referencias incompletas
- Diferencias relevantes entre evidencias

## Preservación

- No modifica el catálogo de evidencias del EAE
- No accede al Modelo Comparativo Definitivo ni documentos originales
- Registra inconsistencias sin corregirlas automáticamente

## Próximo paso

**Implementación 7.4** — Risk Analysis Engine (RAE).
