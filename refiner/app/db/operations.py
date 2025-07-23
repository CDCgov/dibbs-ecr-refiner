import psycopg

from app.core.exceptions import (
    DatabaseConnectionError,
    DatabaseQueryError,
    InputValidationError,
    ResourceNotFoundError,
)

from .connection import DatabaseConnection
from .models import GrouperRow


class GrouperOperations:
    """
    Database operations for the groupers table.

    Provides methods to query and retrieve raw grouper data from the database
    as GrouperRow TypedDict instances, which can then be processed by the
    terminology service.

    Attributes:
        db: Database connection manager for groupers table operations
    """

    db: DatabaseConnection

    def __init__(self, db: DatabaseConnection) -> None:
        """
        Initialize grouper operations with database connection.
        """

        self.db = db

    def get_grouper_by_condition(self, condition: str) -> GrouperRow:
        """
        Get a single grouper by condition code.

        Args:
            condition: SNOMED CT code for the condition

        Returns:
            GrouperRow containing the grouper data

        Raises:
            ResourceNotFoundError: If no grouper with specified condition is found
            DatabaseQueryError: If database query execution fails
            DatabaseConnectionError: If database connection fails
            InputValidationError: If the condition parameter is invalid
        """

        if not condition or not isinstance(condition, str):
            raise InputValidationError(
                message="Invalid condition code", details={"condition": condition}
            )

        query = """
            SELECT condition, display_name, loinc_codes, snomed_codes,
                icd10_codes, rxnorm_codes
            FROM groupers
            WHERE condition = %s
        """

        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(query, (condition,))
                row = cursor.fetchone()

                if row is None:
                    raise ResourceNotFoundError(
                        message="Grouper with condition not found",
                        details={"condition": condition},
                    )

                return GrouperRow(
                    condition=str(row["condition"]),
                    display_name=str(row["display_name"]),
                    loinc_codes=str(row["loinc_codes"]),
                    snomed_codes=str(row["snomed_codes"]),
                    icd10_codes=str(row["icd10_codes"]),
                    rxnorm_codes=str(row["rxnorm_codes"]),
                )
        except (ResourceNotFoundError, InputValidationError):
            # re-raise these exceptions directly
            raise
        except psycopg.Error as e:
            raise DatabaseQueryError(
                message="Failed to query grouper",
                details={"condition": condition, "error": str(e)},
            )
        except DatabaseConnectionError:
            # re-raise database connection errors
            raise
