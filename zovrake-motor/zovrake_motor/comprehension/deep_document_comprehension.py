"""Comprensión profunda unificada, genérica y determinista de documentos PDF.

Esta capa trabaja exclusivamente sobre ``DocumentKnowledge`` ya construido.
No vuelve a abrir el PDF, no usa servicios remotos y no depende de LLM,
transformers, tokenizers ni redes neuronales.

Objetivo de diseño
------------------
La comprensión profunda no puede reducirse a una plantilla de cotización.
El documento se trata como un sistema de evidencia compuesto por:

* regiones y orden espacial;
* texto nativo y OCR;
* tablas físicas y tablas semánticas;
* imágenes y observaciones visuales;
* objetos estructurales del PDF;
* hechos y atributos ya detectados;
* entidades y relaciones ya resueltas;
* referencias, valores tipados, contexto y contradicciones.

El resultado es una representación semántica documental más rica que queda
conservada en ``DocumentKnowledge.metadata`` para las siguientes capas.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from datetime import datetime
from decimal import Decimal, InvalidOperation
import math
import re
import unicodedata
from hashlib import sha256
from typing import Any, Iterable

from zovrake_motor.comprehension.models import (
    DocumentEntity,
    DocumentKnowledge,
    DocumentRelationship,
)
from zovrake_motor.comprehension.universal_document_semantic_reasoner import (
    UniversalDocumentSemanticReasoner,
)


class DeepDocumentComprehensionEngine:
    """Motor genérico de comprensión semántica documental local.

    La salida es deliberadamente conservadora: cuando la evidencia no permite
    resolver algo con seguridad, se registra como candidato/no resuelto en vez
    de fabricar un hecho.
    """

    MODEL_VERSION = "3.0-universal-multimodal-reasoning"
    SCHEMA_VERSION = "deep-comprehension-schema-v2"

    # ------------------------------------------------------------------
    # Léxico semántico transversal. No representa un dominio único.
    # ------------------------------------------------------------------
    _LABEL_ALIASES = {
        # Common / English
        "cost": "cost",
        "coste": "cost",
        "price": "price",
        "unit price": "unit_price",
        "amount": "amount",
        "total": "total",
        "subtotal": "subtotal",
        "quantity": "quantity",
        "qty": "quantity",
        "unit": "unit",
        "product": "product",
        "item": "item",
        "material": "material",
        "service": "service",
        "brand": "brand",
        "model": "model",
        "code": "code",
        "sku": "sku",
        "serial": "serial_number",
        "serial number": "serial_number",
        "currency": "currency",
        "payment method": "payment_method",
        "payment terms": "payment_terms",
        "delivery time": "delivery_time",
        "delivery location": "delivery_location",
        "validity": "validity",
        "warranty": "warranty",
        "tax id": "tax_id",
        "legal name": "legal_name",
        "address": "address",
        "phone": "phone",
        "mobile": "phone",
        "email": "email",
        "date": "date",
        "reference": "reference",
        "description": "description",
        "title": "title",
        # Spanish
        "costo": "cost",
        "coste": "cost",
        "precio": "price",
        "precio unitario": "unit_price",
        "importe": "amount",
        "monto": "amount",
        "total": "total",
        "subtotal": "subtotal",
        "cantidad": "quantity",
        "cant": "quantity",
        "unidad": "unit",
        "u medida": "unit",
        "u medida": "unit",
        "producto": "product",
        "item": "item",
        "ítem": "item",
        "material": "material",
        "servicio": "service",
        "marca": "brand",
        "modelo": "model",
        "codigo": "code",
        "código": "code",
        "sku": "sku",
        "serie": "serial_number",
        "nro serie": "serial_number",
        "numero de serie": "serial_number",
        "número de serie": "serial_number",
        "moneda": "currency",
        "forma de pago": "payment_method",
        "medio de pago": "payment_method",
        "condiciones de pago": "payment_terms",
        "tiempo de entrega": "delivery_time",
        "plazo de entrega": "delivery_time",
        "lugar de entrega": "delivery_location",
        "validez": "validity",
        "vigencia": "validity",
        "garantia": "warranty",
        "garantía": "warranty",
        "ruc": "tax_id",
        "razon social": "legal_name",
        "razón social": "legal_name",
        "direccion": "address",
        "dirección": "address",
        "telefono": "phone",
        "teléfono": "phone",
        "móvil": "phone",
        "correo": "email",
        "email": "email",
        "fecha": "date",
        "referencia": "reference",
        "descripcion": "description",
        "descripción": "description",
        "titulo": "title",
        "título": "title",
        # Portuguese
        "preço": "price",
        "preço unitário": "unit_price",
        "quantidade": "quantity",
        "unidade": "unit",
        "produto": "product",
        "serviço": "service",
        "marca": "brand",
        "modelo": "model",
        "código": "code",
        "moeda": "currency",
        "forma de pagamento": "payment_method",
        "prazo de pagamento": "payment_terms",
        "entrega": "delivery_time",
        "validade": "validity",
        "garantia": "warranty",
        "razão social": "legal_name",
        "endereço": "address",
        "telefone": "phone",
        "data": "date",
    }

    _ROLE_LABELS = {
        "provider": {
            "provider", "supplier", "vendor", "seller", "issuer", "emitter",
            "proveedor", "proveedora", "emisor", "emisora", "vendedor", "vendedora",
        },
        "customer": {
            "customer", "buyer", "client", "recipient", "purchaser",
            "cliente", "comprador", "compradora", "destinatario", "destinataria",
        },
        "manufacturer": {
            "manufacturer", "maker", "fabricante", "fabricante del producto",
        },
        "distributor": {
            "distributor", "distribuidor", "distribuidora",
        },
        "carrier": {
            "carrier", "transport company", "transportista", "transportadora",
        },
        "representative": {
            "representative", "sales representative", "representante", "asesor",
        },
        "author": {"author", "autor", "autora"},
        "approver": {"approver", "approved by", "aprobado por", "aprobador"},
        "beneficiary": {"beneficiary", "beneficiario", "beneficiaria"},
        "owner": {"owner", "propietario", "propietaria", "titular"},
        "bank": {"bank", "banco", "entidad bancaria"},
    }

    _SECTION_ROLE_MAP = {
        "provider_identity": "provider",
        "customer_identity": "customer",
        "banking": "bank",
    }

    _DOCUMENT_PATTERNS = {
        "invoice": ("invoice", "factura", "comprobante de pago", "e-factura", "boleta"),
        "quotation": ("quotation", "quote", "cotizacion", "cotización", "oferta comercial", "proposal"),
        "purchase_order": ("purchase order", "orden de compra", "oc ", "o/c"),
        "sales_order": ("sales order", "orden de venta"),
        "receipt": ("receipt", "recibo", "voucher", "ticket"),
        "contract": ("contract", "agreement", "contrato", "convenio"),
        "report": ("report", "informe", "reporte", "analysis", "análisis"),
        "technical_specification": ("technical specification", "specification", "ficha tecnica", "ficha técnica", "especificaciones técnicas", "datasheet"),
        "manual": ("manual", "guide", "guía", "instructivo", "instructions", "instrucciones"),
        "certificate": ("certificate", "certificado", "constancia", "declaración de conformidad"),
        "statement": ("statement", "estado de cuenta", "account statement", "movimientos"),
        "form": ("form", "formulario", "application form", "solicitud"),
        "resume": ("resume", "curriculum vitae", "cv", "currículo"),
        "academic": ("thesis", "tesis", "paper", "articulo científico", "artículo científico", "academic"),
        "legal": ("legal", "notarial", "resolución", "resolution", "demanda", "expediente"),
        "financial": ("balance", "income statement", "estado financiero", "presupuesto", "budget", "cash flow", "flujo de caja"),
        "presentation": ("presentation", "presentación", "slide", "diapositiva"),
    }

    _TEXT_VALUE_PATTERNS = {
        "email": re.compile(r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b", re.I),
        "url": re.compile(r"\b(?:https?://|www\.)[^\s<>]+", re.I),
        "tax_id": re.compile(r"\b(?:RUC|VAT|TIN|TAX\s*ID)\s*[:#\-]?\s*[A-Z0-9\-]{6,20}\b", re.I),
        "phone": re.compile(r"(?<!\d)(?:\+?\d[\d\s().\-]{7,}\d)(?!\d)"),
        "date": re.compile(r"\b(?:\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4}|\d{4}[\-/]\d{1,2}[\-/]\d{1,2})\b"),
        "percentage": re.compile(r"(?<![\w])[-+]?\d+(?:[.,]\d+)?\s*%(?!\w)"),
        "money": re.compile(
            r"(?<!\w)(?:US\$|U\$S|S\/?\.?|PEN|USD|EUR|GBP|COP|MXN|CLP|ARS|BOB|BRL|CAD|AUD|€|£|¥|\$)"
            r"\s*[-+]?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?|"
            r"(?<!\w)[-+]?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?\s*(?:PEN|USD|EUR|GBP|COP|MXN|CLP|ARS|BOB|BRL|CAD|AUD|€|£|¥|\$)(?!\w)",
            re.I,
        ),
        "measurement": re.compile(
            r"(?<!\w)[-+]?\d+(?:[.,]\d+)?\s*(?:mm|cm|m|km|m2|m²|m3|m³|kg|g|mg|t|tn|l|lt|ml|hz|khz|mhz|w|kw|mw|v|kv|a|ma|°c|c|bar|psi|pa|kpa|mpa|hz|s|min|h|hr|hrs|dias|días|meses|years|años|%)(?!\w)",
            re.I,
        ),
        "identifier": re.compile(r"(?<![A-Z0-9])(?:ID|REF|REFERENCE|CODIGO|CÓDIGO|CODE|SKU|SERIE|SERIAL|NRO|NO\.?|NUMERO|NÚMERO)\s*[:#\-]?\s*[A-Z0-9][A-Z0-9_.\-/]{2,30}(?![A-Z0-9])", re.I),
    }

    _LEGAL_SUFFIX = re.compile(
        r"\b(?:S\.?\s*A\.?\.?\s*C?\.?|S\.?\s*R\.?\.?\s*L\.?|S\.?\s*A\.?|LLC|INC\.?|LTD\.?|LIMITED|CORP\.?|CORPORATION|PLC|GMBH|SAS|SA|SRL|EIRL)\b",
        re.I,
    )

    _MONEY_PATTERN = re.compile(
        r"(?P<prefix>US\$|U\$S|S\.?/|S\/?\.?|€|£|¥|\$)?\s*"
        r"(?P<number>\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?)"
        r"\s*(?P<currency>PEN|USD|EUR|GBP|COP|MXN|CLP|ARS|BOB|BRL|CAD|AUD)?",
        re.I,
    )

    _REGION_LINE_TOLERANCE = 3.5
    _REGION_NEAR_DISTANCE = 18.0
    _MAX_SPATIAL_EDGES_PER_REGION = 8

    def comprehend(self, knowledge: DocumentKnowledge) -> DocumentKnowledge:
        if not isinstance(knowledge, DocumentKnowledge):
            raise TypeError("knowledge debe ser una instancia de DocumentKnowledge")

        universal_understanding = UniversalDocumentSemanticReasoner().analyze(knowledge)
        document_understanding = universal_understanding.get("document_understanding", {})
        resolved_roles = universal_understanding.get("resolved_roles", [])
        multimodal_reasoning = universal_understanding.get("multimodal_reasoning", {})
        semantic_dictionary = universal_understanding.get("semantic_dictionary", [])
        entity_profiles = universal_understanding.get("entity_profiles", [])
        semantic_graph = universal_understanding.get("semantic_graph", {})

        concepts = self._build_semantic_concepts(knowledge)
        line_model = self._build_reading_lines(knowledge)
        lexical_observations = self._extract_lexical_observations(knowledge, line_model)
        concepts.extend(lexical_observations)
        concepts = self._dedupe_concepts(concepts)

        typed_values = self._build_typed_values(knowledge, line_model)
        entity_candidates = self._build_entity_candidates(knowledge, line_model)
        spatial_relations = self._build_spatial_relations(knowledge)
        reference_relations = self._build_reference_relations(knowledge, concepts, entity_candidates)
        table_findings = self._evaluate_tables(knowledge)
        consistency = self._evaluate_consistency(knowledge, table_findings, concepts)
        document_profile = self._build_document_profile(knowledge, concepts, line_model, entity_candidates)
        semantic_index = self._build_semantic_index(knowledge, concepts, entity_candidates)
        coverage = self._build_comprehension_coverage(knowledge, concepts, typed_values)

        relationships = list(knowledge.relationships)
        relationships.extend(spatial_relations)
        relationships.extend(reference_relations)
        relationships = self._dedupe_relationships(relationships)

        unresolved = list(knowledge.unresolved)
        unresolved.extend(consistency.get("unresolved", ()))
        unresolved.extend(self._uncertainty_records(entity_candidates, line_model))

        confidence = self._semantic_confidence(
            knowledge=knowledge,
            concepts=concepts,
            consistency=consistency,
            coverage=coverage,
        )

        metadata = dict(knowledge.metadata)
        metadata.update(
            {
                "deep_comprehension_model_version": self.MODEL_VERSION,
                "deep_comprehension_schema_version": self.SCHEMA_VERSION,
                "deep_comprehension_stage": "unified_semantic_reasoning",
                "deep_comprehension_profile": document_profile,
                "deep_universal_understanding": universal_understanding,
                "deep_universal_semantic_model_version": universal_understanding["model_version"],
                "deep_document_understanding": document_understanding,
                "deep_resolved_roles": resolved_roles,
                "deep_semantic_dictionary": semantic_dictionary,
                "deep_entity_profiles": entity_profiles,
                "deep_semantic_graph": semantic_graph,
                "deep_multimodal_reasoning": multimodal_reasoning,
                "deep_semantic_concepts": concepts,
                "deep_semantic_index": semantic_index,
                "deep_typed_values": typed_values,
                "deep_reading_lines": line_model,
                "deep_entity_candidates": entity_candidates,
                "deep_spatial_relations": [item.to_dict() for item in spatial_relations],
                "deep_reference_relations": [item.to_dict() for item in reference_relations],
                "deep_table_findings": table_findings,
                "deep_consistency": consistency.get("summary", {}),
                "deep_consistency_details": {
                    "numeric_checks": consistency.get("numeric_checks", []),
                    "contradictions": consistency.get("contradictions", []),
                },
                "deep_comprehension_coverage": coverage,
                "deep_cross_region_relationship_count": len(spatial_relations) + len(reference_relations),
                "deep_comprehension_confidence": confidence,
                "deep_comprehension_unresolved_count": len(unresolved),
                "deep_reasoning_ready": bool(document_understanding.get("answer_ready")) and not any(
                    str(item.get("decision") or "") == "ambiguous"
                    for item in resolved_roles
                    if str(item.get("role") or "") in {"provider", "customer"}
                ),
                "deep_resolved_provider_count": sum(
                    1 for item in resolved_roles
                    if item.get("role") == "provider" and item.get("decision") == "resolved"
                ),
            }
        )

        return replace(
            knowledge,
            relationships=tuple(relationships),
            unresolved=tuple(unresolved),
            confidence=confidence,
            metadata=metadata,
        )

    # ==================================================================
    # 1. Conceptos semánticos
    # ==================================================================
    def _build_semantic_concepts(self, knowledge: DocumentKnowledge) -> list[dict[str, Any]]:
        concepts: list[dict[str, Any]] = []

        for attribute in knowledge.attributes:
            label = self._canonical_label(attribute.get("name") or attribute.get("raw_label"))
            value = self._clean(attribute.get("value"))
            if not label or not value:
                continue
            concepts.append(self._concept_from_source(
                source=attribute,
                kind="attribute",
                name=label,
                raw_label=self._clean(attribute.get("raw_label")) or label,
                value=value,
                confidence=attribute.get("confidence", 0.0),
            ))

        for fact in knowledge.facts:
            label = self._canonical_label(fact.get("normalized_label") or fact.get("label"))
            value = self._clean(fact.get("raw_value"))
            if not label or not value:
                continue
            concept = self._concept_from_source(
                source=fact,
                kind="fact",
                name=label,
                raw_label=self._clean(fact.get("label")) or label,
                value=value,
                confidence=fact.get("confidence", 0.0),
            )
            concept["fact_type"] = fact.get("fact_type", "")
            concept["source_normalized_value"] = fact.get("normalized_value")
            concepts.append(concept)

        # Semantic tables: cada celda queda disponible como concepto con
        # identidad de tabla/fila. Esta información es crítica para no mezclar
        # valores de filas distintas al razonar después.
        for table in knowledge.tables:
            semantic = table.get("semantic") if isinstance(table, dict) else None
            if not isinstance(semantic, dict):
                continue
            table_id = str(semantic.get("table_id") or table.get("table_id") or "")
            source_page = semantic.get("source_page_number") or table.get("page_number")
            columns = semantic.get("columns") or ()
            rows = semantic.get("rows") or ()
            if not table_id:
                continue
            for row_index, row in enumerate(rows):
                if not isinstance(row, dict):
                    continue
                for key, value in row.items():
                    value_text = self._clean(value)
                    if not value_text:
                        continue
                    canonical = self._canonical_label(key)
                    concepts.append({
                        "concept_id": self._table_concept_id(table_id, row_index, canonical, value_text),
                        "kind": "table_cell",
                        "name": canonical or str(key),
                        "raw_label": str(key),
                        "value": value_text,
                        "normalized_value": self._normalize_typed_value(canonical, value_text),
                        "page_number": source_page,
                        "region_id": "",
                        "evidence_id": "",
                        "confidence": self._table_cell_confidence(columns, str(key), table),
                        "source_table_id": table_id,
                        "row_index": row_index,
                        "source_kind": "semantic_table",
                    })

        # Las tablas semánticas también pueden existir únicamente como
        # regiones (``DocumentKnowledge.tables`` conserva las tablas físicas).
        # Se leen desde su representación ya construida y se normalizan de
        # nuevo para mantener una fuente única de verdad en la comprensión.
        for region in knowledge.regions:
            if region.region_type != "semantic_table":
                continue
            table_id = str(region.metadata.get("table_id") or region.region_id)
            role = str(region.metadata.get("table_role") or "unknown")
            source_page = region.metadata.get("source_page_number") or region.page_number
            for row_index, raw_row in enumerate(str(region.content or "").splitlines()):
                row = raw_row.strip()
                if not row:
                    continue
                fields: dict[str, str] = {}
                for cell in row.split("|"):
                    if "=" not in cell:
                        continue
                    key, value = cell.split("=", 1)
                    key, value = self._clean(key), self._clean(value)
                    if key and value:
                        fields[key] = value
                for key, value in fields.items():
                    canonical = self._canonical_label(key) or self._normalize(key).replace(" ", "_")
                    concepts.append({
                        "concept_id": self._table_concept_id(table_id, row_index, canonical, value),
                        "kind": "table_cell",
                        "name": canonical,
                        "raw_label": key,
                        "value": value,
                        "normalized_value": self._normalize_typed_value(canonical, value),
                        "page_number": source_page,
                        "region_id": region.region_id,
                        "evidence_id": self._region_evidence_id(knowledge, region.region_id),
                        "confidence": round(max(0.0, min(1.0, region.confidence)), 4),
                        "source_table_id": table_id,
                        "row_index": row_index,
                        "table_role": role,
                        "source_kind": "semantic_table_region",
                    })

        # Observaciones visuales: nunca se convierten en un objeto concreto
        # que no haya sido realmente detectado. Se conserva el tipo observado,
        # texto visible y señales visuales como evidencia.
        for image in knowledge.images:
            visual = image.get("visual_understanding") or {}
            if not visual:
                continue
            image_id = str(image.get("image_id") or "")
            concepts.append({
                "concept_id": f"visual:{image_id}",
                "kind": "visual",
                "name": self._clean(visual.get("object_type")) or "visual_content",
                "value": self._clean(visual.get("description")),
                "normalized_value": self._normalize(visual.get("description")),
                "description": self._clean(visual.get("description")),
                "detected_text": self._clean(visual.get("detected_text")),
                "semantic_hints": list(visual.get("semantic_hints") or ()),
                "detected_features": list(visual.get("detected_features") or ()),
                "qr_codes": list(visual.get("qr_codes") or ()),
                "page_number": image.get("page_number"),
                "region_id": "",
                "evidence_id": "",
                "confidence": float(visual.get("visual_confidence", 0.0) or 0.0),
                "source_image_id": image_id,
                "source_kind": "visual_understanding",
            })

        # Page-level visual reasoning is another observation layer.
        for region in knowledge.regions:
            if region.region_type != "page_visual":
                continue
            metadata = region.metadata or {}
            concepts.append({
                "concept_id": f"page-visual:{region.region_id}",
                "kind": "page_visual",
                "name": self._clean(metadata.get("object_type")) or "page_visual",
                "value": self._clean(metadata.get("description") or region.content),
                "normalized_value": self._normalize(metadata.get("description") or region.content),
                "description": self._clean(metadata.get("description") or region.content),
                "detected_text": self._clean(metadata.get("detected_text")),
                "semantic_hints": list(metadata.get("semantic_hints") or ()),
                "detected_features": list(metadata.get("detected_features") or ()),
                "qr_codes": list(metadata.get("qr_codes") or ()),
                "page_number": region.page_number,
                "region_id": region.region_id,
                "evidence_id": self._region_evidence_id(knowledge, region.region_id),
                "confidence": float(region.confidence),
                "source_kind": "page_visual",
            })

        # Objetos estructurales: no son "ruido"; algunas veces contienen la
        # semántica decisiva de un formulario, enlace, adjunto o marcador.
        for item in knowledge.structural_objects:
            if not isinstance(item, dict):
                continue
            item_id = str(item.get("object_id") or "")
            item_type = self._clean(item.get("object_type")) or "structural_object"
            text = self._clean(item.get("text") or item.get("name"))
            metadata = item.get("metadata") or {}
            if not item_id or not (text or metadata):
                continue
            concepts.append({
                "concept_id": f"structural:{item_id}",
                "kind": "structural",
                "name": item_type,
                "value": text,
                "normalized_value": self._normalize(text),
                "page_number": item.get("page_number"),
                "region_id": "",
                "evidence_id": "",
                "confidence": 1.0,
                "source_structural_object_id": item_id,
                "metadata": self._json_safe(metadata),
            })

        return concepts

    def _extract_lexical_observations(
        self,
        knowledge: DocumentKnowledge,
        lines: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Extrae hechos observables aun cuando el extractor previo no creó un fact.

        Esta etapa no reemplaza ``DocumentFactExtractor``; cubre información
        que suele perderse al estar distribuida en múltiples bloques PDF.
        """
        concepts: list[dict[str, Any]] = []
        for line in lines:
            text = self._clean(line.get("text"))
            if not text:
                continue
            page = line.get("page_number")
            region_ids = tuple(line.get("region_ids") or ())
            evidence_id = self._first_region_evidence(knowledge, region_ids)

            labeled = self._parse_labeled_line(text)
            if labeled:
                label, value = labeled
                canonical = self._canonical_label(label)
                concepts.append({
                    "concept_id": f"line-field:{page}:{line.get('line_id')}:{self._normalize(label)}",
                    "kind": "derived_field",
                    "name": canonical or self._normalize(label),
                    "raw_label": label,
                    "value": value,
                    "normalized_value": self._normalize_typed_value(canonical, value),
                    "page_number": page,
                    "region_id": region_ids[0] if region_ids else "",
                    "evidence_id": evidence_id,
                    "confidence": self._line_confidence(line, label, value),
                    "source_kind": "reading_line",
                    "line_id": line.get("line_id"),
                })

            # Valores explícitos embebidos en prose / cells.
            for value_type, pattern in self._TEXT_VALUE_PATTERNS.items():
                for match in pattern.finditer(text):
                    raw = match.group(0).strip()
                    concepts.append({
                        "concept_id": f"lexical:{page}:{line.get('line_id')}:{value_type}:{self._digest(raw)}",
                        "kind": "lexical_value",
                        "name": value_type,
                        "raw_label": value_type,
                        "value": raw,
                        "normalized_value": self._normalize_typed_value(value_type, raw),
                        "page_number": page,
                        "region_id": region_ids[0] if region_ids else "",
                        "evidence_id": evidence_id,
                        "confidence": self._lexical_confidence(value_type, raw),
                        "source_kind": "reading_line",
                        "line_id": line.get("line_id"),
                    })

            legal_entities = self._extract_legal_entity_mentions(text)
            for name in legal_entities:
                concepts.append({
                    "concept_id": f"mention:{page}:{line.get('line_id')}:legal_entity:{self._digest(name)}",
                    "kind": "entity_mention",
                    "name": "legal_entity",
                    "raw_label": "entity_mention",
                    "value": name,
                    "normalized_value": self._normalize(name),
                    "page_number": page,
                    "region_id": region_ids[0] if region_ids else "",
                    "evidence_id": evidence_id,
                    "confidence": 0.86,
                    "source_kind": "reading_line",
                    "line_id": line.get("line_id"),
                })

        return concepts

    # ==================================================================
    # 2. Lectura espacial / layout documental
    # ==================================================================
    def _build_reading_lines(self, knowledge: DocumentKnowledge) -> list[dict[str, Any]]:
        grouped: list[dict[str, Any]] = []
        native_blocks = [
            region for region in knowledge.regions
            if region.region_type == "text_block"
            and self._clean(region.content)
            and region.bbox is not None
        ]
        native_pages = {region.page_number for region in native_blocks}
        blocks = [*native_blocks]
        # Full-page OCR se usa como fallback únicamente en páginas donde no
        # existe texto nativo. El OCR específico de imágenes queda representado
        # por ``image_ocr`` y no se mezcla con cada palabra nativa.
        blocks.extend(
            region for region in knowledge.regions
            if region.region_type in {"ocr_block", "image_ocr"}
            and self._clean(region.content)
            and region.bbox is not None
            and (region.region_type == "image_ocr" or region.page_number not in native_pages)
        )
        blocks.sort(key=lambda region: (
            region.page_number,
            float(region.bbox[1]),
            float(region.bbox[0]),
        ))

        page_lines: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for region in blocks:
            x0, y0, x1, y1 = region.bbox or (0.0, 0.0, 0.0, 0.0)
            center_y = (y0 + y1) / 2.0
            target = None
            for candidate in reversed(page_lines[region.page_number][-8:]):
                cy = candidate["center_y"]
                if abs(center_y - cy) <= self._REGION_LINE_TOLERANCE and self._horizontal_line_compatible(candidate, region):
                    target = candidate
                    break
            if target is None:
                target = {
                    "page_number": region.page_number,
                    "center_y": center_y,
                    "regions": [],
                    "region_ids": [],
                    "source_kinds": [],
                }
                page_lines[region.page_number].append(target)
            target["regions"].append(region)
            target["region_ids"].append(region.region_id)
            target["source_kinds"].append(region.source_kind)
            # Weighted running center; native text dominates OCR when both
            # are present on the same line.
            target["center_y"] = sum(
                (r.bbox[1] + r.bbox[3]) / 2.0
                for r in target["regions"]
                if r.bbox is not None
            ) / max(len(target["regions"]), 1)

        line_counter = 0
        for page_number in sorted(page_lines):
            for candidate in sorted(page_lines[page_number], key=lambda item: item["center_y"]):
                regions = sorted(candidate["regions"], key=lambda r: float(r.bbox[0]) if r.bbox else 0.0)
                # Drop OCR duplicate blocks if identical native content is on
                # the same line; keep OCR only when it adds text.
                text_parts: list[str] = []
                kept_ids: list[str] = []
                seen_text: set[str] = set()
                for region in regions:
                    normalized = self._normalize(region.content)
                    if normalized and normalized in seen_text and region.source_kind.startswith("ocr"):
                        continue
                    seen_text.add(normalized)
                    text_parts.append(region.content.strip())
                    kept_ids.append(region.region_id)
                line_counter += 1
                bbox = self._union_bbox(tuple(r.bbox for r in regions if r.bbox is not None))
                grouped.append({
                    "line_id": f"line:{page_number}:{line_counter}",
                    "page_number": page_number,
                    "text": " ".join(text_parts).strip(),
                    "region_ids": kept_ids,
                    "bbox": list(bbox) if bbox else None,
                })

        return grouped

    def _build_spatial_relations(self, knowledge: DocumentKnowledge) -> list[dict[str, Any]]:
        """Construye un grafo ligero de relaciones espaciales entre regiones."""
        region_list = [
            r for r in knowledge.regions
            if r.bbox is not None
            and r.region_type in {"text_block", "semantic_table", "image", "page_visual", "image_ocr"}
            and (r.region_type != "text_block" or len(self._clean(r.content)) >= 8)
        ]
        by_page: dict[int, list[Any]] = defaultdict(list)
        for region in region_list:
            by_page[region.page_number].append(region)

        relations: list[dict[str, Any]] = []
        for page, regions in by_page.items():
            regions.sort(key=lambda r: (float(r.bbox[1]), float(r.bbox[0])))
            for region in regions:
                candidates: list[tuple[float, Any, str]] = []
                for other in regions:
                    if other.region_id == region.region_id:
                        continue
                    relation, distance = self._spatial_relation(region, other)
                    if relation is None:
                        continue
                    candidates.append((distance, other, relation))
                candidates.sort(key=lambda x: x[0])
                for distance, other, relation in candidates[: min(4, self._MAX_SPATIAL_EDGES_PER_REGION)]:
                    relations.append(
                        DocumentRelationship(
                            relationship_id=(
                                f"deep:spatial:{region.region_id}:{relation}:{other.region_id}"
                            ),
                            source_id=region.region_id,
                            relationship_type=f"spatial:{relation}",
                            target_id=other.region_id,
                            confidence=round(self._spatial_confidence(distance, relation), 4),
                            metadata={
                                "distance": round(distance, 3),
                                "page_number": page,
                                "relation": relation,
                            },
                        )
                    )
        return self._dedupe_relationships(relations)

    # ==================================================================
    # 3. Entidades / referencias
    # ==================================================================
    def _build_entity_candidates(
        self,
        knowledge: DocumentKnowledge,
        lines: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        candidates: dict[tuple[str, str], dict[str, Any]] = {}
        evidence_by_region = {
            str(evidence.metadata.get("region_id")): evidence.evidence_id
            for evidence in knowledge.evidence
            if evidence.metadata.get("region_id")
        }

        # Entidades ya resueltas: máxima evidencia disponible.
        for entity in knowledge.entities:
            key = (entity.role or "unknown", self._normalize(entity.name or entity.identifier))
            state = candidates.setdefault(key, {
                "candidate_id": f"entity-candidate:{entity.entity_id}",
                "role": entity.role or "unknown",
                "name": entity.name,
                "identifier": entity.identifier,
                "confidence": float(entity.confidence),
                "evidence_ids": list(entity.evidence_ids),
                "source": "resolved_entity",
                "evidence": [],
            })
            state["confidence"] = max(state["confidence"], float(entity.confidence))
            state["evidence"].append("resolved_entity")

        # Candidatos derivados de líneas legibles.
        for line in lines:
            text = self._clean(line.get("text"))
            if not text:
                continue
            role_context = self._role_context_from_line(text)
            labeled = self._parse_labeled_line(text)
            if labeled:
                label, value = labeled
                label_norm = self._normalize(label)
                for role, labels in self._ROLE_LABELS.items():
                    if label_norm in labels or label_norm in {self._normalize(v) for v in labels}:
                        self._add_entity_candidate(
                            candidates,
                            role=role,
                            name=value,
                            line=line,
                            confidence=0.93,
                            source="explicit_role_label",
                        )
                        break

            for entity_name in self._extract_legal_entity_mentions(text):
                role = role_context or self._section_role_for_line(knowledge, line)
                if not role:
                    role = "unknown"
                self._add_entity_candidate(
                    candidates,
                    role=role,
                    name=entity_name,
                    line=line,
                    confidence=0.72 if role != "unknown" else 0.60,
                    source="legal_entity_mention",
                )

            ruc = self._extract_identifier_value(text, "tax_id")
            if ruc:
                self._attach_identifier_to_candidate(candidates, ruc, line)

        # Conecta identificadores encontrados en conceptos previos.
        for concept in self._iter_concepts_for_identifier_search(knowledge):
            if concept.get("name") != "tax_id":
                continue
            value = str(concept.get("value") or "").strip()
            if value:
                self._attach_identifier_to_candidate(candidates, value, None)

        self._infer_contextual_roles(candidates, lines)
        for candidate in candidates.values():
            candidate["evidence_ids"] = list(dict.fromkeys(
                evidence_by_region.get(rid)
                for rid in candidate.get("source_region_ids", [])
                if evidence_by_region.get(rid)
            ))

        result = []
        for candidate in candidates.values():
            candidate["confidence"] = round(max(0.0, min(1.0, float(candidate.get("confidence", 0.0)))), 4)
            candidate["evidence_ids"] = list(dict.fromkeys(candidate.get("evidence_ids", [])))
            candidate["evidence"] = list(dict.fromkeys(candidate.get("evidence", [])))
            result.append(candidate)
        return sorted(result, key=lambda item: (-float(item.get("confidence", 0.0)), str(item.get("role", "")), str(item.get("name", ""))))

    def _build_reference_relations(
        self,
        knowledge: DocumentKnowledge,
        concepts: list[dict[str, Any]],
        entity_candidates: list[dict[str, Any]],
    ) -> list[DocumentRelationship]:
        relations: list[DocumentRelationship] = []
        normalized_entity_names = {
            self._normalize(item.get("name")): item
            for item in entity_candidates
            if self._normalize(item.get("name"))
        }
        for concept in concepts:
            value_norm = self._normalize(concept.get("value"))
            if not value_norm:
                continue
            candidate = normalized_entity_names.get(value_norm)
            if candidate:
                relations.append(
                    DocumentRelationship(
                        relationship_id=(
                            f"deep:reference:{concept.get('concept_id','')}:{candidate.get('candidate_id','')}"
                        ),
                        source_id=str(concept.get("concept_id", "")),
                        relationship_type="mentions_entity_candidate",
                        target_id=str(candidate.get("candidate_id", "")),
                        confidence=0.90,
                        evidence_ids=((str(concept.get("evidence_id")),)
                                      if concept.get("evidence_id") else ()),
                    )
                )

        by_identifier: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for candidate in entity_candidates:
            identifier = self._normalize(candidate.get("identifier"))
            if identifier:
                by_identifier[identifier].append(candidate)
        for identifier, items in by_identifier.items():
            if len(items) < 2:
                continue
            for left in items:
                for right in items:
                    if left is right:
                        continue
                    relations.append(
                        DocumentRelationship(
                            relationship_id=(
                                f"deep:identifier:{left.get('candidate_id','')}:{right.get('candidate_id','')}"
                            ),
                            source_id=str(left.get("candidate_id", "")),
                            relationship_type="shared_identifier",
                            target_id=str(right.get("candidate_id", "")),
                            confidence=0.98,
                            metadata={"identifier": identifier},
                        )
                    )
        return self._dedupe_relationships(relations)

    # ==================================================================
    # 4. Valores tipados
    # ==================================================================
    def _build_typed_values(self, knowledge: DocumentKnowledge, lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
        values: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()
        for line in lines:
            text = self._clean(line.get("text"))
            if not text:
                continue
            for value_type, pattern in self._TEXT_VALUE_PATTERNS.items():
                for match in pattern.finditer(text):
                    raw = match.group(0).strip()
                    normalized = self._normalize_typed_value(value_type, raw)
                    key = (value_type, self._normalize(raw), str(line.get("page_number")))
                    if key in seen:
                        continue
                    seen.add(key)
                    values.append({
                        "value_type": value_type,
                        "raw_value": raw,
                        "normalized_value": normalized,
                        "page_number": line.get("page_number"),
                        "line_id": line.get("line_id"),
                        "region_ids": list(line.get("region_ids") or ()),
                        "confidence": self._lexical_confidence(value_type, raw),
                    })

        # Añade valores tipados ya disponibles en facts/attributes.
        for source in (*knowledge.facts, *knowledge.attributes):
            raw = self._clean(source.get("raw_value") or source.get("value"))
            if not raw:
                continue
            label = self._canonical_label(source.get("normalized_label") or source.get("name") or source.get("label"))
            detected_type = self._infer_value_type(label, raw)
            if detected_type is None:
                continue
            key = (detected_type, self._normalize(raw), str(source.get("page_number")))
            if key in seen:
                continue
            seen.add(key)
            values.append({
                "value_type": detected_type,
                "raw_value": raw,
                "normalized_value": self._normalize_typed_value(detected_type, raw),
                "page_number": source.get("page_number"),
                "region_id": source.get("region_id", ""),
                "evidence_id": source.get("evidence_id", ""),
                "confidence": float(source.get("confidence", 0.0) or 0.0),
            })
        return values

    # ==================================================================
    # 5. Tablas y consistencia matemática
    # ==================================================================
    def _evaluate_tables(self, knowledge: DocumentKnowledge) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        seen_tables: set[str] = set()

        sources: list[tuple[str, Any, Any, Any, Any]] = []
        for table in knowledge.tables:
            if not isinstance(table, dict):
                continue
            semantic = table.get("semantic") if isinstance(table.get("semantic"), dict) else None
            if semantic is None:
                continue
            table_id = str(semantic.get("table_id") or table.get("table_id") or "")
            if table_id:
                sources.append((table_id, semantic.get("rows") or [], semantic.get("columns") or [], semantic.get("source_page_number") or table.get("page_number"), semantic.get("table_role", "unknown")))

        # La semántica de layout se conserva en regiones porque puede no tener
        # una correspondencia 1:1 con la tabla física. Esa ruta es válida y
        # necesaria para PDFs visuales donde la tabla física no fue reconocida.
        for region in knowledge.regions:
            if region.region_type != "semantic_table":
                continue
            table_id = str(region.metadata.get("table_id") or region.region_id)
            if table_id in seen_tables:
                continue
            rows: list[dict[str, Any]] = []
            for raw_row in str(region.content or "").splitlines():
                row: dict[str, Any] = {}
                for cell in raw_row.split("|"):
                    if "=" not in cell:
                        continue
                    key, value = cell.split("=", 1)
                    key, value = self._clean(key), self._clean(value)
                    if key and value:
                        row[self._canonical_label(key) or self._normalize(key).replace(" ", "_")] = value
                if row:
                    rows.append(row)
            if rows:
                columns = [{"key": key} for key in sorted({k for row in rows for k in row})]
                sources.append((table_id, rows, columns, region.metadata.get("source_page_number") or region.page_number, region.metadata.get("table_role", "unknown")))

        for table_id, rows, columns, page_number, role in sources:
            if table_id in seen_tables:
                continue
            seen_tables.add(table_id)
            row_findings: list[dict[str, Any]] = []
            for index, row in enumerate(rows):
                if not isinstance(row, dict):
                    continue
                normalized = {self._canonical_label(k) or self._normalize(k).replace(" ", "_"): v for k, v in row.items()}
                quantity = self._to_decimal(normalized.get("quantity"))
                unit_price = self._to_decimal(normalized.get("unit_price") or normalized.get("price"))
                total = self._to_decimal(normalized.get("total") or normalized.get("amount"))
                status = "not_checkable"
                delta = None
                expected = None
                if quantity is not None and unit_price is not None and total is not None:
                    expected = quantity * unit_price
                    delta = abs(expected - total)
                    tolerance = max(Decimal("0.01"), abs(total) * Decimal("0.005"))
                    status = "consistent" if delta <= tolerance else "inconsistent"
                row_findings.append({
                    "row_index": index,
                    "status": status,
                    "quantity": self._decimal_string(quantity),
                    "unit_price": self._decimal_string(unit_price),
                    "reported_total": self._decimal_string(total),
                    "expected_total": self._decimal_string(expected),
                    "delta": self._decimal_string(delta),
                    "source_table_id": table_id,
                })
            findings.append({
                "table_id": table_id,
                "page_number": page_number,
                "column_count": len(columns),
                "row_count": len(rows),
                "rows": row_findings,
                "role": role,
            })
        return findings

    def _evaluate_consistency(
        self,
        knowledge: DocumentKnowledge,
        table_findings: list[dict[str, Any]],
        concepts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        contradictions: list[dict[str, Any]] = []
        numeric_checks: list[dict[str, Any]] = []
        unresolved: list[dict[str, Any]] = []

        for table in table_findings:
            for row in table.get("rows", []):
                if row.get("status") == "not_checkable":
                    continue
                record = dict(row)
                record["page_number"] = table.get("page_number")
                numeric_checks.append(record)
                if row.get("status") == "inconsistent":
                    contradictions.append(record)

        # Contradicciones de valores etiquetados: se comparan solo cuando
        # comparten etiqueta y contexto espacial razonablemente cercano.
        groups: dict[tuple[str, int | None, str], list[dict[str, Any]]] = defaultdict(list)
        for concept in concepts:
            name = str(concept.get("name") or "")
            value = str(concept.get("normalized_value") or "")
            if not name or not value:
                continue
            region = str(concept.get("region_id") or "")
            page = concept.get("page_number")
            groups[(name, page, region)].append(concept)

        for (name, page, region), items in groups.items():
            unique = {str(item.get("normalized_value")) for item in items}
            if len(unique) <= 1:
                continue
            if name in {"currency", "payment_method", "payment_terms", "validity", "warranty", "legal_name", "tax_id"}:
                unresolved.append({
                    "type": "contextual_variation",
                    "semantic_name": name,
                    "page_number": page,
                    "region_id": region,
                    "values": sorted(unique),
                    "message": "Se detectaron valores distintos; se conservan como contextos separados.",
                })

        return {
            "summary": {
                "contradiction_count": len(contradictions),
                "numeric_check_count": len(numeric_checks),
                "numeric_inconsistency_count": len([
                    item for item in contradictions if item.get("row_index") is not None
                ]),
                "contextual_variation_count": len(unresolved),
            },
            "numeric_checks": numeric_checks,
            "contradictions": contradictions,
            "unresolved": unresolved,
        }

    # ==================================================================
    # 6. Perfil documental universal
    # ==================================================================
    def _build_document_profile(
        self,
        knowledge: DocumentKnowledge,
        concepts: list[dict[str, Any]],
        lines: list[dict[str, Any]],
        entity_candidates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        text = self._normalize("\n".join([
            knowledge.text,
            knowledge.visual_text,
            *[str(line.get("text") or "") for line in lines],
        ]))

        scores: dict[str, float] = defaultdict(float)
        evidence: dict[str, list[str]] = defaultdict(list)
        for kind, patterns in self._DOCUMENT_PATTERNS.items():
            for pattern in patterns:
                normalized_pattern = self._normalize(pattern)
                if normalized_pattern and normalized_pattern in text:
                    scores[kind] += 1.0
                    evidence[kind].append(f"text:{pattern}")

        concept_names = {str(c.get("name") or "") for c in concepts}
        if {"price", "unit_price", "total", "quantity"} & concept_names:
            scores["commercial"] += 1.5
            evidence["commercial"].append("typed_or_labeled_commercial_values")
        if {"description", "specification", "model", "brand", "material"} & concept_names:
            scores["technical_specification"] += 0.75
        if knowledge.structural_objects:
            scores["structured"] += 0.5
        if knowledge.images:
            scores["multimodal"] += 0.5
        if knowledge.tables:
            scores["tabular"] += 0.5

        # "structured" y "multimodal" no son mutuamente excluyentes; se
        # conservan como propiedades además del tipo principal.
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        primary = "general"
        primary_score = 0.0
        if ranked and ranked[0][1] > 0:
            primary, primary_score = ranked[0]

        if primary == "commercial":
            primary = "commercial_document"
        elif primary in self._DOCUMENT_PATTERNS:
            primary = primary
        elif primary in {"structured", "tabular", "multimodal"}:
            primary = "structured_document"

        return {
            "document_kind": primary,
            "document_kind_confidence": round(self._profile_confidence(primary_score, scores), 4),
            "document_kind_candidates": [
                {"kind": key, "score": round(value, 4), "evidence": evidence.get(key, [])}
                for key, value in ranked[:8]
            ],
            "page_count": knowledge.page_count,
            "properties": {
                "has_text": bool(knowledge.text.strip()),
                "has_visual_text": bool(knowledge.visual_text.strip()),
                "has_tables": bool(knowledge.tables),
                "has_images": bool(knowledge.images),
                "has_structural_objects": bool(knowledge.structural_objects),
                "has_ocr": bool(knowledge.ocr_blocks),
                "page_count": knowledge.page_count,
            },
            "entity_roles": self._count_entity_roles(entity_candidates, knowledge.entities),
            "concept_count": len(concepts),
            "fact_count": len(knowledge.facts),
            "attribute_count": len(knowledge.attributes),
            "entity_count": len(knowledge.entities),
            "entity_candidate_count": len(entity_candidates),
            "table_count": len(knowledge.tables),
            "image_count": len(knowledge.images),
            "structural_object_count": len(knowledge.structural_objects),
        }

    # ==================================================================
    # 7. Índice semántico
    # ==================================================================
    def _build_semantic_index(
        self,
        knowledge: DocumentKnowledge,
        concepts: list[dict[str, Any]],
        entity_candidates: list[dict[str, Any]],
    ) -> dict[str, list[str]]:
        index: dict[str, list[str]] = defaultdict(list)
        for concept in concepts:
            cid = str(concept.get("concept_id") or "")
            name = self._normalize(concept.get("name"))
            value = self._normalize(concept.get("normalized_value") or concept.get("value"))
            page = concept.get("page_number")
            region = self._normalize(concept.get("region_id"))
            if not cid:
                continue
            if name:
                index[f"concept:{name}"].append(cid)
            if value:
                index[f"value:{value}"] .append(cid)
            if page is not None:
                index[f"page:{page}"] .append(cid)
            if region:
                index[f"region:{region}"] .append(cid)

        for entity in knowledge.entities:
            if entity.name:
                index[f"entity:{self._normalize(entity.name)}"].append(entity.entity_id)
            if entity.identifier:
                index[f"identifier:{self._normalize(entity.identifier)}"].append(entity.entity_id)

        for candidate in entity_candidates:
            cid = str(candidate.get("candidate_id") or "")
            if candidate.get("name"):
                index[f"entity_candidate:{self._normalize(candidate.get('name'))}"].append(cid)
            if candidate.get("identifier"):
                index[f"identifier_candidate:{self._normalize(candidate.get('identifier'))}"].append(cid)

        return {key: list(dict.fromkeys(values)) for key, values in index.items()}

    # ==================================================================
    # 8. Cobertura / confianza
    # ==================================================================
    def _build_comprehension_coverage(
        self,
        knowledge: DocumentKnowledge,
        concepts: list[dict[str, Any]],
        typed_values: list[dict[str, Any]],
    ) -> dict[str, Any]:
        pages = list(range(1, knowledge.page_count + 1))
        page_presence = {page: 0 for page in pages}
        for region in knowledge.regions:
            if region.content.strip() or region.metadata:
                page_presence[region.page_number] = page_presence.get(region.page_number, 0) + 1

        pages_with_evidence = sum(1 for count in page_presence.values() if count > 0)
        page_coverage = pages_with_evidence / len(pages) if pages else 0.0
        concept_pages = {c.get("page_number") for c in concepts if c.get("page_number") is not None}
        semantic_page_coverage = len(concept_pages & set(pages)) / len(pages) if pages else 0.0

        source_layers = {
            "native_text": bool(knowledge.text.strip()),
            "visual_text": bool(knowledge.visual_text.strip()),
            "ocr": bool(knowledge.ocr_blocks),
            "tables": bool(knowledge.tables),
            "images": bool(knowledge.images),
            "structure": bool(knowledge.structural_objects),
            "entities": bool(knowledge.entities),
            "facts": bool(knowledge.facts),
            "attributes": bool(knowledge.attributes),
        }
        active_layers = sum(source_layers.values())
        layer_coverage = active_layers / len(source_layers) if source_layers else 0.0

        return {
            "page_coverage": round(page_coverage, 4),
            "semantic_page_coverage": round(semantic_page_coverage, 4),
            "evidence_region_count": len(knowledge.regions),
            "concept_count": len(concepts),
            "typed_value_count": len(typed_values),
            "active_source_layer_count": active_layers,
            "source_layer_coverage": round(layer_coverage, 4),
            "source_layers": source_layers,
        }

    @staticmethod
    def _semantic_confidence(
        *,
        knowledge: DocumentKnowledge,
        concepts: list[dict[str, Any]],
        consistency: dict[str, Any],
        coverage: dict[str, Any],
    ) -> float:
        confidence_values = [
            float(entity.confidence)
            for entity in knowledge.entities
            if float(entity.confidence) > 0
        ]
        confidence_values.extend(
            float(concept.get("confidence", 0.0) or 0.0)
            for concept in concepts
            if float(concept.get("confidence", 0.0) or 0.0) > 0
        )
        evidence_confidence = (
            sum(confidence_values) / len(confidence_values)
            if confidence_values
            else float(knowledge.confidence or 0.0)
        )
        coverage_score = (
            float(coverage.get("page_coverage", 0.0)) * 0.35
            + float(coverage.get("semantic_page_coverage", 0.0)) * 0.20
            + float(coverage.get("source_layer_coverage", 0.0)) * 0.10
        )
        base = evidence_confidence * 0.75 + coverage_score * 0.25
        contradiction_penalty = min(
            0.30,
            0.08 * float(consistency.get("summary", {}).get("contradiction_count", 0)),
        )
        return round(max(0.0, min(0.98, base - contradiction_penalty)), 4)

    # ==================================================================
    # Helpers: parsing, normalización y geometría
    # ==================================================================
    def _canonical_label(self, value: Any) -> str:
        normalized = self._normalize(value)
        if not normalized:
            return ""
        return self._LABEL_ALIASES.get(normalized, normalized.replace(" ", "_"))

    @classmethod
    def _parse_labeled_line(cls, text: str) -> tuple[str, str] | None:
        clean = cls._clean(text)
        match = re.match(r"^\s*([^:=]{2,80})\s*[:=\-]\s*(.+?)\s*$", clean)
        if not match:
            return None
        label = cls._clean(match.group(1)).strip(" -")
        value = cls._clean(match.group(2))
        if not label or not value:
            return None
        # Evita tratar frases largas de prosa como "campos".
        if len(label.split()) > 8:
            return None
        return label, value

    @classmethod
    def _normalize_typed_value(cls, label: str, value: Any) -> str:
        text = cls._clean(value)
        if not text:
            return ""
        label = cls._canonical_static(label)
        if label in {"price", "unit_price", "amount", "total", "subtotal", "cost"}:
            decimal = cls._to_decimal(text)
            return cls._decimal_string(decimal) if decimal is not None else cls._normalize(text)
        if label == "percentage":
            number = cls._to_decimal(text.replace("%", ""))
            return cls._decimal_string(number) if number is not None else cls._normalize(text)
        if label == "email":
            return text.casefold()
        if label in {"url", "tax_id", "code", "sku", "serial_number", "reference"}:
            return re.sub(r"\s+", "", text.casefold())
        if label == "date":
            return cls._normalize_date(text)
        if label in {"phone", "measurement", "money"}:
            return cls._normalize(text)
        return cls._normalize(text)

    @staticmethod
    def _canonical_static(value: Any) -> str:
        normalized = " ".join(str(value or "").strip().casefold().split())
        return DeepDocumentComprehensionEngine._LABEL_ALIASES.get(normalized, normalized.replace(" ", "_"))

    def _concept_from_source(
        self,
        *,
        source: dict[str, Any],
        kind: str,
        name: str,
        raw_label: str,
        value: str,
        confidence: Any,
    ) -> dict[str, Any]:
        return {
            "concept_id": self._concept_id(source, name, value),
            "kind": kind,
            "name": name,
            "raw_label": raw_label,
            "value": value,
            "normalized_value": self._normalize_typed_value(name, value),
            "page_number": source.get("page_number"),
            "region_id": source.get("region_id", ""),
            "evidence_id": source.get("evidence_id", ""),
            "confidence": float(confidence or 0.0),
            "source_kind": kind,
        }

    @staticmethod
    def _concept_id(source: dict[str, Any], name: str, value: str) -> str:
        source_id = str(
            source.get("attribute_id")
            or source.get("fact_id")
            or source.get("evidence_id")
            or "source"
        )
        return f"concept:{source_id}:{name}:{DeepDocumentComprehensionEngine._digest(value)}"

    @staticmethod
    def _table_concept_id(table_id: str, row_index: int, name: str, value: str) -> str:
        return f"table-concept:{table_id}:row:{row_index}:{name}:{DeepDocumentComprehensionEngine._digest(value)}"

    @staticmethod
    def _digest(value: Any) -> str:
        return sha256(str(value or "").encode("utf-8", errors="ignore")).hexdigest()[:16]

    @classmethod
    def _extract_legal_entity_mentions(cls, text: str) -> list[str]:
        mentions: list[str] = []
        for match in cls._LEGAL_SUFFIX.finditer(text):
            start = max(0, match.start() - 120)
            prefix = text[start:match.end()]
            # Captura la secuencia final de palabras/código antes del sufijo.
            candidate_match = re.search(
                r"([A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9&.\-]+(?:\s+[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9&.\-]+){0,8}\s+"
                r"(?:S\.?\s*A\.?\.?\s*C?\.?|S\.?\s*R\.?\.?\s*L\.?|S\.?\s*A\.?|LLC|INC\.?|LTD\.?|LIMITED|CORP\.?|CORPORATION|PLC|GMBH|SAS|SA|SRL|EIRL)\b)",
                prefix,
                re.I,
            )
            if candidate_match:
                candidate = cls._collapse_repeated_tokens(
                    cls._clean(candidate_match.group(1)).strip(" :,-")
                )
                if (
                    len(candidate) >= 5
                    and len(candidate.split()) >= 2
                    and len(re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", candidate)) >= 4
                    and candidate not in mentions
                ):
                    mentions.append(candidate)
        return mentions

    def _role_context_from_line(self, text: str) -> str:
        normalized = self._normalize(text)
        hits: list[str] = []
        for role, labels in self._ROLE_LABELS.items():
            if any(self._normalize(label) in normalized for label in labels):
                hits.append(role)
        if len(hits) == 1:
            return hits[0]
        return ""

    def _section_role_for_line(self, knowledge: DocumentKnowledge, line: dict[str, Any]) -> str:
        region_ids = set(line.get("region_ids") or ())
        matches = []
        for region in knowledge.regions:
            if region.region_id not in region_ids:
                continue
            section = str(region.metadata.get("section") or region.metadata.get("semantic_section") or "")
            role = self._SECTION_ROLE_MAP.get(section, "")
            if role:
                matches.append(role)
        return matches[0] if len(set(matches)) == 1 else ""

    def _add_entity_candidate(
        self,
        candidates: dict[tuple[str, str], dict[str, Any]],
        *,
        role: str,
        name: str,
        line: dict[str, Any],
        confidence: float,
        source: str,
    ) -> None:
        clean_name = self._collapse_repeated_tokens(self._clean(name))
        if not clean_name or len(clean_name) < 5:
            return
        if len(re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", clean_name)) < 4:
            return
        key = (role, self._normalize(clean_name))
        state = candidates.setdefault(key, {
            "candidate_id": f"entity-candidate:{role}:{self._digest(clean_name)}",
            "role": role,
            "name": clean_name,
            "identifier": "",
            "confidence": confidence,
            "evidence_ids": [],
            "source": source,
            "evidence": [],
        })
        state["confidence"] = max(float(state.get("confidence", 0.0)), confidence)
        state["evidence"].append(source)
        region_ids = list(line.get("region_ids") or ())
        state.setdefault("source_region_ids", [])
        for rid in region_ids:
            if rid not in state["source_region_ids"]:
                state["source_region_ids"].append(rid)

    def _attach_identifier_to_candidate(
        self,
        candidates: dict[tuple[str, str], dict[str, Any]],
        identifier: str,
        line: dict[str, Any] | None,
    ) -> None:
        identifier_norm = self._normalize(identifier)
        if not identifier_norm:
            return
        # Primero intenta una coincidencia de nombre/rol en la línea.
        if line is not None:
            role = self._role_context_from_line(str(line.get("text") or ""))
            legal_names = self._extract_legal_entity_mentions(str(line.get("text") or ""))
            for name in legal_names:
                key = (role or "unknown", self._normalize(name))
                state = candidates.get(key)
                if state is not None:
                    state["identifier"] = identifier
                    state["confidence"] = max(float(state["confidence"]), 0.93)
                    return
        # Si no hay nombre asociado, registra un candidato de identidad aún
        # no enlazado. No se asigna arbitrariamente a otra entidad.
        key = ("unknown", f"identifier:{identifier_norm}")
        state = candidates.setdefault(key, {
            "candidate_id": f"entity-candidate:identifier:{self._digest(identifier)}",
            "role": "unknown",
            "name": "",
            "identifier": identifier,
            "confidence": 0.78,
            "evidence_ids": [],
            "source": "identifier_only",
            "evidence": ["identifier_only"],
        })
        state["identifier"] = identifier

    def _infer_contextual_roles(
        self,
        candidates: dict[tuple[str, str], dict[str, Any]],
        lines: list[dict[str, Any]],
    ) -> None:
        """Resuelve roles de entidades sin depender de un tipo documental fijo.

        Señales contextuales fuertes: identidad legal + datos bancarios +
        canales de contacto + lenguaje de emisión/venta. La función nunca
        convierte una mera mención de empresa en proveedor sin evidencia.
        """
        for key, candidate in list(candidates.items()):
            if candidate.get("role") != "unknown":
                continue
            name_norm = self._normalize(candidate.get("name"))
            if not name_norm:
                continue
            line_hits = [
                line for line in lines
                if name_norm and name_norm in self._normalize(line.get("text"))
            ]
            if not line_hits:
                continue
            page_text = self._normalize(" ".join(str(line.get("text") or "") for line in lines))
            banking = sum(
                token in page_text
                for token in ("bank", "banco", "cuenta", "account", "swift", "iban", "cci")
            )
            contact = sum(
                token in page_text
                for token in ("email", "correo", "ventas@", "contact", "telefono", "tel", "www.")
            )
            commercial = sum(
                token in page_text
                for token in ("quotation", "cotizacion", "invoice", "factura", "offer", "oferta", "price", "precio", "total")
            )
            if banking >= 1 and contact >= 1 and commercial >= 1:
                candidate["role"] = "provider"
                candidate["confidence"] = max(float(candidate.get("confidence", 0.0)), 0.86)
                candidate["source"] = "contextual_issuer_identity"
                candidate["evidence"].append("banking+contact+commercial_context")

        # Persistir identificadores detectados por coincidencia textual.
        for candidate in candidates.values():
            name_norm = self._normalize(candidate.get("name"))
            if not name_norm or candidate.get("identifier"):
                continue
            for line in lines:
                text = str(line.get("text") or "")
                if name_norm not in self._normalize(text):
                    continue
                identifier = self._extract_identifier_value(text, "tax_id")
                if identifier:
                    candidate["identifier"] = identifier
                    break

    @staticmethod
    def _collapse_repeated_tokens(value: str) -> str:
        tokens = value.split()
        result: list[str] = []
        for token in tokens:
            if result and token.casefold() == result[-1].casefold():
                continue
            result.append(token)
        return " ".join(result)

    # ==================================================================
    # Helpers de confianza
    # ==================================================================
    @staticmethod
    def _lexical_confidence(value_type: str, raw: str) -> float:
        base = {
            "email": 0.98,
            "url": 0.98,
            "tax_id": 0.95,
            "phone": 0.90,
            "date": 0.94,
            "percentage": 0.96,
            "money": 0.94,
            "measurement": 0.91,
            "identifier": 0.90,
        }.get(value_type, 0.70)
        if len(raw) > 120:
            return max(0.40, base - 0.10)
        return base

    @staticmethod
    def _line_confidence(line: dict[str, Any], label: str, value: str) -> float:
        score = 0.65
        if ":" in str(line.get("text", "")) or "=" in str(line.get("text", "")):
            score += 0.12
        if len(label.split()) <= 4:
            score += 0.08
        if len(value) <= 120:
            score += 0.05
        if line.get("bbox"):
            score += 0.05
        return round(min(1.0, score), 4)

    @staticmethod
    def _profile_confidence(primary_score: float, scores: dict[str, float]) -> float:
        if primary_score <= 0:
            return 0.0
        total = sum(max(v, 0.0) for v in scores.values())
        return min(1.0, primary_score / max(total, 1.0))

    @staticmethod
    def _count_entity_roles(candidates: list[dict[str, Any]], entities: Iterable[DocumentEntity]) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        for entity in entities:
            counts[entity.role or "unknown"] += 1
        for candidate in candidates:
            if candidate.get("confidence", 0.0) >= 0.80:
                counts[str(candidate.get("role") or "unknown")] += 1
        return dict(counts)

    @staticmethod
    def _uncertainty_records(entity_candidates: list[dict[str, Any]], lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
        records = []
        ambiguous = [c for c in entity_candidates if c.get("role") == "unknown" and c.get("name")]
        if ambiguous:
            records.append({
                "type": "entity_role_unresolved",
                "candidate_count": len(ambiguous),
                "message": "Existen menciones de entidades legales cuya función documental no quedó demostrada.",
            })
        return records

    # ==================================================================
    # Geometría
    # ==================================================================
    @staticmethod
    def _horizontal_line_compatible(line: dict[str, Any], region: Any) -> bool:
        bbox = region.bbox
        if bbox is None or not line.get("regions"):
            return True
        lx0 = min(r.bbox[0] for r in line["regions"] if r.bbox is not None)
        lx1 = max(r.bbox[2] for r in line["regions"] if r.bbox is not None)
        rx0, _, rx1, _ = bbox
        return not (rx0 > lx1 + 40 or rx1 < lx0 - 40)

    @classmethod
    def _spatial_relation(cls, a: Any, b: Any) -> tuple[str | None, float]:
        ax0, ay0, ax1, ay1 = a.bbox
        bx0, by0, bx1, by1 = b.bbox
        acx, acy = (ax0 + ax1) / 2, (ay0 + ay1) / 2
        bcx, bcy = (bx0 + bx1) / 2, (by0 + by1) / 2
        if ax0 <= bx0 and ay0 <= by0 and ax1 >= bx1 and ay1 >= by1:
            return "contains", 0.0
        if bx0 <= ax0 and by0 <= ay0 and bx1 >= ax1 and by1 >= ay1:
            return "inside", 0.0
        dx = bcx - acx
        dy = bcy - acy
        if abs(dx) >= abs(dy) * 1.4 and abs(dx) <= cls._REGION_NEAR_DISTANCE:
            return ("right_of" if dx > 0 else "left_of"), abs(dx)
        if abs(dy) > abs(dx) * 1.4 and abs(dy) <= cls._REGION_NEAR_DISTANCE:
            return ("below" if dy > 0 else "above"), abs(dy)
        distance = math.hypot(dx, dy)
        if distance <= cls._REGION_NEAR_DISTANCE:
            return "near", distance
        return None, distance

    @staticmethod
    def _spatial_confidence(distance: float, relation: str) -> float:
        if relation in {"contains", "inside"}:
            return 0.99
        return max(0.55, min(0.98, 1.0 - distance / 50.0))

    @staticmethod
    def _union_bbox(boxes: tuple[tuple[float, float, float, float] | None, ...]) -> tuple[float, float, float, float] | None:
        valid = [b for b in boxes if b is not None]
        if not valid:
            return None
        return (
            min(b[0] for b in valid),
            min(b[1] for b in valid),
            max(b[2] for b in valid),
            max(b[3] for b in valid),
        )

    # ==================================================================
    # Parse helpers / metadata
    # ==================================================================
    @staticmethod
    def _clean(value: Any) -> str:
        return " ".join(str(value or "").replace("\x00", " ").split()).strip()

    @staticmethod
    def _normalize(value: Any) -> str:
        text = " ".join(str(value or "").split()).strip().casefold()
        return "".join(
            char for char in unicodedata.normalize("NFKD", text)
            if not unicodedata.combining(char)
        )

    @classmethod
    def _to_decimal(cls, value: Any) -> Decimal | None:
        text = str(value or "").strip()
        if not text:
            return None
        # Captura el número completo antes de normalizar separadores; esto
        # evita interpretar ``139,403.40`` como ``139.403``.
        generic_match = re.search(r"[-+]?\d[\d.,]*", text)
        candidate = generic_match.group(0) if generic_match else text
        candidate = candidate.replace(" ", "")
        try:
            if "." in candidate and "," in candidate:
                if candidate.rfind(",") > candidate.rfind("."):
                    candidate = candidate.replace(".", "").replace(",", ".")
                else:
                    candidate = candidate.replace(",", "")
            elif candidate.count(",") == 1 and candidate.count(".") == 0:
                candidate = candidate.replace(",", ".")
            elif candidate.count(",") > 1 and candidate.count(".") == 0:
                candidate = candidate.replace(",", "")
            elif candidate.count(".") > 1 and candidate.count(",") == 0:
                candidate = candidate.replace(".", "")
            return Decimal(candidate)
        except (InvalidOperation, ValueError):
            return None

    @staticmethod
    def _decimal_string(value: Decimal | None) -> str:
        return format(value, "f") if value is not None else ""

    @classmethod
    def _normalize_date(cls, value: str) -> str:
        text = cls._clean(value)
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(text, fmt).date().isoformat()
            except ValueError:
                continue
        return cls._normalize(text)

    @classmethod
    def _infer_value_type(cls, label: str, raw: str) -> str | None:
        if label in {"email", "url", "tax_id", "phone", "date", "percentage", "money", "measurement"}:
            return label
        for value_type, pattern in cls._TEXT_VALUE_PATTERNS.items():
            if pattern.search(raw):
                return value_type
        if label in {"price", "unit_price", "amount", "total", "subtotal", "cost"}:
            return "money"
        return None

    @staticmethod
    def _table_cell_confidence(columns: Any, key: str, table: dict[str, Any]) -> float:
        for column in columns or ():
            if isinstance(column, dict) and str(column.get("key")) == key:
                return float(column.get("confidence", table.get("confidence", 0.0)) or 0.0)
        return float(table.get("confidence", 0.0) or 0.0)

    @staticmethod
    def _json_safe(value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, (list, tuple)):
            return [DeepDocumentComprehensionEngine._json_safe(v) for v in value]
        if isinstance(value, dict):
            return {str(k): DeepDocumentComprehensionEngine._json_safe(v) for k, v in value.items()}
        return str(value)

    def _region_evidence_id(self, knowledge: DocumentKnowledge, region_id: str) -> str:
        for evidence in knowledge.evidence:
            if evidence.metadata.get("region_id") == region_id:
                return evidence.evidence_id
            if evidence.source_id == region_id:
                return evidence.evidence_id
        return ""

    def _first_region_evidence(self, knowledge: DocumentKnowledge, region_ids: Iterable[str]) -> str:
        ids = set(region_ids)
        if not ids:
            return ""
        for evidence in knowledge.evidence:
            if evidence.source_id in ids or evidence.metadata.get("region_id") in ids:
                return evidence.evidence_id
        return ""

    @staticmethod
    def _iter_concepts_for_identifier_search(knowledge: DocumentKnowledge) -> Iterable[dict[str, Any]]:
        yield from knowledge.facts
        yield from knowledge.attributes

    @classmethod
    def _extract_identifier_value(cls, text: str, identifier_type: str) -> str:
        if identifier_type == "tax_id":
            match = cls._TEXT_VALUE_PATTERNS["tax_id"].search(text)
            if match:
                value = match.group(0)
                tail = re.split(r"[:#\-]", value, maxsplit=1)
                return tail[-1].strip() if tail else value
        return ""

    @staticmethod
    def _digest_region_key(region_id: str) -> str:
        return DeepDocumentComprehensionEngine._digest(region_id)

    def _dedupe_concepts(self, concepts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        seen: set[str] = set()
        for concept in concepts:
            cid = str(concept.get("concept_id") or "")
            if not cid:
                continue
            if cid in seen:
                continue
            seen.add(cid)
            result.append(concept)
        return result

    @staticmethod
    def _dedupe_relationships(relationships: list[DocumentRelationship]) -> list[DocumentRelationship]:
        seen: set[tuple[str, str, str]] = set()
        result: list[DocumentRelationship] = []
        for rel in relationships:
            key = (rel.source_id, rel.relationship_type, rel.target_id)
            if key in seen:
                continue
            seen.add(key)
            result.append(rel)
        return result

    @staticmethod
    def _dedupe_dict_records(records: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
        seen: set[tuple[Any, ...]] = set()
        result: list[dict[str, Any]] = []
        for record in records:
            key = tuple(record.get(item) for item in keys)
            if key in seen:
                continue
            seen.add(key)
            result.append(record)
        return result

    @classmethod
    def _json_safe_normalize(cls, value: Any) -> Any:
        return cls._json_safe(value)


__all__ = ["DeepDocumentComprehensionEngine"]
