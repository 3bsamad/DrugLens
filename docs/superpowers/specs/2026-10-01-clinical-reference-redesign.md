# DrugLens Clinical Reference Redesign

Date: 2026-10-01
Branch: `redesign/clinical-reference-v1`

## Goal

Evolve DrugLens from a prototype medication lookup demo into a trustworthy, source-forward medication reference tool.

The redesign must improve:
- medical-product semantics and user trust
- accessibility and keyboard support
- information architecture and readability
- backend resilience and data reuse
- testability and repository hygiene

The scope intentionally preserves the lightweight architecture: FastAPI backend, vanilla HTML/CSS/JS frontend, RxNorm, and openFDA.

## Product Positioning

DrugLens is an informational evidence browser, not a clinical decision system.

The UI must not imply that:
- absence of a detected interaction means a combination is safe
- DrugLens computes clinically validated interaction severity
- openFDA label retrieval is exhaustive
- a successful lookup is medical advice

### Interaction checker terminology

Rename "Interaction Checker" to "Interaction Scan" or "FDA Label Interaction Scan".

Replace the current severity framing:
- `warning` -> "Caution language detected"
- `mentioned` -> "Mention detected"

Never display a green "safe" state for no match.

For no detected cross-reference, use wording equivalent to:

> No matching interaction language was detected in the FDA labels retrieved. This does not rule out a drug interaction.

Every interaction result must include a visible limitation note.

## Design Direction

### Design read

Trust-first clinical reference application for consumers, students, and healthcare users.

Target design dials:
- Design variance: 3/10
- Motion intensity: 2/10
- Visual density: 5/10

### Visual language

Use a quiet clinical reference aesthetic:
- light mode as the primary theme
- cool off-white page background
- white primary surfaces
- deep ink/navy text
- slate secondary text
- one cobalt/clinical-blue accent
- amber/red only for semantic warning states
- minimal shadows
- no purple gradients or glow effects
- no decorative glassmorphism

Typography:
- use a neutral modern sans such as Geist or IBM Plex Sans
- use a monospace treatment only for identifiers such as RxCUI
- preserve strong hierarchy and readable long-form label text

### Layout

Replace the current centered single-column "card stack" with a reference-document layout.

Desktop:
- top app header with DrugLens identity and source/data context
- primary search
- top-level mode switch for Drug Lookup and Interaction Scan
- drug result header with normalized name, RxCUI, route/type metadata
- compact FDA label selector
- two-column body:
  - sticky left section navigation
  - main content document on the right

Mobile:
- single-column layout
- section navigation becomes a compact dropdown or horizontal control
- full-width primary actions
- no horizontal overflow for core content

## Drug Lookup Experience

### Search

Keep direct medication search.

Improve semantics:
- use a visible text label or accessible label
- use a standard button
- loading state should use a skeleton or contextual status rather than only a spinner
- announce results/errors using `aria-live`

### Drug header

Show:
- queried/canonical medication name
- RxCUI when available
- generic/substance information
- route/product type
- number of FDA label records retrieved

Avoid pill-heavy decoration. Metadata may use restrained inline text or small tags where useful.

### FDA label selector

Replace horizontally scrolling label cards with a compact label selector.

Each option should expose as much provenance as available:
- brand/generic name
- manufacturer
- route
- effective date
- application or SPL identifiers where available

The selected label's provenance should remain visible above its content.

### Label sections

Display content as a readable document rather than hiding all sections in accordions.

Suggested order:
1. Overview / active ingredients
2. Indications & usage
3. Dosage & administration
4. Warnings
5. Contraindications
6. Adverse reactions
7. Ask doctor / pharmacist
8. Stop use
9. Pregnancy / breastfeeding
10. Description

Only show sections that exist.

On desktop, the left-side index scrolls to sections.
On mobile, use a compact section navigator.

## Interaction Scan Experience

### Input

Use a medication composer rather than visually repetitive form rows.

For the initial implementation, existing text inputs may remain under the hood but should be styled and structured as a cohesive medication list.

Requirements:
- minimum 2 drugs, maximum 6
- reject/deduplicate duplicate entries
- preserve keyboard usability
- clearly expose add/remove controls
- avoid implying medication identity certainty when free text has not been normalized

### Results

For each drug pair:
- show pair names
- show detected FDA-label evidence, if any
- show evidence source/drug label
- distinguish "mention detected" and "caution language detected"
- do not claim clinical severity

No-match result:
- neutral visual treatment, never success-green
- explicitly state that no matching language was detected in retrieved labels
- explicitly state that this does not rule out an interaction

