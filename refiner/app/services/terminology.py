import json
from dataclasses import dataclass

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

    def build_xpath(self) -> str:
        """
        Build XPath to find elements containing any of our codes.

        This XPath search strategy is comprehensive and flexible because it will look in:
          * <observation><code code="code">
          * <observation><value code="code">
          * <manufacturedProduct><code code="code">
          * <act><code code="code">
          * <procedure><code code="code">
          * <translation code="code">
          * etc

        Returns:
            str: XPath expression that finds elements containing matching codes
        """

        if not self.codes:
            return ""

        # create condition for any of our codes
        code_conditions: str = " or ".join(f'@code="{code}"' for code in self.codes)

        # comprehensive but more precise search - find codes in all contexts
        xpath_patterns: list[str] = [
            # elements with matching code children
            f".//hl7:*[hl7:code[{code_conditions}]]",
            # direct code matches
            f".//hl7:code[{code_conditions}]",
            # translation elements
            f".//hl7:translation[{code_conditions}]",
        ]
        return " | ".join(xpath_patterns)
