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

    def __init__(self) -> None:
        """
        Initialize grouper operations with database connection.
        """

        self.db = DatabaseConnection()

    def get_grouper_by_condition(self, condition: str) -> GrouperRow | None:
        """
        Get a single grouper by condition code.

        Args:
            condition: SNOMED CT code for the condition

        Returns:
            GrouperRow if found, None if not found

        Raises:
            sqlite3.Error: If there's a database error
        """

        query = """
            SELECT condition, display_name, loinc_codes, snomed_codes,
                   icd10_codes, rxnorm_codes
            FROM groupers
            WHERE condition = ?
        """

        with self.db.get_cursor() as cursor:
            # use _ to indicate intentionally unused result
            _ = cursor.execute(query, (condition,))
            row = cursor.fetchone()

            if row is None:
                return None

            return GrouperRow(
                condition=str(row["condition"]),
                display_name=str(row["display_name"]),
                loinc_codes=str(row["loinc_codes"]),
                snomed_codes=str(row["snomed_codes"]),
                icd10_codes=str(row["icd10_codes"]),
                rxnorm_codes=str(row["rxnorm_codes"]),
            )
