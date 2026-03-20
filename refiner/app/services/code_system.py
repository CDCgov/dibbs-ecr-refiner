from enum import StrEnum


class CodeSystem(StrEnum):
    """
    An Enum for code systems.
    """

    LOINC = "LOINC"
    SNOMED = "SNOMED"
    ICD10 = "ICD-10"
    RXNORM = "RxNorm"
    CVX = "CVX"
    OTHER = "Other"

    @classmethod
    def sanitize(cls, value: str) -> "CodeSystem":
        """
        Convert value to a santized name from the CodeSystem.
        """
        if not isinstance(value, str):
            raise ValueError(f"System name provided: {value} is invalid.")

        mapping = {item.value.lower(): item for item in cls}
        sanitized = mapping.get(value.strip().lower())
        if not sanitized:
            raise ValueError(f"System name provided: {value} is invalid.")

        return sanitized


ALLOWED_CUSTOM_CODE_SYSTEMS: set[CodeSystem] = set(CodeSystem)
ALLOWED_CUSTOM_CODE_SYSTEM_NAMES = ", ".join(
    item.value for item in ALLOWED_CUSTOM_CODE_SYSTEMS
)