## Accessibility

Meet WCAG 2.1 AA expectations.

Required changes:
- interactive elements must be native buttons/inputs/links where possible
- clickable label cards, hints, and disclosure headers must not remain mouse-only `div`/`span` controls
- top-level mode switch must use semantic tabs or equivalent accessible navigation
- disclosures must expose `aria-expanded`
- dynamic status/result regions use `aria-live` or `role=status`
- strong `:focus-visible` states
- color must not be the sole state indicator
- add `prefers-reduced-motion` handling
- test at 320px, 768px, 1024px, and 1440px

## Frontend Security

Remote FDA/RxNorm data must not be interpolated directly into `innerHTML`.

Use:
- `textContent`
- DOM construction
- tightly controlled static markup

Only static, developer-authored SVG/icon markup may be inserted as markup.

## Backend Architecture

Keep FastAPI and split responsibilities enough to prevent `main.py` from becoming a monolith.

Target structure:

```
backend/
  app/
    main.py
    models.py
    routes/
      drugs.py
      interactions.py
    services/
      drug_service.py
      interaction_service.py
    clients/
      openfda.py
      rxnorm.py
```

This may be introduced incrementally if a smaller refactor achieves the same boundaries.

### Resolved medication data

Avoid repeated API calls by resolving each requested drug once into a reusable internal structure containing:
- normalized query/name
- RxCUI
- labels
- substances
- interaction text/evidence

Reuse that object throughout an interaction request.

### Upstream resilience

Distinguish:
- medication not found
- openFDA returned no results
- RxNorm unavailable
- openFDA unavailable
- timeout
- malformed upstream response

Map dependency failures to appropriate 502/503 responses rather than presenting them as medication absence.

Keep explicit HTTP timeouts.

### Search/query handling

Escape or safely construct openFDA search expressions from user input.

Deduplicate medications before interaction comparison.

### FDA field extraction

Do not silently discard useful repeated section fragments when fields contain arrays.
Combine relevant field text where appropriate.

### Interaction evidence

The backend must represent heuristic evidence, not clinical severity.

Suggested model:
- pair
- evidence_type: `mention` | `caution_language`
- source_drug
- matched_term
- excerpt
- label provenance when available

The keyword heuristic can remain for V1 if clearly labeled as such.

## Repository Hygiene

Add:
- non-empty `.gitignore`
- reproducible dependencies via `requirements.txt` or `pyproject.toml`
- `LICENSE` file matching README claim
- test directory
- GitHub Actions workflow for tests

Fix README:
- actual clone URL
- remove references to nonexistent files/directories
- accurately describe the 5-label retrieval limit
- accurately describe interaction scanning limitations
- update screenshots after redesign

## Testing

### Backend unit tests

Cover:
- `clean_field`
- FDA field extraction
- interaction evidence detection
- duplicate medication handling
- max/min drug validation
- no-label behavior
- upstream timeout/error mapping

Mock network calls.

### API tests

Cover:
- `/health`
- successful drug lookup
- 404 drug lookup
- interaction scan with evidence
- interaction scan without evidence
- invalid input count
- upstream dependency failure

### Frontend verification

At minimum:
- tab/mode navigation works by keyboard
- search via click and Enter
- interaction add/remove works
- loading, error, and empty/no-match states render
- no remote text is injected as HTML
- responsive layout verified at target widths

## Non-Goals For This Redesign

Do not add yet:
- authentication
- personal medicine cabinet
- pill identifier
- adverse-event charts
- recall monitoring
- LLM-generated summaries
- React/Next.js migration
- database persistence

These can be separate follow-up features after the reference experience is solid.

## Implementation Order

1. Add tests around current backend behavior.
2. Refactor upstream clients and reusable resolved-drug data flow.
3. Replace clinical-sounding interaction severity/safe semantics.
4. Fix remote-data HTML injection.
5. Implement accessible frontend structure.
6. Apply the new clinical reference visual system and responsive layout.
7. Add repository hygiene files and CI.
8. Update README and screenshots.
9. Run backend tests and frontend smoke verification.
10. Open a draft PR with the full redesign for review.

## Acceptance Criteria

The redesign is complete when:
- no UI state claims or visually implies medication safety from a missing text match
- interaction evidence is clearly labeled heuristic/label-derived
- remote API strings are not rendered through unsafe `innerHTML`
- core controls are keyboard accessible
- frontend works at mobile and desktop widths
- repeated upstream requests are reduced
- upstream failures are distinguishable from valid "not found"
- tests cover the core backend flows
- README accurately describes implementation and limitations
- CI is present and passing
