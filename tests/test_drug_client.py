import pytest

from backend.app.services.drugs import clean_field, extract_field
from backend.app.services.interactions import find_pair_evidence


def test_clean_field_removes_section_number_and_header():
    assert clean_field('7 WARNINGS: Use with caution.') == 'Use with caution.'


def test_extract_field_combines_multiple_fda_fragments():
    label = {'warnings': ['1 WARNINGS First warning.', 'Second warning.']}
    assert extract_field(label, 'warnings') == 'First warning.\n\nSecond warning.'


def test_find_pair_evidence_marks_caution_language_without_calling_it_severity():
    evidence = find_pair_evidence(
        source_drug='warfarin',
        source_text='Concomitant aspirin use may increase the risk of bleeding.',
        target_drug='aspirin',
        target_substances=['acetylsalicylic acid'],
    )
    assert evidence is not None
    assert evidence.evidence_type == 'caution_language'
    assert evidence.matched_term == 'aspirin'
    assert not hasattr(evidence, 'severity')


def test_find_pair_evidence_returns_none_when_no_name_or_substance_is_mentioned():
    assert find_pair_evidence(
        source_drug='metformin',
        source_text='Monitor renal function periodically.',
        target_drug='amoxicillin',
        target_substances=['amoxicillin'],
    ) is None
