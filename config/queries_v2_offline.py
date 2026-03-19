"""
Parallel non-Anthropic query config for the March 2026 expansion.

This file is intentionally separate from config/queries.py so the original
Anthropic-based pipeline remains unchanged.

Scope for this parallel workflow:
- all healthcare AI, not just generative AI / LLMs
- clinical, patient-facing, and administrative healthcare tasks
- explicit human comparison arm or human-performance benchmark
- four retrieval lanes: diagnosis_reasoning_v3_core, patient_facing_core, admin_core, supplemental_benchmark_implementation
"""

QUERY_VERSION = "v2_offline_20260331"

DATE_START = "2022/01/01"
DATE_END = "2026/03/31"

# I conducted an experiment on false-positive rates for terms on PubMed and
# the rate was decently high, would recommend adding as a step, can share my notebook

AI_TERMS = [
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "neural network",
    "foundation model",
    "computer vision",
    "natural language processing",
    "large language model",
    "LLM",
    "generative artificial intelligence",
    "generative AI",
    "ChatGPT",
    "GPT",
    "Claude",
    "Gemini",
    "Llama",
    "DeepSeek",
    "PaLM",
    "Bard",
]

CLINICAL_TASK_TERMS = [
    "diagnosis",
    "diagnostic",
    "triage",
    "clinical decision",
    "differential diagnosis",
    "clinical reasoning",
    "treatment decision",
    "management decision",
    "risk prediction",
    "prognosis",
    "vignette",
    "imaging interpretation",
    "report generation",
    "documentation",
    "clinical workflow",
    "inbox management",
    "prior authorization",
    "billing",
    "coding",
    "scheduling",
    "administrative workflow",
]

DIAGNOSIS_REASONING_V3_TERMS = [
    "diagnosis",
    "diagnostic",
    "triage",
    "acuity assessment",
    "urgency assessment",
    "escalation",
    "clinical decision",
    "differential diagnosis",
    "clinical reasoning",
    "treatment decision",
    "management decision",
    "therapy selection",
    "treatment planning",
    "risk prediction",
    "prognosis",
    "monitoring",
    "deterioration detection",
    "early warning",
    "imaging interpretation",
    "laboratory interpretation",
    "pathology interpretation",
    "ecg interpretation",
    "report generation",
]

PATIENT_FACING_TERMS = [
    "patient communication",
    "patient education",
    "discharge instructions",
    "discharge support",
    "care navigation",
    "care coordination",
    "care transitions",
    "handoff",
    "symptom checker",
    "self-management",
    "health guidance",
    "patient portal",
    "shared decision-making",
    "medication instructions",
    "follow-up recommendations",
]

PHYSICIAN_TERMS = [
    "physician",
    "clinician",
    "doctor",
    "radiologist",
    "surgeon",
    "nurse",
    "advanced practice provider",
    "healthcare worker",
    "staff",
    "compared to physician",
    "compared to clinician",
    "compared to human",
    "physician performance",
    "human performance",
    "human-AI",
    "AI-assisted",
    "physician augment",
    "clinician augment",

    # include residents?
    "residents",

    # Ran a screening experiment on PubMed only with two runs of (generic terms) vs.
    # (generic terms + specialty ABMS (US/UK variants)) and additional 30% of corpus was captured.
    # Papers found were in radiology, orthopedic, ophthalmology, urology, pathology, etc.
    # Including the list here if useful

    # Imaging / diagnostics
    "radiographer",
    "pathologist",
    "ophthalmologist",
    "dermatologist",
    "endoscopist",

    # Internal medicine / subspecialties
    "oncologist",
    "cardiologist",
    "neurologist",
    "gastroenterologist",
    "rheumatologist",
    "intensivist",
    "hospitalist",
    "internist",
    "endocrinologist",
    "hematologist",
    "haematologist",
    "nephrologist",
    "pulmonologist",
    "respirologist",
    "allergist",
    "immunologist",
    "hepatologist",
    "neonatologist",

    # Surgery / procedural
    "urologist",
    "otolaryngologist",
    "orthopedic",
    "orthopaedic",
    "neurosurgeon",
    "obstetrician",
    "gynecologist",
    "gynaecologist",

    # Primary care / anaesthesia
    "general practitioner",
    "anesthesiologist",
    "anaesthesiologist",
    "anaesthetist",

    # Mental health / paediatrics / rehab / geriatrics
    "psychiatrist",
    "pediatrician",
    "paediatrician",
    "physiatrist",
    "geriatrician",
    "epileptologist",
    "perinatologist",
    "urogynecologist",
]

COMPARISON_TERMS = [
    "compared",
    "comparison",
    "versus",
    "vs",
    "benchmark",
    "head-to-head",
    "reader study",
    "human performance",
    "physician performance",
    "clinician performance",
]


def _or_join(terms: list[str]) -> str:
    return " OR ".join(f'"{t}"' for t in terms)

