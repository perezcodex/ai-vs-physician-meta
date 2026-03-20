"""Query config v3 — expanded specialist, AI, and comparison term coverage.

Scope:
- all healthcare AI, not just generative AI / LLMs
- clinical, patient-facing, and administrative healthcare tasks
- explicit human comparison arm or human-performance benchmark
- four retrieval lanes: diagnosis_reasoning_v3_core, patient_facing_core, admin_core, supplemental_benchmark_implementation
"""

QUERY_VERSION = "v3_20260331"

DATE_START = "2022/01/01"
DATE_END = "2026/03/31"

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
    # 1.4: traditional ML and imaging AI terms
    "convolutional neural network",
    "CNN",
    "recurrent neural network",
    "RNN",
    "transformer",
    "random forest",
    "gradient boosting",
    "XGBoost",
    "ensemble model",
    "Med-PaLM",
    "clinical NLP",
    "automated detection",
    "computer-aided detection",
    "computer-aided diagnosis",
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
    # 1.2: adverse event detection
    "adverse event",
    "adverse drug event",
    "medication error",
    "drug interaction",
    "safety alert",
    "pharmacovigilance",
    # 1.2: sepsis and clinical deterioration
    "sepsis prediction",
    "sepsis detection",
    "clinical deterioration",
    "rapid response",
    # 1.2: readmission
    "readmission prediction",
    "readmission risk",
    "hospital readmission",
    "30-day readmission",
    # 1.2: medication safety
    "medication reconciliation",
    "prescription error",
    "dosing",
    "drug-drug interaction",
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
    # 1.2: sepsis / deterioration also belong in this lane
    "sepsis prediction",
    "sepsis detection",
    "clinical deterioration",
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
    # 1.2: patient sentiment and empathy
    "patient satisfaction",
    "empathy",
    "communication quality",
    "response quality",
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
    # 1.1: specialist terms (excludes fellow, consultant, registrar)
    "dermatologist",
    "pathologist",
    "ophthalmologist",
    "cardiologist",
    "gastroenterologist",
    "emergency physician",
    "intensivist",
    "oncologist",
    "anesthesiologist",
    "psychiatrist",
    "nephrologist",
    "pulmonologist",
    "neurologist",
    "primary care physician",
    "general practitioner",
    "attending physician",
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
    # 1.3: non-inferiority and equivalence language
    "non-inferior",
    "non-inferiority",
    "equivalent",
    "equivalence",
    "concordance",
    "agreement",
    "surpassed",
    "exceeded",
    "matched",
    "comparable",
    "no significant difference",
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
    # secondary RQ: physician+AI augmentation terms
    "augmented",
    "unaided",
    "second reader",
    "AI-augmented",
    "with AI",
    "without AI",
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
    # secondary RQ: physician+AI augmentation comparators
    "AI-augmented",
    "augmented clinician",
    "augmented physician",
    "with AI assistance",
    "without AI",
    "unaided physician",
    "unaided clinician",
    # 1.1: specialist terms in supplemental comparator
    "dermatologist",
    "pathologist",
    "ophthalmologist",
    "cardiologist",
    "gastroenterologist",
    "emergency physician",
    "intensivist",
    "oncologist",
    "anesthesiologist",
    "psychiatrist",
    "nephrologist",
    "pulmonologist",
    "neurologist",
    "primary care physician",
    "general practitioner",
    "attending physician",
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
    # 1.2: sepsis / deterioration / readmission in core clinical lane
    "sepsis prediction",
    "sepsis detection",
    "clinical deterioration",
    "readmission prediction",
    "readmission risk",
    "hospital readmission",
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
    # 1.2: quality measures
    "quality measure",
    "quality metric",
    "quality improvement",
    "clinical quality",
    # 1.2: revenue cycle
    "revenue cycle",
    "claims",
    "denial management",
    "reimbursement",
    "charge capture",
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
    # 1.1: specialist terms in comparator query
    "dermatologist",
    "pathologist",
    "ophthalmologist",
    "cardiologist",
    "gastroenterologist",
    "emergency physician",
    "intensivist",
    "oncologist",
    "anesthesiologist",
    "psychiatrist",
    "nephrologist",
    "pulmonologist",
    "neurologist",
    "primary care physician",
    "general practitioner",
    "attending physician",
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
    # 1.3: non-inferiority and equivalence language
    "non-inferior",
    "non-inferiority",
    "concordance",
    "agreement",
    "equivalent",
    "comparable",
    "no significant difference",
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
    "Uses an AI system for a healthcare task, including clinical decision-making",
    "Includes a human comparison arm or explicit human benchmark",
]

EXCLUSION_CRITERIA = [
    "Review article, systematic review, meta-analysis, editorial, comment, perspective",
    "Case report or case series without a comparison group",
    "No human comparison arm",
    "Patient education or communication-only task without clinician comparison",
    "Student or exam-only study with no clinician comparison",
    "Study protocol without reported results",
    "Retracted article",
]
