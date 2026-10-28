"""Verify a decision package offline: no database, no API key (T3).

Usage:
    python3 -m scripts.verify_package decision-package-xxxx.json
Exit code 0 when every check passes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ddp.package import verify_package  # noqa: E402


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 1:
        print(__doc__)
        return 2
    result = verify_package(json.loads(Path(argv[0]).read_text()))
    for c in result["checks"]:
        print(f"  {'✓' if c['ok'] else '✗'} {c['name']}  {c['detail']}")
    print("PACKAGE VERIFIED" if result["ok"] else "PACKAGE FAILED VERIFICATION")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
