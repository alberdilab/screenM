#!/usr/bin/env python3
import csv
import json
from pathlib import Path

def clean_sample(name: str) -> str:
    """Remove trailing '_1' from the sample name."""
    return name[:-2] if name.endswith("_1") else name

def main():
    import argparse

    ap = argparse.ArgumentParser(description="Convert TSV table to JSON (remove '_1' suffix).")
    ap.add_argument("-i", "--input", required=True, help="Input TSV file")
    ap.add_argument("-o", "--output", required=True, help="Output JSON file")
    args = ap.parse_args()

    records = []

    with open(args.input, newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            # Clean the sample name
            row["sample"] = clean_sample(row["sample"])

            # Convert numeric fields where possible
            cleaned = {}
            for key, val in row.items():
                if val is None or val == "":
                    cleaned[key] = None
                    continue
                try:
                    # convert to int if possible, else to float
                    if val.isdigit():
                        cleaned[key] = int(val)
                    else:
                        cleaned[key] = float(val)
                except ValueError:
                    cleaned[key] = val
            records.append(cleaned)

    # If only one row, output a single JSON object instead of a list
    output_json = records[0] if len(records) == 1 else records

    with open(args.output, "w") as out:
        json.dump(output_json, out, indent=2)

    print(f"[✓] Wrote JSON → {args.output}")

if __name__ == "__main__":
    main()
