# Motor Inteligente ZOVRAKE

Servicio Python **completamente independiente** del ERP frontend (`zovrake-web`).

**Versión:** 3.12.0 — Implementación 3.12 (Cierre formal del Prompt Maestro 5)

## Propósito

El Motor Inteligente de ZOVRAKE ha **cerrado oficialmente el Prompt Maestro 5** con la **Implementación 3.12**. El Módulo de Clasificación Inteligente queda declarado como pieza **estable, modular y certificada**, con el **Modelo Comparativo de Dominio** como único contrato de salida hacia el **Prompt Maestro 6**.

## Objetivo del Motor Inteligente

Actuar como servicio backend independiente que:

- Recibirá documentos y contexto del ERP (etapas futuras).
- Procesará cotizaciones con inteligencia artificial (etapas futuras).
- Devolverá resultados estructurados al ERP (etapas futuras).

El ERP **nunca** ejecutará algoritmos de IA. El Motor **nunca** generará interfaz gráfica.

## Estructura definitiva

```
zovrake-motor/
├── main.py                          # Punto de entrada
├── pyproject.toml                   # Configuración del proyecto
├── README.md                        # Documentación
├── tests/
│   ├── unit/                        # Pruebas unitarias
│   ├── integration/                 # Pruebas de integración
│   └── functional/                  # Pruebas funcionales
└── zovrake_motor/
    ├── certification/               # Certificación arquitectónica (1.10) ✓
    ├── config/                      # Sistema Centralizado de Configuración (1.6) ✓
    ├── coordinator/                 # Coordinador central (1.3) ✓
    ├── reception/                   # Recepción (1.4) ✓
    ├── documents/                   # Gestión de documentos (1.4) ✓
    ├── context/                     # Contexto del requerimiento (1.4) ✓
    ├── states/                      # Gestión de estados (1.4) ✓
    ├── events/                      # Registro de eventos (1.4) ✓
    ├── communication/               # Comunicación ERP (1.4) ✓
    ├── models/                      # Modelos y contratos internos (1.3)
    ├── processing/                  # Pipeline Interno (1.7) ✓
    ├── comprehension/               # Comprensión documental (2.1) ✓
    ├── classification/              # Clasificación inteligente (3.1+)
    ├── comparative_tables/          # Cuadros comparativos (1.6)
    ├── intelligent_analysis/        # Análisis inteligente (1.7)
    ├── integration/                 # Integración ERP ↔ Motor (1.8)
    ├── api/                         # API REST (1.8)
    ├── operations/                  # Arquitectura operativa (1.9)
    └── utils/                       # Utilidades comunes
```

## Responsabilidad de cada módulo

| Módulo | Responsabilidad |
|--------|-----------------|
| `certification` | **Certificación arquitectónica del núcleo — Prompt Maestro 3 (Implementado)** |
| `config` | **Sistema Centralizado de Configuración — fuente única (Implementado)** |
| `coordinator` | **Orquestación del flujo completo — núcleo del sistema (Implementado)** |
| `reception` | **Recibir solicitudes del ERP (Implementado)** |
| `documents` | **Administrar referencias a documentos (Implementado)** |
| `context` | **Administrar 'Detalles del requerimiento' (Implementado)** |
| `states` | **Sistema Central de Gestión de Estados — ciclo de vida por solicitud (Implementado)** |
| `events` | **Sistema Central de Gestión de Eventos — EMS (Implementado)** |
| `communication` | **Comunicación Motor ↔ ERP (Implementado)** |
| `models` | Modelos internos, contratos y objetos de dominio |
| `processing` | **Pipeline Interno — recorrido oficial de solicitudes (Implementado)** |
| `comprehension` | **Comprensión Documental CERTIFICADO (2.1–2.10) — PM4 FINALIZADO** |
| `classification` | Clasificación inteligente y grupos comparables |
| `comparative_tables` | Generación de cuadros comparativos |
| `intelligent_analysis` | Razonamiento y resultado del análisis |
| `integration` | Capa de integración ERP ↔ Motor |
| `api` | Exposición REST del Motor |
| `operations` | Observabilidad, seguridad y escalabilidad |
| `utils` | Utilidades compartidas entre módulos |

