#!/usr/bin/env python3
"""Clean up data/ directory files (audit chains, SQLite DB).

Usage:
    python scripts/cleanup_data.py          # Remove all data files
    python scripts/cleanup_data.py --dry-run # Show what would be removed
"""
import argparse
import os
from pathlib import Path


def cleanup_data(dry_run: bool = False) -> None:
    data_dir = Path("data")
    if not data_dir.exists():
        print("No data/ directory found.")
        return

    files = list(data_dir.glob("*"))
    if not files:
        print("data/ directory is empty.")
        return

    for f in files:
        size = f.stat().st_size if f.is_file() else 0
        if dry_run:
            print(f"  Would remove: {f} ({size} bytes)")
        else:
            if f.is_file():
                f.unlink()
                print(f"  Removed: {f} ({size} bytes)")
            elif f.is_dir():
                import shutil
                shutil.rmtree(f)
                print(f"  Removed dir: {f}")

    if not dry_run:
        # Remove data dir if empty
        if not any(data_dir.iterdir()):
            data_dir.rmdir()
            print("  Removed empty data/ directory")

    print(f"\n{'Would remove' if dry_run else 'Removed'} {len(files)} items.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean up data/ directory")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be removed")
    args = parser.parse_args()
    cleanup_data(dry_run=args.dry_run)
