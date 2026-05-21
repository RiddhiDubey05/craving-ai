"""
seed_data.py — Thin startup wrapper for the Food Ingestion Pipeline
====================================================================
This file is intentionally minimal. All dish knowledge lives in
  backend/data/food_knowledge/catalog.json  (and any other *.json files there)

To add new dishes:
  1. Append entries to catalog.json  (or create a new *.json file there)
  2. Either restart the server  OR  call  POST /api/admin/ingest

To force a full re-embed of all dishes:
  Call  POST /api/admin/reindex
"""
from backend.services.food_pipeline import food_pipeline
from backend.utils.logger import app_logger


def seed_database():
    """
    Called once at server startup.
    Runs the ingestion pipeline in delta mode:
      - Loads all catalog JSON files
      - Auto-enriches every dish
      - Only embeds dishes that are new or changed since last run
      - Adds them incrementally to FAISS
    """
    try:
        stats = food_pipeline.run(force_reindex=False)
        app_logger.info(
            f"Startup seed complete — "
            f"catalog: {stats['total_in_catalog']} dishes, "
            f"newly indexed: {stats['newly_indexed']}, "
            f"FAISS total: {stats['faiss_total']}, "
            f"elapsed: {stats['elapsed_seconds']}s"
        )
    except Exception as e:
        app_logger.error(f"Startup seeding failed: {e}")
        raise


if __name__ == "__main__":
    seed_database()
