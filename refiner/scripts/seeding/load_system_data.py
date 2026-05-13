from config import logger
from lib import (
    get_db_connection,
)

CODE_SYSTEM_DATA = {
    "2.16.840.1.113883.6.96": {"name": "snomed", "display_name": "SNOMED"},
    "2.16.840.1.113883.6.1": {"name": "loinc", "display_name": "LOINC"},
    "2.16.840.1.113883.6.90": {"name": "icd-10", "display_name": "ICD-10"},
    "2.16.840.1.113883.6.88": {"name": "rxnorm", "display_name": "RxNorm"},
    "2.16.840.1.113883.12.292": {"name": "cvx", "display_name": "CVX"},
    "2.16.840.1.113883.5.1008": {"name": "other", "display_name": "Other"},
}


def load_system_data(
    db_url: str,
    db_password: str,
):
    """
    Function to upsert system information.
    """
    try:
        with get_db_connection(db_url, db_password) as conn, conn.cursor() as cursor:
            logger.info("⏳ Upserting system data...")

            system_upsert_query = """
            INSERT INTO systems (
                name,
                display_name,
                oid
            )
            VALUES (
                %(name)s,
                %(display_name)s,
                %(oid)s
            )
            ON CONFLICT (oid)
            DO UPDATE SET
                name = EXCLUDED.name,
                display_name = EXCLUDED.display_name
            WHERE
                systems.display_name IS DISTINCT FROM EXCLUDED.display_name
                OR systems.name IS DISTINCT FROM EXCLUDED.name
            RETURNING id
            """

            params = [
                {
                    "oid": oid,
                    "display_name": item["display_name"],
                    "name": item["name"],
                }
                for oid, item in CODE_SYSTEM_DATA.items()
            ]

            cursor.executemany(system_upsert_query, params)

            conn.commit()
        logger.info("🏁 Done!")

    except Exception:
        logger.error(
            "❌ A critical error occured during upsert of system data",
            exc_info=True,
        )
