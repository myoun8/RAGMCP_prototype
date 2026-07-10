#!/usr/bin/env python3
"""Validate a RAG knowledge pack folder.

Usage:
  python scripts/validate_pack.py candor
  python scripts/validate_pack.py vsans
  python scripts/validate_pack.py nse
  python scripts/validate_pack.py common
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REQUIRED_FILES = [
    'access_policy.yaml',
    'glossary.yaml',
    'ingest_config.yaml'
]

REQUIRED_DIRS = [
    'originals',
    'normalized',
    'chunks',
    'eval',
]

REQUIRED_CHUNK_FIELDS = {'chunk_id', 'doc_id', 'source_id', 'text', 'metadata'}
REQUIRED_METADATA_FIELDS = {
    'instrument',
    'workflow_stage',
    'source_type',
    'access_level',
    'status',
    'source_url_or_path',
}


def load_inventory(pack_dir: Path) -> set[str]:
    inventory_path = pack_dir / 'source_inventory.csv'
    if not inventory_path.exists():
        return set()
    with inventory_path.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return {row.get('source_id', '').strip() for row in reader if row.get('source_id')}


def check_jsonl(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        errors.append(f'Missing JSONL file: {path}')
        return errors
    with path.open(encoding='utf-8') as f:
        for i, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f'{path}:{i}: invalid JSON: {exc}')
    return errors


def validate_chunks(pack_dir: Path, inventory_ids: set[str]) -> list[str]:
    errors: list[str] = []
    for path in sorted((pack_dir / 'chunks').glob('*.jsonl')):
        with path.open(encoding='utf-8') as f:
            for i, line in enumerate(f, start=1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.append(f'{path}:{i}: invalid JSON: {exc}')
                    continue
                missing = REQUIRED_CHUNK_FIELDS - row.keys()
                if missing:
                    errors.append(f'{path}:{i}: missing chunk fields: {sorted(missing)}')
                metadata = row.get('metadata') or {}
                if not isinstance(metadata, dict):
                    errors.append(f'{path}:{i}: metadata must be an object')
                    continue
                missing_meta = REQUIRED_METADATA_FIELDS - metadata.keys()
                if missing_meta:
                    errors.append(f'{path}:{i}: missing metadata fields: {sorted(missing_meta)}')
                source_id = row.get('source_id')
                if inventory_ids and source_id not in inventory_ids:
                    errors.append(f'{path}:{i}: source_id {source_id!r} not found in source_inventory.csv')
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__.strip())
        return 2
    root = Path.cwd()
    pack_dir = root / 'rag' / 'context_database' / sys.argv[1]
    if not pack_dir.exists():
        print(f'ERROR: pack folder not found: {pack_dir}')
        return 1

    errors: list[str] = []
    for rel in REQUIRED_FILES:
        if not (pack_dir / rel).exists():
            errors.append(f'Missing required file: {pack_dir / rel}')
    for rel in REQUIRED_DIRS:
        if not (pack_dir / rel).is_dir():
            errors.append(f'Missing required directory: {pack_dir / rel}')

    inventory_ids = load_inventory(pack_dir)

    if (pack_dir / 'manifest.jsonl').exists():
        errors.extend(check_jsonl(pack_dir / 'manifest.jsonl'))
    for path in sorted((pack_dir / 'eval').glob('*.jsonl')):
        errors.extend(check_jsonl(path))
    if (pack_dir / 'chunks').exists():
        errors.extend(validate_chunks(pack_dir, inventory_ids))

    if errors:
        print('Validation failed:')
        for err in errors:
            print(f' - {err}')
        return 1

    print(f'Validation passed for {pack_dir.name}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
