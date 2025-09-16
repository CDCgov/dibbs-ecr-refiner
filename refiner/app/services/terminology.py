from dataclasses import dataclass

from ..db.conditions.model import DbCondition
from ..db.configurations.model import DbConfiguration

# NOTE:
# This file establishes a consistent pattern for handling terminology data:
# 1. A `Payload` class (e.g., ConditionPayload) holds raw DB models.
# 2. A `Processed` class (e.g., ProcessedCondition) holds the final, ready-to-use data.
# 3. The `Processed` class has a `.from_payload()` factory method that contains all
#    the logic to transform the raw payload into the processed version.
# 4. The `Processed` class has a `.build_xpath()` method for the refiner.
# This separates data fetching, data processing, and data usage into clean, testable steps.
# =============================================================================


# NOTE:
# CONDITION PROCESSING
# =============================================================================


@dataclass(frozen=True)
class ConditionPayload:
    """
    Model representing the raw condition data needed for refinement.

    A raw data container holding a list of DbCondition objects from the database.
    This is the "payload" that will be transformed into a ProcessedCondition.
    """

    conditions: list[DbCondition]


@dataclass(frozen=True)
class ProcessedCondition:
    """
    Represents the processed set of codes from a condition, ready for refinement.

    This model is purposely focused on just the essential data needed for independent
    testing patterns:

    - Independent testing: Reading XML, extracting unique RC SNOMED codes, finding
      configurations via child_rsg_snomed_codes, then using condition_id to get
      included_conditions.
    """

    codes: set[str]

    @classmethod
    def from_payload(cls, payload: ConditionPayload) -> "ProcessedCondition":
        """
        Processes a ConditionPayload to aggregate all unique codes from its conditions.

        Args:
            payload: The raw ConditionPayload containing DbCondition objects.

        Returns:
            A ProcessedCondition instance with the final set of codes.
        """

        all_codes: set[str] = set()
        for condition in payload.conditions:
            # extract codes from each JSONB array within the DbCondition
            for code_list in [
                condition.snomed_codes,
                condition.loinc_codes,
                condition.icd10_codes,
                condition.rxnorm_codes,
            ]:
                all_codes.update(c.code for c in code_list)
        return cls(codes=all_codes)

    def build_xpath(self) -> str:
        """
        Builds a comprehensive XPath query to find any clinical data related to the processed codes.

        This XPath search strategy is comprehensive and flexible because it will look for codes
        in various clinical contexts, such as:
          * <observation><code code="[code]">
          * <observation><value code="[code]">
          * <act><code code="[code]">
          * <translation code="[code]">
          * etc.

        Returns:
            str: XPath expression that finds elements containing matching codes.
        """

        if not self.codes:
            return ""

        code_conditions = " or ".join(f'@code="{code}"' for code in self.codes)
        # this comprehensive XPath finds the code in various clinical contexts
        return (
            f".//hl7:*[hl7:code[{code_conditions}]] | "
            f".//hl7:code[{code_conditions}] | "
            f".//hl7:translation[{code_conditions}]"
        )


# NOTE:
# CONFIGURATION PROCESSING
# =============================================================================


@dataclass(frozen=True)
class ConfigurationPayload:
    """
    Model representing the raw configuration data needed for refinement.

    This model is intentionally minimal to support both inline testing (from configuration building)
    and independent testing (from demo.py processing) patterns. The model focuses on just the
    essential data needed for refinement:

    - conditions: A list of all DbCondition objects to be considered.
    - configuration: The specific DbConfiguration object, which may contain custom codes.

    Note on Testing Patterns:
    - Independent testing: Uses RC SNOMED codes from the RR's coded information organizer to find
      the matching configuration. The RC SNOMED code comes from the RR, not the configuration itself.
    - Inline testing: Directly uses a configuration to test against input data, focusing only on
      the codes defined in that configuration.
    """

    configuration: DbConfiguration
    conditions: list[DbCondition]


@dataclass(frozen=True)
class ProcessedConfiguration:
    """
    Represents the processed set of codes from a configuration, ready for refinement.

    This model is purposely focused on just the essential data needed for both inline
    and independent testing patterns:

    - Inline testing: Running a configuration against test data and only looking for
      that Configuration's codes.
    - Independent testing: Reading XML, extracting unique RC SNOMED codes, finding
      configurations via child_rsg_snomed_codes, then using condition_id to get
      included_conditions.
    """

    codes: set[str]

    @classmethod
    def from_payload(cls, payload: ConfigurationPayload) -> "ProcessedConfiguration":
        """
        Create ProcessedConfiguration from a ConfigurationPayload object.

        This method aggregates codes from both the configuration's associated conditions and
        any custom codes defined on the configuration itself.

        Args:
            payload: The ConfigurationPayload containing the DbConfiguration and its related DbConditions.

        Returns:
            ProcessedConfiguration: An object containing the final, combined set of codes.
        """

        # 1. aggregate codes from all associated conditions
        all_codes: set[str] = set()
        for condition in payload.conditions:
            for code_list in [
                condition.snomed_codes,
                condition.loinc_codes,
                condition.icd10_codes,
                condition.rxnorm_codes,
            ]:
                all_codes.update(c.code for c in code_list)

        # 2. add custom codes defined directly on the configuration
        if payload.configuration.custom_codes:
            all_codes.update(cc.code for cc in payload.configuration.custom_codes)

        return cls(codes=all_codes)

    def build_xpath(self) -> str:
        """
        Builds a comprehensive XPath query to find any clinical data related to the processed codes.

        This XPath search strategy is comprehensive and flexible because it will look for codes
        in various clinical contexts, such as:
          * <observation><code code="[code]">
          * <observation><value code="[code]">
          * <act><code code="[code]">
          * <translation code="[code]">
          * etc.

        Returns:
            str: XPath expression that finds elements containing matching codes.
        """

        if not self.codes:
            return ""

        code_conditions = " or ".join(f'@code="{code}"' for code in self.codes)
        # this comprehensive XPath finds the code in various clinical contexts
        return (
            f".//hl7:*[hl7:code[{code_conditions}]] | "
            f".//hl7:code[{code_conditions}] | "
            f".//hl7:translation[{code_conditions}]"
        )


# NOTE:
# HELPER FUNCTIONS
# =============================================================================


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
