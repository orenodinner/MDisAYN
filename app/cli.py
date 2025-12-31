from __future__ import annotations

import argparse

from rich.console import Console
from rich.table import Table

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


def _print_config_table(config) -> None:
    console = Console()
    table = Table(title="MDisAYN 設定", show_lines=True)
    table.add_column("項目", style="bold")
    table.add_column("値")

    watch_paths = "\n".join(str(path) for path in config.watch_paths) or "-"
    max_file_mb = int(config.max_file_bytes / (1024 * 1024))

    table.add_row("Vault パス", str(config.vault_path))
    table.add_row("Data Lake パス", str(config.data_lake_path))
    table.add_row("DB パス", str(config.db_path))
    table.add_row("監視パス", watch_paths)
    table.add_row("再帰監視", str(config.watch_recursive))
    table.add_row("除外ディレクトリ", ", ".join(config.exclude_dirs) or "-")
    table.add_row("除外グロブ", ", ".join(config.exclude_globs) or "-")
    table.add_row("スキャン間隔(秒)", str(config.scan_interval_sec))
    table.add_row("デバウンス(秒)", str(config.debounce_sec))
    table.add_row("最大ファイル(MB)", str(max_file_mb))
    table.add_row("LLM Base URL", config.llm_base_url)
    table.add_row("LLM Model", config.llm_model)
    table.add_row("LLM Language", config.llm_language)
    table.add_row("Obsidian 出力先", config.obsidian_sources_subdir)
    table.add_row("イベントログ", str(config.log_events))

    console.print(table)


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
    _print_config_table(config)

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
