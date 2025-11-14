#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict


def load_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Input JSON not found: {p}")
    with p.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise TypeError(f"JSON in {p} is not an object/dict.")
    return data


def main():
    ap = argparse.ArgumentParser(
        description=(
            "Merge multiple per-sample JSON files into one grouped JSON.\n"
            "Order of groups: count → fastp → singlem → nonpareil_reads → nonpareil_markers."
        )
    )

    # Inputs
    ap.add_argument("--count", help="JSON file with read counts info")
    ap.add_argument("--fastp", help="JSON file with simplified fastp results")
    ap.add_argument("--singlem", help="JSON file with SingleM / marker info")
    ap.add_argument("--nonpareil-reads", dest="nonpareil_reads",
                    help="JSON file with Nonpareil results based on reads")
    ap.add_argument("--nonpareil-markers", dest="nonpareil_markers",
                    help="JSON file with Nonpareil results based on markers")

    ap.add_argument("-o", "--output", required=True,
                    help="Output merged JSON file")

    args = ap.parse_args()

    # Explicit order — THIS is where fastp is placed after count
    group_args = [
        ("count", args.count),
        ("fastp", args.fastp),
        ("singlem", args.singlem),
        ("nonpareil_reads", args.nonpareil_reads),
        ("nonpareil_markers", args.nonpareil_markers),
    ]

    merged: Dict[str, Any] = {}
    sample_name = None

    for group_name, path in group_args:
        if not path:
            continue

        data = load_json(path)

        # Check or set sample name
        s = data.get("sample")
        if s is not None:
            if sample_name is None:
                sample_name = s
            elif sample_name != s:
                raise ValueError(
                    f"Conflicting sample names: "
                    f"{sample_name!r} vs {s!r} (group {group_name})"
                )

        # Remove inner sample
        data = {k: v for k, v in data.items() if k != "sample"}

        merged[group_name] = data

    if not merged:
        raise SystemExit("No input JSONs provided; nothing to merge.")

    # Add sample name at top
    if sample_name is not None:
        merged = {"sample": sample_name, **merged}

    # Write output
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w") as f:
        json.dump(merged, f, indent=2)

    print(f"[✓] Wrote merged JSON → {out_path}")


if __name__ == "__main__":
    main()
