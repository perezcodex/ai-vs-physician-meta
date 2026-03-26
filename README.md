# AI vs. Physician Meta-Analysis Pipeline

A systematic review pipeline for identifying and extracting AI-vs-human performance comparisons across healthcare tasks (2022–2026).

---

## What this is

This repo contains the search, screening, and extraction pipeline for a meta-analysis comparing AI system performance to physician and clinician performance across clinical and administrative healthcare tasks.

The current version (v3) uses Claude Sonnet 4.6 via the Anthropic Batches API for screening. The v2 rule-based screener is preserved for reference.

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

A study is included if it directly addresses either of the following research questions with measurable outcomes:

1. **Primary RQ** — AI vs. physician/clinician head-to-head comparison (AI alone vs. physician alone)
2. **Secondary RQ** — Physician+AI vs. AI alone comparison (does AI assistance improve on AI alone?)
3. Three-arm studies covering AI, physician, and physician+AI conditions qualify under both RQs

### Exclusion criteria

- Systematic reviews, meta-analyses, review articles, editorials, commentaries, letters to the editor
- Study protocols or pre-registrations without reported results
- Case reports or case series without a comparison group
- No human comparison arm or human benchmark
- Compares AI only to medical students, board exams, or multiple-choice benchmarks with no clinician arm
- Retracted articles

---

## Screening methodology

### Current approach: Claude Sonnet 4.6 (v3)

The v3 screener (`src/screen_claude.py`) uses **Claude Sonnet 4.6 via the Anthropic Batches API** (50% cost reduction vs. standard API). Each title and abstract is evaluated against the inclusion/exclusion criteria above and classified as `include`, `uncertain`, or `exclude`.

Additional fields extracted per paper:
- `physician_type` — `medical_student` | `resident` | `attending` | `specialist_attending` | `mixed` | `not_specified`
- `ai_models` — semicolon-separated list of named AI systems mentioned
- `arm_ai_alone`, `arm_physician_alone`, `arm_physician_plus_ai` — boolean flags for study design

The screener uses 5 few-shot examples drawn from manually reviewed papers to calibrate borderline cases.

Outputs three files per lane: `included.csv`, `uncertain.csv`, `screened.csv` (all records with decisions).

### Corpus status (v3, as of March 2026)

| Lane | Screened | Included | Uncertain | Excluded |
|---|---|---|---|---|
| `diagnosis_reasoning_v3_core` | 4,698 | 1,222 | 177 | 3,299 |
| `admin_core` | 1,412 | 105 | 24 | 1,283 |
| `patient_facing_core` | 405 | 65 | 4 | 336 |
| `supplemental_benchmark_implementation` | 9,403 | 1,559 | 295 | 7,549 |
| **Total** | **15,918** | **2,951** | **500** | **12,467** |

### Human validation (in progress)

Two parallel validation processes are underway:
1. **Screener validation** — 100 papers (30 includes + 70 excludes, stratified by lane) reviewed independently by three human raters to assess screener accuracy and report inter-rater agreement (kappa).
2. **Uncertain adjudication** — the 500 uncertain papers will be split across three reviewers after calibration on a shared set.

### Legacy: rule-based screener (v2)

The original v2 screener (`src/screen_offline_v2.py`) is preserved for reference. It was rule-based and did not call a model API — it matched on keyword signals and was more conservative, leading to higher uncertain rates and lower recall.

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

- The v3 Sonnet screener produces 500 uncertain papers (3.1% of corpus) requiring human adjudication before final inclusion decisions
- The heuristic extractor is a candidate-harvesting step, not a final adjudicated arm table — full-text review is still required for final paired accuracy values
- **Scopus has not been run yet** — the current corpus is PubMed + medRxiv only. A test against the Scopus API returned the following result counts for the four lanes: `diagnosis_reasoning_v3_core` 11,811 · `supplemental_benchmark_implementation` 28,824 · `admin_core` 960 · `patient_facing_core` 391 (total ~42,000). This is likely too large to screen without further query refinement or a pre-filter — the supplemental and diagnosis lanes in particular appear to be returning a broad corpus that would include many irrelevant papers. Before running Scopus, the lane queries should be reviewed and tightened, or a per-lane result cap should be applied to pull a manageable sample first. Set `SCOPUS_API_KEY` in `.env` when ready to run
- **Abstract truncation by source** — abstract completeness varies by source and may affect screening quality. PubMed abstracts are pulled via `efetch` XML and are fully captured, including all labeled sections of structured abstracts (Background, Methods, **Results**, Conclusions) — the Results section, where AI vs. physician comparison language and numeric values typically appear, is reliably present. medRxiv abstracts via Europe PMC (`abstractText` field) can be truncated for some preprints depending on how metadata was deposited; this is particularly harmful because truncation tends to cut off before the Results section, which is where the most screening-relevant content lives. Scopus is the most significant concern: the search API returns `dc:description`, which is typically capped at ~250 characters — well short of a full abstract, and almost certainly before any Results content. This means Scopus abstracts as currently retrieved are likely snippets only, and comparison language or numeric values will be invisible to the screener. A fix would require a separate abstract retrieval call to the Scopus abstract endpoint (`/content/abstract/doi/...`) for each record. This should be resolved before running and screening the Scopus corpus
- Cross-lane deduplication reduces overlap between the four retrieval lanes, but some duplicates may remain across source databases
- The original Anthropic-based pipeline (`run.py`) is preserved separately and remains the stronger path for final structured arm-level extraction when API access is available
