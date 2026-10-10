"""ORM models - re-exports from hexagon domain for backward compat."""
from vaxgenesis.hexagon.domain.entities import (
    Candidate, CandidateStatus, VaccinePlatform,
    Pathogen, PathogenType, Protein,
    Variant, WetLabAssay, AssayStatus,
    Project, Construct, Epitope, EpitopeType,
)
from vaxgenesis.hexagon.domain.value_objects import (
    Sequence, HlaAllele, ConfidenceInterval, UncertaintyScore,
    Mutation, EscapeScore,
)

def load_all_models():
    """Compatibility stub - models are loaded via hexagon domain."""
    pass
