from __future__ import annotations

import argparse
import sys

from .config import load_config
from .db import MetadataDB
from .ingest_files.runner import run_backfill, run_watch_loop


def _status() -> int:
    config = load_config()
    db = MetadataDB(config.db_path, log_events=config.log_events)
    file_count = db.count_sources("file")
    db.close()
    print(f"sources(file)={file_count}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local to Obsidian ingestion tool")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("run", help="Run file watcher and continuous sync")

    backfill = sub.add_parser("backfill", help="One-time scan and ingest")
    backfill.add_argument("--force", action="store_true", help="Reprocess even if unchanged")

    sub.add_parser("reprocess", help="Reprocess all matched files")

    sub.add_parser("status", help="Show ingest status summary")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config()

    if args.command == "run":
        run_watch_loop(config)
        return 0
    if args.command == "backfill":
        run_backfill(config, force=args.force)
        return 0
    if args.command == "reprocess":
        run_backfill(config, force=True)
        return 0
    if args.command == "status":
        return _status()

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