## Módulos Base (Implementación 1.4)

Cada módulo sigue la misma estructura arquitectónica:

```
modulo/
├── __init__.py     # Exportaciones públicas
├── port.py         # Contrato específico del módulo (ABC)
├── models.py       # Estructuras de datos
├── service.py      # Servicio que implementa ModulePort + Port
└── enums.py        # Enumeraciones (si aplica)
```

### Contrato común (`models/ports.py`)

Todo módulo implementa `ModulePort`:

- `module_name` — identificador único
- `is_available()` — estado de disponibilidad
- `initialize()` — inicialización del módulo

### Independencia entre módulos

- Ningún módulo importa a otro módulo base
- Toda interacción futura pasará exclusivamente por el `MotorCoordinator`
- Registro y administración mediante `ModuleAdministrator` (inyección de dependencias)
- Configuración obtenida exclusivamente desde `ConfigurationProvider`

### Módulos implementados

| Módulo | Servicio | Contrato |
|--------|----------|----------|
| `reception` | `ReceptionService` | `ReceptionPort` |
| `documents` | `DocumentService` | `DocumentsPort` |
| `context` | `ContextService` | `ContextPort` |
| `states` | `StateService` | `StatesPort` |
| `events` | `EventService` | `EventsPort` |
| `communication` | `CommunicationService` | `CommunicationPort` |

## Módulo de Comprensión Documental (Implementaciones 2.1–2.10 — CERTIFICADO)

El Prompt Maestro 4 está **oficialmente finalizado**. Ver `comprehension/CERTIFICATION.md` y `comprehension/ARCHITECTURE.md`.

```
comprehension/
├── ARCHITECTURE.md
├── service.py / port.py / registry.py / integration.py / pipeline.py
├── context_integration/         # Context Integration Engine (2.9) ✓
│   ├── ARCHITECTURE.md
│   ├── engine.py                # ContextIntegrationEngine
│   ├── gateway.py               # ContextInputGateway
│   ├── context_builder.py       # RequirementContextBuilder
│   ├── association_builder.py   # ContextAssociationBuilder
│   ├── store.py                 # ContextIntegrationStore
│   ├── dki_hook.py              # DkiAssociationPoint
│   ├── classification_hook.py   # ClassificationContextPoint
│   └── reasoning_hook.py        # ReasoningContextPoint
├── knowledge_index/             # Document Knowledge Index (2.8) ✓
│   ├── ARCHITECTURE.md
│   ├── engine.py                # DocumentKnowledgeIndex
│   ├── gateway.py               # InternalModelGateway
│   ├── entry_builder.py         # IndexEntryBuilder
│   ├── store.py                 # KnowledgeIndexStore
│   ├── query_hook.py            # QueryIntegrationPoint
│   └── reuse_hook.py            # ReuseIntegrationPoint
├── internal_model/              # Internal Document Model Builder (2.7) ✓
│   ├── ARCHITECTURE.md
│   ├── engine.py                # InternalDocumentModelBuilder
│   ├── port.py                  # InternalEntityBuilderPort
│   ├── registry.py              # EntityBuilderRegistry
│   ├── assembler.py             # InternalModelAssembler
│   ├── gateway.py               # CanonicalRepresentationGateway
│   ├── classification_hook.py   # ClassificationIntegrationPoint
│   └── builders/                # 10 constructores de entidad
├── canonical/                   # Canonical Representation Engine (2.6) ✓
├── extraction/                  # Content Extraction Engine (2.5) ✓
├── recognition/                 # Document Recognition Engine (2.4) ✓
├── validation/                  # Document Validation Framework (2.3) ✓
├── adapters/                    # Document Adapter Framework (2.2) ✓
└── components/                  # 11 componentes internos (2.1) ✓
```

