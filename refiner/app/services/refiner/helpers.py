import logging

from ...core.exceptions import (
    DatabaseConnectionError,
    DatabaseQueryError,
    ResourceNotFoundError,
)
from ...db.connection import DatabaseConnection
from ...db.operations import GrouperOperations, GrouperRow
from ...db.pool import AsyncDatabaseConnection
from ..terminology import ProcessedGrouper

log = logging.getLogger(__name__).error


async def get_processed_groupers_from_condition_codes_async(
    condition_codes: str, db: AsyncDatabaseConnection
) -> list[GrouperRow]:
    """
    Async version of `get_processed_groupers_from_condition_codes_async`.
    """
    grouper_ops = GrouperOperations(db)

    grouper_rows = []
    for code in condition_codes.split(","):
        code = code.strip()
        try:
            row = await grouper_ops.get_grouper_by_condition_async(code)
            if row:
                grouper_rows.append(row)
        except (DatabaseConnectionError, DatabaseQueryError) as e:
            # log but continue with other codes
            log(f"Database error processing condition code {code}: {str(e)}")
        except ResourceNotFoundError:
            # log that the code wasn't found but continue
            log(f"Condition code not found: {code}")
    return grouper_rows


# Synchronously connect to the DB
def get_processed_groupers_from_condition_codes(
    condition_codes: str, db: DatabaseConnection
) -> list[GrouperRow]:
    """
    Given a list of condition codes, synchronously connects to the database and creates a list of GrouperRow objects.

    Args:
        condition_codes (str): Comma separated list of SNOMED condition codes
        db (DatabaseConnection): Established database connection

    Returns:
        list[GrouperRow]: List of GrouperRows built from the given list of condition codes

    Raises:
        DatabaseConnectionError
        DatabaseQueryError
        ResourceNotFoundError
    """
    grouper_ops = GrouperOperations(db)

    grouper_rows = []
    for code in condition_codes.split(","):
        code = code.strip()
        try:
            row = grouper_ops.get_grouper_by_condition(code)
            if row:
                grouper_rows.append(row)
        except (DatabaseConnectionError, DatabaseQueryError) as e:
            # log but continue with other codes
            log(f"Database error processing condition code {code}: {str(e)}")
        except ResourceNotFoundError:
            # log that the code wasn't found but continue
            log(f"Condition code not found: {code}")
    return grouper_rows


def get_condition_codes_xpath(grouper_rows: list[GrouperRow]) -> str:
    """
    Generate XPath from a list of GrouperRows using ProcessedGrouper only.

    Takes a list of GrouperRows and builds XPath expressions to find any
    matching codes in HL7 XML documents.

    Args:
        grouper_rows: GrouperRows built from a list of condition codes

    Returns:
        str: Combined XPath expression to find relevant elements, or empty string
    """

    xpath_conditions = []

    for row in grouper_rows:
        processed = ProcessedGrouper.from_grouper_row(row)
        xpath = processed.build_xpath()
        if xpath:
            xpath_conditions.append(xpath)

    if not xpath_conditions:
        return ""

    return " | ".join(xpath_conditions)
