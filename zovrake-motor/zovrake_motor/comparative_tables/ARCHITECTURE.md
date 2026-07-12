# Módulo de Generación de Cuadros Comparativos — Arquitectura Base

**Implementación 4.2 — Prompt Maestro 6 (CSE operativo)**

## Responsabilidad del módulo

Transformar el **Modelo Comparativo de Dominio** (salida certificada del PM5) en modelos de **Cuadros Comparativos dinámicos** que posteriormente serán representados por el Frontend.

En esta etapa el módulo **no genera cuadros comparativos** ni ejecuta lógica de negocio.

## Límites del módulo

| Dentro del módulo | Fuera del módulo |
|-------------------|------------------|
| Estructura de componentes preparados | Construcción de columnas/filas |
| Consumo vía `ComparativeDomainModelReference` | Acceso a documentos originales |
| Orquestación interna futura | Acceso a modelos intermedios de PM4/PM5 |
| Validación estructural del gateway | Representación visual |
| Integración con Coordinator | Integración directa con ERP/Frontend |

## Fronteras arquitectónicas

```
PM5 Clasificación → PM6 Cuadros Comparativos → PM7 Análisis Inteligente
```

Sin comunicación directa entre motores. **Coordinator General** como único orquestador.

## Flujo de integración

1. **MotorCoordinator** registra `ComparativeTablesService` (order 6 en pipeline).
2. **ClassificationOutputGateway** valida referencias al Modelo Comparativo de Dominio.
3. **ComparativeTablesPipeline** define 12 etapas preparadas.
4. **ComponentRegistry** administra 10 componentes (9 stubs + coordinator).
5. **ConfigurationProvider** suministra `ComparativeTablesSettings`.
6. **StateManager / EventManager** disponibles vía `ComparativeTablesMotorIntegration`.

## Contratos internos

| Contrato | Responsabilidad |
|----------|-----------------|
| `ComparativeTablesPort` | Punto de entrada del módulo (`prepare`) |
| `ComparativeTablesComponentPort` | Contrato base de cada componente interno |
| `ComparativeDomainModelReference` | Referencia inmutable al modelo PM5 |
| `ComparativeTablesInputBundle` | Paquete de entrada del proceso |
| `ClassificationOutputGateway` | Consumo desacoplado del modelo de dominio |

## Componentes preparados (Implementación 4.2+)

| Componente | Identificador | Estado |
|------------|---------------|--------|
| Comparative Structure Engine | `comparative_structure_engine` | **4.2 — Operativo** |
| Dynamic Column Builder | `dynamic_column_builder` | **4.3 — Operativo** |
| Dynamic Row Builder | `dynamic_row_builder` | **4.4 — Operativo** |
| Provider Organization Engine | `provider_organization_engine` | **4.5 — Operativo** |
| Group Integrity Engine | `group_integrity_engine` | **4.6 — Operativo** |
| Traceability & Metadata Engine | `traceability_metadata_engine` | **4.7 — Operativo** |
| Comparative Model Builder | `comparative_model_builder` | **4.8 — Operativo** |
| Comparative Validation Framework | `comparative_validation_framework` | **4.9 — Operativo** |
| Comparative Quality Framework | `comparative_quality_framework` | **4.10 — Operativo** |
| Coordinator de Cuadros Comparativos | `comparative_tables_coordinator` | Operativo |

## Pipeline interno (12 etapas)

1. Preparación
2. Consumo del Modelo Comparativo de Dominio
3. Estructura Comparativa → `comparative_structure_engine`
4. Construcción de Columnas → `dynamic_column_builder`
5. Construcción de Filas → `dynamic_row_builder`
6. Organización de Proveedores → `provider_organization_engine`
7. Integridad de Grupos → `group_integrity_engine`
8. Trazabilidad y Metadatos → `traceability_metadata_engine`
9. Modelo Comparativo → `comparative_model_builder`
10. Validación Comparativa → `comparative_validation_framework`
11. Validación de Calidad → `comparative_quality_framework`
12. Finalización

## Puntos de extensión

- Nuevos constructores y validadores mediante `ComponentRegistry.register()`.
- Nuevas etapas del pipeline mediante extensión de `DEFAULT_STAGES`.
- Configuración por componente vía `ConfigurationProvider.comparative_tables()`.
- Sin modificar el núcleo del módulo ni del Coordinator.

## Próximo paso

**Implementación 4.11** — Integración y Certificación Completa del Módulo PM6 — **COMPLETADA**.

**Implementación 4.12** — Cierre oficial, certificación final y congelamiento arquitectónico del Prompt Maestro 6.

## Certificación (4.11)

| Artefacto | Ubicación |
|-----------|-----------|
| Pipeline certificado | `zovrake_motor/certification/comparative_tables_pipeline.py` |
| Checker integral | `zovrake_motor/certification/comparative_tables_checker.py` |
| Fixtures PM5→PM6 | `zovrake_motor/certification/comparative_tables_fixtures.py` |
| Gobierno del módulo | `zovrake_motor/comparative_tables/governance.py` |
| Contrato de salida | `zovrake_motor/comparative_tables/OUTPUT_CONTRACT.md` |
| Documentación | `zovrake_motor/comparative_tables/CERTIFICATION.md` |

### Pipeline certificado (9 etapas funcionales)

```
Modelo Comparativo de Dominio
  → Comparative Structure Engine
  → Dynamic Column Builder
  → Dynamic Row Builder
  → Provider Organization Engine
  → Group Integrity Engine
  → Traceability & Metadata Engine
  → Comparative Model Builder
  → Comparative Validation Framework
  → Comparative Quality Framework
  → Modelo Comparativo Definitivo
```

### Integración con Prompt Maestro 7

El **Modelo Comparativo Definitivo** (`DefinitiveComparativeModelCatalog` v1.0) queda como única fuente oficial de entrada para el Módulo de Razonamiento y Resultado del Análisis Inteligente.
