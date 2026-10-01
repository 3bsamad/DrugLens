from __future__ import annotations

import requests

RXNORM_URL = 'https://rxnav.nlm.nih.gov/REST/rxcui.json'
OPENFDA_URL = 'https://api.fda.gov/drug/label.json'
DEFAULT_TIMEOUT = 10


class UpstreamError(RuntimeError):
    pass


class UpstreamTimeout(UpstreamError):
    pass


class DrugNotFound(LookupError):
    pass


def _escape_phrase(value: str) -> str:
    return value.replace('\\', '\\\\').replace('"', '\\"')


class DrugSources:
    def __init__(self, session=requests):
        self.session = session

    def _request(self, url: str, *, params: dict) -> requests.Response:
        try:
            return self.session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        except requests.Timeout as exc:
            raise UpstreamTimeout(f'Upstream request timed out: {url}') from exc
        except requests.RequestException as exc:
            raise UpstreamError(f'Upstream request failed: {url}') from exc

    def get_rxcui(self, drug_name: str) -> str | None:
        response = self._request(RXNORM_URL, params={'name': drug_name, 'search': 2})
        try:
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise UpstreamError('RxNorm returned an error') from exc
        except ValueError as exc:
            raise UpstreamError('RxNorm returned invalid JSON') from exc
        ids = data.get('idGroup', {}).get('rxnormId', [])
        return ids[0] if ids else None

    def _openfda_search(self, search: str, limit: int) -> list[dict] | None:
        response = self._request(OPENFDA_URL, params={'search': search, 'limit': limit})
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise UpstreamError(f'openFDA returned HTTP {response.status_code}')
        try:
            return response.json().get('results', [])
        except ValueError as exc:
            raise UpstreamError('openFDA returned invalid JSON') from exc

    def get_fda_labels(self, drug_name: str, rxcui: str | None = None, limit: int = 5) -> list[dict]:
        if rxcui:
            results = self._openfda_search(f'openfda.rxcui:{_escape_phrase(rxcui)}', limit)
            if results:
                return results

        escaped = _escape_phrase(drug_name)
        for field in ('generic_name', 'brand_name'):
            results = self._openfda_search(f'openfda.{field}:"{escaped}"', limit)
            if results:
                return results
        return []


DEFAULT_SOURCES = DrugSources()
