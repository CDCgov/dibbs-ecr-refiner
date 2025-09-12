import json
from dataclasses import dataclass

from ..db.conditions.model import DbCondition
from ..db.configurations.model import DbConfiguration
from ..db.models import GrouperRow


@dataclass
class Configuration:
    """
    Model representing the configuration data needed for refinement.

    This model is intentionally minimal to support both inline testing (from configuration building)
    and independent testing (from demo.py processing) patterns. The model focuses on just the
    essential data needed for refinement:

    - DbCondition list: Contains all conditions to be considered, including the primary condition
    - DbConfiguration: Contains configuration-specific data like custom codes (local_codes TBD)

    Note on Testing Patterns:
    - Independent testing: Uses RC SNOMED codes from the RR's coded information organizer to find
      the matching configuration. The RC SNOMED code comes from the RR, not the configuration itself.
    - Inline testing: Directly uses a configuration to test against input data, focusing only on
      the codes defined in that configuration.

    Future Considerations:
    - Additional metadata may be needed depending on testing pattern requirements
    - Wrapper functions may be needed to handle the different testing patterns
    - sections_to_include may be added for more granular section control
    """

    conditions: list["DbCondition"]
    configuration: "DbConfiguration"


@dataclass
class ProcessedConfiguration:
    """
    Represents the minimal configuration needed for refining eICRs.

    This model is purposely focused on just the essential data needed for both inline
    and independent testing patterns:

    - Inline testing: Running a configuration against test data and only looking for
      that Configuration's codes
    - Independent testing: Reading XML, extracting unique RC SNOMED codes, finding
      configurations via child_rsg_snomed_codes, then using condition_id to get
      included_conditions

    Note: While ProcessedGrouper includes additional metadata, that data isn't strictly
    used in refining and may not be available depending on the testing pattern. Future
    wrapper functions may be needed to handle both testing patterns and leverage additional
    metadata if needed.
    """

    codes: set[str]

    @classmethod
    def from_configuration(
        cls, configuration: Configuration
    ) -> "ProcessedConfiguration":
        """
        Create ProcessedConfiguration from a Configuration object.

        This method aggregates codes from both the configuration and its conditions,
        creating a processed version ready for XML searching.

        Args:
            configuration: Configuration object containing conditions and custom codes

        Returns:
            ProcessedConfiguration: Object containing combined codes for XML searching
        """

        # aggregate codes from conditions
        codes = aggregate_codes_from_conditions(configuration.conditions)

        # add custom codes from configuration if they exist
        if configuration.configuration.custom_codes:
            codes.update(
                custom_code.code
                for custom_code in configuration.configuration.custom_codes
            )

        return cls(codes=codes)

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


def aggregate_codes_from_conditions(conditions: list[DbCondition]) -> set[str]:
    """
    Extracts and combines all codes from a list of conditions.

    Handles deduplication automatically via set.

    Args:
        conditions: List of conditions (can be single or multiple)
    """

    all_codes: set[str] = set()

    for condition in conditions:
        # extract codes from each JSONB array
        for codes in [
            condition.snomed_codes,
            condition.loinc_codes,
            condition.icd10_codes,
            condition.rxnorm_codes,
        ]:
            # each codes array contains DbConditionCoding objects
            all_codes.update(code.code for code in codes)

    return all_codes


# TODO:
# these will eventually be depricated once we set up the
# independent testing (not inline testing) to also be
# configuration based. for now, this code will eventually
# be completely removed


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
