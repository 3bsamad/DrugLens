from __future__ import annotations

import re

from backend.app.clients.drug_sources import DEFAULT_SOURCES, DrugNotFound, DrugSources
from backend.app.models import DrugLabel, ResolvedDrug

_HEADERS = (
    'indications and usage', 'indications', 'uses', 'adverse reactions',
    'warnings and cautions', 'warnings', 'warning', 'directions',
    'dosage and administration', 'purpose', 'description', 'contraindications',
    'stop use', 'ask a doctor or pharmacist', 'ask a doctor',
    'drug interactions',
)


def clean_field(text: str | None) -> str | None:
    if not text:
        return None
    value = re.sub(r'^\s*\d+(?:\.\d+)*\s*', '', str(text)).strip()
    lowered = value.lower()
    for prefix in _HEADERS:
        if lowered.startswith(prefix):
            boundary = value[len(prefix):len(prefix) + 1]
            if not boundary or not boundary.isalpha():
                value = value[len(prefix):].lstrip(' :.-')
                break
    return value.strip() or None


def extract_field(label: dict, key: str) -> str | None:
    value = label.get(key)
    if not isinstance(value, list):
        return None
    cleaned = [clean_field(item) for item in value if isinstance(item, str)]
    parts = [item for item in cleaned if item]
    return '\n\n'.join(parts) if parts else None


def _first(value):
    if isinstance(value, list):
        return value[0] if value else None
    return value


def extract_interaction_text(label: dict) -> str | None:
    dedicated = extract_field(label, 'drug_interactions')
    if dedicated:
        return dedicated
    parts = [
        extract_field(label, 'warnings'),
        extract_field(label, 'warnings_and_cautions'),
        extract_field(label, 'do_not_use'),
        extract_field(label, 'ask_doctor_or_pharmacist'),
    ]
    parts = [part for part in parts if part]
    return '\n\n'.join(parts) if parts else None


def build_label(label: dict, index: int) -> DrugLabel:
    meta = label.get('openfda') or {}
    set_id = _first(label.get('set_id'))
    return DrugLabel(
        brand_names=meta.get('brand_name', []),
        generic_names=meta.get('generic_name', []),
        manufacturer=meta.get('manufacturer_name', []),
        substance_name=meta.get('substance_name', []),
        route=meta.get('route', []),
        product_type=_first(meta.get('product_type')),
        active_ingredient=extract_field(label, 'active_ingredient'),
        indications_and_usage=extract_field(label, 'indications_and_usage'),
        adverse_reactions=extract_field(label, 'adverse_reactions'),
        warnings=extract_field(label, 'warnings') or extract_field(label, 'warnings_and_cautions'),
        description=extract_field(label, 'description'),
        ask_doctor=extract_field(label, 'ask_doctor_or_pharmacist'),
        contraindications=extract_field(label, 'contraindications'),
        stop_use=extract_field(label, 'stop_use'),
        pregnancy_or_breast_feeding=extract_field(label, 'pregnancy_or_breast_feeding'),
        dosage_and_administration=extract_field(label, 'dosage_and_administration'),
        interaction_text=extract_interaction_text(label),
        effective_date=_first(label.get('effective_time')),
        application_number=meta.get('application_number', []),
        set_id=set_id,
        source_label_index=index,
    )


def resolve_drug(name: str, label_limit: int = 5, sources: DrugSources = DEFAULT_SOURCES) -> ResolvedDrug:
    query = name.strip().lower()
    if not query:
        raise DrugNotFound('Empty medication name')
    rxcui = sources.get_rxcui(query)
    raw_labels = sources.get_fda_labels(query, rxcui, limit=label_limit)
    if not raw_labels:
        raise DrugNotFound(query)
    labels = [build_label(raw, index) for index, raw in enumerate(raw_labels)]
    substances = []
    seen = set()
    for label in labels:
        for substance in label.substance_name:
            key = substance.casefold()
            if key not in seen:
                seen.add(key)
                substances.append(substance)
    canonical = next((g for label in labels for g in label.generic_names), query)
    return ResolvedDrug(
        query=query,
        name=canonical,
        rxcui=rxcui,
        labels=labels,
        raw_labels=raw_labels,
        substances=substances,
    )
