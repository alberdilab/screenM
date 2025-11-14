#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from string import Template


HTML_TEMPLATE = Template(r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>ScreenM Report</title>

<!-- Basic styling, intentionally lightweight -->
<style>
    body {
        font-family: Arial, sans-serif;
        max-width: 1100px;
        margin: auto;
        padding: 20px;
        background: #fafafa;
    }
    h1 {
        text-align: center;
        margin-bottom: 40px;
    }

    .section {
        margin-bottom: 25px;
        border-radius: 8px;
        padding: 15px;
        border: 1px solid #ccc;
        background: #fff;
    }

    /* Expand / collapse */
    details > summary {
        font-size: 1.1em;
        cursor: pointer;
        padding: 5px;
        margin: -5px;
        font-weight: bold;
    }

    /* Flag-based background colours */
    .flag-1 {
        background-color: #d7f5dd; /* greenish */
    }
    .flag-2 {
        background-color: #fff9c4; /* yellow */
    }
    .flag-3 {
        background-color: #ffd2d2; /* red */
    }

    .figure-container {
        margin-top: 15px;
        padding: 10px;
        background: #f5f5f5;
        border-radius: 6px;
        border: 1px solid #ddd;
    }

    .small-note {
        font-size: 0.9em;
        color: #666;
    }
</style>

</head>
<body>

<h1>ScreenM Summary Report</h1>

<!-- Dynamic content containers -->
<div id="summary-sections"></div>

<h2>Figures</h2>
<div id="figure-sections"></div>

<script>
// Embedded data from Python
const DISTILL_DATA = $DISTILL_JSON;
const FIGURES_DATA = $FIGURES_JSON;

function flagClass(flag) {
    if (flag === 1) return "flag-1";
    if (flag === 2) return "flag-2";
    return "flag-3";
}

/* ---------- Section Rendering (From distill.json) ---------- */

function addSummarySection(parent, title, data, flagKey, messageKey) {
    if (!data) return;

    const flag = data[flagKey];
    const msg = data[messageKey];

    const div = document.createElement("div");
    div.className = "section " + flagClass(flag);

    div.innerHTML = `
        <details>
            <summary>${title}</summary>
            <div class="content">
                <p>${msg}</p>
                <pre>${JSON.stringify(data, null, 2)}</pre>
            </div>
        </details>
    `;

    parent.appendChild(div);
}

/* ---------- Figures Rendering (From figures.json) ---------- */

function addFigureDepthFractions(parent, data) {
    if (!data) return;

    const div = document.createElement("div");
    div.className = "section";

    div.innerHTML = `
        <details open>
            <summary>Sequencing Depth Components</summary>
            <div class="figure-container">
                <div id="figure-depth"></div>
                <p class="small-note">
                    This view shows total reads divided into low-quality, prokaryotic and other fractions.
                    Nonpareil 95% LR_reads targets are included and can be plotted as dashed lines
                    in downstream visualisations.
                </p>
            </div>
        </details>
    `;

    parent.appendChild(div);

    /* For now, render a small preview table. Plotting can be added later (Plotly, etc.). */
    const preview = document.createElement("pre");
    const previewRows = (data.per_sample || []).slice(0, 5);
    preview.textContent =
        JSON.stringify(previewRows, null, 2) +
        (data.per_sample && data.per_sample.length > 5
            ? "\n...\n(Full data available in figures.json)"
            : "");
    div.querySelector("#figure-depth").appendChild(preview);
}


function addFigureRedundancyBiplot(parent, data) {
    if (!data) return;

    const div = document.createElement("div");
    div.className = "section";

    div.innerHTML = `
        <details open>
            <summary>Redundancy Biplot</summary>
            <div class="figure-container">
                <div id="figure-biplot"></div>
                <p class="small-note">
                    Each point represents a sample: read-based vs marker-based Nonpareil redundancy.
                    Use "kappa_reads" and "kappa_markers" as axes; coverage and LR targets can be used
                    for point size, colour or annotations.
                </p>
            </div>
        </details>
    `;

    parent.appendChild(div);

    const preview = document.createElement("pre");
    const previewRows = (data.per_sample || []).slice(0, 5);
    preview.textContent =
        JSON.stringify(previewRows, null, 2) +
        (data.per_sample && data.per_sample.length > 5
            ? "\n...\n(Full data in figures.json)"
            : "");
    div.querySelector("#figure-biplot").appendChild(preview);
}

/* ---------- Main Rendering Pipeline ---------- */

function main() {
    const distill = DISTILL_DATA;
    const figures = FIGURES_DATA;

    const summaryDiv = document.getElementById("summary-sections");
    const figureDiv = document.getElementById("figure-sections");

    const S = distill.summary || {};

    addSummarySection(
        summaryDiv, 
        "Screening Threshold",
        S.screening_threshold,
        "flag_reads_threshold",
        "message_reads_threshold"
    );

    addSummarySection(
        summaryDiv,
        "Sequencing Depth",
        S.sequencing_depth,
        "flag_sequencing_depth",
        "message_sequencing_depth"
    );

    addSummarySection(
        summaryDiv,
        "Low-quality Reads",
        S.low_quality_reads,
        "flag_low_quality",
        "message_low_quality"
    );

    addSummarySection(
        summaryDiv,
        "Prokaryotic Fraction",
        S.prokaryotic_fraction,
        "flag_prokaryotic_fraction",
        "message_prokaryotic_fraction"
    );

    addSummarySection(
        summaryDiv,
        "Redundancy (Reads)",
        S.redundancy_reads,
        "flag_redundancy",
        "message_redundancy"
    );

    addSummarySection(
        summaryDiv,
        "Redundancy (Markers)",
        S.redundancy_markers,
        "flag_redundancy_markers",
        "message_redundancy_markers"
    );

    // Clusters section (if present)
    if (S.clusters) {
        const flagKey = "flag_clusters";
        const messageKey = "message_clusters";
        const div = document.createElement("div");
        const flag = S.clusters[flagKey];
        const msg = S.clusters[messageKey];

        div.className = "section " + flagClass(flag);
        div.innerHTML = `
            <details>
                <summary>Sample Clusters (Mash-based)</summary>
                <div class="content">
                    <p>${msg}</p>
                    <pre>${JSON.stringify(S.clusters, null, 2)}</pre>
                </div>
            </details>
        `;
        summaryDiv.appendChild(div);
    }

    /* FIGURES */

    if (figures.figures && figures.figures.dna_depth_fractions) {
        addFigureDepthFractions(
            figureDiv,
            figures.figures.dna_depth_fractions
        );
    }

    if (figures.figures && figures.figures.redundancy_biplot) {
        addFigureRedundancyBiplot(
            figureDiv,
            figures.figures.redundancy_biplot
        );
    }
}

main();
</script>

</body>
</html>
""")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Create a static HTML report from distill.json and figures.json.\n"
            "The report shows collapsible sections coloured by flags and figure-friendly previews."
        )
    )
    parser.add_argument(
        "--distill-json",
        required=True,
        help="Path to distill.json (summary/distilled metrics).",
    )
    parser.add_argument(
        "--figures-json",
        required=True,
        help="Path to figures.json (figure-friendly data, e.g. depth fractions, redundancy biplot).",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Path to output HTML report (e.g. report.html).",
    )
    args = parser.parse_args()

    distill_path = Path(args.distill_json)
    figures_path = Path(args.figures_json)

    with distill_path.open() as f:
        distill_data = json.load(f)
    with figures_path.open() as f:
        figures_data = json.load(f)

    # Serialize JSON for embedding in JS
    distill_json_str = json.dumps(distill_data, indent=2)
    figures_json_str = json.dumps(figures_data, indent=2)

    html = HTML_TEMPLATE.substitute(
        DISTILL_JSON=distill_json_str,
        FIGURES_JSON=figures_json_str,
    )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    main()
