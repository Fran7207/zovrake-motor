# Evidence Analysis Engine — Arquitectura

**Implementación 7.2 — Prompt Maestro 7 (EAE operativo)**

## Responsabilidad

Identificar y organizar evidencias del **Modelo Comparativo Definitivo** sin interpretar, concluir ni recomendar.

## Entrada

`DefinitiveComparativeModelCatalog` (PM6) vía `DefinitiveComparativeModelCatalogGateway`.

## Salida

`EvidenceAnalysisCatalog` con perfiles por modelo, evidencias categorizadas y ausencias registradas.

## Categorías de evidencia

1. Información comercial
2. Información técnica
3. Condiciones comerciales
4. Tiempos de entrega
5. Garantías
6. Certificaciones
7. Observaciones
8. Restricciones
9. Metadatos
10. Contexto del requerimiento

## Preservación

- No modifica el Modelo Comparativo Definitivo
- No accede a documentos originales ni modelos intermedios
- Registra ausencias sin completar datos

## Próximo paso

**Implementación 7.3** — Consistency Evaluation Engine (CEE).