| Aspecto | Detalle |
|---------|---------|
| Servicio | `ComprehensionService` |
| Integración de Contexto | `ContextIntegrationEngine` (CIE) |
| Índice Documental | `DocumentKnowledgeIndex` (DKI) |
| Modelo Interno | `InternalDocumentModelBuilder` (IDMB) |
| Representación Canónica | `CanonicalRepresentationEngine` (CRE) |
| Extracción | `ContentExtractionEngine` (CEE) |
| Resultado integración contexto | `ContextIntegrationResult` — asociación uniforme y trazable |
| Resultado indexación | `DocumentIndexResult` — entrada uniforme y trazable |
| Resultado modelo interno | `InternalModelBuildResult` — estructura uniforme e inmutable |
| Entidades | Documento, Proveedor, Comercial, Técnica, Ítems, Condiciones, Observaciones, Metadatos, Contexto, Referencias |
| Pipeline documental | ... → `INDEXACION` (8) → `INTEGRACION_CONTEXTO` (9) |
| Fuente de contexto | Exclusivamente `Detalles del requerimiento` |
| Integración DKI | Asociación sin modificar contenido del índice |
| Integración IDMB | Entrada exclusiva vía `InternalModelBuildResult` |
| Clasificación PM5 | `ClassificationContextPoint` preparado — sin ejecución |
| Razonamiento PM7 | `ReasoningContextPoint` preparado — sin ejecución |
| Administración | Exclusivamente por `MotorCoordinator` |

## Sistema Centralizado de Configuración (Implementación 1.6)

`ConfigurationProvider` es la **única fuente oficial** de configuración del Motor Inteligente.

### Arquitectura interna de config

```
config/
├── provider.py              # ConfigurationProvider — punto de acceso único
├── motor_configuration.py   # MotorConfiguration — agregado inmutable
├── loader.py                # ConfigurationLoader — carga por ambiente
├── validator.py             # ConfigurationValidator — validación estructural
├── accessible.py            # ConfigurationAccessible — mixin para módulos
├── enums.py                 # MotorEnvironment, ConfigCategory
├── categories/
│   ├── general.py           # Identidad y versión
│   ├── paths.py             # Rutas internas
│   ├── behavior.py          # Comportamiento del Motor
│   ├── communication.py     # Comunicación
│   ├── processing.py        # Procesamiento
│   ├── security.py          # Seguridad
│   ├── events.py            # Registro de eventos
│   ├── performance.py       # Rendimiento
│   └── future.py            # OCR, IA, API, almacenamiento, monitoreo
└── settings.py              # MotorSettings (alias de GeneralSettings)
```

### Categorías preparadas

| Categoría | Estado |
|-----------|--------|
| General | Activa |
| Rutas internas | Estructura |
| Comportamiento | Estructura |
| Comunicación | Estructura |
| Procesamiento | Estructura |
| Seguridad | Estructura |
| Eventos | Activa |
| Rendimiento | Estructura |
| Futuras (OCR, IA, API…) | Estructura reservada |

### Ambientes preparados

`development` · `testing` · `production` — sin cambio automático entre ambientes en esta etapa.

### Uso básico

```python
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor import ReceptionService, MotorCoordinator

config = ConfigurationProvider.default()
coordinator = MotorCoordinator(config_provider=config)
service = ReceptionService(config_provider=config)
```

## Pipeline Interno (Implementación 1.7)

El **Pipeline Interno** define el recorrido oficial de cada solicitud dentro del Motor. Es administrado **exclusivamente por el Coordinator** — ningún módulo controla el flujo.

### Arquitectura interna de processing

```
processing/
├── pipeline.py      # InternalPipeline — definición oficial de etapas
├── controller.py    # PipelineController — inicio, avance, detención, finalización
├── stages.py        # StageRegistry — registro extensible de etapas
├── models.py        # PipelineContext — contexto compartido de la solicitud
├── enums.py         # PipelineStageType, PipelineExecutionState
└── exceptions.py    # PipelineError, InvalidStageTransitionError
```

