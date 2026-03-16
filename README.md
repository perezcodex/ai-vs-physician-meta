# AI vs. Physician Meta-Analysis Pipeline

A systematic review pipeline for identifying and extracting AI-vs-human performance comparisons across healthcare tasks (2022–2026).

---

## What this is

This repo contains the search, screening, and extraction pipeline for a meta-analysis comparing AI system performance to physician and clinician performance across clinical and administrative healthcare tasks.

The current version (v2) is an expanded offline workflow that does not depend on a model API. A model-based re-screening pass is planned (see [Known Limitations](#known-limitations)).

---

## Search methodology

### Sources

- **PubMed** — via NCBI E-utilities API
- **medRxiv** — via Europe PMC API
- **Scopus** — via API or manual CSV export

### Date range

January 2022 – March 2026

### Retrieval lanes

Search is structured across four independent lanes to ensure broad coverage across clinical and administrative task types:

| Lane | Focus |
|---|---|
| `diagnosis_reasoning_v3_core` | Diagnostic reasoning, triage, clinical decision-making, imaging/lab interpretation, risk prediction |
| `patient_facing_core` | Patient communication, education, care navigation, symptom checking, shared decision-making |
| `admin_core` | Documentation, billing, coding, scheduling, inbox management, prior authorization |
| `supplemental_benchmark_implementation` | Deployment studies, reader studies, RCTs, human-AI collaboration, benchmarking in real-world settings |

The first three lanes are the primary analytic corpora. The supplemental lane is a recall safeguard for implementation and collaborative-workflow studies that may not surface cleanly in task-specific queries.

### Scope

The v2 search is broader than the original pipeline. It includes:

- All healthcare AI — not just LLMs or generative AI
- Classical ML, deep learning, predictive models, and computer vision
- Clinical tasks: diagnosis, triage, treatment/management decisions, prognosis, imaging interpretation
- Administrative tasks: documentation, coding, billing, scheduling, inbox management
- Any study with an explicit human comparison arm or human-performance benchmark, whether quantitative or qualitative

### Inclusion criteria

1. Primary research study (not a review, editorial, comment, or protocol-only paper)
2. Uses an AI system for a healthcare task, including clinical decision-making and administrative workflow tasks
3. Includes a human comparison arm or explicit human benchmark

### Exclusion criteria

- Systematic reviews, meta-analyses, editorials, commentaries
- Case reports or case series without a comparison group
- No human comparison arm
- Student or exam-only studies with no clinician comparison
- Study protocols without reported results
- Retracted articles

---

## Screening methodology

### Current approach: rule-based

The v2 screener (`src/screen_offline_v2.py`) is rule-based and does not call a model API. For each title and abstract it checks for four signals:

- **AI signal** — presence of AI/ML terms (e.g. "machine learning", "LLM", "ChatGPT")
- **Clinical task signal** — presence of healthcare task terms
- **Physician/clinician signal** — presence of comparator terms (e.g. "physician", "radiologist", "nurse")
- **Comparison signal** — explicit comparison language ("versus", "outperformed", "reader study") or assisted-workflow language ("with AI / without AI", "physician-only")

Decision logic:
```
exclusion pattern matched           → exclude
AI + task + physician + comparison  → include
AI + task + partial human signal    → uncertain
otherwise                           → exclude
```

Outputs three files: `included.csv`, `uncertain.csv`, `screened.csv` (all records with decisions).

### Known limitation — planned improvement

**The rule-based screener trades recall for cost.** Because it matches on literal text, it will miss papers that describe a physician comparison using phrasing not in the term lists (e.g. "clinician-level performance was achieved", "non-inferior to attending physicians"). These tend to fall into `uncertain` rather than `include`.

**Planned: re-screen the full deduplicated corpus with Claude Sonnet or better.**

Model-based screening handles semantic variation, infers comparison structure from context, and produces defensible, auditable decisions — which matters for a publishable systematic review. Estimated cost for the full ~8,000–12,000 record corpus is approximately **$40 with Sonnet** or **$10 with Haiku**. The screening prompt and inclusion/exclusion criteria in `config/queries_v2_offline.py` are already structured for direct model use.

Until the model re-screen is run, the `uncertain.csv` output should be treated as requiring human spot-check before final inclusion decisions are made.

---

## Extraction methodology

### Current approach: heuristic + manual batches

The v2 extractor (`src/extract_accuracy_offline_v2.py`) is abstract-based and heuristic. It does not attempt full arm-level extraction. Instead it produces a candidate accuracy table with:

- Guessed AI model
- Guessed metric type (accuracy, AUC, sensitivity, etc.)
- Candidate AI value
- Candidate physician value
- Raw abstract snippet containing the metric
- Manual review priority flag

Manual extraction batches are stored in `src/extract_accuracy_v3_codex.py`. These represent hand-adjudicated comparison arms for high-priority records.

The full adjudication queue is in `data_v2_offline/extracted/`.

### Comparison types preserved

| Type | Description |
|---|---|
| `quantitative_direct` | Paired numeric AI vs. physician values reported |
| `quantitative_partial` | One arm numeric, other inferred or approximate |
| `qualitative_only` | Non-numeric comparison (e.g. "preferred by clinicians") |

---

## How to run

### Prerequisites

```bash
pip install -r requirements.txt
```

Set environment variables as needed:
```bash
SCOPUS_API_KEY=...        # optional — Scopus API access
SCOPUS_INSTTOKEN=...      # optional — institutional token
```

### Run the full v2 offline pipeline

```bash
# With Scopus CSV export
python run_offline_v2.py all --scopus-csv /path/to/scopus_export.csv

# Without Scopus
python run_offline_v2.py search
python run_offline_v2.py deduplicate
python run_offline_v2.py screen
python run_offline_v2.py extract
```

All outputs write to `data_v2_offline/`.

---

## Caveats

- The rule-based screener is more conservative than a model-based screener and will need human spot-checking of `uncertain.csv` before final inclusion decisions
- The heuristic extractor is a candidate-harvesting step, not a final adjudicated arm table — full-text review is still required for final paired accuracy values
- **Scopus has not been run yet** — the current corpus is PubMed + medRxiv only. A test against the Scopus API returned the following result counts for the four lanes: `diagnosis_reasoning_v3_core` 11,811 · `supplemental_benchmark_implementation` 28,824 · `admin_core` 960 · `patient_facing_core` 391 (total ~42,000). This is likely too large to screen without further query refinement or a pre-filter — the supplemental and diagnosis lanes in particular appear to be returning a broad corpus that would include many irrelevant papers. Before running Scopus, the lane queries should be reviewed and tightened, or a per-lane result cap should be applied to pull a manageable sample first. Set `SCOPUS_API_KEY` in `.env` when ready to run
- **Abstract truncation by source** — abstract completeness varies by source and may affect screening quality. PubMed abstracts are pulled via `efetch` XML and are complete, including structured multi-section abstracts. medRxiv abstracts via Europe PMC (`abstractText` field) can be truncated for some preprints depending on how metadata was deposited. Scopus is the most significant concern: the search API returns `dc:description`, which is typically capped at ~250 characters — well short of a full abstract. This means Scopus abstracts as currently retrieved are likely snippets only, and comparison language or numeric values that appear later in the abstract will be invisible to the screener. A fix would require a separate abstract retrieval call to the Scopus abstract endpoint (`/content/abstract/doi/...`) for each record. This should be resolved before running and screening the Scopus corpus
- Cross-lane deduplication reduces overlap between the four retrieval lanes, but some duplicates may remain across source databases
- The original Anthropic-based pipeline (`run.py`) is preserved separately and remains the stronger path for final structured arm-level extraction when API access is available
