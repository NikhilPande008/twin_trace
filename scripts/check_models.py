"""Day-1 check: list the live Token Factory catalog and verify the configured tiers.

Usage:
    python -m scripts.check_models             # list + verify configured model ids
    python -m scripts.check_models --ping      # also send one tiny prompt per tier (costs a few tokens)

Exit code 1 if any configured tier model is missing from the live catalog.
Record the result in DECISIONS.md (model ids are [ASSUMED] until this passes).
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests  # noqa: E402

from ddp.config import get_settings  # noqa: E402
from ddp.llm import TokenFactoryClient  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ping", action="store_true")
    args = ap.parse_args()
    s = get_settings()
    if not s.api_key:
        print("NEBIUS_API_KEY not set (.env). Nothing to check.")
        return 1
    url = s.base_url.rstrip("/") + "/models"
    r = requests.get(url, headers={"Authorization": f"Bearer {s.api_key}"}, timeout=30)
    print(f"GET {url} -> HTTP {r.status_code}")
    r.raise_for_status()
    live = sorted(m.get("id") for m in r.json().get("data", []))
    nvidia = [m for m in live if "nemotron" in m.lower() or m.lower().startswith("nvidia/")]
    print(f"\n{len(live)} models live; NVIDIA/Nemotron ({len(nvidia)}):")
    for m in nvidia:
        print(f"  {m}")
    missing = 0
    print("\nConfigured tiers:")
    for tier, model in s.models.items():
        ok = model in live
        missing += not ok
        print(f"  {tier:12s} {model:50s} {'OK' if ok else 'MISSING — set MODEL_' + tier.upper() + ' in .env'}")
    if args.ping and not missing:
        client = TokenFactoryClient(s)
        for tier in s.models:
            text = client.complete("Reply with the single word: ready", tier=tier, max_tokens=16)
            print(f"  ping {tier}: {text!r}  {client.last_call.get('usage')}  {client.last_call.get('latency_s')}s")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