### Etapas del Pipeline (orden secuencial)

```
Recepción → Validación → Preparación → Coordinación → Procesamiento
→ Respuesta → Finalización
```

### Control exclusivo del Coordinator

| Método | Responsabilidad |
|--------|-----------------|
| `start_pipeline()` | Inicia el recorrido y crea el contexto compartido |
| `advance_pipeline()` | Avanza secuencialmente a la siguiente etapa |
| `run_internal_pipeline()` | Recorre todas las etapas sin procesamiento real |
| `stop_pipeline()` | Detiene el Pipeline |
| `finalize_pipeline()` | Finaliza el recorrido |
| `get_pipeline_context()` | Consulta el contexto compartido de una solicitud |

### Contexto compartido

`PipelineContext` acompaña cada solicitud durante todo su recorrido. Permite que módulos futuros compartan información **sin comunicarse directamente** entre sí. En esta etapa existe únicamente como estructura.

### Uso básico

```python
from uuid import uuid4
from zovrake_motor import MotorCoordinator

coordinator = MotorCoordinator()
process_id = uuid4()
result = coordinator.run_internal_pipeline(process_id)
context = coordinator.get_pipeline_context(process_id)
```

## Sistema de Gestión de Estados (Implementación 1.8)

`StateManager` es el **único responsable** de administrar el estado de cada proceso durante todo su ciclo de vida.

### Arquitectura interna de states

```
states/
├── manager.py         # StateManager — sistema central de estados
├── store.py           # StateStore — almacén independiente por solicitud
├── lifecycle.py       # StateLifecycle — referencia del ciclo de vida
├── observability.py   # StateChangeObserver — preparado para eventos futuros
├── enums.py           # MotorState — estados oficiales
├── models.py          # ProcessStateRecord, StateTransition
├── service.py         # StateService — fachada del módulo
└── exceptions.py      # StateManagementError, ProcessNotFoundError
```

### Estados oficiales

| Estado | Identificador |
|--------|---------------|
| Inicializado | `inicializado` |
| Esperando información | `esperando_informacion` |
| Validando información | `validando_informacion` |
| Información recibida | `informacion_recibida` |
| Preparando procesamiento | `preparando_procesamiento` |
| Procesamiento pendiente | `procesamiento_pendiente` |
| Procesando | `procesando` |
| Procesamiento completado | `procesamiento_completado` |
| Finalizado | `finalizado` |
| Error de validación | `error_validacion` |
| Error interno | `error_interno` |

### Control exclusivo del Coordinator

| Método | Responsabilidad |
|--------|-----------------|
| `create_process_state()` | Crea el estado inicial de una solicitud |
| `get_process_state()` | Consulta el estado actual |
| `transition_process_state()` | Registra una transición de estado |
| `get_state_snapshot()` | Snapshot del sistema de estados |

### Uso básico

```python
from uuid import uuid4
from zovrake_motor import MotorCoordinator, MotorState
from zovrake_motor.states import StateManager

state_manager = StateManager()
coordinator = MotorCoordinator(state_manager=state_manager)
process_id = uuid4()
coordinator.create_process_state(process_id, "REQ-001")
coordinator.transition_process_state(
    process_id,
    MotorState.ESPERANDO_INFORMACION,
    "Esperando datos del ERP",
)
```

## Sistema de Gestión de Eventos — EMS (Implementación 1.9)

`EventManager` es el **único responsable** de administrar eventos internos del Motor Inteligente.

### Arquitectura interna de events

```
events/
├── manager.py         # EventManager — sistema central de eventos
├── store.py           # EventStore — historial independiente por proceso
├── factory.py         # EventFactory — generación sin registro directo
├── lifecycle.py       # EventLifecycle — referencia del ciclo de vida
├── observability.py   # EventObserver — preparado para monitoreo futuro
├── enums.py           # EventType, EventCategory, EventLifecycleState
├── models.py          # MotorEvent — modelo uniforme
├── service.py         # EventService — fachada del módulo
└── exceptions.py      # EventManagementError, EventNotFoundError
```

