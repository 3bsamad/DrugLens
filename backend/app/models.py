from pydantic import BaseModel, Field


class DrugLabel(BaseModel):
    brand_names: list[str] = Field(default_factory=list)
    generic_names: list[str] = Field(default_factory=list)
    manufacturer: list[str] = Field(default_factory=list)
    substance_name: list[str] = Field(default_factory=list)
    route: list[str] = Field(default_factory=list)
    product_type: str | None = None
    active_ingredient: str | None = None
    indications_and_usage: str | None = None
    adverse_reactions: str | None = None
    warnings: str | None = None
    description: str | None = None
    ask_doctor: str | None = None
    contraindications: str | None = None
    stop_use: str | None = None
    pregnancy_or_breast_feeding: str | None = None
    dosage_and_administration: str | None = None
    interaction_text: str | None = None
    effective_date: str | None = None
    application_number: list[str] = Field(default_factory=list)
    set_id: str | None = None
    source_label_index: int = 0


class ResolvedDrug(BaseModel):
    query: str
    name: str
    rxcui: str | None = None
    labels: list[DrugLabel] = Field(default_factory=list)
    raw_labels: list[dict] = Field(default_factory=list, exclude=True)
    substances: list[str] = Field(default_factory=list)


class DrugSearchResult(BaseModel):
    name: str
    rxcui: str | None = None
    label_count: int
    retrieval_limit: int
    labels: list[DrugLabel]


class InteractionEvidence(BaseModel):
    drug_a: str
    drug_b: str
    evidence_type: str
    source_drug: str
    matched_term: str
    excerpt: str
    source_label_index: int | None = None
    source_manufacturer: str | None = None


class InteractionScanResult(BaseModel):
    drugs: list[str]
    evidence: list[InteractionEvidence]
    status: str
    summary: str
    limitation: str
