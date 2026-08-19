import requests


RXNORM_URL = "https://rxnav.nlm.nih.gov/REST/rxcui.json"
OPENFDA_URL = "https://api.fda.gov/drug/label.json"


def get_rxcui(drug_name: str) -> str | None:
    """Resolve a drug name to an RxNorm Concept Unique Identifier."""

    response = requests.get(
        RXNORM_URL,
        params={
            "name": drug_name,
            "search": 2,
        },
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    rxnorm_ids = data.get("idGroup", {}).get("rxnormId", [])

    if not rxnorm_ids:
        return None

    return rxnorm_ids[0]


def get_fda_labels(
    drug_name: str,
    rxcui: str | None = None,
    limit: int = 5,
) -> list[dict]:

    if rxcui:
        response = requests.get(
            OPENFDA_URL,
            params={
                "search": f"openfda.rxcui:{rxcui}",
                "limit": limit,
            },
            timeout=10,
        )

        if response.status_code == 200:
            return response.json().get("results", [])

    # Fallback: search by generic name
    response = requests.get(
        OPENFDA_URL,
        params={
            "search": f'openfda.generic_name:"{drug_name}"',
            "limit": limit,
        },
        timeout=10,
    )

    if response.status_code == 200:
        return response.json().get("results", [])

    # Second fallback: search by brand name
    response = requests.get(
        OPENFDA_URL,
        params={
            "search": f'openfda.brand_name:"{drug_name}"',
            "limit": limit,
        },
        timeout=10,
    )

    if response.status_code == 200:
        return response.json().get("results", [])

    return []


def get_drug_interactions(drug_name: str, rxcui: str | None = None) -> str | None:
    """Fetch interaction-relevant text from the first FDA label for a drug.
    
    Checks drug_interactions first, then falls back to combining
    warnings, do_not_use, and ask_doctor_or_pharmacist fields
    (common in OTC drug labels that lack a dedicated interactions section).
    """
    labels = get_fda_labels(drug_name, rxcui, limit=1)
    if not labels:
        return None

    label = labels[0]

    # Primary: dedicated drug_interactions field
    interactions = label.get("drug_interactions")
    if interactions and isinstance(interactions, list) and len(interactions) > 0:
        return interactions[0]

    # Fallback for OTC drugs: combine interaction-relevant sections
    fallback_keys = ["warnings", "do_not_use", "ask_doctor_or_pharmacist", "warnings_and_cautions"]
    parts = []
    for key in fallback_keys:
        val = label.get(key)
        if val and isinstance(val, list) and len(val) > 0:
            parts.append(val[0])

    return " ".join(parts) if parts else None


def print_label_summary(labels: list[dict]) -> None:
    for i, label in enumerate(labels, start=1):
        metadata = label.get("openfda", {})

        print(f"\n--- Label {i} ---")
        print("Brand:", metadata.get("brand_name"))
        print("Generic:", metadata.get("generic_name"))
        print("Substance:", metadata.get("substance_name"))
        print("Route:", metadata.get("route"))
        print("RxCUI:", metadata.get("rxcui"))
        print("Manufacturer:", metadata.get("manufacturer_name"))

if __name__ == "__main__":
    drug_name = "naproxen"

    rxcui = get_rxcui(drug_name)

    print(f"Drug: {drug_name}")
    print(f"RxCUI: {rxcui}")

    labels = get_fda_labels(drug_name, rxcui)

    print(f"FDA labels found: {len(labels)}")

    print_label_summary(labels)
