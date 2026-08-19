from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import os
import re
from pydantic import BaseModel
from typing import List, Optional

# Assumes running from the project root so `ingestion` is in PYTHONPATH
from ingestion.drug_client import get_rxcui, get_fda_labels, get_drug_interactions

app = FastAPI(
    title="DrugLens API",
    description="Evidence-grounded medication information assistant",
    version="0.1.0",
)


class DrugLabel(BaseModel):
    brand_names: List[str]
    generic_names: List[str]
    manufacturer: List[str]
    substance_name: List[str]
    route: List[str]
    product_type: Optional[str]
    active_ingredient: Optional[str]
    indications_and_usage: Optional[str]
    adverse_reactions: Optional[str]
    warnings: Optional[str]
    description: Optional[str]
    ask_doctor: Optional[str]
    contraindications: Optional[str]
    stop_use: Optional[str]
    pregnancy_or_breast_feeding: Optional[str]
    dosage_and_administration: Optional[str]


class DrugSearchResult(BaseModel):
    name: str
    rxcui: Optional[str]
    label_count: int
    labels: List[DrugLabel]


@app.get("/health")
def health_check():
    return {"status": "ok"}


def clean_field(text: str | None) -> str | None:
    if not text:
        return None

    # 1. Strip leading section numbers and dots
    text = re.sub(r'^\s*\d+\.?\d*\s*', '', text)

    # 2. Remove common headers
    lower_text = text.lower()
    prefixes = [
        "indications and usage", "indications", "uses",
        "adverse reactions",
        "warnings and cautions", "warnings", "warning",
        "directions", "dosage and administration",
        "purpose", "description",
        "contraindications", "stop use", "ask a doctor or pharmacist", "ask a doctor",
    ]

    for prefix in prefixes:
        if lower_text.startswith(prefix):
            if len(lower_text) > len(prefix) and not lower_text[len(prefix)].isalpha():
                text = text[len(prefix):].lstrip(' :.-')
                lower_text = text.lower()
            elif len(lower_text) == len(prefix):
                text = ""

    return text.strip() or None


def _extract_field(label: dict, key: str) -> str | None:
    """Safely extract and clean a text field from an FDA label."""
    val = label.get(key)
    if val and isinstance(val, list) and len(val) > 0:
        return clean_field(val[0])
    return None


def _build_label(label: dict) -> DrugLabel:
    metadata = label.get("openfda", {})
    return DrugLabel(
        brand_names=metadata.get("brand_name", []),
        generic_names=metadata.get("generic_name", []),
        manufacturer=metadata.get("manufacturer_name", []),
        substance_name=metadata.get("substance_name", []),
        route=metadata.get("route", []),
        product_type=(metadata.get("product_type", [None]) or [None])[0],
        active_ingredient=_extract_field(label, "active_ingredient"),
        indications_and_usage=_extract_field(label, "indications_and_usage"),
        adverse_reactions=_extract_field(label, "adverse_reactions"),
        warnings=_extract_field(label, "warnings") or _extract_field(label, "warnings_and_cautions"),
        description=_extract_field(label, "description"),
        ask_doctor=_extract_field(label, "ask_doctor_or_pharmacist"),
        contraindications=_extract_field(label, "contraindications"),
        stop_use=_extract_field(label, "stop_use"),
        pregnancy_or_breast_feeding=_extract_field(label, "pregnancy_or_breast_feeding"),
        dosage_and_administration=_extract_field(label, "dosage_and_administration"),
    )


@app.get("/api/drugs/{drug_name}", response_model=DrugSearchResult)
def get_drug_info(drug_name: str):
    """
    Look up a medicine by name and return ALL matching FDA labels.
    """
    rxcui = get_rxcui(drug_name)

    # We will still try to get labels if rxcui is None (fallback to generic name)
    raw_labels = get_fda_labels(drug_name, rxcui, limit=5)

    if not raw_labels:
        raise HTTPException(status_code=404, detail=f"No information found for '{drug_name}'")

    labels = [_build_label(lbl) for lbl in raw_labels]

    return DrugSearchResult(
        name=drug_name,
        rxcui=rxcui,
        label_count=len(labels),
        labels=labels,
    )


# ============================================================
# Drug Interaction Checker
# ============================================================

class DrugInteractionEntry(BaseModel):
    drug_name: str
    rxcui: Optional[str]
    found: bool
    interaction_text: Optional[str]


