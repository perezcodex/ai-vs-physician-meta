"""
Versioned search queries for the AI-vs-physician meta-analysis.
Never edit a version that has already been used for a search run.
To change: add a new version key.
"""

QUERY_VERSION = "v1"

# ── Date range ────────────────────────────────────────────────────────────────
# Matching Chen et al. (Nature Medicine 2026) start date for comparability.
# End: September 2025 matches Chen's corpus end; update when rerunning.
DATE_START = "2022/01/01"
DATE_END   = "2025/09/30"

# ── Core AI terms ─────────────────────────────────────────────────────────────
AI_TERMS = [
    # Catch-all terms — will capture any LLM-based study regardless of model name
    "large language model",
    "LLM",
    "generative artificial intelligence",
    "generative AI",
    # Major clinically-deployed model families
    "ChatGPT",      # covers most GPT-based studies by brand name (top term in Chen et al.)
    "GPT",          # covers GPT-3, GPT-3.5, GPT-4, GPT-4o without ChatGPT branding
    "Claude",       # Anthropic
    "Gemini",       # Google
    "Llama",        # Meta — widely used in research
    "DeepSeek",     # Rapid growth in clinical studies (132 in Chen et al.)
    "PaLM",         # Google (earlier generation)
    "Bard",         # Google (earlier generation, some legacy studies)
    # Removed: Mistral, Mixtral, Meditron, MedAlpaca, Prometheus
    # Rationale: each had ≤1-2 physician-comparison studies in Takita's full corpus;
    # catch-all terms above will still surface any relevant studies using these models
]

# ── Diagnostic task terms ──────────────────────────────────────────────────────
# "quiz" and "examination" removed: board-exam/noise terms that add irrelevant results;
# our physician filter at screening stage handles any edge cases
DIAGNOSTIC_TERMS = [
    "diagnosis",
    "diagnostic",
    "triage",
    "clinical decision",
    "differential diagnosis",
    "clinical reasoning",
    "vignette",
]

# ── Physician comparison terms (our key inclusion criterion) ──────────────────
PHYSICIAN_TERMS = [
    "physician",
    "clinician",
    "doctor",
    "radiologist",
    "compared to physician",
    "physician performance",
    "human performance",
    "human-AI",
    "AI-assisted",
    "physician augment",
    "clinician augment",
]

# ── PubMed query string ────────────────────────────────────────────────────────
def pubmed_query() -> str:
    ai = " OR ".join(f'"{t}"' for t in AI_TERMS)
    dx = " OR ".join(f'"{t}"' for t in DIAGNOSTIC_TERMS)
    ph = " OR ".join(f'"{t}"' for t in PHYSICIAN_TERMS)
    # humans[MeSH Terms]: keeps only studies on human subjects (removes animal, in-vitro)
    # NOT filter: removes reviews, meta-analyses, editorials, letters at query stage
    return (
        f"({ai}) AND ({dx}) AND ({ph})"
        f" AND humans[MeSH Terms]"
        f" NOT (review[Publication Type] OR meta-analysis[Publication Type]"
        f" OR editorial[Publication Type] OR letter[Publication Type]"
        f" OR comment[Publication Type])"
    )


# ── medRxiv / arXiv free-text query ───────────────────────────────────────────
# Simpler term set — these APIs use basic keyword matching
MEDRXIV_QUERY = (
    "(large language model OR LLM OR ChatGPT OR GPT OR generative AI OR Claude OR Gemini OR Llama OR DeepSeek) "
    "AND (diagnosis OR diagnostic OR triage OR clinical decision) "
    "AND (physician OR clinician OR doctor OR human performance OR human-AI)"
)

ARXIV_QUERY = (
    "large language model diagnosis physician"
)

# ── Inclusion / exclusion criteria (for screener prompt) ──────────────────────
INCLUSION_CRITERIA = [
    "Primary research study (not review, editorial, comment, case report)",
    "Uses a generative AI model (LLM) for a diagnostic or triage task",
    "Reports diagnostic accuracy (accuracy, AUC, sensitivity, specificity, or F1)",
    "Includes at least one comparison arm involving a human clinician/physician",
]

EXCLUSION_CRITERIA = [
    "Review article, systematic review, meta-analysis, editorial, comment",
    "Case report or case series without comparison group",
    "No diagnostic accuracy metric reported",
    "No human physician comparison arm",
    "Uses AI only for administrative tasks (coding, documentation, scheduling)",
    "Study about examination questions / medical students only",
    "Study protocol without results",
    "Retracted article",
]
