import json
from dataclasses import dataclass

from ..core.exceptions import InputValidationError
from ..db.models import GrouperRow


@dataclass(frozen=True)
class ProcessedGrouper:
    """
    Processed grouper optimized for XML searching.

    Simple structure that takes the codes from a grouper row and
    makes them ready for efficient XML searching.
    """

    condition: str
    display_name: str
    codes: set[str]

    @staticmethod
    def _extract_codes(codes_json: str) -> set[str]:
        """
        Extract valid codes from a JSON string.

        Args:
            codes_json: JSON string containing code objects

        Returns:
            Set of valid codes, empty set if JSON is invalid
        """

        try:
            codes_list = json.loads(codes_json)
            if not isinstance(codes_list, list):
                return set()

            return {
                item["code"]
                for item in codes_list
                if isinstance(item, dict) and "code" in item
            }
        except (json.JSONDecodeError, TypeError, KeyError):
            # TODO: should we add logging here? something to consider in the future
            return set()

    @classmethod
    def from_grouper_row(cls, row: GrouperRow) -> "ProcessedGrouper":
        """
        Create from database row.
        """

        all_codes = set()
        for codes_json in [
            row["loinc_codes"],
            row["snomed_codes"],
            row["icd10_codes"],
            row["rxnorm_codes"],
        ]:
            # use _extract_codes instead of direct json.loads
            all_codes.update(cls._extract_codes(codes_json))

        return cls(
            condition=row["condition"],
            display_name=row["display_name"],
            codes=all_codes,
        )

    def build_xpath(self, search_in: str = "section") -> str:
        """
        Build xpath to find any of our codes in the specified element.
        """

        if not search_in:
            # just validate this since it's a parameter
            raise InputValidationError(
                message="Empty search element specified",
                details={"search_in": search_in},
            )

        if not self.codes:
            return ""

        code_conditions = " or ".join(f'@code="{code}"' for code in self.codes)
        return f"//hl7:{search_in}//hl7:code[{code_conditions}]"
