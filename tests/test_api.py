from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models import DrugLabel, ResolvedDrug
from backend.app.clients.drug_sources import UpstreamTimeout

client = TestClient(app)
raw_client = TestClient(app, raise_server_exceptions=False)


def make_resolved(name: str, interaction_text: str | None = None) -> ResolvedDrug:
    label = DrugLabel(
        brand_names=[name.title()],
        generic_names=[name],
        manufacturer=['Example Pharma'],
        substance_name=[name],
        route=['ORAL'],
        product_type='HUMAN PRESCRIPTION DRUG',
        interaction_text=interaction_text,
        source_label_index=0,
    )
    return ResolvedDrug(
        query=name,
        name=name,
        rxcui='123',
        labels=[label],
        raw_labels=[{}],
        substances=[name],
    )


def test_health():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_interaction_scan_deduplicates_case_and_whitespace(monkeypatch):
    calls = []

    def fake_resolve(name: str, label_limit: int = 5):
        calls.append(name)
        return make_resolved(name)

    monkeypatch.setattr('backend.app.main.resolve_drug', fake_resolve)
    response = client.get('/api/interactions', params={'drugs': ' Metformin ,metformin, Warfarin '})
    assert response.status_code == 200
    assert calls == ['metformin', 'warfarin']
    assert response.json()['drugs'] == ['metformin', 'warfarin']


def test_interaction_scan_rejects_when_deduplication_leaves_only_one_unique_drug():
    response = client.get('/api/interactions', params={'drugs': 'Metformin, metformin'})
    assert response.status_code == 400
    assert 'unique' in response.json()['detail'].lower()


def test_interaction_scan_no_match_is_neutral_and_explicitly_not_a_safety_claim(monkeypatch):
    resolved = {
        'metformin': make_resolved('metformin', 'Monitor renal function periodically.'),
        'amoxicillin': make_resolved('amoxicillin', 'Dose adjustment may be needed in renal impairment.'),
    }
    monkeypatch.setattr('backend.app.main.resolve_drug', lambda name, label_limit=5: resolved[name])

    response = client.get('/api/interactions', params={'drugs': 'metformin,amoxicillin'})
    assert response.status_code == 200
    body = response.json()
    assert body['evidence'] == []
    assert body['status'] == 'no_match_detected'
    assert 'No matching interaction language' in body['summary']
    assert 'does not rule out' in body['limitation']
    assert 'safe' not in body['summary'].lower()
    assert 'not a statement that a combination is safe' in body['limitation'].lower()


def test_lookup_maps_upstream_timeout_to_503(monkeypatch):
    def timeout(*args, **kwargs):
        raise UpstreamTimeout('openFDA timed out')

    monkeypatch.setattr('backend.app.main.resolve_drug', timeout)
    response = raw_client.get('/api/drugs/metformin')
    assert response.status_code == 503
    assert 'temporarily unavailable' in response.json()['detail'].lower()
