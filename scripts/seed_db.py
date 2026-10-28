"""(Re)build the local SQLite database from the corpus YAML and seed data.

Usage:
    python -m scripts.seed_db            # seed data/ddp.sqlite3 if empty
    python -m scripts.seed_db --fresh    # delete and rebuild (DESTROYS the local ledger)
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ddp.bootstrap import open_store, seed  # noqa: E402
from ddp.config import get_settings  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fresh", action="store_true", help="delete the DB file first")
    args = ap.parse_args()
    path = get_settings().db_path
    if args.fresh and path.exists():
        path.unlink()
        print(f"deleted {path}")
    store = open_store(path, seed_if_empty=False)
    counts = seed(store)
    print(f"seeded {path}: {counts}")
    print(f"ledger chain: {store.verify_ledger_chain()}")


if __name__ == "__main__":
    main()
