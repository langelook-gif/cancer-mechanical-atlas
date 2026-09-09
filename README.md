# Cancer Mechanical Atlas

A research prototype that turns cancer mechanobiology literature into a curated evidence table and **exploratory** cancer-vs-healthy mechanical-response hypotheses.

## What it does
- Searches PubMed with NCBI E-utilities.
- Fetches article metadata and abstracts.
- Extracts candidate Young's modulus, stiffness, cell-size, and nuclear-size measurements.
- Requires human curation before values should be treated as evidence.
- Compares cancer and healthy distributions and estimates overlap.
- Runs a deliberately simplified frequency-response proxy only when enough evidence exists.

## What it does NOT do
It does not identify a treatment frequency, safe ultrasound dose, or clinical protocol. The frequency module is a hypothesis generator. Its default oscillator equation is explicitly a replaceable proxy, not a validated cancer-cell ablation model.

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud
1. Create a GitHub repository and upload this folder.
2. Go to Streamlit Community Cloud.
3. Create an app from the GitHub repository.
4. Use `app.py` as the entrypoint.
5. In Secrets, optionally add:
```toml
NCBI_EMAIL="you@example.com"
NCBI_API_KEY="optional_key"
```
6. Deploy.

## Recommended research sequence
### Phase 1 — GBM only
Build a high-quality evidence set before expanding to other cancers. Search terms should include GBM/glioblastoma plus Young's modulus, AFM, stiffness, cell mechanics, nuclear mechanics, viscoelasticity, normal astrocytes, and healthy brain controls.

For every value, verify: exact sample/cell line, cancer vs healthy/control, method, units, live/fixed state, substrate/culture context, and whether the value is mean/median/range.

### Phase 2 — multiple matched cancers
Add matched cancer/healthy comparisons for breast, pancreatic, lung, melanoma, colorectal, etc. Do not compare a cancer cell to an unrelated healthy cell unless the research question explicitly requires it.

### Phase 3 — production meta-analysis
Replace naive pooling with hierarchical models that account for measurement method, cell line, substrate stiffness, culture system, tissue context, patient/sample source, and study-level effects.

### Phase 4 — validated mechanics
Replace the simplified oscillator proxy in `cma/physics.py` with a literature-validated multi-component model and calibrate it against independent experimental response data.

## Scaling to millions of papers
Streamlit should eventually become only the front end. A production system should use:
- PubMed / PMC / Semantic Scholar harvesting jobs
- worker queue
- PostgreSQL
- object storage for licensed/open full text
- vector retrieval for passages
- human review queue
- versioned parameter sets and model runs
- immutable provenance/audit logs

The key principle is: **every output must be traceable back to evidence.**


## Manually verified GBM starter library

This build ships with a curated starter library of primary/review papers checked manually against PubMed/PMC records. The bundled studies deliberately include both supportive and contradictory evidence.

The app automatically seeds directly verified numeric measurements when the database is first created. New PubMed search hits are **not** auto-marked verified; they enter the review queue instead.

This design is intentional: a trustworthy research platform must preserve negative evidence and must be able to conclude that cancer/healthy mechanical distributions overlap too much to support the hypothesis.