### Modelo uniforme de evento

| Campo | Descripción |
|-------|-------------|
| `event_id` | Identificador único del evento |
| `process_id` | Identificador del proceso/solicitud |
| `module` | Módulo que originó el evento |
| `event_type` | Tipo oficial del evento |
| `occurred_at` | Fecha y hora |
| `associated_state` | Estado asociado (opcional) |
| `message` | Información descriptiva |
| `metadata` | Metadatos estructurados |

### Control exclusivo del Coordinator

| Método | Responsabilidad |
|--------|-----------------|
| `create_event()` | Crea un evento sin registrarlo |
| `register_event()` | Registra un evento en el EMS |
| `register_coordination_event()` | Registra evento de coordinación |
| `get_process_events()` | Consulta historial por solicitud |
| `finalize_event()` | Finaliza el ciclo de vida del evento |
| `get_event_snapshot()` | Snapshot del EMS |

### Uso básico

```python
from uuid import uuid4
from zovrake_motor import MotorCoordinator
from zovrake_motor.events import EventManager, EventType

event_manager = EventManager()
coordinator = MotorCoordinator(event_manager=event_manager)
process_id = uuid4()
coordinator.register_coordination_event(
    process_id=process_id,
    message="Solicitud recibida",
    event_type=EventType.CREATED,
)
```

## Coordinator Central (Implementación 1.3 y 1.5)

El `MotorCoordinator` es el único componente autorizado para coordinar el flujo interno y **administrar todos los módulos**. Los módulos nunca se comunican directamente entre sí.

### Arquitectura interna del Coordinator

```
coordinator/
├── coordinator.py           # MotorCoordinator — orquestación y administración
├── module_administrator.py  # Registro, descubrimiento y ciclo de vida
├── pipeline.py              # Estructura del flujo futuro
├── enums.py                 # Estados del Coordinator y ciclo de módulos
├── models.py                # CoordinationProcess, CoordinationResult
├── ports.py                 # BASE_MODULES, PLANNED_MODULES
├── registry.py              # ModuleRegistry — almacenamiento por composición
├── lifecycle.py             # LifecycleManager — fases del ciclo
├── events.py                # EventCollector — preparado para eventos
└── exceptions.py            # ModuleNotFoundError, ModuleNotAvailableError
```

### Responsabilidades del Coordinator (1.5)

| Capacidad | Descripción |
|-----------|-------------|
| Registro | `register_module()` — cada módulo se registra de forma independiente |
| Consulta | `get_module()`, `list_modules()`, `get_module_status()` |
| Descubrimiento | `discover_modules()` — módulos registrados vs. planificados |
| Validación | `validate_base_modules()`, `is_module_available()` |
| Ciclo de vida | `initialize_modules()`, `prepare_modules()`, `finalize_modules()` |
| Flujo futuro | `get_pipeline_stages()` — estructura sin ejecutar procesamiento |

### Pipeline de coordinación (estructura)

```
Recepción → Documentos → Contexto → Comprensión → Clasificación
→ Cuadros Comparativos → Análisis Inteligente
```

Módulos transversales: `states`, `events`. Integración futura: `communication`.

En esta etapa el pipeline existe únicamente como estructura administrativa.

### Estados del Coordinator

| Estado | Descripción |
|--------|-------------|
| `inicializado` | Coordinator creado |
| `esperando_modulos` | Preparado para recibir módulos |
| `preparado` | Listo para coordinar |
| `coordinando` | Ciclo de coordinación en curso |
| `finalizado` | Ciclo completado |
| `error_interno` | Error controlado |

### Ciclo de coordinación

```
Solicitud → Inicialización → Coordinación → Procesamiento → Finalización
```

En esta etapa recorre las fases sin ejecutar lógica de negocio.

### Uso básico