class InteractionFlag(BaseModel):
    drug_a: str
    drug_b: str
    severity: str  # "mentioned", "warning", or "unknown"
    detail: str


class InteractionCheckResult(BaseModel):
    drugs: List[DrugInteractionEntry]
    flags: List[InteractionFlag]
    summary: str


def _check_mentions(drug_a_name: str, drug_a_text: str | None,
                    drug_b_name: str, drug_b_substances: list[str]) -> InteractionFlag | None:
    """
    Check if drug A's interaction text mentions drug B (by name or substance).
    """
    if not drug_a_text:
        return None

    text_lower = drug_a_text.lower()
    # Check drug B's name and all its substance names
    search_terms = [drug_b_name.lower()] + [s.lower() for s in drug_b_substances]

    for term in search_terms:
        if term in text_lower:
            # Try to extract the relevant sentence(s)
            sentences = re.split(r'(?<=[.!?])\s+', drug_a_text)
            relevant = [s.strip() for s in sentences if term in s.lower()]
            detail = ' '.join(relevant[:3]) if relevant else f"{drug_a_name}'s label mentions {drug_b_name} in its drug interactions section."

            # Simple severity heuristic
            severity = "mentioned"
            warning_words = ["contraindicated", "avoid", "do not", "serious", "fatal", "risk", "caution"]
            if any(w in detail.lower() for w in warning_words):
                severity = "warning"

            return InteractionFlag(
                drug_a=drug_a_name,
                drug_b=drug_b_name,
                severity=severity,
                detail=clean_field(detail) or detail,
            )

    return None


@app.get("/api/interactions")
def check_interactions(drugs: str):
    """
    Check interactions between multiple drugs.
    Query param `drugs` is a comma-separated list of drug names.
    Example: /api/interactions?drugs=metformin,warfarin
    """
    drug_names = [d.strip().lower() for d in drugs.split(",") if d.strip()]

    if len(drug_names) < 2:
        raise HTTPException(status_code=400, detail="Please provide at least 2 drugs separated by commas.")
    if len(drug_names) > 6:
        raise HTTPException(status_code=400, detail="Please provide at most 6 drugs.")

    # Fetch data for each drug
    entries: list[DrugInteractionEntry] = []
    substance_map: dict[str, list[str]] = {}  # drug_name -> substance names
    interaction_texts: dict[str, str | None] = {}

    for name in drug_names:
        rxcui = get_rxcui(name)
        interaction_text = get_drug_interactions(name, rxcui)

        # Also get substance names for cross-referencing
        labels = get_fda_labels(name, rxcui, limit=1)
        substances = []
        if labels:
            meta = labels[0].get("openfda", {})
            substances = meta.get("substance_name", [])

        entries.append(DrugInteractionEntry(
            drug_name=name,
            rxcui=rxcui,
            found=interaction_text is not None or len(labels) > 0,
            interaction_text=clean_field(interaction_text),
        ))
        substance_map[name] = substances
        interaction_texts[name] = interaction_text

    # Cross-reference: check each pair
    flags: list[InteractionFlag] = []
    seen_pairs: set[tuple[str, str]] = set()

    for i, drug_a in enumerate(drug_names):
        for j, drug_b in enumerate(drug_names):
            if i >= j:
                continue
            pair = (min(drug_a, drug_b), max(drug_a, drug_b))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            # Check A's text for B
            flag = _check_mentions(drug_a, interaction_texts[drug_a],
                                   drug_b, substance_map.get(drug_b, []))
            if flag:
                flags.append(flag)
                continue

            # Check B's text for A
            flag = _check_mentions(drug_b, interaction_texts[drug_b],
                                   drug_a, substance_map.get(drug_a, []))
            if flag:
                flags.append(flag)

    # Summary
    if flags:
        warning_count = sum(1 for f in flags if f.severity == "warning")
        summary = f"Found {len(flags)} potential interaction(s) between your medications"
        if warning_count:
            summary += f", including {warning_count} that may need attention."
        else:
            summary += "."
    else:
        summary = (
            f"No interaction between {', '.join(drug_names)} "
            "was identified in the FDA labeling data retrieved."
        )

    return InteractionCheckResult(drugs=entries, flags=flags, summary=summary)


# Mount static files for the frontend
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")