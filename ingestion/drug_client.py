"""Backwards-compatible wrappers for DrugLens data-source access."""
from backend.app.clients.drug_sources import DEFAULT_SOURCES
from backend.app.services.drugs import extract_interaction_text


def get_rxcui(drug_name: str) -> str | None:
    return DEFAULT_SOURCES.get_rxcui(drug_name)


def get_fda_labels(drug_name: str, rxcui: str | None = None, limit: int = 5) -> list[dict]:
    return DEFAULT_SOURCES.get_fda_labels(drug_name, rxcui, limit)


def get_drug_interactions(drug_name: str, rxcui: str | None = None) -> str | None:
    labels = get_fda_labels(drug_name, rxcui, limit=1)
    return extract_interaction_text(labels[0]) if labels else None
