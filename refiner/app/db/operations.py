from typing import Any

import psycopg

from app.core.exceptions import (
    DatabaseQueryError,
    InputValidationError,
    ResourceNotFoundError,
)

from .connection import DatabaseConnection
from .models import GrouperRow
from .pool import AsyncDatabaseConnection


class GrouperOperations:
    """
    Database operations for the groupers table.

    Provides methods to query and retrieve raw grouper data from the database
    as GrouperRow TypedDict instances, which can then be processed by the
    terminology service.

    Attributes:
        db: Database connection manager for groupers table operations
    """

    db: DatabaseConnection | AsyncDatabaseConnection

    def __init__(self, db: DatabaseConnection | AsyncDatabaseConnection) -> None:
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

        if not isinstance(self.db, DatabaseConnection):
            raise DatabaseQueryError(
                message="Cannot use async connection with a sync query."
            )

        self._validate_condition(condition)
        query = self._get_query()

        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(query, (condition,))
                row = cursor.fetchone()
                return self._parse_row(row, condition)
        except (ResourceNotFoundError, InputValidationError):
            # re-raise these exceptions directly
            raise
        except psycopg.Error as e:
            raise DatabaseQueryError(
                message="Failed to query grouper",
                details={"condition": condition, "error": str(e)},
            )

    async def get_grouper_by_condition_async(self, condition: str) -> GrouperRow:
        """
        Async version of `GrouperRow.get_grouper_by_condition()`.
        """
        if not isinstance(self.db, AsyncDatabaseConnection):
            raise DatabaseQueryError(
                message="Cannot use sync connection with an async query."
            )

        self._validate_condition(condition)
        query = self._get_query()

        try:
            async with self.db.get_cursor() as cursor:
                await cursor.execute(query, (condition,))
                row = await cursor.fetchone()
                return self._parse_row(row, condition)
        except (ResourceNotFoundError, InputValidationError):
            raise
        except psycopg.Error as e:
            raise DatabaseQueryError(
                message="Failed to query grouper (async)",
                details={"condition": condition, "error": str(e)},
            )

    def _get_query(self) -> str:
        return """
            SELECT condition, display_name, loinc_codes, snomed_codes,
            icd10_codes, rxnorm_codes
            FROM groupers
            WHERE condition = %s
        """

    def _validate_condition(self, condition: str) -> None:
        if not condition or not isinstance(condition, str):
            raise InputValidationError(
                message="Invalid condition code", details={"condition": condition}
            )

    def _parse_row(self, row: Any, condition: str) -> GrouperRow:
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
