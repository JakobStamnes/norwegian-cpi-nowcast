"""CLI entry point to compute daily_index for today (or a given date).

Usage:
    python -m indexer.run_daily
    python -m indexer.run_daily --date 2026-04-15
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import date

import asyncpg
import structlog

from indexer.laspeyres import compute_and_store
from scraper.config import settings

log = structlog.get_logger(__name__)


async def run(target_date: date) -> None:
    """Compute daily Laspeyres index for the given date."""
    try:
        log.info("indexer_starting", date=target_date)
        pool = await asyncpg.create_pool(settings.database_url)
        log.info("database_connected", date=target_date)
        await compute_and_store(pool, target_date)
        await pool.close()
        log.info("indexer_done", date=target_date)
    except asyncpg.PostgresError as e:
        log.error("database_error", error=str(e), date=target_date)
        raise
    except Exception as e:
        log.error("indexer_error", error=str(e), date=target_date)
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=str(date.today()))
    args = parser.parse_args()
    try:
        target = date.fromisoformat(args.date)
        asyncio.run(run(target))
    except ValueError as e:
        log.error("invalid_date_format", error=str(e))
        raise
    except Exception as e:
        log.error("fatal_error", error=str(e))
        raise


if __name__ == "__main__":
    main()
