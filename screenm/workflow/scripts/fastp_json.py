#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict


def extract_fields(data: Dict[str, Any], sample_name: str) -> Dict[str, Any]:
    summary = data.get("summary", {})
    before = summary.get("before_filtering", {}) or {}
    after = summary.get("after_filtering", {}) or {}
    filtering = data.get("filtering_result", {}) or {}
    duplication = data.get("duplication", {}) or {}
    adapter = data.get("adapter_cutting", {}) or {}

    # Prefer "before_filtering" for total_reads and gc_content, fall back to "after_filtering"
    total_reads = before.get("total_reads", after.get("total_reads"))
    gc_content = before.get("gc_content", after.get("gc_content"))

    result = {
        "sample": sample_name,
        "total_reads": total_reads,
        "gc_content": gc_content,
        "passed_filter_reads": filtering.get("passed_filter_reads"),
        "low_quality_reads": filtering.get("low_quality_reads"),
        "too_many_N_reads": filtering.get("too_many_N_reads"),
        "low_complexity_reads": filtering.get("low_complexity_reads"),
        "too_short_reads": filtering.get("too_short_reads"),
        "too_long_reads": filtering.get("too_long_reads"),
        "adapter_trimmed_reads": adapter.get("adapter_trimmed_reads"),
        "duplication": duplication.get("rate"),
    }
    return result


def main():
    ap = argparse.ArgumentParser(
        description="Extract selected metrics from fastp JSON into a simplified JSON."
    )
    ap.add_argument(
        "-i", "--input",
        required=True,
        help="Input fastp JSON file (e.g. Sample1_full.json)"
    )
    ap.add_argument(
        "-o", "--output",
        required=True,
        help="Output simplified JSON file"
    )
    ap.add_argument(
        "--sample",
        help=(
            "Sample name to use in output JSON. "
            "If not provided, the input filename stem is used."
        ),
    )
    args = ap.parse_args()

    in_path = Path(args.input)
    with in_path.open() as f:
        data = json.load(f)

    # Either explicit --sample or fall back to file stem
    sample_name = args.sample if args.sample else in_path.stem

    simplified = extract_fields(data, sample_name)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as out:
        json.dump(simplified, out, indent=2)

    print(f"[✓] Wrote simplified JSON for sample '{sample_name}' → {out_path}")


if __name__ == "__main__":
    main()
