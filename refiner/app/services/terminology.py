from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from ..db.conditions.model import DbCondition
from ..db.configurations.model import DbConfiguration

# NOTE:
# This file establishes a consistent pattern for handling terminology data:
# 1. A `Payload` class (e.g., ConfigurationPayload) holds raw DB models.
# 2. A `Processed` class (e.g., ProcessedConfiguration) holds the final, ready-to-use data.
# 3. The `Processed` class has a `.from_payload()` factory method that contains all
#    the logic to transform the raw payload into the processed version.
# 4. The `Processed` class has a `.build_xpath()` method for the refiner.
# This separates data fetching, data processing, and data usage into clean, testable steps.
# =============================================================================


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


class Section(BaseModel):
    """
    Section data coming from an active.json S3 file.
    """

    code: str
    name: str
    action: str


class ProcessedConfigurationData(BaseModel):
    """
    ProcessedConfiguration data coming from an active.json S3 file.
    """

    codes: set[str] = Field(min_length=1)
    sections: list[Section]
    included_condition_rsg_codes: set[str]


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
    section_processing: list[dict]
    included_condition_rsg_codes: set[str]

    @classmethod
    def from_dict(cls, data: dict) -> "ProcessedConfiguration":
        """
        Creates a ProcessedConfiguration from a validated dictionary.

        Args:
            data (dict): Input dictionary with required data.

        Returns:
            ProcessedConfiguration: A ProcessedConfiguration built from the dictionary
        """
        validated = ProcessedConfigurationData.model_validate(data)

        return cls(
            codes=validated.codes,
            section_processing=[s.model_dump() for s in validated.sections],
            included_condition_rsg_codes=validated.included_condition_rsg_codes,
        )

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

        # STEP 1:
        # aggregate codes from all associated conditions
        all_codes: set[str] = set()
        for condition in payload.conditions:
            for code_list in [
                condition.snomed_codes,
                condition.loinc_codes,
                condition.icd10_codes,
                condition.rxnorm_codes,
            ]:
                all_codes.update(code.code for code in code_list)

        # STEP 2:
        # add custom codes defined directly on the configuration
        all_codes.update(
            custom_code.code for custom_code in payload.configuration.custom_codes
        )

        # STEP 3:
        # convert the list of DbConfigurationSectionProcessing objects into
        # a simple list of dictionaries
        section_processing_as_dicts: list[dict[str, Any]] = [
            {
                "code": section_process.code,
                "name": section_process.name,
                "action": section_process.action,
            }
            for section_process in payload.configuration.section_processing
        ]

        included_condition_rsg_codes = set()
        for c in payload.conditions:
            included_condition_rsg_codes.update(c.child_rsg_snomed_codes)

        return cls(
            codes=all_codes,
            section_processing=section_processing_as_dicts,
            included_condition_rsg_codes=included_condition_rsg_codes,
        )
