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
        height: 360px;
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
                    : (summary.low_quality_reads || {}).total_reads
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
    div.className = "section " + flagClass(data.flag_low_quality);

    const msg = data.message_low_quality || "";

    const overall = data.percent_removed_reads_overall;
    const meanFrac = data.mean_fraction_removed;
    const medianFrac = data.median_fraction_removed;

    const status = sectionStatus("Sequencing quality", data.flag_low_quality);

    div.innerHTML = `
        <h2 class="section-title">Sequencing quality</h2>
        <p class="section-intro">
            This section reports how many reads are discarded by quality trimming and filtering across samples.
            High proportions of low-quality reads may indicate suboptimal sequencing performance, so it is important 
            to quantify the extent of this potential issue.
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
                        <div class="quality-stat-label">Overall removed</div>
                        <div class="quality-stat-value">${fmtFloat(overall, 2)}%</div>
                        <div class="quality-stat-note">Fraction of reads removed across all samples</div>
                    </div>
                    <div class="quality-stat-item">
                        <div class="quality-stat-label">Mean removed per sample</div>
                        <div class="quality-stat-value">${fmtFloat(100 * meanFrac, 2)}%</div>
                        <div class="quality-stat-note">Average fraction removed per sample</div>
                    </div>
                    <div class="quality-stat-item">
                        <div class="quality-stat-label">Median removed per sample</div>
                        <div class="quality-stat-value">${fmtFloat(100 * medianFrac, 2)}%</div>
                        <div class="quality-stat-note">Typical per-sample fraction of discarded reads</div>
                    </div>
                </div>
                <div class="quality-plot-container">
                    <div id="quality-plot" class="plotly-chart"></div>
                </div>
                <p class="small-note">
                    Interactive barplot of per-sample removed fractions (fastp). Bars are green (&le; 5%),
                    yellow (5–20%) or red (&gt; 20%). Horizontal dashed lines (when applicable) mark 5% and
                    20% thresholds, and the median removed fraction is shown as a dark grey dashed line.
                    The plot resizes with the page width.
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
    const fracs = perSample.map(d => {
        const v = Number(d.fraction_low_quality_of_total);
        return Number.isFinite(v) && v >= 0 ? v : 0;
    });

    const colors = fracs.map(v => {
        if (v <= THRESH_GOOD) return "#2e7d32";
        if (v <= THRESH_MOD) return "#f9a825";
        return "#c62828";
    });

    const hover = fracs.map((val, idx) => {
        return [
            `<b>${samples[idx]}</b>`,
            `Removed: ${(val * 100).toFixed(2)}%`,
            `Thresholds: 5% & 20%`
        ].join("<br>");
    });

    const trace = {
        type: "bar",
        x: samples,
        y: fracs,
        marker: {color: colors},
        hovertemplate: "%{customdata}<extra></extra>",
        customdata: hover,
    };

    const maxFracObserved = Math.max(...fracs, 0);
    const hasGoodLine = maxFracObserved >= THRESH_GOOD - 1e-9;
    const hasModLine = maxFracObserved >= THRESH_MOD - 1e-9;
    const medianRemoved = Number(medianFrac) || 0;

    const maxCandidates = [maxFracObserved];
    if (hasGoodLine) maxCandidates.push(THRESH_GOOD);
    if (hasModLine) maxCandidates.push(THRESH_MOD);
    if (medianRemoved > 0) maxCandidates.push(medianRemoved);
    const maxFrac = Math.max(0.05, Math.max(...maxCandidates) * 1.1);

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

    if (medianRemoved > 0) {
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

    const layout = {
        height: 360,
        margin: {l: 80, r: 28, t: 16, b: bottomMargin},
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
            title: "Reads removed by fastp (%)",
            range: [0, maxFrac],
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

    Plotly.newPlot(plotDiv, [trace], layout, config);
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
            This section describes how much of the sequencing effort is targeting prokaryotic genomes
            versus non-prokaryotic or low-quality reads.
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
        hovertemplate: "%{text}<extra></extra>",
        text: hoverLow,
    };

    const traceProk = {
        type: "bar",
        name: "",
        x: samples,
        y: fracProk,
        marker: {color: prokColors},
        hovertemplate: "%{text}<extra></extra>",
        text: hoverProk,
    };

    const traceOther = {
        type: "bar",
        name: "",
        x: samples,
        y: fracOther,
        marker: {color: "#bdbdbd"},
        hovertemplate: "%{text}<extra></extra>",
        text: hoverOther,
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

/* Overall metagenomic coverage (reads Nonpareil) */
function addRedundancyReadsSection(parent, data, depthPerSample) {
    if (!data) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(data.flag_redundancy);

    const msg = data.message_redundancy || "";

    const nLR = data.n_samples_with_lr || 0;
    const nBelow = data.n_samples_lr_exceeds_depth || 0;
    const nAtOrAbove = nLR ? (nLR - nBelow) : 0;
    const fracAtOrAbove = nLR ? (100 * nAtOrAbove / nLR) : null;
    const coverageVals = (Array.isArray(data.coverage_ratios) && data.coverage_ratios.length)
        ? data.coverage_ratios.filter(v => typeof v === "number" && isFinite(v))
        : (data.coverage_median !== undefined ? [data.coverage_median] : []);
    const covMedian = data.coverage_median != null ? data.coverage_median : median(coverageVals);
    const covCV = data.coverage_cv != null ? data.coverage_cv : coeffVar(coverageVals);

    const status = sectionStatus("Overall metagenomic coverage", data.flag_redundancy);

    div.innerHTML = `
        <h2 class="section-title">Metagenomic coverage of samples</h2>
        <p class="section-intro">
            This section evaluates how close the sequencing depth is to the Nonpareil LR target for metagenomic reads.
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
                        <div class="redundancy-stat-note">Estimated Nonpareil coverage (C_total)</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Coverage CV</div>
                        <div class="redundancy-stat-value">${covCV === null ? "NA" : fmtFloat(covCV, 3)}</div>
                        <div class="redundancy-stat-note">Coefficient of variation of coverage estimates</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">kappa median</div>
                        <div class="redundancy-stat-value">${fmtFloat(data.median_kappa_total, 3)}</div>
                        <div class="redundancy-stat-note">Median Nonpareil kappa_total (reads)</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">kappa CV</div>
                        <div class="redundancy-stat-value">${fmtFloat(data.cv_kappa_total, 3)}</div>
                        <div class="redundancy-stat-note">Variation in kappa_total across samples</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Samples above LR target</div>
                        <div class="redundancy-stat-value">
                            ${fmtInt(nAtOrAbove)} / ${fmtInt(nLR)}
                        </div>
                        <div class="redundancy-stat-note">
                            ${fracAtOrAbove === null ? "NA" : fmtFloat(fracAtOrAbove, 1) + "%"} of samples with LR target
                        </div>
                    </div>
                </div>
                <p class="small-note">
                    LR target used: ${data.lr_target_used || "NA"}% of metagenomic diversity (Nonpareil 95% LR_reads).
                </p>
                <div class="lr-target-plot-container">
                    <svg id="lr-target-svg" class="lr-target-svg" viewBox="0 0 1000 320" preserveAspectRatio="none"></svg>
                </div>
                <p class="small-note">
                    X axis: samples; Y axis: sequenced depth relative to the LR_reads 95% target.
                    The black dashed midline corresponds to the LR target. Tick labels above
                    start at 1×, showing how many times more than necessary has been sequenced;
                    ticks below show -1×, -2×, -3× etc. Bars more than 3× short of the target
                    are shown in red.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const svg = div.querySelector("#lr-target-svg");

    const combined = (depthPerSample || []).map(d => {
        const observed = d.total_reads != null ? Number(d.total_reads) : null;
        const target = d.target_reads_95_LR_reads != null ? Number(d.target_reads_95_LR_reads) : null;
        let ratio = null;
        if (observed != null && target && target > 0) {
            ratio = observed / target;
        }
        return {
            sample: d.sample,
            observed,
            target,
            ratio
        };
    }).filter(d => d.ratio != null);

    if (!combined.length) {
        svg.outerHTML = `<div class="small-note">No per-sample LR_reads and depth information available to compare against LR targets (reads).</div>`;
        return;
    }

    const width = 1000;
    const height = 320;
    const margin = {left: 60, right: 20, top: 20, bottom: 80};
    const plotW = width - margin.left - margin.right;
    const plotH = height - margin.top - margin.bottom;
    const svgns = "http://www.w3.org/2000/svg";

    const x0 = margin.left;
    const yTop = margin.top;
    const yBottom = height - margin.bottom;
    const baselineY = yTop + plotH / 2;

    function transformRatio(r) {
        if (r >= 1) return r - 1;
        return -(1 / r - 1);
    }

    const values = combined.map(d => transformRatio(d.ratio));
    let maxAbs = 0;
    values.forEach(v => {
        const a = Math.abs(v);
        if (a > maxAbs) maxAbs = a;
    });
    maxAbs = Math.max(maxAbs * 1.05, 1);

    function yForVal(v) {
        const f = v / maxAbs;
        return baselineY - f * (plotH / 2);
    }

    const xAxis = document.createElementNS(svgns, "line");
    xAxis.setAttribute("x1", x0);
    xAxis.setAttribute("y1", yBottom);
    xAxis.setAttribute("x2", x0 + plotW);
    xAxis.setAttribute("y2", yBottom);
    xAxis.setAttribute("stroke", "#555");
    svg.appendChild(xAxis);

    const yAxis = document.createElementNS(svgns, "line");
    yAxis.setAttribute("x1", x0);
    yAxis.setAttribute("y1", yBottom);
    yAxis.setAttribute("x2", x0);
    yAxis.setAttribute("y2", yTop);
    yAxis.setAttribute("stroke", "#555");
    svg.appendChild(yAxis);

    const baseLine = document.createElementNS(svgns, "line");
    baseLine.setAttribute("x1", x0);
    baseLine.setAttribute("y1", baselineY);
    baseLine.setAttribute("x2", x0 + plotW);
    baseLine.setAttribute("y2", baselineY);
    baseLine.setAttribute("stroke", "#000000");
    baseLine.setAttribute("stroke-width", "1.4");
    baseLine.setAttribute("stroke-dasharray", "4,2");
    svg.appendChild(baseLine);

    const baseLabel = document.createElementNS(svgns, "text");
    baseLabel.setAttribute("x", x0 + plotW - 4);
    baseLabel.setAttribute("y", baselineY - 4);
    baseLabel.setAttribute("font-size", "10");
    baseLabel.setAttribute("text-anchor", "end");
    baseLabel.setAttribute("fill", "#000000");
    baseLabel.textContent = "LR target";
    svg.appendChild(baseLabel);

    const maxTick = Math.max(1, Math.ceil(maxAbs));
    const stepTick = Math.max(1, Math.round(maxTick / 5));
    for (let v = -maxTick; v <= maxTick; v += stepTick) {
        const y = yForVal(v);
        const tick = document.createElementNS(svgns, "line");
        tick.setAttribute("x1", x0 - 4);
        tick.setAttribute("y1", y);
        tick.setAttribute("x2", x0);
        tick.setAttribute("y2", y);
        tick.setAttribute("stroke", "#555");
        svg.appendChild(tick);

        if (v === 0) continue;

        const lab = document.createElementNS(svgns, "text");
        lab.setAttribute("x", x0 - 6);
        lab.setAttribute("y", y + 3);
        lab.setAttribute("font-size", "10");
        lab.setAttribute("text-anchor", "end");

        let labelStr;
        if (v > 0) {
            labelStr = v.toFixed(0) + "×";
        } else {
            labelStr = "-" + Math.abs(v).toFixed(0) + "×";
        }
        lab.textContent = labelStr;
        svg.appendChild(lab);
    }

    if (maxAbs >= 3) {
        const yThr = yForVal(-3);
        const thrLine = document.createElementNS(svgns, "line");
        thrLine.setAttribute("x1", x0);
        thrLine.setAttribute("y1", yThr);
        thrLine.setAttribute("x2", x0 + plotW);
        thrLine.setAttribute("y2", yThr);
        thrLine.setAttribute("stroke", "#c62828");
        thrLine.setAttribute("stroke-width", "1.4");
        thrLine.setAttribute("stroke-dasharray", "4,2");
        svg.appendChild(thrLine);

        const thrLabel = document.createElementNS(svgns, "text");
        thrLabel.setAttribute("x", x0 + plotW - 4);
        thrLabel.setAttribute("y", yThr - 2);
        thrLabel.setAttribute("font-size", "10");
        thrLabel.setAttribute("text-anchor", "end");
        thrLabel.setAttribute("fill", "#c62828");
        thrLabel.textContent = "-3×";
        svg.appendChild(thrLabel);
    }

    const ylabel = document.createElementNS(svgns, "text");
    ylabel.setAttribute("x", 16);
    ylabel.setAttribute("y", margin.top + plotH / 2);
    ylabel.setAttribute("text-anchor", "middle");
    ylabel.setAttribute("font-size", "11");
    ylabel.setAttribute("transform", `rotate(-90 16 ${margin.top + plotH / 2})`);
    ylabel.textContent = "Sequenced depth vs LR target (extra / missing ×)";
    svg.appendChild(ylabel);

    const xlabel = document.createElementNS(svgns, "text");
    xlabel.setAttribute("x", margin.left + plotW / 2);
    xlabel.setAttribute("y", height - 8);
    xlabel.setAttribute("text-anchor", "middle");
    xlabel.setAttribute("font-size", "11");
    xlabel.textContent = "Samples";
    svg.appendChild(xlabel);

    const tooltip = getOrCreateTooltip();

    const n = combined.length;
    const stepX = plotW / n;
    const barWidth = Math.min(16, stepX * 0.8);

    combined.forEach((d, i) => {
        const ratio = d.ratio;
        const v = transformRatio(ratio);
        const yVal = yForVal(v);

        const xCenter = x0 + stepX * i + stepX / 2;
        const x = xCenter - barWidth / 2;

        let yRect, hRect;
        if (v >= 0) {
            yRect = yVal;
            hRect = baselineY - yVal;
        } else {
            yRect = baselineY;
            hRect = yVal - baselineY;
        }
        hRect = Math.abs(hRect);

        let fillColor;
        if (v >= 0) {
            fillColor = "#4caf50";
        } else if (v >= -3) {
            fillColor = "#ffa000";
        } else {
            fillColor = "#c62828";
        }

        const rect = document.createElementNS(svgns, "rect");
        rect.setAttribute("x", x);
        rect.setAttribute("y", yRect);
        rect.setAttribute("width", barWidth);
        rect.setAttribute("height", hRect);
        rect.setAttribute("fill", fillColor);
        rect.setAttribute("fill-opacity", "0.9");
        rect.style.cursor = "pointer";

        const extraOrNeeded = v >= 0 ? (ratio - 1) : (1 / ratio - 1);
        const tooltipText =
            `${d.sample}\n` +
            `Sequenced: ${fmtMillions(d.observed)} reads\n` +
            `Target (95% LR): ${fmtMillions(d.target)} reads\n` +
            `Relative depth: ${(ratio * 100).toFixed(1)}%\n` +
            (v >= 0
                ? `Excess sequencing: ${extraOrNeeded.toFixed(2)}× above target`
                : `Additional needed: ${extraOrNeeded.toFixed(2)}× more to reach target`);

        rect.addEventListener("mouseenter", (evt) => {
            rect.setAttribute("stroke", "#000");
            rect.setAttribute("stroke-width", "1");
            tooltip.style.display = "block";
            tooltip.textContent = tooltipText;
            tooltip.style.left = evt.clientX + "px";
            tooltip.style.top = evt.clientY + "px";
        });
        rect.addEventListener("mousemove", (evt) => {
            tooltip.style.left = evt.clientX + "px";
            tooltip.style.top = evt.clientY + "px";
        });
        rect.addEventListener("mouseleave", () => {
            rect.removeAttribute("stroke");
            rect.removeAttribute("stroke-width");
            tooltip.style.display = "none";
        });

        svg.appendChild(rect);

        const showAll = n <= 40;
        const show = showAll || (i % 5 === 0);
        if (show) {
            const lab = document.createElementNS(svgns, "text");
            lab.setAttribute("x", xCenter);
            lab.setAttribute("y", yBottom + 10);
            lab.setAttribute("font-size", "9");
            lab.setAttribute("text-anchor", "end");
            lab.setAttribute("transform", `rotate(-60 ${xCenter} ${yBottom + 10})`);
            lab.textContent = d.sample;
            svg.appendChild(lab);
        }
    });
}

