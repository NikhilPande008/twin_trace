"""Export a recorded decision as a self-contained package (T3).

Usage:
    python3 -m scripts.export_decision <DECISION_ID> [--out decision-package.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ddp.bootstrap import open_store  # noqa: E402
from ddp.package import build_package  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("decision_id")
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    pkg = build_package(open_store(seed_if_empty=False), args.decision_id)
    out = Path(args.out or f"decision-package-{args.decision_id[:8]}.json")
    out.write_text(json.dumps(pkg, indent=2, default=str))
    print(f"wrote {out} (package sha256 {pkg['manifest']['package_sha256'][:16]}…)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
