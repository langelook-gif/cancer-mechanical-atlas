from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Paper:
    pmid: str
    title: str
    abstract: str
    journal: str = ""
    year: Optional[int] = None
    doi: str = ""
    authors: str = ""
    source: str = "PubMed"
    def to_dict(self): return asdict(self)

@dataclass
class Measurement:
    pmid: str
    title: str
    cancer_type: str
    tissue_context: str
    cohort_label: str
    property_name: str
    value: float
    unit: str
    normalized_value: float
    normalized_unit: str
    measurement_method: str = ""
    context_snippet: str = ""
    evidence_level: str = "abstract_extracted"
    extraction_confidence: float = 0.5
    notes: str = ""
    def to_dict(self): return asdict(self)
