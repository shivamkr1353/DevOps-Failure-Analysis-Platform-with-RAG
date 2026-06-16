import json
import logging
from pathlib import Path
import aiosqlite

from database.repository import store_incident
from rag.retriever import store_failure
from services.log_cleaner import clean_logs

logger = logging.getLogger("failure_analysis_api")


async def seed_database_if_empty(db_path: str) -> None:
    """Check if the SQLite database is empty. If so, seed it with initial failures and index them in ChromaDB."""

    try:
        # Check SQLite count
        async with aiosqlite.connect(db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM failure_incidents") as cursor:
                row = await cursor.fetchone()
                count = row[0] if row else 0

        if count > 0:
            logger.info("Database already seeded with %d failure incidents. Skipping seeding.", count)
            return

        # Locate seed file
        seed_file_path = Path(__file__).parent / "seed_incidents.json"
        if not seed_file_path.exists():
            logger.warning("Seed file not found at %s. Skipping database seeding.", seed_file_path)
            return

        logger.info("Seeding database from %s...", seed_file_path)
        with open(seed_file_path, "r", encoding="utf-8") as f:
            incidents = json.load(f)

        seeded_count = 0
        for inc in incidents:
            try:
                # 1. Store in SQLite
                incident_id = await store_incident(
                    workflow_name=inc.get("workflow_name", ""),
                    run_id=inc.get("run_id", ""),
                    source_type=inc.get("source_type", "manual"),
                    logs=inc["logs"],
                    root_cause=inc["root_cause"],
                    summary=inc["summary"],
                    fix=inc["fix"],
                )

                # 2. Clean logs and index in ChromaDB
                cleaned = clean_logs(inc["logs"])
                store_failure(
                    incident_id=incident_id,
                    logs=cleaned,
                    root_cause=inc["root_cause"],
                    fix=inc["fix"],
                )
                seeded_count += 1
            except Exception as e:
                logger.warning("Failed to seed single incident (workflow: %s): %s", inc.get("workflow_name"), e)

        logger.info("Successfully seeded %d incidents in SQLite and ChromaDB.", seeded_count)

    except Exception as exc:
        logger.error("Error during database seeding: %s", exc)
