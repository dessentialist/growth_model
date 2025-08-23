#!/usr/bin/env python3
"""Migrate scenario YAML files from legacy 'material' keys to 'product'.

Usage:
    python scripts/migrate_material_to_product.py input.yaml [-o output.yaml]

If no output path is provided the input file is overwritten in place.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import yaml

def _replace_keys(obj):
    if isinstance(obj, dict):
        return {("product" if k == "material" else k): _replace_keys(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_replace_keys(v) for v in obj]
    return obj

def main() -> None:
    parser = argparse.ArgumentParser(description="Replace 'material' keys with 'product'")
    parser.add_argument("input", type=Path, help="Path to legacy scenario YAML")
    parser.add_argument("-o", "--output", type=Path, help="Optional output path")
    args = parser.parse_args()

    data = yaml.safe_load(args.input.read_text(encoding="utf-8"))
    migrated = _replace_keys(data)
    out_path = args.output or args.input
    out_path.write_text(yaml.safe_dump(migrated, sort_keys=False), encoding="utf-8")
    print(f"Migrated scenario written to {out_path}")

if __name__ == "__main__":
    main()
