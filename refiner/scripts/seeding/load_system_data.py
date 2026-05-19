from config import logger
from lib import (
    get_db_connection,
)

CODE_SYSTEM_DATA = {
    "snomed": {"oid": "2.16.840.1.113883.6.96", "display_name": "SNOMED"},
    "loinc": {"oid": "2.16.840.1.113883.6.1", "display_name": "LOINC"},
    "icd-10": {"oid": "2.16.840.1.113883.6.90", "display_name": "ICD-10"},
    "rxnorm": {"oid": "2.16.840.1.113883.6.88", "display_name": "RxNorm"},
    "cvx": {"oid": "2.16.840.1.113883.12.292", "display_name": "CVX"},
    "other": {"oid": None, "display_name": "Other"},
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
                key,
                display_name,
                oid
            )
            VALUES (
                %(key)s,
                %(display_name)s,
                %(oid)s
            )
            ON CONFLICT (oid)
            DO UPDATE SET
                key = EXCLUDED.key,
                display_name = EXCLUDED.display_name
            WHERE
                systems.display_name IS DISTINCT FROM EXCLUDED.display_name
                OR systems.key IS DISTINCT FROM EXCLUDED.key
            RETURNING id
            """

            params = [
                {
                    "key": key,
                    "oid": item["oid"],
                    "display_name": item["display_name"],
                }
                for key, item in CODE_SYSTEM_DATA.items()
            ]

            cursor.executemany(system_upsert_query, params)

            conn.commit()
        logger.info("🏁 Done!")

    except Exception:
        logger.error(
            "❌ A critical error occured during upsert of system data",
            exc_info=True,
        )