/* Prokaryotic coverage (markers Nonpareil) */
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
            This section evaluates coverage of marker genes relative to the 95% Nonpareil target.
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
                        <div class="redundancy-stat-note">Estimated Nonpareil coverage (C_total)</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Coverage CV</div>
                        <div class="redundancy-stat-value">${covCV === null ? "NA" : fmtFloat(covCV, 3)}</div>
                        <div class="redundancy-stat-note">Coefficient of variation of coverage estimates</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">kappa median</div>
                        <div class="redundancy-stat-value">${fmtFloat(data.median_kappa_total, 3)}</div>
                        <div class="redundancy-stat-note">Median Nonpareil kappa_total (markers)</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">kappa CV</div>
                        <div class="redundancy-stat-value">${fmtFloat(data.cv_kappa_total, 3)}</div>
                        <div class="redundancy-stat-note">Variation in kappa_total across samples</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Samples above LR target</div>
                        <div class="redundancy-stat-value">
                            ${fmtInt(nAtOrAbove)} / ${fmtInt(nLR)}
                        </div>
                        <div class="redundancy-stat-note">
                            ${fracAtOrAbove === null ? "NA" : fmtFloat(fracAtOrAbove, 1) + "%"} of samples with LR target
                        </div>
                    </div>
                </div>
                <p class="small-note">
                    LR target used: ${data.lr_target_used || "NA"}% of marker-based diversity (Nonpareil 95% LR_reads).
                </p>
                <div class="lr-target-markers-plot-container">
                    <svg id="lr-target-markers-svg" class="lr-target-markers-svg" viewBox="0 0 1000 320" preserveAspectRatio="none"></svg>
                </div>
                <p class="small-note">
                    X axis: samples; Y axis: estimated marker coverage relative to the 95% target.
                    The black dashed midline corresponds to the 95% coverage target. Bars above it show excess
                    coverage (1×, 2×, ...), while bars below show how many times more coverage would be needed
                    (-1×, -2×, -3× etc.). Bars more than 3× short of the target are shown in red.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const svg = div.querySelector("#lr-target-markers-svg");

    const combined = (redBiplotPerSample || []).map(r => {
        const coverage = r.coverage_markers != null ? Number(r.coverage_markers) : null;
        let ratio = null;
        if (coverage != null && coverage > 0) {
            ratio = coverage / 0.95;
        }
        return {
            sample: r.sample,
            coverage,
            ratio
        };
    }).filter(d => d.ratio != null);

    if (!combined.length) {
        svg.outerHTML = `<div class="small-note">No per-sample marker coverage / LR target information available for marker redundancy plot.</div>`;
        return;
    }

    const width = 1000;
    const height = 320;
    const margin = {left: 60, right: 20, top: 20, bottom: 80};
    const plotW = width - margin.left - margin.right;
    const plotH = height - margin.top - margin.bottom;
    const svgns = "http://www.w3.org/2000/svg";

    const x0 = margin.left;
    const yTop = margin.top;
    const yBottom = height - margin.bottom;
    const baselineY = yTop + plotH / 2;

    function transformRatio(r) {
        if (r >= 1) return r - 1;
        return -(1 / r - 1);
    }

    const values = combined.map(d => transformRatio(d.ratio));
    let maxAbs = 0;
    values.forEach(v => {
        const a = Math.abs(v);
        if (a > maxAbs) maxAbs = a;
    });
    maxAbs = Math.max(maxAbs * 1.05, 1);

    function yForVal(v) {
        const f = v / maxAbs;
        return baselineY - f * (plotH / 2);
    }

    const xAxis = document.createElementNS(svgns, "line");
    xAxis.setAttribute("x1", x0);
    xAxis.setAttribute("y1", yBottom);
    xAxis.setAttribute("x2", x0 + plotW);
    xAxis.setAttribute("y2", yBottom);
    xAxis.setAttribute("stroke", "#555");
    svg.appendChild(xAxis);

    const yAxis = document.createElementNS(svgns, "line");
    yAxis.setAttribute("x1", x0);
    yAxis.setAttribute("y1", yBottom);
    yAxis.setAttribute("x2", x0);
    yAxis.setAttribute("y2", yTop);
    yAxis.setAttribute("stroke", "#555");
    svg.appendChild(yAxis);

    const baseLine = document.createElementNS(svgns, "line");
    baseLine.setAttribute("x1", x0);
    baseLine.setAttribute("y1", baselineY);
    baseLine.setAttribute("x2", x0 + plotW);
    baseLine.setAttribute("y2", baselineY);
    baseLine.setAttribute("stroke", "#000000");
    baseLine.setAttribute("stroke-width", "1.4");
    baseLine.setAttribute("stroke-dasharray", "4,2");
    svg.appendChild(baseLine);

    const baseLabel = document.createElementNS(svgns, "text");
    baseLabel.setAttribute("x", x0 + plotW - 4);
    baseLabel.setAttribute("y", baselineY - 4);
    baseLabel.setAttribute("font-size", "10");
    baseLabel.setAttribute("text-anchor", "end");
    baseLabel.setAttribute("fill", "#000000");
    baseLabel.textContent = "95% coverage target";
    svg.appendChild(baseLabel);

    const maxTick = Math.max(1, Math.ceil(maxAbs));
    const stepTick = Math.max(1, Math.round(maxTick / 5));
    for (let v = -maxTick; v <= maxTick; v += stepTick) {
        const y = yForVal(v);
        const tick = document.createElementNS(svgns, "line");
        tick.setAttribute("x1", x0 - 4);
        tick.setAttribute("y1", y);
        tick.setAttribute("x2", x0);
        tick.setAttribute("y2", y);
        tick.setAttribute("stroke", "#555");
        svg.appendChild(tick);

        if (v === 0) continue;

        const lab = document.createElementNS(svgns, "text");
        lab.setAttribute("x", x0 - 6);
        lab.setAttribute("y", y + 3);
        lab.setAttribute("font-size", "10");
        lab.setAttribute("text-anchor", "end");

        let labelStr;
        if (v > 0) {
            labelStr = v.toFixed(0) + "×";
        } else {
            labelStr = "-" + Math.abs(v).toFixed(0) + "×";
        }
        lab.textContent = labelStr;
        svg.appendChild(lab);
    }

    if (maxAbs >= 3) {
        const yThr = yForVal(-3);
        const thrLine = document.createElementNS(svgns, "line");
        thrLine.setAttribute("x1", x0);
        thrLine.setAttribute("y1", yThr);
        thrLine.setAttribute("x2", x0 + plotW);
        thrLine.setAttribute("y2", yThr);
        thrLine.setAttribute("stroke", "#c62828");
        thrLine.setAttribute("stroke-width", "1.4");
        thrLine.setAttribute("stroke-dasharray", "4,2");
        svg.appendChild(thrLine);

        const thrLabel = document.createElementNS(svgns, "text");
        thrLabel.setAttribute("x", x0 + plotW - 4);
        thrLabel.setAttribute("y", yThr - 2);
        thrLabel.setAttribute("font-size", "10");
        thrLabel.setAttribute("text-anchor", "end");
        thrLabel.setAttribute("fill", "#c62828");
        thrLabel.textContent = "-3×";
        svg.appendChild(thrLabel);
    }

    const ylabel = document.createElementNS(svgns, "text");
    ylabel.setAttribute("x", 16);
    ylabel.setAttribute("y", margin.top + plotH / 2);
    ylabel.setAttribute("text-anchor", "middle");
    ylabel.setAttribute("font-size", "11");
    ylabel.setAttribute("transform", `rotate(-90 16 ${margin.top + plotH / 2})`);
    ylabel.textContent = "Marker coverage vs 95% target (extra / missing ×)";
    svg.appendChild(ylabel);

    const xlabel = document.createElementNS(svgns, "text");
    xlabel.setAttribute("x", margin.left + plotW / 2);
    xlabel.setAttribute("y", height - 8);
    xlabel.setAttribute("text-anchor", "middle");
    xlabel.setAttribute("font-size", "11");
    xlabel.textContent = "Samples";
    svg.appendChild(xlabel);

    const tooltip = getOrCreateTooltip();

    const n = combined.length;
    const stepX = plotW / n;
    const barWidth = Math.min(16, stepX * 0.8);

    combined.forEach((d, i) => {
        const ratio = d.ratio;
        const v = transformRatio(ratio);
        const yVal = yForVal(v);

        const xCenter = x0 + stepX * i + stepX / 2;
        const x = xCenter - barWidth / 2;

        let yRect, hRect;
        if (v >= 0) {
            yRect = yVal;
            hRect = baselineY - yVal;
        } else {
            yRect = baselineY;
            hRect = yVal - baselineY;
        }
        hRect = Math.abs(hRect);

        let fillColor;
        if (v >= 0) {
            fillColor = "#4caf50";
        } else if (v >= -3) {
            fillColor = "#ffa000";
        } else {
            fillColor = "#c62828";
        }

        const rect = document.createElementNS(svgns, "rect");
        rect.setAttribute("x", x);
        rect.setAttribute("y", yRect);
        rect.setAttribute("width", barWidth);
        rect.setAttribute("height", hRect);
        rect.setAttribute("fill", fillColor);
        rect.setAttribute("fill-opacity", "0.9");
        rect.style.cursor = "pointer";

        const extraOrNeeded = v >= 0 ? (ratio - 1) : (1 / ratio - 1);
        const tooltipText =
            `${d.sample}\n` +
            `Coverage (markers): ${(d.coverage * 100).toFixed(2)}%\n` +
            `Relative to 95% target: ${(ratio * 100).toFixed(1)}%\n` +
            (v >= 0
                ? `Excess coverage: ${extraOrNeeded.toFixed(2)}× above target`
                : `Additional needed: ${extraOrNeeded.toFixed(2)}× more to reach target`);

        rect.addEventListener("mouseenter", (evt) => {
            rect.setAttribute("stroke", "#000");
            rect.setAttribute("stroke-width", "1");
            tooltip.style.display = "block";
            tooltip.textContent = tooltipText;
            tooltip.style.left = evt.clientX + "px";
            tooltip.style.top = evt.clientY + "px";
        });
        rect.addEventListener("mousemove", (evt) => {
            tooltip.style.left = evt.clientX + "px";
            tooltip.style.top = evt.clientY + "px";
        });
        rect.addEventListener("mouseleave", () => {
            rect.removeAttribute("stroke");
            rect.removeAttribute("stroke-width");
            tooltip.style.display = "none";
        });

        svg.appendChild(rect);

        const showAll = n <= 40;
        const show = showAll || (i % 5 === 0);
        if (show) {
            const lab = document.createElementNS(svgns, "text");
            lab.setAttribute("x", xCenter);
            lab.setAttribute("y", yBottom + 10);
            lab.setAttribute("font-size", "9");
            lab.setAttribute("text-anchor", "end");
            lab.setAttribute("transform", `rotate(-60 ${xCenter} ${yBottom + 10})`);
            lab.textContent = d.sample;
            svg.appendChild(lab);
        }
    });
}

