from __future__ import annotations

import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from backend.app.clients.drug_sources import DrugNotFound, UpstreamError, UpstreamTimeout
from backend.app.models import DrugSearchResult, InteractionScanResult
from backend.app.services.drugs import resolve_drug
from backend.app.services.interactions import scan_interactions

app = FastAPI(
    title='DrugLens API',
    description='Source-forward medication information from FDA labeling data',
    version='0.2.0',
)


@app.get('/health')
def health_check():
    return {'status': 'ok'}


def _http_error(exc: Exception):
    if isinstance(exc, DrugNotFound):
        raise HTTPException(status_code=404, detail='No FDA label information was found for that medication.')
    if isinstance(exc, UpstreamTimeout):
        raise HTTPException(status_code=503, detail='Medication data sources are temporarily unavailable. Please try again.')
    if isinstance(exc, UpstreamError):
        raise HTTPException(status_code=502, detail='A medication data source returned an error. Please try again.')
    raise exc


@app.get('/api/drugs/{drug_name}', response_model=DrugSearchResult)
def get_drug_info(drug_name: str):
    try:
        resolved = resolve_drug(drug_name, label_limit=5)
    except (DrugNotFound, UpstreamError) as exc:
        _http_error(exc)
    return DrugSearchResult(
        name=resolved.name,
        rxcui=resolved.rxcui,
        label_count=len(resolved.labels),
        retrieval_limit=5,
        labels=resolved.labels,
    )


def _normalize_unique_drugs(raw: str) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for part in raw.split(','):
        name = part.strip().lower()
        if not name:
            continue
        key = name.casefold()
        if key not in seen:
            seen.add(key)
            unique.append(name)
    return unique


@app.get('/api/interactions', response_model=InteractionScanResult)
def check_interactions(drugs: str):
    drug_names = _normalize_unique_drugs(drugs)
    if len(drug_names) < 2:
        raise HTTPException(status_code=400, detail='Please provide at least 2 unique medications.')
    if len(drug_names) > 6:
        raise HTTPException(status_code=400, detail='Please provide at most 6 medications.')
    try:
        resolved = [resolve_drug(name, label_limit=5) for name in drug_names]
    except (DrugNotFound, UpstreamError) as exc:
        _http_error(exc)
    return scan_interactions(resolved)


frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend')
if os.path.exists(frontend_path):
    app.mount('/', StaticFiles(directory=frontend_path, html=True), name='frontend')
