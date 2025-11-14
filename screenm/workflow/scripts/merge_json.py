#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Dict, Any, List


def load_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Input JSON not found: {path}")
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise TypeError(f"JSON in {path} is not an object/dict.")
    return data


def main():
    ap = argparse.ArgumentParser(
        description=(
            "Merge many sample-specific JSON files into one JSON, and optionally attach\n"
            "Mash-based distance summaries (mash_markers.json, mash_reads.json).\n\n"
            "Per-sample JSONs must contain a 'sample' field. The merged structure is:\n"
            "{\n"
            "  'n_samples': N,\n"
            "  'samples': {\n"
            "      '<sample1>': { ... },\n"
            "      '<sample2>': { ... },\n"
            "      ...\n"
            "  },\n"
            "  'mash_markers': { ... },   # if provided\n"
            "  'mash_reads': { ... }      # if provided\n"
            "}\n\n"
            "All per-sample structure is kept as-is; only 'sample' is removed from the\n"
            "nested object (it's used as the key instead)."
        )
    )
    ap.add_argument(
        "-i", "--input",
        nargs="+",
        required=True,
        help="Per-sample JSON files to merge (e.g. Sample1.json Sample2.json ...)",
    )
    ap.add_argument(
        "--mash-markers",
        help="Optional Mash markers summary JSON (e.g. mash_markers.json).",
    )
    ap.add_argument(
        "--mash-reads",
        help="Optional Mash reads/genes summary JSON (e.g. mash_reads.json).",
    )
    ap.add_argument(
        "-o", "--output",
        required=True,
        help="Output merged JSON file",
    )
    args = ap.parse_args()

    samples: Dict[str, Dict[str, Any]] = {}

    # --- Merge per-sample JSONs ---
    for p_str in args.input:
        path = Path(p_str)
        data = load_json(path)

        sample_name = data.get("sample")
        if not sample_name:
            raise ValueError(f"JSON file {path} has no 'sample' field.")

        if sample_name in samples:
            raise ValueError(
                f"Duplicate sample name {sample_name!r} from file {path} "
                f"(already seen)."
            )

        # Remove 'sample' from nested dict to avoid redundancy; keep all other keys
        nested = {k: v for k, v in data.items() if k != "sample"}
        samples[sample_name] = nested

    merged: Dict[str, Any] = {
        "n_samples": len(samples),
        "samples": samples,
    }

    # --- Optionally attach Mash markers summary ---
    if args.mash_markers:
        mash_markers_path = Path(args.mash_markers)
        mash_markers_json = load_json(mash_markers_path)
        # This will typically add a "mash_markers" top-level key.
        merged.update(mash_markers_json)

    # --- Optionally attach Mash reads summary ---
    if args.mash_reads:
        mash_reads_path = Path(args.mash_reads)
        mash_reads_json = load_json(mash_reads_path)
        # This will typically add a "mash_reads" top-level key.
        merged.update(mash_reads_json)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(merged, f, indent=2)

    msg = f"[✓] Merged {len(samples)} samples"
    if args.mash_markers:
        msg += f" + mash_markers({args.mash_markers})"
    if args.mash_reads:
        msg += f" + mash_reads({args.mash_reads})"
    msg += f" → {out_path}"
    print(msg)


if __name__ == "__main__":
    main()