/* Sample clusters */
function addClustersSection(parent, clusters) {
    if (!clusters) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(clusters.flag_clusters);

    const msg = clusters.message_clusters || "";
    const markers = clusters.markers || {};
    const reads = clusters.reads || {};

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
            This section highlights similarity-based clusters inferred from Mash distances on reads and marker genes.
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
                <p class="small-note">
                    Heatmap below shows cluster assignments per sample. Rows correspond to marker-based
                    and read-based clustering; columns are samples. Colour palettes are distinct per row,
                    so cluster IDs are not directly comparable between the two.
                </p>
                <div class="clusters-heatmap-scroll">
                    <svg id="clusters-heatmap-svg" class="clusters-heatmap-svg" viewBox="0 0 1000 210" preserveAspectRatio="none"></svg>
                </div>
                <p class="small-note">
                    Hover over tiles for exact cluster assignments. Samples without an assignment in a given
                    row are shown as light grey.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const svg = div.querySelector("#clusters-heatmap-svg");
    const svgns = "http://www.w3.org/2000/svg";
    const tooltip = getOrCreateTooltip();

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
        svg.outerHTML = `<div class="small-note">Per-sample cluster assignments not available; heatmap cannot be drawn.</div>`;
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

    const markerPalette = [
        "#08306b", "#08519c", "#2171b5", "#4292c6",
        "#41b6c4", "#1d91c0", "#2c7fb8", "#7fcdbb",
        "#0c2c84", "#4eb3d3", "#2b8cbe", "#a1dab4"
    ];
    const readPalette = [
        "#7f0000", "#b30000", "#e31a1c", "#ff7f00",
        "#f03b20", "#bd0026", "#fd8d3c", "#fc4e2a",
        "#b10026", "#dd1c77", "#df65b0", "#ff1493"
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

    const markerColors = buildClusterColorMap(markersMap, markerPalette);
    const readColors = buildClusterColorMap(readsMap, readPalette);

    const height = 240;
    const margin = {left: 80, right: 20, top: 20, bottom: 60};
    const rows = 2;
    const cellH = (height - margin.top - margin.bottom) / rows;
    const baseCellW = 20;
    const width = Math.max(1000, margin.left + margin.right + nSamples * baseCellW);
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

    const plotW = width - margin.left - margin.right;
    const x0 = margin.left;

    function drawRow(rowIndex, label, map, colorMap, defaultColor) {
        const yRowTop = margin.top + rowIndex * cellH;
        const labelX = 10;
        thelabelY = yRowTop + cellH / 2 + 4;
        const labelText = document.createElementNS(svgns, "text");
        labelText.setAttribute("x", labelX);
        labelText.setAttribute("y", thelabelY);
        labelText.setAttribute("font-size", "11");
        labelText.setAttribute("text-anchor", "start");
        labelText.textContent = label;
        svg.appendChild(labelText);

        const cellW = plotW / nSamples;

        samples.forEach((sampleName, i) => {
            const cluster = map[sampleName];
            const hasCluster = cluster !== null && cluster !== undefined;
            const fill = hasCluster ? (colorMap[cluster] || defaultColor) : "#eeeeee";

            const x = x0 + i * cellW;
            const y = yRowTop;

            const rect = document.createElementNS(svgns, "rect");
            rect.setAttribute("x", x);
            rect.setAttribute("y", y);
            rect.setAttribute("width", cellW);
            rect.setAttribute("height", cellH);
            rect.setAttribute("fill", fill);
            rect.setAttribute("stroke", "#ffffff");
            rect.setAttribute("stroke-width", "0.5");
            rect.style.cursor = hasCluster ? "pointer" : "default";

            const tooltipText = hasCluster
                ? `${sampleName}\n${label}: cluster ${cluster}`
                : `${sampleName}\n${label}: no cluster assigned`;

            rect.addEventListener("mouseenter", (evt) => {
                rect.setAttribute("stroke", "#000");
                rect.setAttribute("stroke-width", "1");
                tooltip.style.display = "block";
                tooltip.textContent = tooltipText;
                tooltip.style.left = evt.clientX + "px";
                tooltip.style.top = evt.clientY + "px";
            });
            rect.addEventListener("mousemove", (evt) => {
                tooltip.style.left = evt.clientX + "px";
                tooltip.style.top = evt.clientY + "px";
            });
            rect.addEventListener("mouseleave", () => {
                rect.setAttribute("stroke", "#ffffff");
                rect.setAttribute("stroke-width", "0.5");
                tooltip.style.display = "none";
            });

            svg.appendChild(rect);

            if (rowIndex === rows - 1) {
                const showAll = nSamples <= 40;
                const show = showAll || (i % 5 === 0);
                if (show) {
                    const lab = document.createElementNS(svgns, "text");
                    lab.setAttribute("x", x + cellW / 2);
                    lab.setAttribute("y", height - 8);
                    lab.setAttribute("font-size", "9");
                    lab.setAttribute("text-anchor", "end");
                    lab.setAttribute(
                        "transform",
                        `rotate(-60 ${x + cellW / 2} ${height - 8})`
                    );
                    lab.textContent = sampleName;
                    svg.appendChild(lab);
                }
            }
        });
    }

    drawRow(0, "Markers", markersMap, markerColors, "#9ecae1");
    drawRow(1, "Reads", readsMap, readColors, "#fcae91");
}

/* Overall metagenomic coverage summary */
function addOverallReadCoverageSection(parent, data) {
    if (!data) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(data.flag_overall_read_coverage);

    const status = sectionStatus("Overall metagenomic coverage", data.flag_overall_read_coverage);

    div.innerHTML = `
        <h2 class="section-title">Overall metagenomic coverage</h2>
        <p class="section-intro">
            Aggregated Nonpareil metagenomic coverage across all samples.
        </p>
        <details>
            <summary>
                <span class="status-emoji">${status.emoji}</span>
                <span class="status-text">${status.text}</span>
                <span class="summary-hint">(click to expand)</span>
            </summary>
            <div class="content">
                <p class="summary-message">${data.message_overall_read_coverage || ""}</p>
                <div class="redundancy-stats">
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Coverage (C_total)</div>
                        <div class="redundancy-stat-value">${data.coverage_percent != null ? fmtFloat(data.coverage_percent, 1) + "%" : "NA"}</div>
                        <div class="redundancy-stat-note">Pooled metagenomic coverage across all samples</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">kappa_total</div>
                        <div class="redundancy-stat-value">${fmtFloat(data.kappa_total, 3)}</div>
                        <div class="redundancy-stat-note">Nonpareil pooled metagenomic redundancy</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Total reads</div>
                        <div class="redundancy-stat-value">${fmtMillions(data.total_reads)}</div>
                        <div class="redundancy-stat-note">Sum of reads included in pooled metagenomic Nonpareil</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">LR target (95%)</div>
                        <div class="redundancy-stat-value">${fmtMillions(data.lr_95_reads)}</div>
                        <div class="redundancy-stat-note">Reads estimated for 95% coverage</div>
                    </div>
                </div>
            </div>
        </details>
    `;

    parent.appendChild(div);
}

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
                        <div class="redundancy-stat-label">kappa_total</div>
                        <div class="redundancy-stat-value">${fmtFloat(data.kappa_total, 3)}</div>
                        <div class="redundancy-stat-note">Nonpareil pooled marker redundancy</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Total reads</div>
                        <div class="redundancy-stat-value">${fmtMillions(data.total_reads)}</div>
                        <div class="redundancy-stat-note">Sum of reads included in pooled marker Nonpareil</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">LR target (95%)</div>
                        <div class="redundancy-stat-value">${fmtMillions(data.lr_95_reads)}</div>
                        <div class="redundancy-stat-note">Reads estimated for 95% coverage</div>
                    </div>
                </div>
            </div>
        </details>
    `;

    parent.appendChild(div);
}

/* Mash distance overview */
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
    const status = sectionStatus("Mash distance overview", clusters.flag_clusters);

    div.innerHTML = `
        <h2 class="section-title">Mash distance overview</h2>
        <p class="section-intro">
            Average pairwise Mash distances across all samples (markers and reads), with heatmaps for both.
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
                <div class="clusters-heatmap-scroll" style="margin-top:12px; max-height:720px; width:100%; overflow:auto;">
                    <div style="display:flex; gap:8px; margin-bottom:8px;">
                        <button id="mash-tab-markers" class="tab-btn active">Markers</button>
                        <button id="mash-tab-reads" class="tab-btn">Reads</button>
                    </div>
                    <svg id="mash-heatmap-markers" class="clusters-heatmap-svg"></svg>
                    <svg id="mash-heatmap-reads" class="clusters-heatmap-svg" style="display:none;"></svg>
                </div>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const heatMarkers = div.querySelector("#mash-heatmap-markers");
    const heatReads = div.querySelector("#mash-heatmap-reads");
    const tabMarkers = div.querySelector("#mash-tab-markers");
    const tabReads = div.querySelector("#mash-tab-reads");
    const svgns = "http://www.w3.org/2000/svg";

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

    const sharedOrder = orderSamples(markersPairs.length ? markersPairs : readsPairs);

    function drawHeatmap(svg, pairs) {
        const sampleSet = new Set();
        pairs.forEach(p => { if (p.sample1) sampleSet.add(p.sample1); if (p.sample2) sampleSet.add(p.sample2); });
        let samples = Array.from(sampleSet);
        if (sharedOrder && sharedOrder.length === samples.length) {
            samples = sharedOrder;
        } else {
            samples.sort();
        }
        const n = samples.length;
        if (!n) {
            svg.outerHTML = `<div class="small-note">No pairwise distances available.</div>`;
            return;
        }

        const map = {};
        let maxD = 0;
        pairs.forEach(p => {
            const d = Number(p.distance);
            if (!isFinite(d) || p.sample1 == null || p.sample2 == null) return;
            map[`${p.sample1}||${p.sample2}`] = d;
            map[`${p.sample2}||${p.sample1}`] = d;
            if (d > maxD) maxD = d;
        });
        if (maxD <= 0) maxD = 1;

        const margin = {left: 160, right: 30, top: 160, bottom: 60};
        const cellSize = Math.max(26, Math.min(40, (1200 - margin.left - margin.right) / Math.max(n, 20)));
        const width = margin.left + margin.right + n * cellSize;
        const height = margin.top + margin.bottom + n * cellSize;
        svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
        svg.style.width = `${width}px`;
        svg.style.height = `${height}px`;

        function colorFor(val) {
            const f = Math.max(0, Math.min(1, val / maxD));
            const c = Math.round(255 - f * 220);
            return `rgb(${c},${c+40},255)`;
        }

        samples.forEach((s1, i) => {
            samples.forEach((s2, j) => {
                const key = `${s1}||${s2}`;
                const d = map[key];
                const has = d != null;
                const fill = has ? colorFor(d) : "#eeeeee";
                const x = margin.left + j * cellSize;
                const y = margin.top + i * cellSize;
                const rect = document.createElementNS(svgns, "rect");
                rect.setAttribute("x", x);
                rect.setAttribute("y", y);
                rect.setAttribute("width", cellSize);
                rect.setAttribute("height", cellSize);
                rect.setAttribute("fill", fill);
                rect.setAttribute("stroke", "#ffffff");
                rect.setAttribute("stroke-width", "0.5");
                if (has) {
                    rect.style.cursor = "pointer";
                    rect.addEventListener("mouseenter", (evt) => {
                        const tooltip = getOrCreateTooltip();
                        tooltip.style.display = "block";
                        tooltip.textContent = `${s1} vs ${s2}\nMash distance: ${fmtFloat(d, 4)}`;
                        tooltip.style.left = evt.clientX + "px";
                        tooltip.style.top = evt.clientY + "px";
                    });
                    rect.addEventListener("mousemove", (evt) => {
                        const tooltip = getOrCreateTooltip();
                        tooltip.style.left = evt.clientX + "px";
                        tooltip.style.top = evt.clientY + "px";
                    });
                    rect.addEventListener("mouseleave", () => {
                        const tooltip = getOrCreateTooltip();
                        tooltip.style.display = "none";
                    });
                }
                svg.appendChild(rect);
            });
        });

        samples.forEach((s, idx) => {
            const x = margin.left + idx * cellSize + cellSize / 2;
            const yTop = margin.top - 18;
            const labTop = document.createElementNS(svgns, "text");
            labTop.setAttribute("x", x);
            labTop.setAttribute("y", yTop);
            labTop.setAttribute("font-size", "10");
            labTop.setAttribute("text-anchor", "end");
            labTop.setAttribute("transform", `rotate(-60 ${x} ${yTop})`);
            labTop.textContent = s;
            svg.appendChild(labTop);

            const labLeft = document.createElementNS(svgns, "text");
            labLeft.setAttribute("x", margin.left - 10);
            labLeft.setAttribute("y", margin.top + idx * cellSize + cellSize / 2 + 4);
            labLeft.setAttribute("font-size", "10");
            labLeft.setAttribute("text-anchor", "end");
            labLeft.textContent = s;
            svg.appendChild(labLeft);
        });
    }

    drawHeatmap(heatMarkers, markersPairs);
    drawHeatmap(heatReads, readsPairs);

    if (tabMarkers && tabReads) {
        tabMarkers.addEventListener("click", () => {
            tabMarkers.classList.add("active");
            tabReads.classList.remove("active");
            heatMarkers.style.display = "block";
            heatReads.style.display = "none";
        });
        tabReads.addEventListener("click", () => {
            tabReads.classList.add("active");
            tabMarkers.classList.remove("active");
            heatMarkers.style.display = "none";
            heatReads.style.display = "block";
        });
    }
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
    addLowQualitySection(summaryDiv, S.low_quality_reads, depthPerSample);
    addProkFractionSection(summaryDiv, S.prokaryotic_fraction, depthPerSample);
    addRedundancyReadsSection(summaryDiv, S.redundancy_reads, depthPerSample);
    addOverallReadCoverageSection(summaryDiv, S.overall_metagenomic_coverage);
    addRedundancyMarkersSection(summaryDiv, S.redundancy_markers, redBiplotPerSample);
    addOverallProkCoverageSection(summaryDiv, S.overall_prokaryotic_coverage);
    addMashDistanceSection(summaryDiv, S.clusters);
    addClustersSection(summaryDiv, S.clusters);
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
