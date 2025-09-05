from pydantic import BaseModel

from ...db.conditions.model import DbCondition
from ...db.configurations.model import DbConfiguration


class Configuration(BaseModel):
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


class ProcessedConfiguration(BaseModel):
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

    # list of codes for processing XML documents
    codes: list[str]
