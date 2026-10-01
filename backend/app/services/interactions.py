from __future__ import annotations

import re
from itertools import combinations

from backend.app.models import InteractionEvidence, InteractionScanResult, ResolvedDrug

_CAUTION_WORDS = ('contraindicated', 'avoid', 'do not', 'serious', 'fatal', 'risk', 'caution', 'monitor closely')
_LIMITATION = (
    'This scan only checks interaction-related language in the FDA labels retrieved by DrugLens. '
    'A missing match does not rule out a drug interaction and is not a statement that a combination is safe.'
)


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r'(?<=[.!?])\s+', text) if part.strip()]


def _contains_term(text: str, term: str) -> bool:
    pattern = r'(?<!\w)' + re.escape(term) + r'(?!\w)'
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def find_pair_evidence(
    source_drug: str,
    source_text: str | None,
    target_drug: str,
    target_substances: list[str],
    *,
    source_label_index: int | None = None,
    source_manufacturer: str | None = None,
) -> InteractionEvidence | None:
    if not source_text:
        return None
    terms = []
    for term in [target_drug, *target_substances]:
        normalized = term.strip()
        if normalized and normalized.casefold() not in {t.casefold() for t in terms}:
            terms.append(normalized)
    for term in terms:
        if not _contains_term(source_text, term):
            continue
        matching = [sentence for sentence in _sentences(source_text) if _contains_term(sentence, term)]
        excerpt = ' '.join(matching[:3]) or source_text[:600]
        evidence_type = 'caution_language' if any(word in excerpt.casefold() for word in _CAUTION_WORDS) else 'mention'
        return InteractionEvidence(
            drug_a=source_drug,
            drug_b=target_drug,
            evidence_type=evidence_type,
            source_drug=source_drug,
            matched_term=term,
            excerpt=excerpt,
            source_label_index=source_label_index,
            source_manufacturer=source_manufacturer,
        )
    return None


def scan_interactions(resolved: list[ResolvedDrug]) -> InteractionScanResult:
    evidence: list[InteractionEvidence] = []
    for drug_a, drug_b in combinations(resolved, 2):
        match = _scan_direction(drug_a, drug_b)
        if match is None:
            match = _scan_direction(drug_b, drug_a)
        if match:
            evidence.append(match)
    names = [drug.query for drug in resolved]
    if evidence:
        caution_count = sum(item.evidence_type == 'caution_language' for item in evidence)
        summary = f'Found label-derived interaction evidence for {len(evidence)} medication pair(s).'
        if caution_count:
            summary += f' {caution_count} pair(s) contain caution language in the retrieved FDA label text.'
        status = 'evidence_detected'
    else:
        summary = 'No matching interaction language was detected in the FDA labels retrieved.'
        status = 'no_match_detected'
    return InteractionScanResult(
        drugs=names,
        evidence=evidence,
        status=status,
        summary=summary,
        limitation=_LIMITATION,
    )


def _scan_direction(source: ResolvedDrug, target: ResolvedDrug) -> InteractionEvidence | None:
    for label in source.labels:
        manufacturer = label.manufacturer[0] if label.manufacturer else None
        match = find_pair_evidence(
            source.query,
            label.interaction_text,
            target.query,
            target.substances,
            source_label_index=label.source_label_index,
            source_manufacturer=manufacturer,
        )
        if match:
            return match
    return None
