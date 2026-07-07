#!/usr/bin/env python3
"""
run_pipeline.py

Chains the full RAG ingestion pipeline in order:

  1. full_document_ingestion.py  — LLM normalisation of originals/ (interactive)
  2. chunk_markdown.py           — heading-based chunking  (per pack)
  3. validate_pack.py            — structural/schema linting  (per pack; skippable)
  4. embed_and_ingest.py         — embed all chunks and load into Chroma

Normalisation (step 1) uses the RChat API (OpenAI-compatible).
RCHAT_API_KEY is read from a .env file in the repo root (or the environment).

Flags:
  --skip-normalize   Skip step 1 (originals already normalized)
  --skip-validate    Skip step 3
  --model NAME       RChat model to use (default: gemma-4-31B-it)

Usage:
  python scripts/run_pipeline.py [--pack PACK] [--skip-normalize] [--skip-validate]
      [--model gemma-4-31B-it] [--dry-run]
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
from _common import PACKS  # noqa: E402

RCHAT_API_KEY_ENV = "RCHAT_API_KEY"
DEFAULT_MODEL = "gemma-4-31B-it"


def _load_dotenv(path: Path) -> None:
    """Load KEY=VALUE pairs from a .env file into os.environ (skips already-set keys)."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = value


def run_step(cmd: list[str], label: str) -> None:
    """Run a command with inherited stdio; abort the pipeline on non-zero exit."""
    print(f"\n{'═' * 64}")
    print(f"  {label}")
    print(f"{'═' * 64}\n", flush=True)
    result = subprocess.run(cmd, cwd=str(REPO_ROOT))
    if result.returncode != 0:
        print(
            f"\n[pipeline] '{label}' exited with code {result.returncode}. "
            "Aborting.",
            file=sys.stderr,
        )
        sys.exit(result.returncode)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--pack", choices=PACKS,
        help="Scope normalisation/chunking/validation to one pack "
             "(embed_and_ingest always ingests all available chunk files)",
    )
    p.add_argument("--skip-normalize", action="store_true",
                   help="Skip full_document_ingestion.py (originals already normalized)")
    p.add_argument("--skip-validate", action="store_true",
                   help="Skip validate_pack.py")
    p.add_argument("--dry-run", action="store_true",
                   help="Pass --dry-run to full_document_ingestion.py; other steps still run")
    p.add_argument("--model", default=DEFAULT_MODEL, metavar="NAME",
                   help=f"RChat model name (default: {DEFAULT_MODEL})")
    return p


def main() -> None:
    _load_dotenv(REPO_ROOT.parent / ".env")
    args = build_parser().parse_args()
    packs = [args.pack] if args.pack else PACKS
    py = sys.executable

    # ── Step 1: Normalize via RChat API ───────────────────────────────────────
    if not args.skip_normalize:
        api_key = os.environ.get(RCHAT_API_KEY_ENV)
        if not api_key:
            print(
                f"[pipeline] {RCHAT_API_KEY_ENV} not found in environment or .env file.",
                file=sys.stderr,
            )
            sys.exit(1)

        cmd = [
            py, str(SCRIPTS / "full_document_ingestion.py"),
            "--model", args.model,
            "--api-key", api_key,
        ]
        if args.pack:
            cmd += ["--pack", args.pack]
        if args.dry_run:
            cmd.append("--dry-run")
        run_step(cmd, f"Step 1/4 — Normalize originals via RChat [{args.model}] (full_document_ingestion.py)")

    # ── Step 2: Chunk ────────────────────────────────────────────────────────
    for pack in packs:
        run_step(
            [py, str(SCRIPTS / "chunk_markdown.py"), pack],
            f"Step 2/4 — Chunk [{pack}] (chunk_markdown.py)",
        )

    # ── Step 3: Validate ──────────────────────────────────────────────────────
    if not args.skip_validate:
        for pack in packs:
            run_step(
                [py, str(SCRIPTS / "validate_pack.py"), pack],
                f"Step 3/4 — Validate [{pack}] (validate_pack.py)",
            )

    # ── Step 4: Embed and ingest ──────────────────────────────────────────────
    run_step(
        [py, str(SCRIPTS / "embed_and_ingest.py")],
        "Step 4/4 — Embed and ingest all chunks (embed_and_ingest.py)",
    )

    # ── Done ──────────────────────────────────────────────────────────────────
    print("\n" + "═" * 64)
    print("  Pipeline complete!")
    print("═" * 64 + "\n")


if __name__ == "__main__":
    main()
