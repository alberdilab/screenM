#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>ScreenM Report</title>

<style>
    body {
        font-family: Arial, sans-serif;
        max-width: 1100px;
        margin: auto;
        padding: 20px 20px 60px 20px;
        background: #fafafa;
    }
    h1 {
        text-align: center;
        margin-bottom: 30px;
    }

    .run-meta {
        margin-bottom: 16px;
        padding: 12px 14px;
        border-radius: 10px;
        border: 1px dashed #c2cfe0;
        background: #eef3fb;
        display: flex;
        gap: 14px;
        flex-wrap: wrap;
    }
    .run-meta-item {
        min-width: 220px;
    }
    .run-meta-label {
        font-size: 0.88em;
        color: #4a5568;
        margin-bottom: 2px;
    }
    .run-meta-value {
        font-weight: 650;
        font-size: 1.05em;
        color: #0f172a;
    }

    .project-highlights {
        margin-bottom: 22px;
        padding: 14px 16px 16px 16px;
        border-radius: 10px;
        border: 1px solid #cfd7e6;
        background: #f6f8ff;
    }
    .project-highlights-title {
        margin: 0 0 10px 0;
        font-size: 1.1em;
    }
    .highlights-grid {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
    }
    .highlight-card {
        flex: 1;
        min-width: 200px;
        background: #ffffff;
        border: 1px solid #dfe6f5;
        border-radius: 8px;
        padding: 10px 12px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    .highlight-label {
        font-size: 0.92em;
        color: #444;
        margin-bottom: 2px;
    }
    .highlight-value {
        font-size: 1.5em;
        font-weight: 700;
        color: #1a237e;
    }
    .highlight-note {
        font-size: 0.85em;
        color: #555;
        margin-top: 2px;
    }

    .section {
        margin-bottom: 24px;
        border-radius: 8px;
        padding: 12px 16px 18px 16px;
        border: 1px solid #ccc;
        background: #fff;
    }

    .section-title {
        margin: 2px 0 4px 0;
        font-size: 1.25em;
    }

    .section-intro {
        margin: 0 0 6px 0;
        font-size: 0.95em;
        color: #444;
    }

    details {
        margin-top: 6px;
    }

    details > summary {
        font-size: 0.98em;
        cursor: pointer;
        padding: 4px 0;
        font-weight: 600;
        list-style: none;
    }

    details[open] > summary {
        margin-bottom: 8px;
    }
    .summary-hint {
        margin-left: 8px;
        font-size: 0.85em;
        color: #666;
        font-weight: 500;
    }
    details[open] .summary-hint {
        color: #444;
    }

    .flag-1 {
        background-color: #d7f5dd;
    }
    .flag-2 {
        background-color: #fff9c4;
    }
    .flag-3 {
        background-color: #ffd2d2;
    }

    .summary-message {
        margin-bottom: 12px;
    }

    .small-note {
        font-size: 0.85em;
        color: #666;
        margin-top: 8px;
    }

    .status-emoji {
        margin-right: 6px;
    }
    .status-text {
        font-weight: 500;
    }

    .screen-overview-stats,
    .seq-depth-stats,
    .prok-stats,
    .redundancy-stats,
    .cluster-stats,
    .quality-stats {
        display: flex;
        gap: 16px;
        justify-content: space-between;
        margin-bottom: 14px;
        flex-wrap: wrap;
    }

    .screen-overview-stat-item,
    .seq-depth-stat-item,
    .prok-stat-item,
    .redundancy-stat-item,
    .cluster-stat-item,
    .quality-stat-item {
        flex: 1;
        min-width: 160px;
    }

    .screen-overview-stat-label,
    .seq-depth-stat-label,
    .prok-stat-label,
    .redundancy-stat-label,
    .cluster-stat-label,
    .quality-stat-label {
        font-size: 0.9em;
        color: #555;
        margin-bottom: 2px;
    }

    .screen-overview-stat-value,
    .seq-depth-stat-value,
    .prok-stat-value,
    .redundancy-stat-value,
    .cluster-stat-value,
    .quality-stat-value {
        font-size: 1.4em;
        font-weight: 600;
    }

    .screen-overview-stat-note,
    .seq-depth-stat-note,
    .prok-stat-note,
    .redundancy-stat-note,
    .cluster-stat-note,
    .quality-stat-note {
        font-size: 0.8em;
        color: #666;
        margin-top: 2px;
    }

    .seq-depth-plot-container,
    .prok-depth-plot-container,
    .lr-target-plot-container,
    .lr-target-markers-plot-container,
    .quality-plot-container {
        width: 100%;
        border: 1px solid #ddd;
        border-radius: 4px;
        background: #fcfcfc;
        padding: 6px 6px 2px 6px;
        box-sizing: border-box;
        margin-top: 10px;
        margin-bottom: 6px;
    }

    .seq-depth-svg,
    .prok-depth-svg,
    .lr-target-svg,
    .lr-target-markers-svg,
    .quality-svg {
        display: block;
        width: 100%;
        height: 320px;
    }

    .plotly-chart {
        width: 100%;
        min-width: 0;
        min-height: 320px;
    }
    .coverage-plot {
        height: 220px !important;
        min-height: 220px !important;
    }

    .clusters-heatmap-scroll {
        overflow-x: auto;
        margin-top: 10px;
        border: 1px solid #ddd;
        border-radius: 4px;
        background: #fcfcfc;
    }
    .clusters-heatmap-svg {
        display: block;
        width: 100%;
        height: 210px;
    }
    .cluster-plot-area {
        margin-top: 10px;
        border: 1px solid #ddd;
        border-radius: 4px;
        background: #fff;
        padding: 10px;
    }
    .cluster-ordinations {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 10px;
        margin: 10px 0 6px 0;
    }

    .chart-tooltip {
        position: fixed;
        pointer-events: none;
        background: rgba(0,0,0,0.85);
        color: #fff;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8em;
        z-index: 1000;
        white-space: pre-line;
        transform: translate(8px, -20px);
    }

    .tab-btn {
        border: 1px solid #cbd5e1;
        background: #f1f5f9;
        color: #0f172a;
        padding: 6px 10px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.9em;
    }
    .tab-btn.active {
        background: #1d4ed8;
        color: #fff;
        border-color: #1d4ed8;
    }

    .recommendations {
        display: flex;
        flex-direction: column;
        gap: 10px;
        margin-top: 10px;
    }
    .recommendation-overall {
        font-weight: 600;
        color: #0f172a;
    }
    .recommendation-item {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        padding: 8px 10px;
        border-radius: 8px;
        border: 1px solid #dce3f0;
        background: #f8fafc;
    }
    .rec-badge {
        padding: 3px 6px;
        border-radius: 6px;
        font-size: 0.8em;
        font-weight: 700;
        color: #fff;
        min-width: 54px;
        text-align: center;
    }
    .rec-badge.high { background: #2e7d32; }
    .rec-badge.info { background: #1976d2; }
    .rec-badge.warn { background: #c62828; }
</style>

<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>

</head>
<body>

<h1>ScreenM Summary Report</h1>
<p class="section-intro" style="text-align:center; max-width: 900px; margin: -10px auto 24px auto;">
    ScreenM screens metagenomic datasets for suitability in downstream analyses by analysing sequencing read quality,
    metagenomic redundancy, prokaryotic marker gene coverage and differences between samples. This report summarises key statistics
    from the screening, and provides recommendations for the most appropriate downstream analyses.
</p>

<div id="project-highlights"></div>
<div id="summary-sections"></div>

<script>
const DISTILL_DATA = __DISTILL_JSON__;
const FIGURES_DATA = __FIGURES_JSON__;

const COMPLETENESS_TARGET = (() => {
    const val = DISTILL_DATA?.meta?.metadata?.parameters?.completeness;
    const num = Number(val);
    if (Number.isFinite(num) && num > 0) {
        return num;
    }
    return 95;
})();
const COMPLETENESS_FRACTION = COMPLETENESS_TARGET / 100;
const COMPLETENESS_LABEL = Number.isInteger(COMPLETENESS_TARGET)
    ? COMPLETENESS_TARGET.toFixed(0)
    : COMPLETENESS_TARGET.toFixed(1);

function flagClass(flag) {
    if (flag === 1) return "flag-1";
    if (flag === 2) return "flag-2";
    return "flag-3";
}

function fmtInt(x) {
    if (x === null || x === undefined) return "NA";
    return Math.round(x).toLocaleString();
}

function fmtFloat(x, digits) {
    if (x === null || x === undefined) return "NA";
    return Number(x).toFixed(digits);
}

function fmtMillions(x) {
    if (x === null || x === undefined) return "NA";
    const v = Number(x);
    if (!isFinite(v)) return "∞";
    if (v >= 1e9) return (v / 1e9).toFixed(2) + " B";
    if (v >= 1e6) return (v / 1e6).toFixed(2) + " M";
    if (v >= 1e3) return (v / 1e3).toFixed(1) + " k";
    return v.toString();
}

function median(arr) {
    if (!arr || !arr.length) return null;
    const sorted = [...arr].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    if (sorted.length % 2 === 0) {
        return (sorted[mid - 1] + sorted[mid]) / 2;
    }
    return sorted[mid];
}

function coeffVar(arr) {
    if (!arr || !arr.length) return null;
    const mean = arr.reduce((a, b) => a + b, 0) / arr.length;
    if (mean === 0) return null;
    const variance = arr.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / arr.length;
    return Math.sqrt(variance) / mean;
}

function makeTicksAroundTen(maxVal) {
    if (maxVal <= 0) return [0];
    const niceSteps = [
        0.0005, 0.001, 0.0025, 0.005,
        0.01, 0.02, 0.025, 0.05,
        0.1, 0.2, 0.25, 0.5, 1, 2, 2.5, 5, 10
    ];
    const targetTicks = 10;
    let best = niceSteps[0];
    let bestDiff = Number.POSITIVE_INFINITY;
    niceSteps.forEach(step => {
        const nTicks = maxVal / step;
        const diff = Math.abs(nTicks - targetTicks);
        if (diff < bestDiff) {
            bestDiff = diff;
            best = step;
        }
    });
    const ticks = [];
    for (let v = 0; v <= maxVal + 1e-9; v += best) {
        ticks.push(v);
    }
    if (ticks[ticks.length - 1] < maxVal - best * 0.25) {
        ticks.push(maxVal);
    }
    return ticks;
}

function getOrCreateTooltip() {
    let tooltip = document.querySelector(".chart-tooltip");
    if (!tooltip) {
        tooltip = document.createElement("div");
        tooltip.className = "chart-tooltip";
        tooltip.style.display = "none";
        document.body.appendChild(tooltip);
    }
    return tooltip;
}

function setSummaryHintBehaviour(root) {
    const detailsList = root.querySelectorAll("details");
    detailsList.forEach(det => {
        const hint = det.querySelector(".summary-hint");
        if (!hint) return;
        const update = () => {
            hint.textContent = det.open ? "(click to collapse)" : "(click to expand)";
        };
        det.addEventListener("toggle", update);
        update();
    });
}

function addRecommendationsSection(parent, data) {
    if (!data) return;
    const wrapper = document.createElement("div");
    wrapper.className = "section";

    const items = Array.isArray(data.items) ? data.items : [];
    const overall = data.overall || "Recommendations based on current screening results.";

    const recList = items.map(it => {
        const badgeClass = it.priority === "warn" ? "warn" :
                           it.priority === "info" ? "info" : "high";
        const text = it.text || "";
        return `
            <div class="recommendation-item">
                <span class="rec-badge ${badgeClass}">${badgeClass}</span>
                <div class="rec-text">${text}</div>
            </div>
        `;
    }).join("");

    wrapper.innerHTML = `
        <h2 class="section-title">Recommendations</h2>
        <p class="section-intro">Suggested downstream strategies based on coverage, quality, and clustering results.</p>
        <div class="recommendations">
            <div class="recommendation-overall">${overall}</div>
            ${recList || '<div class="small-note">No specific recommendations available.</div>'}
        </div>
    `;

    parent.appendChild(wrapper);
}

/* ---------- Section-level status (emoji + short text) ---------- */
function sectionStatus(sectionLabel, flag) {
    let emoji, descriptor;
    if (flag === 1) {
        emoji = "😊";
        descriptor = "contains no warnings";
    } else if (flag === 2) {
        emoji = "😐";
        descriptor = "contains some warnings";
    } else {
        emoji = "☹️";
        descriptor = "contains many warnings";
    }
    return {
        emoji,
        text: `${sectionLabel} ${descriptor}`
    };
}

function fmtDateTime(isoStr) {
    if (!isoStr) return "NA";
    const d = new Date(isoStr);
    if (isNaN(d.getTime())) return isoStr;
    return d.toLocaleString();
}

/* ---------- Project highlights (compact overview) ---------- */
function addProjectHighlights(container, distill, summary) {
    if (!container) return;

    const meta = distill.meta || {};
    const metadata = meta.metadata || {};
    const parameters = metadata.parameters || {};
    const screening = summary.screening_overview || {};

    const projectName =
        metadata.project ||
        metadata.project_name ||
        metadata.study ||
        metadata.run ||
        metadata.name ||
        "Project overview";

    const highlights = [
        {
            label: "Samples analysed",
            value: fmtInt(
                screening.n_samples_total !== undefined && screening.n_samples_total !== null
                    ? screening.n_samples_total
                    : meta.n_samples_in_results
            ),
            note: "Libraries included in this run"
        },
        {
            label: "Total reads",
            value: fmtMillions(
                summary.total_reads_all_samples !== undefined && summary.total_reads_all_samples !== null
                    ? summary.total_reads_all_samples
                    : (summary.sequencing_quality || {}).total_reads
            ),
            note: "Sum of input reads across samples"
        },
        {
            label: "Read threshold",
            value: fmtMillions(screening.reads_threshold),
            note: "Reads used for screening each sample"
        },
        {
            label: "Completeness target",
            value: (() => {
                const comp =
                    parameters.completeness ??
                    metadata.completeness ??
                    metadata.completeness_target ??
                    metadata.targets ??
                    metadata.completeness_threshold;
                if (comp === null || comp === undefined) return "NA";
                const num = Number(comp);
                if (!isNaN(num)) {
                    const pct = num > 1 ? num : num * 100;
                    return `${fmtFloat(pct, pct >= 10 ? 0 : 1)}%`;
                }
                return String(comp);
            })(),
            note: "Percentage of completeness aimed"
        },
    ];

    const wrapper = document.createElement("div");
    wrapper.className = "project-highlights";

    const runMeta = document.createElement("div");
    runMeta.className = "run-meta";
    const runItems = [
        {
            label: "Run name",
            value: metadata.run_name || metadata.run || projectName
        },
        {
            label: "Run date",
            value: fmtDateTime(metadata.created_at || metadata.run_date || metadata.date)
        },
        {
            label: "Seed",
            value: metadata.seed ?? metadata.random_seed ?? metadata.parameters?.seed ?? "NA"
        },
        {
            label: "ScreenM version",
            value: metadata.software_version || metadata.screenm_version || metadata.version || "unknown"
        },
    ];
    runItems.forEach(item => {
        const div = document.createElement("div");
        div.className = "run-meta-item";
        div.innerHTML = `
            <div class="run-meta-label">${item.label}</div>
            <div class="run-meta-value">${item.value}</div>
        `;
        runMeta.appendChild(div);
    });
    wrapper.appendChild(runMeta);

    const grid = document.createElement("div");
    grid.className = "highlights-grid";
    highlights.forEach(item => {
        const card = document.createElement("div");
        card.className = "highlight-card";
        card.innerHTML = `
            <div class="highlight-label">${item.label}</div>
            <div class="highlight-value">${item.value}</div>
            <div class="highlight-note">${item.note}</div>
        `;
        grid.appendChild(card);
    });
    wrapper.appendChild(grid);
    container.appendChild(wrapper);
}

/* ---------- Screening overview (merged) ---------- */
function addScreeningOverviewSection(parent, data, depthPerSample) {
    if (!data) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(data.flag_screening_overview);

    const msg = data.message_screening_overview || "";

    const total = data.n_samples_total;
    const above = data.n_samples_above_threshold;
    const perc = data.percent_above_threshold;

    const medianReads = data.median_reads;
    const cvReads = data.cv_reads;

    const status = sectionStatus("Screening overview", data.flag_screening_overview);

    div.innerHTML = `
        <h2 class="section-title">Screening overview</h2>
        <p class="section-intro">
            This section provides an overview of the quality of the screenM analysis. It reports the number of samples that passed 
            the read threshold and were included in the analysis, and it also describes how evenly sequencing depth is distributed 
            across the dataset. The proportion of analysed samples and the distribution of sequencing depth are important because 
            they determine how representative the summary statistics are for the entire dataset and individual samples.
        </p>
        <details>
            <summary>
                <span class="status-emoji">${status.emoji}</span>
                <span class="status-text">${status.text}</span>
                <span class="summary-hint">(click to expand)</span>
            </summary>
            <div class="content">
                <p class="summary-message">${msg}</p>
                <div class="screen-overview-stats">
                    <div class="screen-overview-stat-item">
                        <div class="screen-overview-stat-label">Above read threshold</div>
                        <div class="screen-overview-stat-value">
                            ${fmtInt(above)} (${fmtFloat(perc, 1)}%)
                        </div>
                        <div class="screen-overview-stat-note">Samples passing the screening threshold</div>
                    </div>
                    <div class="screen-overview-stat-item">
                        <div class="screen-overview-stat-label">Median depth</div>
                        <div class="screen-overview-stat-value">${fmtMillions(medianReads)}</div>
                        <div class="screen-overview-stat-note">Median reads per sample</div>
                    </div>
                    <div class="screen-overview-stat-item">
                        <div class="screen-overview-stat-label">Depth variation (CV)</div>
                        <div class="screen-overview-stat-value">${fmtFloat(cvReads, 3)}</div>
                        <div class="screen-overview-stat-note">Coefficient of variation across samples</div>
                    </div>
                </div>
                <div class="seq-depth-plot-container">
                    <div id="seq-depth-plot" class="plotly-chart"></div>
                </div>
                <p class="small-note">
                    Interactive barplot of per-sample total reads that stretches to the available width and resizes
                    with the page. Bars are green if above the screening threshold and red if below. Horizontal dashed
                    lines mark the median sequencing depth and the read threshold.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const plotDiv = div.querySelector("#seq-depth-plot");
    const perSample = (depthPerSample || [])
        .filter(d => d.total_reads !== null && d.total_reads !== undefined);

    if (!perSample.length) {
        plotDiv.outerHTML = `<div class="small-note">Per-sample read counts not available for sequencing depth barplot.</div>`;
        return;
    }

    if (typeof Plotly === "undefined") {
        plotDiv.outerHTML = `<div class="small-note">Plotly failed to load; cannot render sequencing depth plot.</div>`;
        return;
    }

    const thresholdReads = Number(data.reads_threshold) || null;
    const medianDepth = Number(medianReads) || 0;

    const samples = perSample.map((d, idx) => d.sample || `sample ${idx + 1}`);
    const depths = perSample.map(d => {
        const v = Number(d.total_reads);
        return Number.isFinite(v) && v > 0 ? v : 0;
    });

    const colors = depths.map(val => {
        if (thresholdReads && thresholdReads > 0) {
            return val >= thresholdReads ? "#2e7d32" : "#c62828";
        }
        return "#1976d2";
    });

    const hover = depths.map((val, idx) => {
        const lines = [
            `<b>${samples[idx]}</b>`,
            `Depth: ${fmtMillions(val)} reads`
        ];
        if (thresholdReads && thresholdReads > 0) {
            lines.push(`Threshold: ${fmtMillions(thresholdReads)} reads`);
            lines.push(val >= thresholdReads ? "Above threshold" : "Below threshold");
        }
        if (medianDepth > 0) {
            lines.push(`Median: ${fmtMillions(medianDepth)} reads`);
        }
        return lines.join("<br>");
    });

    const trace = {
        type: "bar",
        x: samples,
        y: depths,
        marker: {color: colors},
        hovertemplate: "%{customdata}<extra></extra>",
        customdata: hover,
    };

    const shapes = [];
    const annotations = [];
    const maxDepthObserved = Math.max(...depths);
    const includeThresholdLine =
        thresholdReads && thresholdReads > 0 && thresholdReads <= maxDepthObserved * 1.05;
    const maxDepth = Math.max(maxDepthObserved, medianDepth || 0, includeThresholdLine ? thresholdReads : 0);

    if (includeThresholdLine) {
        shapes.push({
            type: "line",
            xref: "paper",
            x0: 0,
            x1: 1,
            y0: thresholdReads,
            y1: thresholdReads,
            line: {color: "#1d4ed8", width: 1.6, dash: "dot"}
        });
        annotations.push({
            xref: "paper",
            x: 0.995,
            y: thresholdReads,
            xanchor: "right",
            yanchor: "bottom",
            text: `threshold (${fmtMillions(thresholdReads)})`,
            showarrow: false,
            font: {color: "#1d4ed8", size: 11},
            align: "right"
        });
    }

    if (medianDepth > 0) {
        shapes.push({
            type: "line",
            xref: "paper",
            x0: 0,
            x1: 1,
            y0: medianDepth,
            y1: medianDepth,
            line: {color: "#424242", width: 1.4, dash: "dash"}
        });
        annotations.push({
            xref: "paper",
            x: 0.995,
            y: medianDepth,
            xanchor: "right",
            yanchor: "bottom",
            text: `median (${fmtMillions(medianDepth)})`,
            showarrow: false,
            font: {color: "#424242", size: 11},
            align: "right"
        });
    }

    const n = perSample.length;
    const tickAngle = n > 80 ? -75 : n > 40 ? -60 : -45;
    const tickSize = n > 120 ? 7 : n > 60 ? 8 : 10;
    const bottomMargin = n > 80 ? 200 : n > 40 ? 150 : 110;

    const layout = {
        height: 360,
        margin: {l: 90, r: 28, t: 16, b: bottomMargin},
        bargap: 0.12,
        hovermode: "closest",
        showlegend: false,
        xaxis: {
            title: "Samples",
            type: "category",
            tickangle: tickAngle,
            tickfont: {size: tickSize},
            automargin: true,
        },
        yaxis: {
            title: "Sequencing depth (reads)",
            rangemode: "tozero",
            tickformat: ".3s",
            separatethousands: true,
        },
        shapes,
        annotations,
    };

    const config = {
        displaylogo: false,
        responsive: true,
        modeBarButtonsToRemove: ["toggleSpikelines", "autoScale2d"],
    };

    Plotly.newPlot(plotDiv, [trace], layout, config);
    window.addEventListener("resize", () => Plotly.Plots.resize(plotDiv));
}

/* Sequencing quality */
function addLowQualitySection(parent, data, depthPerSample) {
    if (!data) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(data.flag_sequencing_quality);

    const msg = data.message_low_quality || "";

    const meanFrac = data.mean_fraction_removed;
    const meanLowQ = data.mean_fraction_low_quality;
    const meanComplex = data.mean_fraction_low_complexity;
    const meanTooShort = data.mean_fraction_too_short;
    const meanAdapter = data.mean_fraction_adapter_trimmed;
    const meanDup = data.mean_duplication_rate;
    const pct = (value) => (value === null || value === undefined ? null : 100 * value);

    const status = sectionStatus("Sequencing quality", data.flag_sequencing_quality);

    div.innerHTML = `
        <h2 class="section-title">Sequencing quality</h2>
        <p class="section-intro">
            This section reports statistics about different type of low-quality reads and their potential impact on downstream analyses.
            High proportions of low-quality reads may indicate suboptimal sequencing performance, reducing the effective sequencing depth 
            for metagenomicn assembly and microbiome profiling.
        </p>
        <details>
            <summary>
                <span class="status-emoji">${status.emoji}</span>
                <span class="status-text">${status.text}</span>
                <span class="summary-hint">(click to expand)</span>
            </summary>
            <div class="content">
                <p class="summary-message">${msg}</p>
                <div class="quality-stats">
                    <div class="quality-stat-item">
                        <div class="quality-stat-label">Low-quality reads</div>
                        <div class="quality-stat-value">${fmtFloat(pct(meanFrac), 2)}%</div>
                        <div class="quality-stat-note">Average fraction removed per sample</div>
                    </div>
                    <div class="quality-stat-item">
                        <div class="quality-stat-label">Low phred score</div>
                        <div class="quality-stat-value">${fmtFloat(pct(meanLowQ), 2)}%</div>
                        <div class="quality-stat-note">Average proportion flagged as low phred</div>
                    </div>
                    <div class="quality-stat-item">
                        <div class="quality-stat-label">Low-complexity reads</div>
                        <div class="quality-stat-value">${fmtFloat(pct(meanComplex), 2)}%</div>
                        <div class="quality-stat-note">Average fraction filtered for low complexity</div>
                    </div>
                    <div class="quality-stat-item">
                        <div class="quality-stat-label">Too short</div>
                        <div class="quality-stat-value">${fmtFloat(pct(meanTooShort), 2)}%</div>
                        <div class="quality-stat-note">Average fraction removed due to length filters</div>
                    </div>
                    <div class="quality-stat-item">
                        <div class="quality-stat-label">Adapter-trimmed reads</div>
                        <div class="quality-stat-value">${fmtFloat(pct(meanAdapter), 2)}%</div>
                        <div class="quality-stat-note">Average fraction affected by adapter trimming</div>
                    </div>
                    <div class="quality-stat-item">
                        <div class="quality-stat-label">Duplication rate</div>
                        <div class="quality-stat-value">${fmtFloat(pct(meanDup), 2)}%</div>
                        <div class="quality-stat-note">Average proportion of duplicate reads</div>
                    </div>
                </div>
                <div class="quality-plot-container">
                    <div id="quality-plot" class="plotly-chart"></div>
                </div>
                <p class="small-note">
                    Interactive stacked barplot showing the type of deficience of low-quality reads. Overall bar colour stays
                    green (&le; 5%), yellow (5-20%) or red (&gt; 20%) depending on the total removed fraction, while
                    each stack segments low-phred-score, too many Ns, low-complexity and too-short reads. Horizontal dashed
                    lines (when at applicable scale) mark the 5% and 20% thresholds, and the median removed fraction appears as
                    a dark grey dashed line.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const plotDiv = div.querySelector("#quality-plot");
    const perSample = (depthPerSample || [])
        .filter(d => d.fraction_low_quality_of_total !== null &&
                     d.fraction_low_quality_of_total !== undefined);

    if (!perSample.length) {
        plotDiv.outerHTML = `<div class="small-note">Per-sample removed fractions not available for sequencing quality plot.</div>`;
        return;
    }

    if (typeof Plotly === "undefined") {
        plotDiv.outerHTML = `<div class="small-note">Plotly failed to load; cannot render sequencing quality plot.</div>`;
        return;
    }

    const THRESH_GOOD = 0.05;
    const THRESH_MOD  = 0.20;

    const samples = perSample.map((d, idx) => d.sample || `sample ${idx + 1}`);
    const totalRemovedFracs = perSample.map(d => {
        const v = Number(d.fraction_low_quality_of_total);
        return Number.isFinite(v) && v >= 0 ? v : 0;
    });

    const categories = [
        {key: "fraction_removed_low_quality", label: "Low phred score"},
        {key: "fraction_removed_too_many_N", label: "Too many Ns"},
        {key: "fraction_removed_low_complexity", label: "Low complexity"},
        {key: "fraction_removed_too_short", label: "Too short"},
    ];

    const categoryValues = categories.map(cat => perSample.map(sample => {
        const v = Number(sample[cat.key]);
        return Number.isFinite(v) && v >= 0 ? v : 0;
    }));

    const statusPalettes = {
        good: ["#0b5a24", "#187133", "#279842", "#36b150"],
        moderate: ["#a86200", "#c17800", "#d89000", "#efaa1a"],
        poor: ["#7a0015", "#931327", "#ac2539", "#c6384c"],
    };

    const statusForSample = totalRemovedFracs.map(val => {
        if (val <= THRESH_GOOD) return "good";
        if (val <= THRESH_MOD) return "moderate";
        return "poor";
    });

    const traces = categories.map((cat, catIdx) => {
        const yVals = categoryValues[catIdx];
        const colors = yVals.map((_, sampleIdx) => {
            const status = statusForSample[sampleIdx];
            const palette = statusPalettes[status] || statusPalettes.poor;
            return palette[catIdx % palette.length];
        });
        const custom = yVals.map((val, sampleIdx) => {
            const totalReads = Math.max(0, Number(perSample[sampleIdx].total_reads) || 0);
            const reads = totalReads * val;
            return (
                `<b>${samples[sampleIdx]}</b><br>` +
                `${cat.label}: ${(val * 100).toFixed(2)}% (${fmtMillions(reads)} reads)`
            );
        });
        return {
            type: "bar",
            name: cat.label,
            x: samples,
            y: yVals,
            marker: {color: colors},
            hovertemplate: "%{customdata}<extra></extra>",
            customdata: custom,
        };
    });

    const maxFracObserved = Math.max(...totalRemovedFracs, 0);
    const hasGoodLine = maxFracObserved >= THRESH_GOOD;
    const hasModLine = maxFracObserved >= THRESH_MOD;
    const medianFracValue = median(totalRemovedFracs);
    const medianRemoved = Number(medianFracValue) || 0;

    const maxCandidates = [maxFracObserved];
    if (hasGoodLine) maxCandidates.push(THRESH_GOOD);
    if (hasModLine) maxCandidates.push(THRESH_MOD);
    if (medianRemoved > 0) maxCandidates.push(medianRemoved);
    const rangeMax = Math.max(...maxCandidates);
    const maxFrac = rangeMax > 0 ? rangeMax * 1.1 : 0.01;
    const yTickFormat = (maxFrac * 100) < 10 ? ".1%" : ".0%";

    const shapes = [];
    const annotations = [];

    if (hasGoodLine) {
        shapes.push({
            type: "line",
            xref: "paper",
            x0: 0,
            x1: 1,
            y0: THRESH_GOOD,
            y1: THRESH_GOOD,
            line: {color: "#2e7d32", width: 1.4, dash: "dot"}
        });
        annotations.push({
            xref: "paper",
            x: 0.995,
            y: THRESH_GOOD,
            xanchor: "right",
            yanchor: "bottom",
            text: "5%",
            showarrow: false,
            font: {color: "#2e7d32", size: 11},
            align: "right"
        });
    }

    if (hasModLine) {
        shapes.push({
            type: "line",
            xref: "paper",
            x0: 0,
            x1: 1,
            y0: THRESH_MOD,
            y1: THRESH_MOD,
            line: {color: "#c62828", width: 1.4, dash: "dot"}
        });
        annotations.push({
            xref: "paper",
            x: 0.995,
            y: THRESH_MOD,
            xanchor: "right",
            yanchor: "bottom",
            text: "20%",
            showarrow: false,
            font: {color: "#c62828", size: 11},
            align: "right"
        });
    }

    if (medianRemoved > 0 && medianRemoved <= maxFrac) {
        shapes.push({
            type: "line",
            xref: "paper",
            x0: 0,
            x1: 1,
            y0: medianRemoved,
            y1: medianRemoved,
            line: {color: "#424242", width: 1.2, dash: "dash"}
        });
        annotations.push({
            xref: "paper",
            x: 0.995,
            y: medianRemoved,
            xanchor: "right",
            yanchor: "bottom",
            text: `median (${(medianRemoved * 100).toFixed(1)}%)`,
            showarrow: false,
            font: {color: "#424242", size: 11},
            align: "right"
        });
    }

    const n = perSample.length;
    const tickAngle = n > 80 ? -75 : n > 40 ? -60 : -45;
    const tickSize = n > 120 ? 7 : n > 60 ? 8 : 10;
    const bottomMargin = n > 80 ? 200 : n > 40 ? 150 : 110;

    const baseHeight = Math.max(340, Math.min(560, 260 + n * 2));
    plotDiv.style.height = baseHeight + "px";

    const layout = {
        height: baseHeight,
        margin: {l: 80, r: 28, t: 16, b: bottomMargin},
        bargap: 0.12,
        barmode: "stack",
        hovermode: "closest",
        showlegend: true,
        legend: {
            orientation: "h",
            x: 0,
            y: 1.12,
            yanchor: "bottom",
            xanchor: "left",
        },
        xaxis: {
            title: "Samples",
            type: "category",
            tickangle: tickAngle,
            tickfont: {size: tickSize},
            automargin: true,
        },
        yaxis: {
            title: "Percentage of low-quality reads",
            range: [0, maxFrac],
            tickformat: yTickFormat,
            separatethousands: true,
        },
        shapes,
        annotations,
    };

    const config = {
        displaylogo: false,
        responsive: true,
        modeBarButtonsToRemove: ["toggleSpikelines", "autoScale2d"],
    };

    Plotly.newPlot(plotDiv, traces, layout, config);
    window.addEventListener("resize", () => Plotly.Plots.resize(plotDiv));
}

/* Prokaryotic fraction & depth components */
function addProkFractionSection(parent, data, depthPerSample) {
    if (!data) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(data.flag_prokaryotic_fraction);

    const msg = data.message_prokaryotic_fraction || "";
    const status = sectionStatus("Prokaryotic fraction", data.flag_prokaryotic_fraction);

    div.innerHTML = `
        <h2 class="section-title">Prokaryotic fraction</h2>
        <p class="section-intro">
            This section describes how much of the sequencing effort is covering prokaryotic genomes
            in comparison to non-prokaryotic genomes. These values are estimated based on marker-gene
            profiling of metagenomic reads. A high prokaryotic fraction is desirable for metagenomic
            assembly and microbiome profiling, while a low prokaryotic fraction may indicate
            contamination with host or other non-prokaryotic DNA.
        </p>
        <details>
            <summary>
                <span class="status-emoji">${status.emoji}</span>
                <span class="status-text">${status.text}</span>
                <span class="summary-hint">(click to expand)</span>
            </summary>
            <div class="content">
                <p class="summary-message">${msg}</p>
                <div class="prok-stats">
                    <div class="prok-stat-item">
                        <div class="prok-stat-label">Mean prokaryotic fraction</div>
                        <div class="prok-stat-value">${fmtFloat(data.mean_prokaryotic_fraction, 2)}%</div>
                        <div class="prok-stat-note">Average prokaryotic share of reads</div>
                    </div>
                    <div class="prok-stat-item">
                        <div class="prok-stat-label">Median prokaryotic fraction</div>
                        <div class="prok-stat-value">${fmtFloat(data.median_prokaryotic_fraction, 2)}%</div>
                        <div class="prok-stat-note">Typical prokaryotic share across samples</div>
                    </div>
                    <div class="prok-stat-item">
                        <div class="prok-stat-label">Variation</div>
                        <div class="prok-stat-value">${fmtFloat(data.cv_prokaryotic_fraction, 3)}</div>
                        <div class="prok-stat-note">Coefficient of variation (CV)</div>
                    </div>
                </div>
                <p class="small-note">
                    SingleM warnings in ${fmtInt(data.n_warnings)} samples may indicate reduced reliability
                    of the estimated prokaryotic fractions in those libraries.
                </p>
                <div class="prok-depth-plot-container">
                    <div id="prok-depth-plot" class="plotly-chart"></div>
                </div>
                <p class="small-note">
                    Interactive stacked barplot of per-sample read composition. Bars are low-quality (dark grey),
                    prokaryotic (green/yellow/red depending on the prokaryotic fraction) and other QC-passing reads
                    (light grey). Horizontal dashed lines (if reached) mark 50% (yellow) and 90% (green) prokaryotic
                    fraction; the median prokaryotic fraction is shown as a dark grey dashed line. Hover for exact
                    fractions and read counts. The plot resizes with page width.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const plotDiv = div.querySelector("#prok-depth-plot");
    const dataPerSample = (depthPerSample || []).filter(d =>
        d.total_reads !== null &&
        d.total_reads !== undefined
    );

    if (!dataPerSample.length) {
        plotDiv.outerHTML = `<div class="small-note">Per-sample depth component data not available.</div>`;
        return;
    }

    if (typeof Plotly === "undefined") {
        plotDiv.outerHTML = `<div class="small-note">Plotly failed to load; cannot render prokaryotic fraction plot.</div>`;
        return;
    }

    const THRESH_PROK_MOD = 0.50;
    const THRESH_PROK_HIGH = 0.90;

    const samples = dataPerSample.map((d, idx) => d.sample || `sample ${idx + 1}`);
    const fracLow = dataPerSample.map(d => Math.max(0, Number(d.fraction_low_quality_of_total) || 0));
    const fracProk = dataPerSample.map(d => Math.max(0, Number(d.fraction_prokaryotic_of_total) || 0));
    const fracOther = dataPerSample.map(d => Math.max(0, Number(d.fraction_non_prokaryotic_of_total) || 0));

    const totalReads = dataPerSample.map(d => Math.max(0, Number(d.total_reads) || 0));
    const lowReads = dataPerSample.map(d => Math.max(0, Number(d.low_quality_reads_est) || 0));
    const prokReads = dataPerSample.map(d => Math.max(0, Number(d.prokaryotic_reads_est) || 0));
    const otherReads = dataPerSample.map(d => Math.max(0, Number(d.non_prokaryotic_reads_est) || 0));

    const prokColors = fracProk.map(v => {
        if (v >= THRESH_PROK_HIGH) return "#2e7d32";
        if (v >= THRESH_PROK_MOD) return "#f9a825";
        return "#c62828";
    });

    const hoverLow = dataPerSample.map((d, idx) =>
        `<b>${samples[idx]}</b><br>` +
        `Low-quality: ${(fracLow[idx] * 100).toFixed(2)}% (${fmtMillions(lowReads[idx])} reads)<br>` +
        `Total: ${fmtMillions(totalReads[idx])} reads`
    );
    const hoverProk = dataPerSample.map((d, idx) =>
        `<b>${samples[idx]}</b><br>` +
        `Prokaryotic: ${(fracProk[idx] * 100).toFixed(2)}% (${fmtMillions(prokReads[idx])} reads)<br>` +
        `Total: ${fmtMillions(totalReads[idx])} reads`
    );
    const hoverOther = dataPerSample.map((d, idx) =>
        `<b>${samples[idx]}</b><br>` +
        `Other: ${(fracOther[idx] * 100).toFixed(2)}% (${fmtMillions(otherReads[idx])} reads)<br>` +
        `Total: ${fmtMillions(totalReads[idx])} reads`
    );

    const traceLow = {
        type: "bar",
        name: "",
        x: samples,
        y: fracLow,
        marker: {color: "#424242"},
        hovertemplate: "%{customdata}<extra></extra>",
        customdata: hoverLow,
    };

    const traceProk = {
        type: "bar",
        name: "",
        x: samples,
        y: fracProk,
        marker: {color: prokColors},
        hovertemplate: "%{customdata}<extra></extra>",
        customdata: hoverProk,
    };

    const traceOther = {
        type: "bar",
        name: "",
        x: samples,
        y: fracOther,
        marker: {color: "#e0e0e0"},
        hovertemplate: "%{customdata}<extra></extra>",
        customdata: hoverOther,
    };

    const stacks = dataPerSample.map((_, idx) => fracLow[idx] + fracProk[idx] + fracOther[idx]);
    const maxFracObserved = Math.max(...stacks, 0);
    const has50 = maxFracObserved >= THRESH_PROK_MOD - 1e-9;
    const has90 = maxFracObserved >= THRESH_PROK_HIGH - 1e-9;
    const medianProkFrac = (Number(data.median_prokaryotic_fraction) || 0) / 100;

    const shapes = [];
    const annotations = [];

    if (has50) {
        shapes.push({
            type: "line",
            xref: "paper",
            x0: 0,
            x1: 1,
            y0: THRESH_PROK_MOD,
            y1: THRESH_PROK_MOD,
            line: {color: "#f9a825", width: 1.4, dash: "dot"}
        });
        annotations.push({
            xref: "paper",
            x: 0.995,
            y: THRESH_PROK_MOD,
            xanchor: "right",
            yanchor: "bottom",
            text: "50%",
            showarrow: false,
            font: {color: "#f9a825", size: 11},
            align: "right"
        });
    }

    if (has90) {
        shapes.push({
            type: "line",
            xref: "paper",
            x0: 0,
            x1: 1,
            y0: THRESH_PROK_HIGH,
            y1: THRESH_PROK_HIGH,
            line: {color: "#2e7d32", width: 1.4, dash: "dot"}
        });
        annotations.push({
            xref: "paper",
            x: 0.995,
            y: THRESH_PROK_HIGH,
            xanchor: "right",
            yanchor: "bottom",
            text: "90%",
            showarrow: false,
            font: {color: "#2e7d32", size: 11},
            align: "right"
        });
    }

    if (medianProkFrac > 0) {
        shapes.push({
            type: "line",
            xref: "paper",
            x0: 0,
            x1: 1,
            y0: medianProkFrac,
            y1: medianProkFrac,
            line: {color: "#424242", width: 1.2, dash: "dash"}
        });
        annotations.push({
            xref: "paper",
            x: 0.995,
            y: medianProkFrac,
            xanchor: "right",
            yanchor: "bottom",
            text: `median (${fmtFloat(medianProkFrac * 100, 1)}%)`,
            showarrow: false,
            font: {color: "#424242", size: 11},
            align: "right"
        });
    }

    const n = dataPerSample.length;
    const tickAngle = n > 80 ? -75 : n > 40 ? -60 : -45;
    const tickSize = n > 120 ? 7 : n > 60 ? 8 : 10;
    const bottomMargin = n > 80 ? 200 : n > 40 ? 150 : 110;

    const maxCandidates = [maxFracObserved];
    if (has50) maxCandidates.push(THRESH_PROK_MOD);
    if (has90) maxCandidates.push(THRESH_PROK_HIGH);
    if (medianProkFrac > 0) maxCandidates.push(medianProkFrac);
    const maxY = Math.max(0.05, Math.min(1, Math.max(...maxCandidates) * 1.1));

    const layout = {
        height: 360,
        margin: {l: 80, r: 28, t: 16, b: bottomMargin},
        bargap: 0.12,
        barmode: "stack",
        hovermode: "closest",
        showlegend: false,
        xaxis: {
            title: "Samples",
            type: "category",
            tickangle: tickAngle,
            tickfont: {size: tickSize},
            automargin: true,
        },
        yaxis: {
            title: "Fraction of total reads",
            range: [0, maxY],
            tickformat: ".0%",
            separatethousands: true,
        },
        shapes,
        annotations,
    };

    const config = {
        displaylogo: false,
        responsive: true,
        modeBarButtonsToRemove: ["toggleSpikelines", "autoScale2d"],
    };

    Plotly.newPlot(plotDiv, [traceLow, traceProk, traceOther], layout, config);
    window.addEventListener("resize", () => Plotly.Plots.resize(plotDiv));
}

/* Metagenomic coverage of samples */
function addRedundancyReadsSection(parent, data, depthPerSample) {
    if (!data) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(data.flag_redundancy);

    const msg = data.message_redundancy || "";

    const nLR = data.n_samples_with_lr || 0;
    const nBelow = data.n_samples_lr_exceeds_depth || 0;
    const nAtOrAbove = nLR ? (nLR - nBelow) : 0;
    const fracAtOrAbove = nLR ? (100 * nAtOrAbove / nLR) : null;
    const coverageVals = Array.isArray(data.per_sample_coverage)
        ? data.per_sample_coverage.map(d => d.coverage).filter(v => typeof v === "number" && isFinite(v))
        : [];
    const covMedian = data.coverage_median != null ? data.coverage_median : median(coverageVals);
    const covCV = data.coverage_cv != null ? data.coverage_cv : coeffVar(coverageVals);

    const status = sectionStatus("Overall metagenomic coverage", data.flag_redundancy);

    div.innerHTML = `
        <h2 class="section-title">Metagenomic coverage of samples</h2>
        <p class="section-intro">
            This section evaluates how close the sequencing depth of individual samples is from the metagenomic 
            completeness target of ${COMPLETENESS_LABEL}%. This is estimated based on the redundancy of sequencing reads in each sample. 
            Samples that meet or exceed this target are estimated to have sufficient information to properly characterise the
            metagenomic (not just prokaryotes but also eukaryotes and viruses) complexity of the sample. Samples below this target may require 
            input from other samples or additional sequencing. Note that the relationship between metagenomic completeness and sequencing depth
            is not linear, so a 5% gap does not mean that 5% more sequencing reads are needed.
        </p>
        <details>
            <summary>
                <span class="status-emoji">${status.emoji}</span>
                <span class="status-text">${status.text}</span>
                <span class="summary-hint">(click to expand)</span>
            </summary>
            <div class="content">
                <p class="summary-message">${msg}</p>
                <div class="redundancy-stats">
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Coverage median</div>
                        <div class="redundancy-stat-value">${covMedian === null ? "NA" : fmtFloat(covMedian * 100, 1)}%</div>
                        <div class="redundancy-stat-note">Estimated for the total sequencing depth</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Coefficient of variation of coverage</div>
                        <div class="redundancy-stat-value">${covCV === null ? "NA" : fmtFloat(covCV, 3)}</div>
                        <div class="redundancy-stat-note">Coefficient of variation of coverage estimates</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Samples above the ${COMPLETENESS_LABEL}% completeness target</div>
                        <div class="redundancy-stat-value">
                            ${fmtInt(nAtOrAbove)} / ${fmtInt(nLR)}
                        </div>
                        <div class="redundancy-stat-note">
                            ${fracAtOrAbove === null ? "NA" : fmtFloat(fracAtOrAbove, 1) + "%"} of samples reached the target
                        </div>
                    </div>
                </div>
                <div class="lr-target-plot-container">
                    <div id="lr-target-plot" class="plotly-chart"></div>
                </div>
                <p class="small-note">
                    The plot represents the proportion of the estimated complexity of each sample that is covered by the actual data,
                    based on the redundancy of sequencing reads. Samples with estimated coverage at or above the ${COMPLETENESS_LABEL}%
                    target (dashed line) are shown in green, those within 15% of the target in yellow, and those further below the target in red.
                    Hover for exact coverage estimates.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const combined = (data.per_sample_coverage || []).map(d => ({
        sample: d.sample,
        coverage: Number(d.coverage),
        extra: Number(d.extra_needed),
    })).filter(d => Number.isFinite(d.coverage));

    const plotDiv = div.querySelector("#lr-target-plot");

    if (!combined.length) {
        plotDiv.outerHTML = `<div class="small-note">No per-sample LR_reads and depth information available to compare against LR targets (reads).</div>`;
        return;
    }

    if (typeof Plotly === "undefined") {
        plotDiv.outerHTML = `<div class="small-note">Plotly failed to load; cannot render metagenomic coverage plot.</div>`;
        return;
    }

    const targetFrac = COMPLETENESS_FRACTION;
    const samples = combined.map((d, idx) => d.sample || `sample ${idx + 1}`);
    const values = combined.map(d => d.coverage);

    const colors = values.map(v => {
        if (v >= targetFrac) return "#4caf50";
        if (v >= targetFrac * 0.85) return "#f9a825";
        return "#c62828";
    });

    const hover = combined.map((d, idx) => {
        const cov = values[idx];
        const extraNeeded = Number.isFinite(d.extra) ? Math.max(d.extra, 0) : (cov >= targetFrac ? 0 : (targetFrac - cov) / Math.max(cov, 1e-9));
        return [
            `<b>${d.sample || `sample ${idx + 1}`}</b>`,
            `Estimated coverage: ${(cov * 100).toFixed(1)}%`,
            `Additional sequencing needed: ${extraNeeded.toFixed(2)}×`
        ].filter(Boolean).join("<br>");
    });

    const maxVal = 1.0;
    const shapes = [
        {
            type: "line",
            xref: "paper",
            x0: 0,
            x1: 1,
            y0: targetFrac,
            y1: targetFrac,
            line: {color: "#000", width: 1.4, dash: "dot"}
        }
    ];
    const annotations = [
        {
            xref: "paper",
            x: 0.995,
            y: targetFrac,
            xanchor: "right",
            yanchor: "bottom",
            text: `${COMPLETENESS_LABEL}% target`,
            showarrow: false,
            font: {color: "#000", size: 11}
        }
    ];

    const n = samples.length;
    const tickAngle = n > 80 ? -75 : n > 40 ? -60 : -45;
    const tickSize = n > 120 ? 7 : n > 60 ? 8 : 10;
    const bottomMargin = n > 80 ? 200 : n > 40 ? 150 : 110;

    const trace = {
        type: "bar",
        x: samples,
        y: values,
        marker: {color: colors},
        hovertemplate: "%{customdata}<extra></extra>",
        customdata: hover,
    };

    const layout = {
        height: 360,
        margin: {l: 80, r: 28, t: 16, b: bottomMargin},
        bargap: 0.18,
        hovermode: "closest",
        showlegend: false,
        xaxis: {
            title: "Samples",
            type: "category",
            tickangle: tickAngle,
            tickfont: {size: tickSize},
            automargin: true,
        },
        yaxis: {
            title: "Estimated coverage (fraction)",
            range: [0, maxVal],
            separatethousands: true,
            zeroline: false,
        },
        shapes,
        annotations,
    };

    const config = {
        displaylogo: false,
        responsive: true,
        modeBarButtonsToRemove: ["toggleSpikelines", "autoScale2d"],
    };

    Plotly.newPlot(plotDiv, [trace], layout, config);
    window.addEventListener("resize", () => Plotly.Plots.resize(plotDiv));
}

/* Prokaryotic coverage of samples */
function addRedundancyMarkersSection(parent, data, redBiplotPerSample) {
    if (!data) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(data.flag_redundancy_markers);

    const msg = data.message_redundancy_markers || "";

    const nLR = data.n_samples_with_lr || 0;
    const nBelow = data.n_samples_lr_exceeds_depth || 0;
    const nAtOrAbove = nLR ? (nLR - nBelow) : 0;
    const fracAtOrAbove = nLR ? (100 * nAtOrAbove / nLR) : null;
    const coverageVals = (Array.isArray(data.coverage_ratios) && data.coverage_ratios.length)
        ? data.coverage_ratios.filter(v => typeof v === "number" && isFinite(v))
        : (data.coverage_median !== undefined ? [data.coverage_median] : []);
    const covMedian = data.coverage_median != null ? data.coverage_median : median(coverageVals);
    const covCV = data.coverage_cv != null ? data.coverage_cv : coeffVar(coverageVals);

    const status = sectionStatus("Prokaryotic coverage", data.flag_redundancy_markers);

    div.innerHTML = `
        <h2 class="section-title">Prokaryotic coverage of samples</h2>
        <p class="section-intro">
            This section evaluates coverage of marker gene sequences (rather than all reads in the previous section) of individual samples relative to the completeness target of ${COMPLETENESS_LABEL}%.
            This target is estimated based on the redundancy of reads previously mapped to prokaryotic marker genes, so unlike the previous section,
            providing an estimation specifically on coverage of prokaryotic genomes. Samples that meet or exceed this target are expected to have sufficient sequencing
            depth for capturing most of the prokaryotic metagenomic diversity. Samples below this target may require 
            input from other samples or additional sequencing. Note that the relationship between metagenomic completeness and sequencing depth
            is not linear, so a 5% gap does not mean that 5% more sequencing reads are needed.
        </p>
        <details>
            <summary>
                <span class="status-emoji">${status.emoji}</span>
                <span class="status-text">${status.text}</span>
                <span class="summary-hint">(click to expand)</span>
            </summary>
            <div class="content">
                <p class="summary-message">${msg}</p>
                <div class="redundancy-stats">
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Coverage median</div>
                        <div class="redundancy-stat-value">${covMedian === null ? "NA" : fmtFloat(covMedian * 100, 1)}%</div>
                        <div class="redundancy-stat-note">Estimated for the prokaryotic marker genes</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Coverage CV</div>
                        <div class="redundancy-stat-value">${covCV === null ? "NA" : fmtFloat(covCV, 3)}</div>
                        <div class="redundancy-stat-note">Coefficient of variation of coverage estimates</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Samples above the ${COMPLETENESS_LABEL}% completeness target</div>
                        <div class="redundancy-stat-value">
                            ${fmtInt(nAtOrAbove)} / ${fmtInt(nLR)}
                        </div>
                        <div class="redundancy-stat-note">
                            ${fracAtOrAbove === null ? "NA" : fmtFloat(fracAtOrAbove, 1) + "%"} of samples reached the target
                        </div>
                    </div>
                </div>
                <div class="lr-target-markers-plot-container">
                    <div id="lr-target-markers-plot" class="plotly-chart"></div>
                </div>
                <p class="small-note">
                    The plot represents the proportion of the estimated complexity of pyokariotic marker genes in each sample that is covered by the actual data,
                    based on the redundancy of sequencing reads mapped to pyokariotic marker genes . Samples with estimated coverage at or above the ${COMPLETENESS_LABEL}%
                    target (dashed line) are shown in green, those within 15% of the target in yellow, and those further below the target in red.
                    Hover for exact coverage estimates.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const combined = (data.per_sample_coverage_markers || []).map(r => ({
        sample: r.sample,
        coverage: Number(r.coverage),
    })).filter(d => Number.isFinite(d.coverage));

    const plotDiv = div.querySelector("#lr-target-markers-plot");

    if (!combined.length) {
        plotDiv.outerHTML = `<div class="small-note">No per-sample marker coverage / LR target information available for marker redundancy plot.</div>`;
        return;
    }

    if (typeof Plotly === "undefined") {
        plotDiv.outerHTML = `<div class="small-note">Plotly failed to load; cannot render prokaryotic coverage plot.</div>`;
        return;
    }

    const targetFrac = COMPLETENESS_FRACTION;
    const samples = combined.map((d, idx) => d.sample || `sample ${idx + 1}`);
    const values = combined.map(d => {
        const cov = Number(d.coverage);
        return Number.isFinite(cov) ? cov : 0;
    });

    const colors = values.map(v => {
        if (v >= targetFrac) return "#4caf50";
        if (v >= targetFrac * 0.85) return "#f9a825";
        return "#c62828";
    });

    const hover = combined.map((d, idx) => {
        const cov = values[idx];
        const shortfall = cov >= targetFrac ? 0 : (targetFrac - cov);
        const extraNeeded = shortfall > 0 ? (shortfall / Math.max(cov, 1e-9)) : 0;
        return [
            `<b>${d.sample || `sample ${idx + 1}`}</b>`,
            `Coverage (markers): ${(cov * 100).toFixed(2)}%`,
            shortfall > 0
                ? `Additional sequencing needed: ${extraNeeded.toFixed(2)}×`
                : `Additional sequencing needed: 0×`
        ].filter(Boolean).join("<br>");
    });

    const maxVal = 1.0;
    const shapes = [
        {
            type: "line",
            xref: "paper",
            x0: 0,
            x1: 1,
            y0: targetFrac,
            y1: targetFrac,
            line: {color: "#000", width: 1.4, dash: "dot"}
        }
    ];
    const annotations = [
        {
            xref: "paper",
            x: 0.995,
            y: targetFrac,
            xanchor: "right",
            yanchor: "bottom",
            text: `${COMPLETENESS_LABEL}% coverage target`,
            showarrow: false,
            font: {color: "#000", size: 11}
        }
    ];

    const n = samples.length;
    const tickAngle = n > 80 ? -75 : n > 40 ? -60 : -45;
    const tickSize = n > 120 ? 7 : n > 60 ? 8 : 10;
    const bottomMargin = n > 80 ? 200 : n > 40 ? 150 : 110;

    const trace = {
        type: "bar",
        x: samples,
        y: values,
        marker: {color: colors},
        hovertemplate: "%{customdata}<extra></extra>",
        customdata: hover,
    };

    const layout = {
        height: 360,
        margin: {l: 80, r: 28, t: 16, b: bottomMargin},
        bargap: 0.18,
        hovermode: "closest",
        showlegend: false,
        xaxis: {
            title: "Samples",
            type: "category",
            tickangle: tickAngle,
            tickfont: {size: tickSize},
            automargin: true,
        },
        yaxis: {
            title: "Estimated coverage (fraction)",
            range: [0, maxVal],
            separatethousands: true,
            zeroline: false,
        },
        shapes,
        annotations,
    };

    const config = {
        displaylogo: false,
        responsive: true,
        modeBarButtonsToRemove: ["toggleSpikelines", "autoScale2d"],
    };

    Plotly.newPlot(plotDiv, [trace], layout, config);
    window.addEventListener("resize", () => Plotly.Plots.resize(plotDiv));
}

/* Sample clusters */
function addClustersSection(parent, clusters, ordinations) {
    if (!clusters) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(clusters.flag_clusters);

    const msg = clusters.message_clusters || "";
    const markers = clusters.markers || {};
    const reads = clusters.reads || {};
    const ord = ordinations || {};
    const ordMarkers = ord.markers;
    const ordReads = ord.reads;

    const nClustersMarkers = markers.n_clusters != null ? markers.n_clusters : "NA";
    const nClustersReads = reads.n_clusters != null ? reads.n_clusters : "NA";
    const withinMarkers = markers.mean_within_distance != null ? markers.mean_within_distance : null;
    const betweenMarkers = markers.mean_between_distance != null ? markers.mean_between_distance : null;
    const withinReads = reads.mean_within_distance != null ? reads.mean_within_distance : null;
    const betweenReads = reads.mean_between_distance != null ? reads.mean_between_distance : null;

    const status = sectionStatus("Sample clusters", clusters.flag_clusters);

    div.innerHTML = `
        <h2 class="section-title">Sample clusters</h2>
        <p class="section-intro">
            This section presents details of the clusters of samples inferred based on their pairwise dissimilarities,
            based on both marker gene sequences or sequencing reads. Samples within the same cluster are expected to be more similar
            to each other than to samples in other clusters, which may indicate they originate from similar environments
            or conditions. Clustering can help identify groups of related samples for coassembly or comparative analyses.
        </p>
        <details>
            <summary>
                <span class="status-emoji">${status.emoji}</span>
                <span class="status-text">${status.text}</span>
                <span class="summary-hint">(click to expand)</span>
            </summary>
            <div class="content">
                <p class="summary-message">${msg}</p>
                <div class="cluster-stats">
                    <div class="cluster-stat-item">
                        <div class="cluster-stat-label">Marker-based clusters</div>
                        <div class="cluster-stat-value">${fmtInt(nClustersMarkers)}</div>
                        <div class="cluster-stat-note">Clusters inferred from marker-based Mash distances</div>
                    </div>
                    <div class="cluster-stat-item">
                        <div class="cluster-stat-label">Read-based clusters</div>
                        <div class="cluster-stat-value">${fmtInt(nClustersReads)}</div>
                        <div class="cluster-stat-note">Clusters inferred from read-based Mash distances</div>
                    </div>
                    <div class="cluster-stat-item">
                        <div class="cluster-stat-label">Within / between (markers)</div>
                        <div class="cluster-stat-value">${fmtFloat(withinMarkers, 3)} / ${fmtFloat(betweenMarkers, 3)}</div>
                        <div class="cluster-stat-note">Mean Mash distance within / between marker clusters</div>
                    </div>
                    <div class="cluster-stat-item">
                    <div class="cluster-stat-label">Within / between (reads)</div>
                    <div class="cluster-stat-value">${fmtFloat(withinReads, 3)} / ${fmtFloat(betweenReads, 3)}</div>
                    <div class="cluster-stat-note">Mean Mash distance within / between read clusters</div>
                </div>
            </div>
                <div class="cluster-plot-area">
                    <div class="cluster-ordinations">
                        <div id="pcoa-markers-plot" class="plotly-chart" style="min-height:260px;"></div>
                        <div id="pcoa-reads-plot" class="plotly-chart" style="min-height:260px;"></div>
                    </div>
                </div>
                <p class="small-note">
                    PCoA plots above place samples in 2D using Mash distances; colours match the cluster heatmap below. Heatmap rows
                    correspond to marker-based and read-based clustering; columns are samples. Colour palettes are distinct per row,
                    so cluster IDs are not directly comparable. Samples are ordered to keep cluster mates adjacent.
                </p>
                <div class="clusters-heatmap-scroll" style="width:100%; overflow-x:auto; overflow-y:visible;">
                    <div id="clusters-heatmap-plot" class="plotly-chart" style="min-width:860px;"></div>
                </div>
                <p class="small-note">
                    Hover over tiles for exact cluster assignments. Samples without an assignment in a given
                    row are shown as light grey.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const plotDiv = div.querySelector("#clusters-heatmap-plot");

    const markersPS = (markers.clusters || []).flatMap(cl => {
        const cid = cl.cluster_id;
        const members = cl.members || [];
        return members.map(m => ({ sample: m, cluster: cid }));
    });

    const readsPS = (reads.clusters || []).flatMap(cl => {
        const cid = cl.cluster_id;
        const members = cl.members || [];
        return members.map(m => ({ sample: m, cluster: cid }));
    });

    if (!markersPS.length && !readsPS.length) {
        plotDiv.outerHTML = `<div class="small-note">Per-sample cluster assignments not available; heatmap cannot be drawn.</div>`;
        return;
    }

    const markersMap = {};
    markersPS.forEach(d => {
        if (d.sample != null) markersMap[d.sample] = d.cluster;
    });

    const readsMap = {};
    readsPS.forEach(d => {
        if (d.sample != null) readsMap[d.sample] = d.cluster;
    });

    const sampleSet = new Set();
    Object.keys(markersMap).forEach(s => sampleSet.add(s));
    Object.keys(readsMap).forEach(s => sampleSet.add(s));
    const samples = Array.from(sampleSet);
    samples.sort();

    const nSamples = samples.length;
    if (!nSamples) {
        plotDiv.outerHTML = `<div class="small-note">Per-sample cluster assignments not available; heatmap cannot be drawn.</div>`;
        return;
    }

    const coldPalette = [
        "#08306b", "#08519c", "#2171b5", "#2c7fb8", "#41b6c4",
        "#66c2a4", "#7bccc4", "#a1dab4", "#c7e9c0", "#edf8fb"
    ];
    const warmPalette = [
        "#7f0000", "#b30000", "#e31a1c", "#fc4e2a", "#fd8d3c",
        "#feb24c", "#ffdd57", "#ffb300", "#ff7f00", "#d95f0e"
    ];

    function buildClusterColorMap(map, palette) {
        const clusters = Array.from(new Set(
            Object.values(map).filter(v => v !== null && v !== undefined)
        ));
        clusters.sort((a, b) => {
            const na = Number(a), nb = Number(b);
            if (!isNaN(na) && !isNaN(nb)) return na - nb;
            return String(a).localeCompare(String(b));
        });
        const colorMap = {};
        clusters.forEach((cl, idx) => {
            colorMap[cl] = palette[idx % palette.length];
        });
        return colorMap;
    }

    const markerColors = buildClusterColorMap(markersMap, coldPalette);
    const readColors = buildClusterColorMap(readsMap, warmPalette);

    const markerClustersPresent = Object.keys(markerColors).length > 0;
    const readClustersPresent = Object.keys(readColors).length > 0;

    // Order to keep cluster mates adjacent; prefer marker clusters, else read clusters.
    let sampleOrder = [...samples];
    const groupBy = markerClustersPresent ? markersMap : (readClustersPresent ? readsMap : null);
    if (groupBy) {
        const clList = Array.from(new Set(
            sampleOrder
                .map(s => groupBy[s])
                .filter(v => v !== null && v !== undefined)
        )).sort((a, b) => {
            const na = Number(a), nb = Number(b);
            if (!isNaN(na) && !isNaN(nb)) return na - nb;
            return String(a).localeCompare(String(b));
        });
        const grouped = [];
        clList.forEach(cl => {
            sampleOrder.forEach(s => {
                if (groupBy[s] === cl) grouped.push(s);
            });
        });
        const noCluster = sampleOrder.filter(s => groupBy[s] === null || groupBy[s] === undefined);
        sampleOrder = [...grouped, ...noCluster];
    }

    if (typeof Plotly === "undefined") {
        plotDiv.outerHTML = `<div class="small-note">Plotly failed to load; cannot render sample clusters heatmap.</div>`;
        return;
    }

    const markerClusterList = Object.keys(markerColors);
    const readClusterList = Object.keys(readColors);

    const markerClusterMap = {};
    markerClusterList.forEach((cl, idx) => { markerClusterMap[cl] = idx; });
    const readStart = markerClusterList.length;
    const readClusterMap = {};
    readClusterList.forEach((cl, idx) => { readClusterMap[cl] = readStart + idx; });

    const missingVal = -1;
    const maxVal = Math.max(
        markerClusterList.length ? markerClusterList.length - 1 : 0,
        readClusterList.length ? readStart + readClusterList.length - 1 : 0,
        0
    );

    const colorscale = [];
    const range = maxVal - missingVal || 1;
    colorscale.push([0, "#ffffff"]);
    markerClusterList.forEach((cl, idx) => {
        const val = markerClusterMap[cl];
        const pos = (val - missingVal) / range;
        const color = coldPalette[idx % coldPalette.length];
        colorscale.push([pos, color]);
    });
    readClusterList.forEach((cl, idx) => {
        const val = readClusterMap[cl];
        const pos = (val - missingVal) / range;
        const color = warmPalette[idx % warmPalette.length];
        colorscale.push([pos, color]);
    });
    colorscale.sort((a, b) => a[0] - b[0]);

    const yLabels = ["Markers", "Reads"];
    const z = [[], []];
    const displayText = [[], []];
    const hoverText = [[], []];
    sampleOrder.forEach(sample => {
        const mCl = markersMap.hasOwnProperty(sample) ? markersMap[sample] : null;
        const rCl = readsMap.hasOwnProperty(sample) ? readsMap[sample] : null;
        const mVal = mCl === null || mCl === undefined ? missingVal : markerClusterMap[mCl];
        const rVal = rCl === null || rCl === undefined ? missingVal : readClusterMap[rCl];
        z[0].push(mVal);
        z[1].push(rVal);
        displayText[0].push(mCl === null || mCl === undefined ? "" : String(mCl));
        displayText[1].push(rCl === null || rCl === undefined ? "" : String(rCl));
        hoverText[0].push(
            mCl === null || mCl === undefined
                ? `${sample}<br>Markers: not assigned`
                : `${sample}<br>Markers cluster: ${mCl}`
        );
        hoverText[1].push(
            rCl === null || rCl === undefined
                ? `${sample}<br>Reads: not assigned`
                : `${sample}<br>Reads cluster: ${rCl}`
        );
    });

    const heatmap = {
        type: "heatmap",
        x: sampleOrder,
        y: yLabels,
        z,
        text: displayText,
        texttemplate: "%{text}",
        textfont: {
            color: "#ffffff",
            size: 14,
            family: "Arial, sans-serif",
            weight: "bold",
        },
        customdata: hoverText,
        hovertemplate: "%{customdata}<extra></extra>",
        colorscale,
        zmin: missingVal,
        zmax: Math.max(maxVal, 0),
        showscale: false,
        xgap: 1,
        ygap: 1,
    };

    const tickAngle = sampleOrder.length > 18 ? -60 : -45;
    const bottomMargin = sampleOrder.length > 18 ? 110 : 90;

    // Restore heatmap height while trimming excess outer box space
    const layoutHeight = Math.max(220, 80 + sampleOrder.length * 10);
    plotDiv.style.height = `${layoutHeight}px`;

    const layout = {
        height: layoutHeight,
        margin: {l: 90, r: 20, t: 20, b: bottomMargin},
        xaxis: {
            tickangle: tickAngle,
            automargin: true,
        },
        yaxis: {
            automargin: true,
            autorange: "reversed",
        },
        hovermode: "closest",
        showlegend: false,
    };

    const config = {
        displaylogo: false,
        responsive: true,
        modeBarButtonsToRemove: ["toggleSpikelines", "autoScale2d"],
    };

    Plotly.newPlot(plotDiv, [heatmap], layout, config);
    window.addEventListener("resize", () => Plotly.Plots.resize(plotDiv));

    const pcoaMarkersDiv = div.querySelector("#pcoa-markers-plot");
    const pcoaReadsDiv = div.querySelector("#pcoa-reads-plot");

    function renderPCoA(container, ordData, colorMap, label, clusterKey) {
        if (!container) return;
        const samplesOrd = ordData && Array.isArray(ordData.samples) ? ordData.samples : [];
        const points = samplesOrd.map(s => ({
            sample: s.sample,
            x: Number(s.x),
            y: Number(s.y),
            cl: s[clusterKey]
        })).filter(p => isFinite(p.x) && isFinite(p.y));

        if (!points.length) {
            container.outerHTML = `<div class="small-note">No ordination available for ${label.toLowerCase()}.</div>`;
            return;
        }
        if (typeof Plotly === "undefined") {
            container.outerHTML = `<div class="small-note">Plotly failed to load; cannot render ${label.toLowerCase()} PCoA plot.</div>`;
            return;
        }

        const varExpl = Array.isArray(ordData.variance_explained) ? ordData.variance_explained : [];
        const axisLabel = (name, idx) => {
            const v = Number(varExpl[idx]);
            return Number.isFinite(v) ? `${name} (${(v * 100).toFixed(1)}%)` : name;
        };

        const grouped = {};
        points.forEach(p => {
            const key = p.cl === null || p.cl === undefined ? "__unassigned__" : String(p.cl);
            if (!grouped[key]) grouped[key] = [];
            grouped[key].push(p);
        });

        const clusterKeys = Object.keys(grouped).sort((a, b) => {
            if (a === "__unassigned__") return 1;
            if (b === "__unassigned__") return -1;
            const na = Number(a), nb = Number(b);
            if (!isNaN(na) && !isNaN(nb)) return na - nb;
            return a.localeCompare(b);
        });

        const traces = clusterKeys.map(key => {
            const pts = grouped[key];
            const color = key === "__unassigned__" ? "#9ca3af" : (colorMap[key] || "#9ca3af");
            const hover = pts.map(p => {
                const clusterLabel = key === "__unassigned__" ? "not assigned" : `cluster ${key}`;
                return [
                    `<b>${p.sample}</b>`,
                    `Cluster: ${clusterLabel}`,
                    `X: ${p.x.toFixed(3)}`,
                    `Y: ${p.y.toFixed(3)}`
                ].join("<br>");
            });
            return {
                type: "scatter",
                mode: "markers",
                name: key === "__unassigned__" ? "Unassigned" : `Cluster ${key}`,
                x: pts.map(p => p.x),
                y: pts.map(p => p.y),
                customdata: hover,
                hovertemplate: "%{customdata}<extra></extra>",
                marker: {color, size: 9, line: {width: 0.5, color: "#ffffff"}}
            };
        });

        const layout = {
            height: 320,
            margin: {l: 70, r: 20, t: 30, b: 80},
            title: {text: label + " dissimilarity", x: 0, font: {size: 13}},
            xaxis: {title: axisLabel("Axis 1", 0), zeroline: false},
            yaxis: {title: axisLabel("Axis 2", 1), zeroline: false},
            hovermode: "closest",
            showlegend: true,
            legend: {orientation: "h", y: -0.28, x: 0}
        };

        const config = {
            displaylogo: false,
            responsive: true,
            modeBarButtonsToRemove: ["toggleSpikelines", "autoScale2d"],
        };

        Plotly.newPlot(container, traces, layout, config);
        window.addEventListener("resize", () => Plotly.Plots.resize(container));
    }

    renderPCoA(pcoaMarkersDiv, ordMarkers, markerColors, "Markers", "cluster_markers");
    renderPCoA(pcoaReadsDiv, ordReads, readColors, "Reads", "cluster_reads");
}

/* Combined overall coverage summary */
function addOverallCoverageSection(parent, data) {
    if (!data) return;
    const metaBlock = data.metagenomic || {};
    const prokBlock = data.prokaryotic || {};
    if (!metaBlock && !prokBlock) return;

    const combinedFlag = data.flag_overall_coverage
        ?? metaBlock.flag_overall_read_coverage
        ?? prokBlock.flag_overall_prok_coverage
        ?? 3;
    const status = sectionStatus("Overall coverage", combinedFlag);
    const message =
        data.message_overall_coverage ||
        [
            metaBlock.message_overall_read_coverage,
            prokBlock.message_overall_prok_coverage,
        ].filter(Boolean).join(" " );

    const div = document.createElement("div");
    div.className = "section " + flagClass(combinedFlag);

    div.innerHTML = `
        <h2 class="section-title">Overall coverage of the dataset</h2>
        <p class="section-intro">
            This section provides an estimation of the opposite end of the sequencing spectrum_ whether and how the pooled set of
            reads from all samples is sufficient to reach the ${COMPLETENESS_LABEL}% completeness target. 
            This is complementary to the previous sections that focused on individual samples. Here, both total reads (Metagenomic target) and
            prokaryotic marker gene-based (Marker target) coverage are evaluated against the ${COMPLETENESS_LABEL}% completeness target.
        </p>
        <details>
            <summary>
                <span class="status-emoji">${status.emoji}</span>
                <span class="status-text">${status.text}</span>
                <span class="summary-hint">(click to expand)</span>
            </summary>
            <div class="content">
                <p class="summary-message">${message}</p>
                <div class="redundancy-stats">
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Metagenomic coverage</div>
                        <div class="redundancy-stat-value">${metaBlock.coverage_percent != null ? fmtFloat(metaBlock.coverage_percent, 1) + "%" : "NA"}</div>
                        <div class="redundancy-stat-note">Pooled reads across all samples</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Read-based target</div>
                        <div class="redundancy-stat-value">${fmtMillions(metaBlock.lr_95_reads)}</div>
                        <div class="redundancy-stat-note">Reads estimated for ${COMPLETENESS_LABEL}% metagenomic coverage</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Marker coverage</div>
                        <div class="redundancy-stat-value">${prokBlock.coverage_percent != null ? fmtFloat(prokBlock.coverage_percent, 1) + "%" : "NA"}</div>
                        <div class="redundancy-stat-note">Pooled marker coverage across all samples</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Marker-based target</div>
                        <div class="redundancy-stat-value">${fmtMillions(prokBlock.lr_95_reads)}</div>
                        <div class="redundancy-stat-note">Reads estimated for ${COMPLETENESS_LABEL}% marker coverage</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Total pooled reads</div>
                        <div class="redundancy-stat-value">${fmtMillions(metaBlock.total_reads ?? prokBlock.total_reads)}</div>
                        <div class="redundancy-stat-note">Sum of reads in the dataset</div>
                    </div>
                </div>
                <div class="lr-target-plot-container">
                    <div id="overall-coverage-plot" class="plotly-chart coverage-plot"></div>
                </div>
                <p class="small-note">
                    The horizontal bar shows pooled reads; vertical dashed lines mark the metagenomic (blue) and marker (purple)
                    ${COMPLETENESS_LABEL}% LR_reads targets.
                </p>
            </div>
        </details>
    `;

    parent.appendChild(div);

    const plotDiv = div.querySelector("#overall-coverage-plot");
    const totalReads = Number(metaBlock.total_reads ?? prokBlock.total_reads);
    if (!isFinite(totalReads) || totalReads <= 0) {
        plotDiv.outerHTML = `<div class="small-note">Pooled read information was unavailable for the combined coverage plot.</div>`;
        return;
    }
    if (typeof Plotly === "undefined") {
        plotDiv.outerHTML = `<div class="small-note">Plotly failed to load; cannot render combined coverage plot.</div>`;
        return;
    }

    const metaTarget = Number(metaBlock.lr_95_reads);
    const markerTarget = Number(prokBlock.lr_95_reads);
    const meetsMeta = !isFinite(metaTarget) || metaTarget <= 0 ? true : totalReads >= metaTarget;
    const meetsMarker = !isFinite(markerTarget) || markerTarget <= 0 ? true : totalReads >= markerTarget;
    const barColor = (meetsMeta && meetsMarker)
        ? "#4caf50"
        : (meetsMeta || meetsMarker ? "#f9a825" : "#c62828");
    const shapes = [];
    const annotations = [];

    const addTargetLine = (targetValue, label, color, position) => {
        if (!isFinite(targetValue) || targetValue <= 0) return;
        shapes.push({
            type: "line",
            xref: "x",
            yref: "paper",
            x0: targetValue,
            x1: targetValue,
            y0: 0,
            y1: 1,
            line: {color, width: 1.4, dash: "dot"}
        });
        annotations.push({
            x: targetValue,
            yref: "paper",
            y: position === "bottom" ? 0.2 : 0.8,
            xanchor: position === "bottom" ? "right" : "left",
            text: label,
            showarrow: false,
            font: {size: 11, color},
            yanchor: position === "bottom" ? "top" : "bottom",
        });
    };

    addTargetLine(metaTarget, "Metagenomic target", "#1e88e5", "top");
    addTargetLine(markerTarget, "Marker target", "#8e24aa", "bottom");

    const fig = {
        type: "bar",
        orientation: "h",
        x: [totalReads],
        y: ["Pooled reads"],
        marker: {color: barColor},
        hovertemplate: [
            `<b>Pooled reads</b>`,
            `Reads: ${fmtMillions(totalReads)}`,
            metaBlock.lr_95_reads ? `Metagenomic target: ${fmtMillions(metaBlock.lr_95_reads)}` : null,
            prokBlock.lr_95_reads ? `Marker target: ${fmtMillions(prokBlock.lr_95_reads)}` : null,
        ].filter(Boolean).join("<br>") + "<extra></extra>",
    };

    const maxTarget = Math.max(
        totalReads,
        Number(metaBlock.lr_95_reads) || 0,
        Number(prokBlock.lr_95_reads) || 0,
    );
    const rangeMax = Math.max(totalReads, maxTarget) * 1.1;

    const layout = {
        height: 200,
        margin: {l: 140, r: 30, t: 10, b: 20},
        xaxis: {
            title: "Reads",
            range: [0, rangeMax],
            separatethousands: true,
        },
        yaxis: {showticklabels: true},
        shapes,
        annotations,
        hovermode: "closest",
        showlegend: false,
    };

    const config = {displaylogo: false, responsive: true};
    Plotly.newPlot(plotDiv, [fig], layout, config);
    window.addEventListener("resize", () => Plotly.Plots.resize(plotDiv));
}

/* Prokaryotic coverage (markers Nonpareil) */
/* Overall marker coverage summary */
function addOverallProkCoverageSection(parent, data) {
    if (!data) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(data.flag_overall_prok_coverage);

    const status = sectionStatus("Overall prokaryotic coverage", data.flag_overall_prok_coverage);

    div.innerHTML = `
        <h2 class="section-title">Overall prokaryotic coverage</h2>
        <p class="section-intro">
            Aggregated Nonpareil marker coverage across samples.
        </p>
        <details>
            <summary>
                <span class="status-emoji">${status.emoji}</span>
                <span class="status-text">${status.text}</span>
                <span class="summary-hint">(click to expand)</span>
            </summary>
            <div class="content">
                <p class="summary-message">${data.message_overall_prok_coverage || ""}</p>
                <div class="redundancy-stats">
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Coverage (C_total)</div>
                        <div class="redundancy-stat-value">${data.coverage_percent != null ? fmtFloat(data.coverage_percent, 1) + "%" : "NA"}</div>
                        <div class="redundancy-stat-note">Pooled marker coverage across all samples</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Generated reads</div>
                        <div class="redundancy-stat-value">${fmtMillions(data.total_reads)}</div>
                        <div class="redundancy-stat-note">Sum of reads accross all samples</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Required reads</div>
                        <div class="redundancy-stat-value">${fmtMillions(data.lr_95_reads)}</div>
                        <div class="redundancy-stat-note">Reads estimated for target coverage</div>
                    </div>
                </div>
                <div class="lr-target-plot-container">
                    <div id="overall-prok-plot" class="plotly-chart" style="height:240px;"></div>
                </div>
                <p class="small-note">
                    Horizontal bar shows pooled marker reads; dashed line marks the coverage target. Bars are green (≥ target),
                    yellow (50-99% of target) or red (&lt; 50% of target).
                </p>
            </div>
        </details>
    `;

    parent.appendChild(div);

    const plotDiv = div.querySelector("#overall-prok-plot");
    const total = Number(data.total_reads);
    const target = Number(data.lr_95_reads);

    if (!isFinite(total) || !isFinite(target) || target <= 0) {
        plotDiv.outerHTML = `<div class="small-note">Insufficient pooled marker read / target information to draw coverage bar.</div>`;
        return;
    }
    if (typeof Plotly === "undefined") {
        plotDiv.outerHTML = `<div class="small-note">Plotly failed to load; cannot render overall prokaryotic coverage bar.</div>`;
        return;
    }

    const ratio = total / target;
    const color = ratio >= 1 ? "#4caf50" : ratio >= 0.5 ? "#f9a825" : "#c62828";

    const fig = {
        type: "bar",
        orientation: "h",
        x: [total],
        y: ["Pooled marker reads"],
        marker: {color},
        hovertemplate: [
            `<b>Pooled marker reads</b>`,
            `Reads: ${fmtMillions(total)}`,
            `Target (${COMPLETENESS_LABEL}% LR): ${fmtMillions(target)}`,
            `Relative to target: ${(ratio * 100).toFixed(1)}%`
        ].join("<br>") + "<extra></extra>",
    };

    const rangeMax = Math.max(total, target) * 1.1;

    const layout = {
        height: 220,
        margin: {l: 160, r: 30, t: 10, b: 40},
        xaxis: {
            title: "Reads",
            range: [0, rangeMax],
            separatethousands: true,
        },
        yaxis: {showticklabels: true},
        shapes: [
            {
                type: "line",
                xref: "x",
                yref: "paper",
                x0: target,
                x1: target,
                y0: 0,
                y1: 1,
                line: {color: "#000", width: 1.4, dash: "dot"}
            }
        ],
        annotations: [
            {
                x: target,
                yref: "paper",
                y: 1.02,
                xanchor: "left",
                text: "${COMPLETENESS_LABEL}% target",
                showarrow: false,
                font: {size: 11}
            }
        ],
        hovermode: "closest",
        showlegend: false,
    };

    const config = {displaylogo: false, responsive: true};
    Plotly.newPlot(plotDiv, [fig], layout, config);
    window.addEventListener("resize", () => Plotly.Plots.resize(plotDiv));
}

/* Pairwise sample dissimilarities */
function addMashDistanceSection(parent, clusters) {
    if (!clusters) return;

    const markersPairs = Array.isArray(clusters.pairwise_markers) ? clusters.pairwise_markers : [];
    const readsPairs = Array.isArray(clusters.pairwise_reads) ? clusters.pairwise_reads : [];

    const markersDistances = markersPairs.map(p => Number(p.distance)).filter(d => isFinite(d));
    const readsDistances = readsPairs.map(p => Number(p.distance)).filter(d => isFinite(d));

    const meanMarkers = markersDistances.length ? markersDistances.reduce((a, b) => a + b, 0) / markersDistances.length : null;
    const meanReads = readsDistances.length ? readsDistances.reduce((a, b) => a + b, 0) / readsDistances.length : null;

    function calcCV(arr, mean) {
        if (!arr.length || !mean) return null;
        const varval = arr.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / arr.length;
        return Math.sqrt(varval) / mean;
    }
    const cvMarkers = calcCV(markersDistances, meanMarkers);
    const cvReads = calcCV(readsDistances, meanReads);

    const div = document.createElement("div");
    div.className = "section " + flagClass(clusters.flag_clusters);
    const status = sectionStatus("Pairwise sample dissimilarities", clusters.flag_clusters);

    div.innerHTML = `
        <h2 class="section-title">Sample dissimilarities</h2>
        <p class="section-intro">
            This section displays the average pairwise dissimilarities across all analysed samples, both for reads (representing the entire metagenome) 
            and marker genes (representing the prokaryotic fraction of the metagenome). Mean distances and coefficients of variation (CV)  
            are useful to assess how much individual samples can benefit from the information provided by other samples in the dataset, as well as to
            identify cutoffs that can guide sample clustering for coassembly or other analyses.
        </p>
        <details>
            <summary>
                <span class="status-emoji">${status.emoji}</span>
                <span class="status-text">${status.text}</span>
                <span class="summary-hint">(click to expand)</span>
            </summary>
            <div class="content">
                <div class="redundancy-stats">
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Mean distance (markers)</div>
                        <div class="redundancy-stat-value">${fmtFloat(meanMarkers, 4)}</div>
                        <div class="redundancy-stat-note">Average pairwise Mash distance</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">CV (markers)</div>
                        <div class="redundancy-stat-value">${fmtFloat(cvMarkers, 3)}</div>
                        <div class="redundancy-stat-note">Coefficient of variation</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Mean distance (reads)</div>
                        <div class="redundancy-stat-value">${fmtFloat(meanReads, 4)}</div>
                        <div class="redundancy-stat-note">Average pairwise Mash distance</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">CV (reads)</div>
                        <div class="redundancy-stat-value">${fmtFloat(cvReads, 3)}</div>
                        <div class="redundancy-stat-note">Coefficient of variation</div>
                    </div>
                </div>
                <div class="clusters-heatmap-scroll" style="margin-top:12px; width:100%; overflow-x:auto; overflow-y:visible;">
                    <div id="mash-heatmap-plot" class="plotly-chart" style="height:420px; min-width:720px;"></div>
                </div>
                <p class="small-note">
                    Upper triangle shows marker-based distances; lower triangle shows read-based distances. Samples are ordered
                    by marker similarity. Cells without data are blank.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const plotDiv = div.querySelector("#mash-heatmap-plot");

    const allSamples = Array.from(new Set(
        [...markersPairs, ...readsPairs].flatMap(p => [p.sample1, p.sample2])
    )).filter(Boolean);

    function orderSamples(pairs) {
        const dist = {};
        pairs.forEach(p => {
            const d = Number(p.distance);
            if (!isFinite(d) || p.sample1 == null || p.sample2 == null) return;
            dist[`${p.sample1}||${p.sample2}`] = d;
            dist[`${p.sample2}||${p.sample1}`] = d;
        });
        if (allSamples.length <= 2) return allSamples.slice().sort();
        const remaining = new Set(allSamples);
        let current = allSamples[0];
        const order = [current];
        remaining.delete(current);
        while (remaining.size) {
            let best = null, bestD = Infinity;
            remaining.forEach(s => {
                const d = dist[`${current}||${s}`];
                const val = isFinite(d) ? d : Infinity;
                if (val < bestD) {
                    bestD = val;
                    best = s;
                }
            });
            if (!best) {
                remaining.forEach(s => order.push(s));
                break;
            }
            order.push(best);
            remaining.delete(best);
            current = best;
        }
        return order;
    }

    const orderedSamples = orderSamples(markersPairs.length ? markersPairs : readsPairs);
    if (!orderedSamples.length) {
        plotDiv.outerHTML = `<div class="small-note">No pairwise distances available.</div>`;
        return;
    }

    if (typeof Plotly === "undefined") {
        plotDiv.outerHTML = `<div class="small-note">Plotly failed to load; cannot render Mash distance heatmap.</div>`;
        return;
    }

    const markersMap = {};
    markersPairs.forEach(p => {
        const d = Number(p.distance);
        if (!isFinite(d) || p.sample1 == null || p.sample2 == null) return;
        markersMap[`${p.sample1}||${p.sample2}`] = d;
        markersMap[`${p.sample2}||${p.sample1}`] = d;
    });
    const readsMap = {};
    readsPairs.forEach(p => {
        const d = Number(p.distance);
        if (!isFinite(d) || p.sample1 == null || p.sample2 == null) return;
        readsMap[`${p.sample1}||${p.sample2}`] = d;
        readsMap[`${p.sample2}||${p.sample1}`] = d;
    });

    const n = orderedSamples.length;
    const zMarkers = Array.from({length: n}, () => Array(n).fill(null));
    const textMarkers = Array.from({length: n}, () => Array(n).fill(""));
    const zReads = Array.from({length: n}, () => Array(n).fill(null));
    const textReads = Array.from({length: n}, () => Array(n).fill(""));
    let maxD = 0;

    orderedSamples.forEach((s1, i) => {
        orderedSamples.forEach((s2, j) => {
            if (i === j) return;
            const key = `${s1}||${s2}`;
            let d = null;
            let source = "";
            if (i < j && markersMap.hasOwnProperty(key)) {
                d = markersMap[key];
                source = "Markers";
            } else if (i > j && readsMap.hasOwnProperty(key)) {
                d = readsMap[key];
                source = "Reads";
            }
            if (d != null) {
                if (source === "Markers") {
                    zMarkers[i][j] = d;
                    textMarkers[i][j] = `${s1} vs ${s2}<br>${source} distance: ${fmtFloat(d, 4)}`;
                } else {
                    zReads[i][j] = d;
                    textReads[i][j] = `${s1} vs ${s2}<br>${source} distance: ${fmtFloat(d, 4)}`;
                }
                if (d > maxD) maxD = d;
            }
        });
    });
    if (maxD <= 0) maxD = 1;

    const makeColorscale = (colors) =>
        colors.map((c, idx) => [idx / Math.max(1, colors.length - 1), c]);

    const markersHeatmap = {
        type: "heatmap",
        x: orderedSamples,
        y: orderedSamples,
        z: zMarkers,
        text: textMarkers,
        hovertemplate: "%{text}<extra></extra>",
        hoverinfo: "text",
        colorscale: makeColorscale([
            "#f7fbff", "#c6dbef", "#9ecae1", "#6baed6", "#3182bd", "#08519c", "#08306b"
        ]),
        zmin: 0,
        zmax: maxD,
        colorbar: {
            title: "Dissimilarity",
            titleside: "right",
            x: 1.12,
        },
        showscale: true,
    };
    const readsHeatmap = {
        type: "heatmap",
        x: orderedSamples,
        y: orderedSamples,
        z: zReads,
        text: textReads,
        hovertemplate: "%{text}<extra></extra>",
        hoverinfo: "text",
        colorscale: makeColorscale([
            "#fff5eb", "#fdd0a2", "#fdae6b", "#fd8d3c", "#f16913", "#d94801", "#8c2d04"
        ]),
        zmin: 0,
        zmax: maxD,
        colorbar: {
            title: "",
            titleside: "right",
            x: 1.02,
            tickvals: [],
            ticktext: [],
            ticks: "",
            showticklabels: false,
        },
        showscale: true,
    };

    const tickAngle = n > 18 ? -60 : -45;
    const bottomMargin = n > 18 ? 140 : 100;
    const leftMargin = n > 12 ? 170 : 140;

    const layoutHeight = Math.max(320, n * 20 + 220);

    const layout = {
        height: layoutHeight,
        margin: {l: leftMargin, r: 40, t: 20, b: bottomMargin},
        xaxis: {
            tickangle: tickAngle,
            automargin: true,
        },
        yaxis: {
            automargin: true,
            autorange: "reversed",
        },
        hovermode: "closest",
    };

    const config = {
        displaylogo: false,
        responsive: true,
        modeBarButtonsToRemove: ["toggleSpikelines", "autoScale2d"],
    };

    Plotly.newPlot(plotDiv, [readsHeatmap, markersHeatmap], layout, config);
    window.addEventListener("resize", () => Plotly.Plots.resize(plotDiv));
}

/* Sample clusters */
/* Main JS entry */
function main() {
    const distill = DISTILL_DATA;
    const figures = FIGURES_DATA;

    const summaryDiv = document.getElementById("summary-sections");
    const highlightsDiv = document.getElementById("project-highlights");

    const S = distill.summary || {};

    const depthFig = figures.figures && figures.figures.dna_depth_fractions
        ? figures.figures.dna_depth_fractions
        : null;
    const depthPerSample = depthFig ? (depthFig.per_sample || []) : [];

    const redBiplot = figures.figures && figures.figures.redundancy_biplot
        ? figures.figures.redundancy_biplot
        : null;
    const redBiplotPerSample = redBiplot ? (redBiplot.per_sample || []) : [];

    addProjectHighlights(highlightsDiv, distill, S);
    addScreeningOverviewSection(summaryDiv, S.screening_overview, depthPerSample);
    addLowQualitySection(summaryDiv, S.sequencing_quality, depthPerSample);
    addProkFractionSection(summaryDiv, S.prokaryotic_fraction, depthPerSample);
    addRedundancyReadsSection(summaryDiv, S.redundancy_reads, depthPerSample);
    addRedundancyMarkersSection(summaryDiv, S.redundancy_markers, redBiplotPerSample);
    addOverallCoverageSection(summaryDiv, S.overall_coverage_summary);
    addMashDistanceSection(summaryDiv, S.clusters);
    addClustersSection(summaryDiv, S.clusters, S.ordinations);
    addRecommendationsSection(summaryDiv, S.recommendations);
    setSummaryHintBehaviour(document.body);
}

main();
</script>

</body>
</html>
"""

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Create a static HTML report from distill.json and figures.json.\n"
            "The report shows collapsible sections coloured by flags, with user-friendly text and figures."
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
        help="Path to figures.json (figure-friendly data).",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Path to output HTML report (e.g. screenm_report.html).",
    )
    args = parser.parse_args()

    distill_path = Path(args.distill_json)
    figures_path = Path(args.figures_json)

    with distill_path.open() as f:
        distill_data = json.load(f)
    with figures_path.open() as f:
        figures_data = json.load(f)

    distill_json_str = json.dumps(distill_data, indent=2)
    figures_json_str = json.dumps(figures_data, indent=2)

    distill_json_str = distill_json_str.replace("</script>", "<\\/script>")
    figures_json_str = figures_json_str.replace("</script>", "<\\/script>")

    html = (
        HTML_TEMPLATE
        .replace("__DISTILL_JSON__", distill_json_str)
        .replace("__FIGURES_JSON__", figures_json_str)
    )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    main()
