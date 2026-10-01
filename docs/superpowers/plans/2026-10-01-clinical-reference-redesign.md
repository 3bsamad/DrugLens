# DrugLens Clinical Reference Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn DrugLens into a trustworthy, accessible clinical-reference interface with safer interaction semantics, cleaner backend boundaries, tests, and production-ready repository hygiene.

**Architecture:** Keep the lightweight FastAPI + vanilla HTML/CSS/JS stack. Separate API models, upstream clients, and service logic enough to make the backend testable while preserving the current deployment model. Rebuild the frontend around a source-forward document layout rather than a card-heavy dark SaaS aesthetic.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic, requests, vanilla HTML/CSS/JS, pytest.

**Spec:** `docs/superpowers/specs/2026-10-01-clinical-reference-redesign.md`

## Global Constraints

- Preserve FastAPI + vanilla frontend; do not migrate to React/Next.js.
- DrugLens is informational only; no UI may imply clinical safety from a missing text match.
- Interaction results must describe label-derived evidence, not clinically validated severity.
- Remote API text must not be inserted into the DOM through unsafe `innerHTML`.
- Core controls must be keyboard accessible and meet WCAG 2.1 AA expectations.
- Primary visual direction is light, calm, clinical, source-forward; no purple glow or generic AI glassmorphism.
- Maximum interaction inputs: 6; minimum: 2.
- Do not add authentication, persistence, adverse-event charts, recalls, cabinet monitoring, pill ID, or LLM summaries in this redesign.

## Review Focus

- Duplicate medication names differing only in case/whitespace should be deduplicated before comparison.
- A dependency timeout must not be presented as "drug not found".
- No interaction-language match must render as neutral/unknown, never "safe".
- FDA strings containing markup-looking characters must render as literal text.
- Mobile widths around 320px must not overflow or hide core actions.

---

### Task 1: Test foundation and repository hygiene

**Files:**
- Create: `requirements.txt`
- Create: `tests/test_drug_client.py`
- Create: `tests/test_api.py`
- Create: `LICENSE`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: current public functions from `backend.app.main` and `ingestion.drug_client`
- Produces: reproducible test environment and regression coverage for current/refactored behavior

- [ ] Add pytest/FastAPI test dependencies to `requirements.txt`.
- [ ] Add Python/cache/editor/environment patterns to `.gitignore`.
- [ ] Add MIT `LICENSE`.
- [ ] Write failing tests for cleaning, field extraction, validation, duplicate handling, and upstream failures.
- [ ] Run `pytest -q` and confirm the new behavioral tests expose current gaps.
- [ ] Commit the test/hygiene foundation.

### Task 2: Upstream clients and resilient drug resolution

**Files:**
- Create: `backend/app/clients/__init__.py`
- Create: `backend/app/clients/drug_sources.py`
- Create: `backend/app/models.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/drugs.py`
- Modify: `backend/app/main.py`
- Modify: `ingestion/drug_client.py`
- Test: `tests/test_drug_client.py`, `tests/test_api.py`

**Interfaces:**
- Produces: `resolve_drug(name: str, label_limit: int = 5) -> ResolvedDrug`
- Produces: typed upstream exceptions for not-found, timeout, and dependency failure
- Consumes: RxNorm/openFDA HTTP APIs

- [ ] Write tests for escaped search input, multi-fragment fields, timeout/error mapping, and one-resolution-per-drug behavior.
- [ ] Implement typed models for FDA label provenance and resolved medications.
- [ ] Implement reusable RxNorm/openFDA client functions with explicit timeout/error behavior.
- [ ] Implement `resolve_drug` so labels/substances/interaction text are fetched once and reused.
- [ ] Update lookup endpoint to use the service and return accurate retrieved-label metadata.
- [ ] Run focused tests, then the full suite.
- [ ] Commit backend resolution refactor.

### Task 3: Safe interaction evidence model

