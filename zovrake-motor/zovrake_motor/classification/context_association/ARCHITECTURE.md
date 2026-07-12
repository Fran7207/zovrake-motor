# Context Association Engine (CAE-Context) — Arquitectura

**Implementación 3.8 — Prompt Maestro 5**

## Responsabilidad

Asociar el contexto del requerimiento ("Detalles del requerimiento") con cada Grupo Comparable sin modificar ninguno.

## Reglas

- No modifica el contexto original
- No modifica los Grupos Comparables
- No toma decisiones ni aplica reglas de negocio
- Entrada: catálogo CGB + contexto integrado
- Salida: `ContextAssociationCatalog`

## Próximo paso

**Implementación 3.9** — Comparative Domain Model Builder (CDMB).