```python
from zovrake_motor import MotorCoordinator, ReceptionService

coordinator = MotorCoordinator()
coordinator.register_module(ReceptionService())
coordinator.initialize_modules()

discovery = coordinator.discover_modules()
pipeline = coordinator.get_pipeline_snapshot()
```

## Certificación Arquitectónica (Implementación 1.10)

El núcleo del Motor Inteligente ha sido **certificado** para evolucionar hacia el Prompt Maestro 4 sin modificar la arquitectura existente.

### Componentes evaluados

| Área | Verificación |
|------|--------------|
| Inicialización | Motor, Coordinator, Pipeline, Config, Estados, Eventos |
| Arquitectura | Separación de responsabilidades, independencia, desacoplamiento ERP |
| Coordinator | Único punto de coordinación, sin lógica de negocio |
| Módulos base | Contratos, inicialización, independencia |
| Pipeline | Etapas, orden secuencial, control del Coordinator |
| Gestión de Estados | 11 estados oficiales, ciclo por solicitud |
| Gestión de Eventos | Modelo uniforme, historial por proceso |
| Configuración | Fuente única, categorías extensibles |
| Prompt Maestro 4 | Módulos y configuración futuros reservados |

### Ejecutar certificación

```bash
python certify.py
# o
zovrake-motor-certify
```

### Ejecutar todas las pruebas

```bash
pytest tests/ -v
```

## Requisitos mínimos

- Python 3.11 o superior
- Sin dependencias de ejecución (stdlib únicamente)

## Instalación

```bash
cd zovrake-motor
pip install -e .
```

Para desarrollo con pruebas:

```bash
pip install -e ".[dev]"
```

## Ejecución

```bash
python main.py
```

Salida esperada:

```
zovrake-motor v1.0.0 iniciado correctamente.
Paquete: zovrake_motor v1.0.0
Ambiente: development
Coordinator: preparado
Módulos registrados: 7
Módulos base válidos: True
Estados oficiales: 11
EMS inicializado: 0 eventos
```

Certificación:

```bash
python certify.py
# Certificación global: APROBADA (67 verificaciones)
# Prompt Maestro 4 COMPLETO: SÍ

python certify_comprehension.py
# Certificación del módulo Comprensión: APROBADA (21 verificaciones)
# Preparado para Prompt Maestro 5: SÍ

python -m pytest tests/integration/test_comprehension_module_certification.py -v
```

## Roadmap de implementaciones

| Implementación | Componente |
|----------------|------------|
| 1.1 | Base del proyecto |
| 1.2 | Estructura definitiva (actual) |
| 1.3 | Coordinator Central (actual) |
| 1.4 | Módulos base |
| 1.5 | Administración central de módulos |
| 1.6 | Sistema centralizado de configuración |
| 1.7 | Pipeline Interno del Motor |
| 1.8 | Sistema de Gestión de Estados |
| 1.9 | Sistema de Gestión de Eventos — EMS |
| 1.10 | Certificación arquitectónica del núcleo (actual) |
| 2.0 | Prompt Maestro 4 — Comprensión Documental |
| 2.1 | Arquitectura base del Módulo de Comprensión Documental |
| 2.2 | Document Adapter Framework |
| 2.3 | Document Validation Framework |
| 2.4 | Document Recognition Engine |
| 2.5 | Content Extraction Engine (CEE) |
| 2.6 | Canonical Representation Engine (CRE) |
| 2.7 | Internal Document Model Builder (IDMB) |
| 2.8 | Document Knowledge Index (DKI) |
| 2.9 | Context Integration Engine (CIE) |
| 2.10 | Certificación integral Comprensión Documental (actual) |
| PM5 | Módulo de Clasificación Inteligente |

## Principios de arquitectura

- Clean Architecture
- SOLID — una responsabilidad por módulo
- Bajo acoplamiento con el ERP
- Organización consistente y preparada para crecimiento

## Licencia

Proprietary — ZOVRAKE
