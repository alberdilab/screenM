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
            "Merge multiple per-sample JSON files into one grouped JSON:\n"
            "top-level 'sample', plus groups: 'count', 'singlem', "
            "'nonpareil_reads', 'nonpareil_markers'."
        )
    )
    ap.add_argument("--count", help="JSON file with read counts info")
    ap.add_argument("--singlem", help="JSON file with SingleM / marker info")
    ap.add_argument("--nonpareil-reads", dest="nonpareil_reads",
                    help="JSON file with Nonpareil results based on reads")
    ap.add_argument("--nonpareil-markers", dest="nonpareil_markers",
                    help="JSON file with Nonpareil results based on markers")
    ap.add_argument("-o", "--output", required=True,
                    help="Output JSON file")
    args = ap.parse_args()

    group_args = {
        "count": args.count,
        "singlem": args.singlem,
        "nonpareil_reads": args.nonpareil_reads,
        "nonpareil_markers": args.nonpareil_markers,
    }

    merged: Dict[str, Any] = {}
    sample_name = None

    for group_name, path in group_args.items():
        if not path:
            continue  # group not provided

        data = load_json(path)

        # Check / unify sample
        s = data.get("sample")
        if s is not None:
            if sample_name is None:
                sample_name = s
            elif sample_name != s:
                raise ValueError(
                    f"Conflicting sample names between files: "
                    f"{sample_name!r} vs {s!r} (group {group_name})"
                )

        # Remove 'sample' from nested group to avoid duplication
        data = {k: v for k, v in data.items() if k != "sample"}

        merged[group_name] = data

    if not merged:
        raise SystemExit("No input JSONs provided; nothing to merge.")

    if sample_name is not None:
        merged = {"sample": sample_name, **merged}
    else:
        # If none of the JSONs had 'sample', just leave it out
        pass

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(merged, f, indent=2)

    print(f"[✓] Wrote merged JSON → {out_path}")


if __name__ == "__main__":
    main()