**Files:**
- Create: `backend/app/services/interactions.py`
- Modify: `backend/app/models.py`
- Modify: `backend/app/main.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: `ResolvedDrug` from Task 2
- Produces: interaction evidence with `evidence_type`, `source_drug`, `matched_term`, and `excerpt`

- [ ] Write failing tests for duplicate input normalization, mention evidence, caution-language evidence, and neutral no-match wording.
- [ ] Implement pairwise evidence detection without the term `severity`.
- [ ] Ensure missing matches return explicit limitation text and never a safety claim.
- [ ] Update `/api/interactions` response model and endpoint.
- [ ] Run focused and full tests.
- [ ] Commit interaction semantics changes.

### Task 4: Accessible clinical-reference HTML structure

**Files:**
- Modify: `frontend/index.html`

**Interfaces:**
- Consumes: existing backend endpoints
- Produces: semantic tabs, labeled search, source disclosure, document-style result containers, accessible interaction form

- [ ] Replace centered demo header with a compact reference-app header.
- [ ] Implement semantic tablist/tab controls with associated panels.
- [ ] Add labeled search and live status/error regions.
- [ ] Add drug result header, provenance selector, desktop section navigation, and document content region.
- [ ] Rename the interaction surface to "Interaction Scan" and add a visible limitation note.
- [ ] Keep IDs stable where practical for JS wiring.
- [ ] Commit accessible HTML structure.

### Task 5: Safe frontend rendering and interaction behavior

**Files:**
- Modify: `frontend/app.js`

**Interfaces:**
- Consumes: Task 3 API response
- Produces: DOM rendering without remote-string `innerHTML`; keyboard-friendly tabs, label selection, section navigation, and interaction rows

- [ ] Add a small DOM helper layer that creates elements and assigns remote strings via `textContent`.
- [ ] Replace remote-data template interpolation in drug results.
- [ ] Replace remote-data template interpolation in interaction results.
- [ ] Implement proper tab keyboard behavior and `aria-selected`.
- [ ] Implement label selector behavior and section navigation.
- [ ] Deduplicate interaction inputs client-side before request.
- [ ] Add loading/status behavior using `aria-busy` and live regions.
- [ ] Verify no remote API string is assigned through `innerHTML`.
- [ ] Commit frontend behavior refactor.

### Task 6: GPT Taste clinical visual system

**Files:**
- Modify: `frontend/style.css`

**Interfaces:**
- Consumes: Task 4 semantic markup
- Produces: responsive visual design for 320px, 768px, 1024px, and 1440px widths

- [ ] Replace dark navy/purple/glow palette with cool off-white, white, ink/slate, and single clinical-blue accent.
- [ ] Replace Inter-first styling with a more intentional neutral sans stack and system fallbacks without requiring a JS framework.
- [ ] Build desktop reference-document layout with sticky section index and readable content column.
- [ ] Create restrained source/provenance treatments instead of horizontal label cards.
- [ ] Design neutral, caution, and evidence states that do not rely on color alone.
- [ ] Add consistent `:focus-visible` styles and minimum touch targets.
- [ ] Add skeleton loading and `prefers-reduced-motion` handling.
- [ ] Add mobile collapse rules with no horizontal overflow.
- [ ] Run the Taste/UI-engineering pre-flight checklist against the finished CSS.
- [ ] Commit clinical UI redesign.

### Task 7: Documentation and CI

**Files:**
- Modify: `README.md`
- Create: `.github/workflows/tests.yml`

**Interfaces:**
- Consumes: final app behavior
- Produces: accurate project documentation and automated regression testing

- [ ] Update clone URL and project structure.
- [ ] Replace "interaction checker/severity" claims with accurate label-scan language.
- [ ] Document retrieved-label limit and data-source limitations.
- [ ] Remove references to nonexistent files/directories.
- [ ] Add GitHub Actions workflow for Python tests.
- [ ] Run the full test suite.
- [ ] Commit docs and CI.

### Task 8: Final verification and PR

**Files:**
- Review all changed files.

**Interfaces:**
- Consumes: Tasks 1-7
- Produces: reviewable draft pull request

- [ ] Run `pytest -q`.
- [ ] Run Python syntax compilation for backend/ingestion.
- [ ] Search frontend JS for unsafe remote-data `innerHTML` usage.
- [ ] Check git diff for accidental scope creep or stale README claims.
- [ ] Compare branch against `main`.
- [ ] Open a draft PR summarizing safety, backend, accessibility, and visual changes.
