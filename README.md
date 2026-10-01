# DrugLens

**A source-forward medication reference built on NIH RxNorm and openFDA drug labels.**

DrugLens helps you inspect FDA medication labeling without reading raw regulatory payloads. It provides a structured drug lookup and an interaction-language scan across the FDA label records retrieved for the medications you enter.

> DrugLens is for informational use only. It is not a substitute for medical advice, diagnosis, or treatment.

## What it does

### Drug lookup

Search by a brand, generic, or active ingredient name. DrugLens resolves the query with RxNorm when possible, retrieves up to five matching openFDA label records, and presents their content in a readable reference layout.

The UI surfaces source provenance such as manufacturer, route, effective date, application number, Set ID, and RxCUI when those fields are available.

### FDA label interaction scan

Enter two to six medications. DrugLens scans interaction-related sections from the retrieved FDA label records and looks for references to the other medications or their active substances.

Results are intentionally described as **label-derived evidence**, not clinical interaction severity:

- **Mention detected** means the other medication or substance appears in retrieved interaction-related label text.
- **Caution language detected** means the matching excerpt also contains caution terms such as `avoid`, `contraindicated`, `risk`, or `caution`.
- **No matching interaction language detected** means DrugLens did not find a text match in the retrieved records. It does **not** rule out an interaction and does not establish that a medication combination is appropriate.

DrugLens is not a replacement for a pharmacist, clinician, or validated clinical interaction database.

## Data sources

| Source | Purpose |
|---|---|
| NIH RxNorm | Resolve medication names to standardized RxCUI identifiers when possible |
| openFDA Drug Labels | Retrieve structured FDA labeling sections and source metadata |

openFDA results are not exhaustive clinical knowledge. Some records do not contain harmonized identifiers, not every label exposes every section, and DrugLens currently limits each lookup to five retrieved label records.

## Architecture

```text
Browser
  |
  | GET /api/drugs/{name}
  | GET /api/interactions?drugs=a,b
  v
FastAPI
  |
  +-- services/drugs.py
  |     clean/normalize FDA label data
  |     resolve one reusable medication object per query
  |
  +-- services/interactions.py
  |     scan retrieved label text for cross-medication evidence
  |
  +-- clients/drug_sources.py
        RxNorm + openFDA HTTP access
```

The frontend is intentionally framework-free HTML, CSS, and JavaScript. The backend uses FastAPI, Pydantic, requests, and a small service/client split for testability.

## Quick start

```bash
git clone https://github.com/3bsamad/DrugLens.git
cd DrugLens
python -m venv .venv
pip install -r requirements.txt
python -m uvicorn backend.app.main:app --reload
```

Open `http://localhost:8000`.

Run tests with:

```bash
pytest -q
```

## Safety and reliability choices

- Remote FDA/RxNorm text is rendered with DOM `textContent`, not injected as HTML.
- RxNorm/openFDA timeouts and dependency failures are distinguished from valid no-result responses.
- Duplicate medication inputs are normalized before interaction scanning.
- FDA field arrays are combined instead of silently discarding all but the first fragment.
- The interaction scan reuses one resolved medication object per input instead of repeating the same upstream calls.
- The UI never presents a missing text match as a green or "safe" result.

## License

MIT. See [LICENSE](LICENSE).