SUPPLEMENTAL_TERMS = [
    "implementation",
    "real-world",
    "deployed",
    "workflow",
    "assistance",
    "assisted",
    "assistant",
    "collaborative",
    "collaboration",
    "teammate",
    "decision support",
    "clinical implementation",
    "reader study",
    "randomized",
    "trial",
    "diagnostic reasoning",
    "reasoning tasks",
    "complex care",
    "multireader",
    "human expertise",
]

SUPPLEMENTAL_COMPARATOR_QUERY = _or_join([
    "physician",
    "clinician",
    "doctor",
    "radiologist",
    "surgeon",
    "nurse",
    "staff",
    "expert",
    "specialist",
    "practitioner",
    "human performance",
    "physician performance",
    "clinician performance",
    "human expertise",
    "collaborative workflow",
    "human-ai collaboration",
    "ai-assisted",
])

METRIC_TERMS = [
    "accuracy",
    "auc",
    "auroc",
    "sensitivity",
    "specificity",
    "f1",
    "precision",
    "recall",
]


def pubmed_query() -> str:
    ai = " OR ".join(f'"{t}"' for t in AI_TERMS)
    task = " OR ".join(f'"{t}"' for t in CLINICAL_TASK_TERMS)
    physician = " OR ".join(f'"{t}"' for t in PHYSICIAN_TERMS)
    comparison = " OR ".join(f'"{t}"' for t in COMPARISON_TERMS)
    return (
        f"({ai}) AND ({task}) AND ({physician}) AND ({comparison})"
        f" AND humans[MeSH Terms]"
        f" NOT (review[Publication Type] OR meta-analysis[Publication Type]"
        f" OR editorial[Publication Type] OR letter[Publication Type]"
        f" OR comment[Publication Type])"
    )


CORE_AI_QUERY = _or_join(AI_TERMS)
CLINICAL_TASK_QUERY = _or_join([
    "diagnosis",
    "diagnostic",
    "triage",
    "clinical decision",
    "differential diagnosis",
    "clinical reasoning",
    "treatment decision",
    "management decision",
    "risk prediction",
    "prognosis",
    "imaging interpretation",
    "report generation",
])
ADMIN_TASK_QUERY = _or_join([
    "documentation",
    "clinical workflow",
    "inbox management",
    "prior authorization",
    "billing",
    "coding",
    "scheduling",
    "administrative workflow",
    "resource allocation",
    "capacity management",
    "staffing",
    "bed management",
    "throughput",
])
HEALTHCARE_COMPARATOR_QUERY = _or_join([
    "physician",
    "clinician",
    "doctor",
    "radiologist",
    "surgeon",
    "nurse",
    "advanced practice provider",
    "healthcare worker",
    "staff",
    "reader study",
    "human performance",
    "physician performance",
    "clinician performance",
])
STUDY_DESIGN_QUERY = _or_join([
    "accuracy",
    "performance",
    "evaluation",
    "validated",
    "validation",
    "benchmark",
    "reader study",
])
COMPARISON_QUERY = _or_join([
    "compared",
    "comparison",
    "versus",
    "vs",
    "head-to-head",
    "against",
    "human performance",
    "physician performance",
    "clinician performance",
])
SUPPLEMENTAL_QUERY = _or_join(SUPPLEMENTAL_TERMS)


PUBMED_LANE_QUERIES = {
    "diagnosis_reasoning_v3_core": (
        f"({CORE_AI_QUERY}) AND ({_or_join(DIAGNOSIS_REASONING_V3_TERMS)}) AND ({HEALTHCARE_COMPARATOR_QUERY}) "
        f"AND ({STUDY_DESIGN_QUERY}) AND ({COMPARISON_QUERY})"
        f" AND humans[MeSH Terms]"
        f" NOT (review[Publication Type] OR meta-analysis[Publication Type]"
        f" OR editorial[Publication Type] OR letter[Publication Type]"
        f" OR comment[Publication Type])"
    ),
    "patient_facing_core": (
        f"({CORE_AI_QUERY}) AND ({_or_join(PATIENT_FACING_TERMS)}) AND ({HEALTHCARE_COMPARATOR_QUERY}) "
        f"AND ({STUDY_DESIGN_QUERY}) AND ({COMPARISON_QUERY})"
        f" AND humans[MeSH Terms]"
        f" NOT (review[Publication Type] OR meta-analysis[Publication Type]"
        f" OR editorial[Publication Type] OR letter[Publication Type]"
        f" OR comment[Publication Type])"
    ),
    "admin_core": (
        f"({CORE_AI_QUERY}) AND ({ADMIN_TASK_QUERY}) AND ({HEALTHCARE_COMPARATOR_QUERY}) "
        f"AND ({STUDY_DESIGN_QUERY}) AND ({COMPARISON_QUERY})"
        f" AND humans[MeSH Terms]"
        f" NOT (review[Publication Type] OR meta-analysis[Publication Type]"
        f" OR editorial[Publication Type] OR letter[Publication Type]"
        f" OR comment[Publication Type])"
    ),
    "supplemental_benchmark_implementation": (
        f"({CORE_AI_QUERY}) AND (({CLINICAL_TASK_QUERY}) OR ({ADMIN_TASK_QUERY}) OR ({_or_join(PATIENT_FACING_TERMS)})) AND ({SUPPLEMENTAL_COMPARATOR_QUERY}) "
        f"AND ({SUPPLEMENTAL_QUERY})"
        f" AND humans[MeSH Terms]"
        f" NOT (review[Publication Type] OR meta-analysis[Publication Type]"
        f" OR editorial[Publication Type] OR letter[Publication Type]"
        f" OR comment[Publication Type])"
    ),
}


MEDRXIV_LANE_QUERIES = {
    "diagnosis_reasoning_v3_core": (
        f"({CORE_AI_QUERY}) AND ({_or_join(DIAGNOSIS_REASONING_V3_TERMS)}) AND ({HEALTHCARE_COMPARATOR_QUERY}) "
        f"AND ({STUDY_DESIGN_QUERY}) AND ({COMPARISON_QUERY})"
    ),
    "patient_facing_core": (
        f"({CORE_AI_QUERY}) AND ({_or_join(PATIENT_FACING_TERMS)}) AND ({HEALTHCARE_COMPARATOR_QUERY}) "
        f"AND ({STUDY_DESIGN_QUERY}) AND ({COMPARISON_QUERY})"
    ),
    "admin_core": (
        f"({CORE_AI_QUERY}) AND ({ADMIN_TASK_QUERY}) AND ({HEALTHCARE_COMPARATOR_QUERY}) "
        f"AND ({STUDY_DESIGN_QUERY}) AND ({COMPARISON_QUERY})"
    ),
    "supplemental_benchmark_implementation": (
        f"({CORE_AI_QUERY}) AND (({CLINICAL_TASK_QUERY}) OR ({ADMIN_TASK_QUERY}) OR ({_or_join(PATIENT_FACING_TERMS)})) AND ({SUPPLEMENTAL_COMPARATOR_QUERY}) "
        f"AND ({SUPPLEMENTAL_QUERY})"
    ),
}


SCOPUS_LANE_QUERIES = {
    "diagnosis_reasoning_v3_core": (
        f'TITLE-ABS-KEY(({CORE_AI_QUERY}) AND ({_or_join(DIAGNOSIS_REASONING_V3_TERMS)}) AND ({HEALTHCARE_COMPARATOR_QUERY}) '
        f'AND ({STUDY_DESIGN_QUERY}) AND ({COMPARISON_QUERY})) AND PUBYEAR > 2021 AND PUBYEAR < 2027'
    ),
    "patient_facing_core": (
        f'TITLE-ABS-KEY(({CORE_AI_QUERY}) AND ({_or_join(PATIENT_FACING_TERMS)}) AND ({HEALTHCARE_COMPARATOR_QUERY}) '
        f'AND ({STUDY_DESIGN_QUERY}) AND ({COMPARISON_QUERY})) AND PUBYEAR > 2021 AND PUBYEAR < 2027'
    ),
    "admin_core": (
        f'TITLE-ABS-KEY(({CORE_AI_QUERY}) AND ({ADMIN_TASK_QUERY}) AND ({HEALTHCARE_COMPARATOR_QUERY}) '
        f'AND ({STUDY_DESIGN_QUERY}) AND ({COMPARISON_QUERY})) AND PUBYEAR > 2021 AND PUBYEAR < 2027'
    ),
    "supplemental_benchmark_implementation": (
        f'TITLE-ABS-KEY(({CORE_AI_QUERY}) AND (({CLINICAL_TASK_QUERY}) OR ({ADMIN_TASK_QUERY}) OR ({_or_join(PATIENT_FACING_TERMS)})) AND ({SUPPLEMENTAL_COMPARATOR_QUERY}) '
        f'AND ({SUPPLEMENTAL_QUERY})) AND PUBYEAR > 2021 AND PUBYEAR < 2027'
    ),
}


INCLUSION_CRITERIA = [
    "Primary research study (not review, editorial, comment, or protocol-only paper)",
    "Uses an AI system for a healthcare task, including clinical decision-making and healthcare administrative workflow tasks such as documentation, billing, coding, scheduling, or inbox/workflow management",
    "Includes a human comparison arm or explicit human benchmark, whether the comparison is quantitative or qualitative",
]

EXCLUSION_CRITERIA = [
    "Review article, systematic review, meta-analysis, editorial, comment, perspective",
    "Case report or case series without a comparison group",
    "No human comparison arm",
    "Patient education or communication-only task without a clinician or staff performance comparison",
    "Student or exam-only study with no clinician comparison",
    "Study protocol without reported results",
    "Retracted article",
]
