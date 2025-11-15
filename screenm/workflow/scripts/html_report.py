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
        background: #f5f5f8;
        color: #222;
        padding: 20px 15px 40px 15px;
        line-height: 1.5;
    }
    h1 {
        text-align: center;
        margin-bottom: 0.5em;
        font-size: 2.2em;
        color: #222;
    }
    .subtitle {
        text-align: center;
        margin-top: 0;
        margin-bottom: 1.5em;
        font-size: 0.95em;
        color: #555;
    }
    .section {
        margin-bottom: 18px;
        border-radius: 8px;
        padding: 12px 14px;
        border: 1px solid #ddd;
        background-color: #ffffff;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .section h2 {
        margin-top: 0;
        margin-bottom: 4px;
        font-size: 1.3em;
    }
    .section-intro {
        margin-top: 0;
        margin-bottom: 8px;
        font-size: 0.95em;
        color: #444;
    }
    details {
        margin-top: 6px;
    }
    summary {
        cursor: pointer;
        font-weight: bold;
        list-style: none;
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 6px 8px;
        border-radius: 6px;
        background: rgba(255,255,255,0.5);
        border: 1px solid rgba(0,0,0,0.06);
    }
    summary::-webkit-details-marker {
        display: none;
    }
    .status-emoji {
        font-size: 1.2em;
    }
    .status-text {
        font-size: 0.95em;
    }
    .content {
        margin-top: 10px;
        padding: 6px 2px 2px 2px;
    }

    .flag-good {
        border-left: 6px solid #2e7d32;
        background-color: #e8f5e9;
    }
    .flag-medium {
        border-left: 6px solid #f9a825;
        background-color: #fff8e1;
    }
    .flag-bad {
        border-left: 6px solid #c62828;
        background-color: #ffebee;
    }

    .summary-message {
        margin-bottom: 12px;
        font-size: 0.95em;
    }

    .screen-overview-stats,
    .quality-stats,
    .prok-fraction-stats,
    .coverage-stats,
    .cluster-stats {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 12px;
    }

    .screen-overview-stat-item,
    .quality-stat-item,
    .prok-fraction-stat-item,
    .coverage-stat-item,
    .cluster-stat-item {
        min-width: 170px;
        padding: 8px 10px;
        background: #ffffff;
        border-radius: 6px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }

    .screen-overview-stat-label,
    .quality-stat-label,
    .prok-fraction-stat-label,
    .coverage-stat-label,
    .cluster-stat-label {
        font-size: 0.80em;
        text-transform: uppercase;
        color: #666;
        margin-bottom: 3px;
    }

    .screen-overview-stat-value,
    .quality-stat-value,
    .prok-fraction-stat-value,
    .coverage-stat-value,
    .cluster-stat-value {
        font-size: 1.25em;
        font-weight: 600;
        margin-bottom: 2px;
    }

    .screen-overview-stat-note,
    .quality-stat-note,
    .prok-fraction-stat-note,
    .coverage-stat-note,
    .cluster-stat-note {
        font-size: 0.78em;
        color: #777;
    }

    .small-note {
        font-size: 0.80em;
        color: #666;
        margin-top: 6px;
        margin-bottom: 4px;
    }

    .seq-depth-plot-container,
    .quality-plot-container,
    .prok-fraction-plot-container,
    .coverage-plot-container {
        margin-top: 10px;
    }

    .seq-depth-svg,
    .quality-svg {
        display: block;
        width: 100%;
        height: 320px;
    }

    .prok-fraction-svg {
        display: block;
        width: 100%;
        height: 320px;
    }

    .coverage-svg {
        display: block;
        width: 100%;
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

    .pairwise-heatmap-container {
        margin-top: 16px;
    }
    .pairwise-tabs {
        display: inline-flex;
        gap: 8px;
        margin-bottom: 6px;
    }
    .pairwise-tab {
        padding: 4px 10px;
        font-size: 0.9em;
        border-radius: 4px;
        border: 1px solid #bbb;
        background: #eee;
        cursor: pointer;
    }
    .pairwise-tab.active {
        background: #1976d2;
        color: #fff;
        border-color: #1976d2;
    }
    .pairwise-heatmap-scroll {
        overflow-x: auto;
        border: 1px solid #ddd;
        border-radius: 4px;
        background: #fcfcfc;
    }
    .pairwise-heatmap-svg {
        display: block;
        width: 100%;
        height: 420px;
    }


    .global-summary {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        justify-content: center;
        margin: 16px 0 20px 0;
    }
    .global-stat-item {
        min-width: 200px;
        padding: 8px 10px;
        border-radius: 6px;
        background: #ffffff;
        border: 1px solid #ddd;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .global-stat-label {
        font-size: 0.9em;
        color: #555;
        margin-bottom: 2px;
    }
    .global-stat-value {
        font-size: 1.6em;
        font-weight: 600;
    }
    .global-stat-note {
        font-size: 0.8em;
        color: #666;
        margin-top: 2px;
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
        white-space: nowrap;
        transform: translate(8px, -20px);
    }
</style>

</head>
<body>

<h1>ScreenM Summary Report</h1>

<div id="global-summary"></div>
<div id="summary-sections"></div>

<script>
const DISTILL_DATA = __DISTILL_JSON__;
const FIGURES_DATA = __FIGURES_JSON__;

function flagClass(flag) {
    if (flag === 1) {
        return "flag-good";
    } else if (flag === 2) {
        return "flag-medium";
    } else if (flag === 3) {
        return "flag-bad";
    }
    return "";
}

function fmtInt(x) {
    if (x === null || x === undefined || isNaN(x)) return "NA";
    return Number(x).toLocaleString("en-US", {maximumFractionDigits: 0});
}

function fmtFloat(x, digits) {
    if (x === null || x === undefined || isNaN(x)) return "NA";
    return Number(x).toFixed(digits);
}

function fmtMillions(x) {
    if (x === null || x === undefined || isNaN(x)) return "NA";
    const num = Number(x);
    if (num >= 1e6) {
        return (num / 1e6).toFixed(2) + " M";
    } else if (num >= 1e3) {
        return (num / 1e3).toFixed(2) + " k";
    }
    return num.toString();
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


function addGlobalSummary(container, distill, depthPerSample) {
    if (!container) return;
    const meta = distill.meta || {};
    const S = distill.summary || {};

    const nSamplesFromMeta = meta.n_samples_in_results;
    const nSamplesFromScreen = S.screening_overview ? S.screening_overview.n_samples_total : null;
    const nSamples = (nSamplesFromMeta != null ? nSamplesFromMeta : nSamplesFromScreen);

    let totalReads = null;
    if (S.low_quality_reads && S.low_quality_reads.total_reads != null) {
        totalReads = S.low_quality_reads.total_reads;
    } else if (Array.isArray(depthPerSample) && depthPerSample.length) {
        totalReads = depthPerSample.reduce((acc, d) => acc + (Number(d.total_reads) || 0), 0);
    }

    container.innerHTML = `
        <div class="global-summary">
            <div class="global-stat-item">
                <div class="global-stat-label">Samples</div>
                <div class="global-stat-value">${fmtInt(nSamples)}</div>
                <div class="global-stat-note">Samples included in ScreenM</div>
            </div>
            <div class="global-stat-item">
                <div class="global-stat-label">Total reads</div>
                <div class="global-stat-value">${fmtMillions(totalReads)}</div>
                <div class="global-stat-note">Sum of reads across all samples</div>
            </div>
        </div>
    `;
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
    } else if (flag === 3) {
        emoji = "⚠️";
        descriptor = "contains many warnings";
    } else {
        emoji = "ℹ️";
        descriptor = "has no formal flag";
    }

    return {
        emoji,
        text: `${sectionLabel} ${descriptor}`
    };
}

/* ---------- Section 1: Screening overview ---------- */
function addScreeningOverviewSection(parent, data, depthPerSample) {
    if (!data) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(data.flag_screening_overview);

    const msg = data.message_screening_overview || "";

    const total = data.n_samples_total;
    const above = data.n_samples_above_threshold;
    const perc = data.percent_above_threshold;
    const thr  = data.reads_threshold;

    const medianReads = data.median_reads;
    const cvReads = data.cv_reads;

    const status = sectionStatus("Screening overview", data.flag_screening_overview);

    div.innerHTML = `
        <h2 class="section-title">Screening overview</h2>
        <p class="section-intro">
            This section summarises how many samples pass the read threshold and how evenly sequencing depth is distributed.
        </p>
        <details open>
            <summary>
                <span class="status-emoji">${status.emoji}</span>
                <span class="status-text">${status.text}</span>
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
                        <div class="screen-overview-stat-label">Read threshold</div>
                        <div class="screen-overview-stat-value">${fmtMillions(thr)}</div>
                        <div class="screen-overview-stat-note">Minimum reads used for screening</div>
                    </div>
                    <div class="screen-overview-stat-item">
                        <div class="screen-overview-stat-label">Median depth / variation</div>
                        <div class="screen-overview-stat-value">
                            ${fmtMillions(medianReads)} / ${fmtFloat(cvReads, 3)}
                        </div>
                        <div class="screen-overview-stat-note">Median reads per sample / CV</div>
                    </div>
                </div>

                <div class="seq-depth-plot-container">
                    <svg id="seq-depth-svg" class="seq-depth-svg" viewBox="0 0 1000 320" preserveAspectRatio="none"></svg>
                </div>
                <p class="small-note">
                    X axis: samples; Y axis: sequencing depth in reads. Bars show depth per sample; the dashed line marks the
                    median depth, and the red line shows the read threshold used for screening.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const svg = div.querySelector("#seq-depth-svg");
    if (!svg || !depthPerSample || !depthPerSample.length) {
        if (svg) {
            svg.outerHTML = '<div class="small-note">Per-sample depth data not available for plotting.</div>';
        }
        return;
    }

    const tooltip = getOrCreateTooltip();
    const svgns = "http://www.w3.org/2000/svg";

    const samples = depthPerSample.map(d => d.sample || "NA");
    const depths = depthPerSample.map(d => Number(d.total_reads) || 0);

    const n = samples.length;
    const margin = {left: 80, right: 20, top: 30, bottom: 90};
    const width = 1000;
    const height = 320;
    const plotW = width - margin.left - margin.right;
    const plotH = height - margin.top - margin.bottom;

    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

    const maxDepth = Math.max(...depths, thr || 0);
    const yMax = maxDepth <= 0 ? 1 : maxDepth * 1.1;

    function yScale(val) {
        return margin.top + plotH - (val / yMax) * plotH;
    }

    const barW = plotW / Math.max(n, 1);

    const yAxis = document.createElementNS(svgns, "line");
    yAxis.setAttribute("x1", margin.left);
    yAxis.setAttribute("y1", margin.top);
    yAxis.setAttribute("x2", margin.left);
    yAxis.setAttribute("y2", margin.top + plotH);
    yAxis.setAttribute("stroke", "#444");
    yAxis.setAttribute("stroke-width", "1");
    svg.appendChild(yAxis);

    const ticks = 5;
    for (let i = 0; i <= ticks; i++) {
        const frac = i / ticks;
        const y = margin.top + plotH - frac * plotH;
        const value = frac * yMax;
        const tick = document.createElementNS(svgns, "line");
        tick.setAttribute("x1", margin.left - 4);
        tick.setAttribute("y1", y);
        tick.setAttribute("x2", margin.left);
        tick.setAttribute("y2", y);
        tick.setAttribute("stroke", "#444");
        tick.setAttribute("stroke-width", "1");
        svg.appendChild(tick);

        const label = document.createElementNS(svgns, "text");
        label.setAttribute("x", margin.left - 6);
        label.setAttribute("y", y + 3);
        label.setAttribute("font-size", "9");
        label.setAttribute("text-anchor", "end");
        label.textContent = fmtMillions(value);
        svg.appendChild(label);
    }

    if (thr && thr > 0) {
        const yThr = yScale(thr);
        const thrLine = document.createElementNS(svgns, "line");
        thrLine.setAttribute("x1", margin.left);
        thrLine.setAttribute("y1", yThr);
        thrLine.setAttribute("x2", margin.left + plotW);
        thrLine.setAttribute("y2", yThr);
        thrLine.setAttribute("stroke", "#c62828");
        thrLine.setAttribute("stroke-width", "1.5");
        thrLine.setAttribute("stroke-dasharray", "4 4");
        svg.appendChild(thrLine);

        const thrLabel = document.createElementNS(svgns, "text");
        thrLabel.setAttribute("x", margin.left + 4);
        thrLabel.setAttribute("y", yThr - 4);
        thrLabel.setAttribute("font-size", "9");
        thrLabel.setAttribute("fill", "#c62828");
        thrLabel.textContent = "Read threshold";
        svg.appendChild(thrLabel);
    }

    const sortedIndices = depths.map((v, i) => i);
    sortedIndices.sort((a, b) => depths[a] - depths[b]);
    const mid = Math.floor(sortedIndices.length / 2);
    const medianDepth = sortedIndices.length % 2 === 1
        ? depths[sortedIndices[mid]]
        : (depths[sortedIndices[mid - 1]] + depths[sortedIndices[mid]]) / 2;

    const yMed = yScale(medianDepth);
    const medLine = document.createElementNS(svgns, "line");
    medLine.setAttribute("x1", margin.left);
    medLine.setAttribute("y1", yMed);
    medLine.setAttribute("x2", margin.left + plotW);
    medLine.setAttribute("y2", yMed);
    medLine.setAttribute("stroke", "#1565c0");
    medLine.setAttribute("stroke-width", "1.5");
    medLine.setAttribute("stroke-dasharray", "4 4");
    svg.appendChild(medLine);

    const medLabel = document.createElementNS(svgns, "text");
    medLabel.setAttribute("x", margin.left + 4);
    medLabel.setAttribute("y", yMed - 4);
    medLabel.setAttribute("font-size", "9");
    medLabel.setAttribute("fill", "#1565c0");
    medLabel.textContent = "Median depth";
    svg.appendChild(medLabel);

    depths.forEach((depth, i) => {
        const x = margin.left + i * barW;
        const y = yScale(depth);
        const barHeight = margin.top + plotH - y;

        const bar = document.createElementNS(svgns, "rect");
        bar.setAttribute("x", x + 1);
        bar.setAttribute("y", y);
        bar.setAttribute("width", Math.max(1, barW - 2));
        bar.setAttribute("height", barHeight);
        bar.setAttribute("fill", "#64b5f6");
        bar.style.cursor = "pointer";

        bar.addEventListener("mouseenter", (evt) => {
            tooltip.style.display = "block";
            tooltip.textContent = `${samples[i]}\nReads: ${fmtInt(depth)}`;
            tooltip.style.left = evt.clientX + "px";
            tooltip.style.top = evt.clientY + "px";
        });
        bar.addEventListener("mousemove", (evt) => {
            tooltip.style.left = evt.clientX + "px";
            tooltip.style.top = evt.clientY + "px";
        });
        bar.addEventListener("mouseleave", () => {
            tooltip.style.display = "none";
        });

        svg.appendChild(bar);

        const showAll = n <= 40;
        const show = showAll || (i % 5 === 0);
        if (show) {
            const lab = document.createElementNS(svgns, "text");
            lab.setAttribute("x", x + barW / 2);
            lab.setAttribute("y", margin.top + plotH + 14);
            lab.setAttribute("font-size", "9");
            lab.setAttribute("text-anchor", "end");
            lab.setAttribute(
                "transform",
                `rotate(-60 ${x + barW / 2} ${margin.top + plotH + 14})`
            );
            lab.textContent = samples[i];
            svg.appendChild(lab);
        }
    });

    const yLabel = document.createElementNS(svgns, "text");
    yLabel.setAttribute("x", 16);
    yLabel.setAttribute("y", margin.top + plotH / 2);
    yLabel.setAttribute("font-size", "11");
    yLabel.setAttribute("text-anchor", "middle");
    yLabel.setAttribute("transform", `rotate(-90 16 ${margin.top + plotH / 2})`);
    yLabel.textContent = "Total reads (per sample)";
    svg.appendChild(yLabel);
}

/* ---------- Section 2: Sequencing quality (fastp) ---------- */
function addLowQualitySection(parent, data, depthPerSample) {
    if (!data) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(data.flag_low_quality);

    const msg = data.message_low_quality || "";

    const nFastp = data.n_samples;
    const meanFrac = data.mean_fraction_removed;
    const medianFrac = data.median_fraction_removed;
    const percRemovedOverall = data.percent_removed_reads_overall;

    const status = sectionStatus("Sequencing quality", data.flag_low_quality);

    div.innerHTML = `
        <h2 class="section-title">Sequencing quality</h2>
        <p class="section-intro">
            This section summarises how many reads were removed by quality filtering (fastp) and how this varies across samples.
        </p>
        <details>
            <summary>
                <span class="status-emoji">${status.emoji}</span>
                <span class="status-text">${status.text}</span>
            </summary>
            <div class="content">
                <p class="summary-message">${msg}</p>
                <div class="quality-stats">
                    <div class="quality-stat-item">
                        <div class="quality-stat-label">Samples with fastp stats</div>
                        <div class="quality-stat-value">${fmtInt(nFastp)}</div>
                        <div class="quality-stat-note">Samples with QC information</div>
                    </div>
                    <div class="quality-stat-item">
                        <div class="quality-stat-label">Mean removed fraction</div>
                        <div class="quality-stat-value">${fmtFloat(meanFrac * 100, 1)}%</div>
                        <div class="quality-stat-note">Average fraction of reads removed by fastp</div>
                    </div>
                    <div class="quality-stat-item">
                        <div class="quality-stat-label">Median removed fraction</div>
                        <div class="quality-stat-value">${fmtFloat(medianFrac * 100, 1)}%</div>
                        <div class="quality-stat-note">Median fraction of reads removed by fastp</div>
                    </div>
                    <div class="quality-stat-item">
                        <div class="quality-stat-label">Removed reads (overall)</div>
                        <div class="quality-stat-value">${fmtFloat(percRemovedOverall, 1)}%</div>
                        <div class="quality-stat-note">Reads discarded across the entire dataset</div>
                    </div>
                </div>

                <div class="quality-plot-container">
                    <svg id="quality-svg" class="quality-svg" viewBox="0 0 1000 320" preserveAspectRatio="none"></svg>
                </div>
                <p class="small-note">
                    X axis: samples; Y axis: fraction of reads removed by fastp. Dashed lines at 5% and 20% highlight thresholds where
                    quality filtering starts to become moderate or severe.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const svg = div.querySelector("#quality-svg");
    if (!svg || !depthPerSample || !depthPerSample.length) {
        if (svg) {
            svg.outerHTML = '<div class="small-note">Per-sample quality data not available for plotting.</div>';
        }
        return;
    }

    const tooltip = getOrCreateTooltip();
    const svgns = "http://www.w3.org/2000/svg";

    const sampleToRemoved = {};
    (DISTILL_DATA.summary.low_quality_reads.per_sample || []).forEach(d => {
        if (d.sample != null && d.fraction_removed != null) {
            sampleToRemoved[d.sample] = d.fraction_removed;
        }
    });

    const samples = depthPerSample.map(d => d.sample || "NA");
    const removed = samples.map(s => {
        const val = sampleToRemoved[s];
        return val != null ? Number(val) : 0;
    });

    const n = samples.length;
    const margin = {left: 80, right: 20, top: 30, bottom: 90};
    const width = 1000;
    const height = 320;
    const plotW = width - margin.left - margin.right;
    const plotH = height - margin.top - margin.bottom;

    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

    const maxRemoved = Math.max(...removed, 0.25);
    const yMax = maxRemoved <= 0 ? 0.01 : maxRemoved * 1.1;

    function yScale(val) {
        return margin.top + plotH - (val / yMax) * plotH;
    }

    const barW = plotW / Math.max(n, 1);

    const yAxis = document.createElementNS(svgns, "line");
    yAxis.setAttribute("x1", margin.left);
    yAxis.setAttribute("y1", margin.top);
    yAxis.setAttribute("x2", margin.left);
    yAxis.setAttribute("y2", margin.top + plotH);
    yAxis.setAttribute("stroke", "#444");
    yAxis.setAttribute("stroke-width", "1");
    svg.appendChild(yAxis);

    const ticks = 5;
    for (let i = 0; i <= ticks; i++) {
        const frac = i / ticks;
        const y = margin.top + plotH - frac * plotH;
        const value = frac * yMax;
        const tick = document.createElementNS(svgns, "line");
        tick.setAttribute("x1", margin.left - 4);
        tick.setAttribute("y1", y);
        tick.setAttribute("x2", margin.left);
        tick.setAttribute("y2", y);
        tick.setAttribute("stroke", "#444");
        tick.setAttribute("stroke-width", "1");
        svg.appendChild(tick);

        const label = document.createElementNS(svgns, "text");
        label.setAttribute("x", margin.left - 6);
        label.setAttribute("y", y + 3);
        label.setAttribute("font-size", "9");
        label.setAttribute("text-anchor", "end");
        label.textContent = (value * 100).toFixed(1) + "%";
        svg.appendChild(label);
    }

    const thresholds = [
        {value: 0.05, color: "#f9a825", label: "5% threshold"},
        {value: 0.20, color: "#c62828", label: "20% threshold"}
    ];

    thresholds.forEach(th => {
        const yThr = yScale(th.value);
        const line = document.createElementNS(svgns, "line");
        line.setAttribute("x1", margin.left);
        line.setAttribute("y1", yThr);
        line.setAttribute("x2", margin.left + plotW);
        line.setAttribute("y2", yThr);
        line.setAttribute("stroke", th.color);
        line.setAttribute("stroke-width", "1.5");
        line.setAttribute("stroke-dasharray", "4 4");
        svg.appendChild(line);

        const lab = document.createElementNS(svgns, "text");
        lab.setAttribute("x", margin.left + 4);
        lab.setAttribute("y", yThr - 4);
        lab.setAttribute("font-size", "9");
        lab.setAttribute("fill", th.color);
        lab.textContent = th.label;
        svg.appendChild(lab);
    });

    removed.forEach((frac, i) => {
        const x = margin.left + i * barW;
        const y = yScale(frac);
        const barHeight = margin.top + plotH - y;

        const bar = document.createElementNS(svgns, "rect");
        bar.setAttribute("x", x + 1);
        bar.setAttribute("y", y);
        bar.setAttribute("width", Math.max(1, barW - 2));
        bar.setAttribute("height", barHeight);
        bar.setAttribute("fill", "#90caf9");
        bar.style.cursor = "pointer";

        bar.addEventListener("mouseenter", (evt) => {
            tooltip.style.display = "block";
            tooltip.textContent = `${samples[i]}\nRemoved: ${(frac * 100).toFixed(1)}%`;
            tooltip.style.left = evt.clientX + "px";
            tooltip.style.top = evt.clientY + "px";
        });
        bar.addEventListener("mousemove", (evt) => {
            tooltip.style.left = evt.clientX + "px";
            tooltip.style.top = evt.clientY + "px";
        });
        bar.addEventListener("mouseleave", () => {
            tooltip.style.display = "none";
        });

        svg.appendChild(bar);

        const showAll = n <= 40;
        const show = showAll || (i % 5 === 0);
        if (show) {
            const lab = document.createElementNS(svgns, "text");
            lab.setAttribute("x", x + barW / 2);
            lab.setAttribute("y", margin.top + plotH + 14);
            lab.setAttribute("font-size", "9");
            lab.setAttribute("text-anchor", "end");
            lab.setAttribute(
                "transform",
                `rotate(-60 ${x + barW / 2} ${margin.top + plotH + 14})`
            );
            lab.textContent = samples[i];
            svg.appendChild(lab);
        }
    });

    const yLabel = document.createElementNS(svgns, "text");
    yLabel.setAttribute("x", 16);
    yLabel.setAttribute("y", margin.top + plotH / 2);
    yLabel.setAttribute("font-size", "11");
    yLabel.setAttribute("text-anchor", "middle");
    yLabel.setAttribute("transform", `rotate(-90 16 ${margin.top + plotH / 2})`);
    yLabel.textContent = "Fraction of reads removed";
    svg.appendChild(yLabel);
}

/* ---------- Section 3: Prokaryotic fraction + depth components ---------- */
function addProkFractionSection(parent, data, depthPerSample) {
    if (!data) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(data.flag_prokaryotic_fraction);

    const msg = data.message_prokaryotic_fraction || "";

    const meanFrac = data.mean_prokaryotic_fraction;
    const medianFrac = data.median_prokaryotic_fraction;
    const cvFrac = data.cv_prokaryotic_fraction;
    const nWarnings = data.n_warnings;

    const status = sectionStatus("Prokaryotic fraction", data.flag_prokaryotic_fraction);

    div.innerHTML = `
        <h2 class="section-title">Prokaryotic fraction</h2>
        <p class="section-intro">
            This section summarises the fraction of reads assigned to prokaryotic genomes (SingleM) and how host/other DNA
            affects the effective sequencing depth.
        </p>
        <details>
            <summary>
                <span class="status-emoji">${status.emoji}</span>
                <span class="status-text">${status.text}</span>
            </summary>
            <div class="content">
                <p class="summary-message">${msg}</p>
                <div class="prok-fraction-stats">
                    <div class="prok-fraction-stat-item">
                        <div class="prok-fraction-stat-label">Mean prokaryotic fraction</div>
                        <div class="prok-fraction-stat-value">${fmtFloat(meanFrac, 1)}%</div>
                        <div class="prok-fraction-stat-note">Average fraction of reads assigned to prokaryotes</div>
                    </div>
                    <div class="prok-fraction-stat-item">
                        <div class="prok-fraction-stat-label">Median prokaryotic fraction</div>
                        <div class="prok-fraction-stat-value">${fmtFloat(medianFrac, 1)}%</div>
                        <div class="prok-fraction-stat-note">Median fraction of reads assigned to prokaryotes</div>
                    </div>
                    <div class="prok-fraction-stat-item">
                        <div class="prok-fraction-stat-label">Variation (CV)</div>
                        <div class="prok-fraction-stat-value">${fmtFloat(cvFrac, 3)}</div>
                        <div class="prok-fraction-stat-note">Coefficient of variation across samples</div>
                    </div>
                    <div class="prok-fraction-stat-item">
                        <div class="prok-fraction-stat-label">Samples with warnings</div>
                        <div class="prok-fraction-stat-value">${fmtInt(nWarnings)}</div>
                        <div class="prok-fraction-stat-note">Samples with SingleM estimation warnings</div>
                    </div>
                </div>

                <div class="prok-fraction-plot-container">
                    <svg id="prok-fraction-svg" class="prok-fraction-svg" viewBox="0 0 1000 320" preserveAspectRatio="none"></svg>
                </div>
                <p class="small-note">
                    X axis: samples; Y axis: prokaryotic read fraction. Bars are coloured by fraction thresholds (>90% green,
                    50–90% yellow, &lt;50% red). The blue dashed line marks the median prokaryotic fraction, and coloured dashed
                    lines mark the classification thresholds.
                </p>

                <div class="seq-depth-plot-container">
                    <svg id="dna-depth-svg" class="seq-depth-svg" viewBox="0 0 1000 320" preserveAspectRatio="none"></svg>
                </div>
                <p class="small-note">
                    X axis: samples; Y axis: total reads. Stacked bars show quality-filtered prokaryotic reads, quality-filtered
                    non-prokaryotic reads, and reads removed by quality filtering.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const svgFrac = div.querySelector("#prok-fraction-svg");
    const svgDepth = div.querySelector("#dna-depth-svg");

    if (!svgFrac || !depthPerSample || !depthPerSample.length) {
        if (svgFrac) {
            svgFrac.outerHTML = '<div class="small-note">Per-sample prokaryotic fraction data not available.</div>';
        }
    } else {
        drawProkFractionPlot(svgFrac, depthPerSample);
    }

    if (!svgDepth || !depthPerSample || !depthPerSample.length) {
        if (svgDepth) {
            svgDepth.outerHTML = '<div class="small-note">Per-sample depth components not available.</div>';
        }
    } else {
        drawDepthComponentsPlot(svgDepth, depthPerSample);
    }
}

function drawProkFractionPlot(svg, depthPerSample) {
    const tooltip = getOrCreateTooltip();
    const svgns = "http://www.w3.org/2000/svg";

    const samples = depthPerSample.map(d => d.sample || "NA");
    const fracProk = depthPerSample.map(d => {
        const v = d.prokaryotic_fraction;
        return (v == null || isNaN(v)) ? 0 : Number(v);
    });

    const n = samples.length;
    const margin = {left: 80, right: 20, top: 30, bottom: 90};
    const width = 1000;
    const height = 320;
    const plotW = width - margin.left - margin.right;
    const plotH = height - margin.top - margin.bottom;

    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

    const yMax = 100;

    function yScale(val) {
        return margin.top + plotH - (val / yMax) * plotH;
    }

    const barW = plotW / Math.max(n, 1);

    const yAxis = document.createElementNS(svgns, "line");
    yAxis.setAttribute("x1", margin.left);
    yAxis.setAttribute("y1", margin.top);
    yAxis.setAttribute("x2", margin.left);
    yAxis.setAttribute("y2", margin.top + plotH);
    yAxis.setAttribute("stroke", "#444");
    yAxis.setAttribute("stroke-width", "1");
    svg.appendChild(yAxis);

    const ticks = 5;
    for (let i = 0; i <= ticks; i++) {
        const frac = i / ticks;
        const y = margin.top + plotH - frac * plotH;
        const value = frac * yMax;
        const tick = document.createElementNS(svgns, "line");
        tick.setAttribute("x1", margin.left - 4);
        tick.setAttribute("y1", y);
        tick.setAttribute("x2", margin.left);
        tick.setAttribute("y2", y);
        tick.setAttribute("stroke", "#444");
        tick.setAttribute("stroke-width", "1");
        svg.appendChild(tick);

        const label = document.createElementNS(svgns, "text");
        label.setAttribute("x", margin.left - 6);
        label.setAttribute("y", y + 3);
        label.setAttribute("font-size", "9");
        label.setAttribute("text-anchor", "end");
        label.textContent = value.toFixed(0) + "%";
        svg.appendChild(label);
    }

    const thresholds = [
        {value: 50, color: "#f9a825", label: "50% threshold"},
        {value: 90, color: "#2e7d32", label: "90% threshold"}
    ];

    thresholds.forEach(th => {
        const yThr = yScale(th.value);
        const line = document.createElementNS(svgns, "line");
        line.setAttribute("x1", margin.left);
        line.setAttribute("y1", yThr);
        line.setAttribute("x2", margin.left + plotW);
        line.setAttribute("y2", yThr);
        line.setAttribute("stroke", th.color);
        line.setAttribute("stroke-width", "1.5");
        line.setAttribute("stroke-dasharray", "4 4");
        svg.appendChild(line);

        const lab = document.createElementNS(svgns, "text");
        lab.setAttribute("x", margin.left + 4);
        lab.setAttribute("y", yThr - 4);
        lab.setAttribute("font-size", "9");
        lab.setAttribute("fill", th.color);
        lab.textContent = th.label;
        svg.appendChild(lab);
    });

    const sorted = fracProk
        .map((v, i) => ({v, i}))
        .filter(d => d.v != null && !isNaN(d.v));
    if (sorted.length) {
        sorted.sort((a, b) => a.v - b.v);
        const mid = Math.floor(sorted.length / 2);
        const medianVal = sorted.length % 2 === 1
            ? sorted[mid].v
            : (sorted[mid - 1].v + sorted[mid].v) / 2;

        const yMed = yScale(medianVal);
        const medLine = document.createElementNS(svgns, "line");
        medLine.setAttribute("x1", margin.left);
        medLine.setAttribute("y1", yMed);
        medLine.setAttribute("x2", margin.left + plotW);
        medLine.setAttribute("y2", yMed);
        medLine.setAttribute("stroke", "#1565c0");
        medLine.setAttribute("stroke-width", "1.5");
        medLine.setAttribute("stroke-dasharray", "4 4");
        svg.appendChild(medLine);

        const medLabel = document.createElementNS(svgns, "text");
        medLabel.setAttribute("x", margin.left + 4);
        medLabel.setAttribute("y", yMed - 4);
        medLabel.setAttribute("font-size", "9");
        medLabel.setAttribute("fill", "#1565c0");
        medLabel.textContent = "Median prokaryotic fraction";
        svg.appendChild(medLabel);
    }

    fracProk.forEach((frac, i) => {
        const x = margin.left + i * barW;
        const y = yScale(frac);
        const barHeight = margin.top + plotH - y;

        let color = "#c62828";
        if (frac > 90) {
            color = "#2e7d32";
        } else if (frac > 50) {
            color = "#f9a825";
        }

        const bar = document.createElementNS(svgns, "rect");
        bar.setAttribute("x", x + 1);
        bar.setAttribute("y", y);
        bar.setAttribute("width", Math.max(1, barW - 2));
        bar.setAttribute("height", barHeight);
        bar.setAttribute("fill", color);
        bar.style.cursor = "pointer";

        bar.addEventListener("mouseenter", (evt) => {
            tooltip.style.display = "block";
            tooltip.textContent = `${samples[i]}\nProkaryotic fraction: ${frac.toFixed(1)}%`;
            tooltip.style.left = evt.clientX + "px";
            tooltip.style.top = evt.clientY + "px";
        });
        bar.addEventListener("mousemove", (evt) => {
            tooltip.style.left = evt.clientX + "px";
            tooltip.style.top = evt.clientY + "px";
        });
        bar.addEventListener("mouseleave", () => {
            tooltip.style.display = "none";
        });

        svg.appendChild(bar);

        const showAll = n <= 40;
        const show = showAll || (i % 5 === 0);
        if (show) {
            const lab = document.createElementNS(svgns, "text");
            lab.setAttribute("x", x + barW / 2);
            lab.setAttribute("y", margin.top + plotH + 14);
            lab.setAttribute("font-size", "9");
            lab.setAttribute("text-anchor", "end");
            lab.setAttribute(
                "transform",
                `rotate(-60 ${x + barW / 2} ${margin.top + plotH + 14})`
            );
            lab.textContent = samples[i];
            svg.appendChild(lab);
        }
    });

    const yLabel = document.createElementNS(svgns, "text");
    yLabel.setAttribute("x", 16);
    yLabel.setAttribute("y", margin.top + plotH / 2);
    yLabel.setAttribute("font-size", "11");
    yLabel.setAttribute("text-anchor", "middle");
    yLabel.setAttribute("transform", `rotate(-90 16 ${margin.top + plotH / 2})`);
    yLabel.textContent = "Prokaryotic read fraction (%)";
    svg.appendChild(yLabel);
}

function drawDepthComponentsPlot(svg, depthPerSample) {
    const tooltip = getOrCreateTooltip();
    const svgns = "http://www.w3.org/2000/svg";

    const samples = depthPerSample.map(d => d.sample || "NA");
    const total = depthPerSample.map(d => Number(d.total_reads) || 0);
    const prok = depthPerSample.map(d => Number(d.prokaryotic_qc_reads) || 0);
    const nonProk = depthPerSample.map(d => Number(d.non_prokaryotic_qc_reads) || 0);
    const removed = depthPerSample.map(d => Number(d.removed_reads) || 0);

    const n = samples.length;
    const margin = {left: 80, right: 20, top: 30, bottom: 90};
    const width = 1000;
    const height = 320;
    const plotW = width - margin.left - margin.right;
    const plotH = height - margin.top - margin.bottom;

    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

    const maxTotal = Math.max(...total, 1);
    const yMax = maxTotal * 1.1;

    function yScale(val) {
        return margin.top + plotH - (val / yMax) * plotH;
    }

    const barW = plotW / Math.max(n, 1);

    const yAxis = document.createElementNS(svgns, "line");
    yAxis.setAttribute("x1", margin.left);
    yAxis.setAttribute("y1", margin.top);
    yAxis.setAttribute("x2", margin.left);
    yAxis.setAttribute("y2", margin.top + plotH);
    yAxis.setAttribute("stroke", "#444");
    yAxis.setAttribute("stroke-width", "1");
    svg.appendChild(yAxis);

    const ticks = 5;
    for (let i = 0; i <= ticks; i++) {
        const frac = i / ticks;
        const y = margin.top + plotH - frac * plotH;
        const value = frac * yMax;
        const tick = document.createElementNS(svgns, "line");
        tick.setAttribute("x1", margin.left - 4);
        tick.setAttribute("y1", y);
        tick.setAttribute("x2", margin.left);
        tick.setAttribute("y2", y);
        tick.setAttribute("stroke", "#444");
        tick.setAttribute("stroke-width", "1");
        svg.appendChild(tick);

        const label = document.createElementNS(svgns, "text");
        label.setAttribute("x", margin.left - 6);
        label.setAttribute("y", y + 3);
        label.setAttribute("font-size", "9");
        label.setAttribute("text-anchor", "end");
        label.textContent = fmtMillions(value);
        svg.appendChild(label);
    }

    for (let i = 0; i < n; i++) {
        const x = margin.left + i * barW;
        const yBase = margin.top + plotH;

        const remVal = removed[i];
        const yRemTop = yScale(remVal);
        const remHeight = yBase - yRemTop;
        const remRect = document.createElementNS(svgns, "rect");
        remRect.setAttribute("x", x + 1);
        remRect.setAttribute("y", yRemTop);
        remRect.setAttribute("width", Math.max(1, barW - 2));
        remRect.setAttribute("height", remHeight);
        remRect.setAttribute("fill", "#ef9a9a");
        remRect.style.cursor = "pointer";

        remRect.addEventListener("mouseenter", (evt) => {
            tooltip.style.display = "block";
            tooltip.textContent = `${samples[i]}\nRemoved reads: ${fmtInt(remVal)}`;
            tooltip.style.left = evt.clientX + "px";
            tooltip.style.top = evt.clientY + "px";
        });
        remRect.addEventListener("mousemove", (evt) => {
            tooltip.style.left = evt.clientX + "px";
            tooltip.style.top = evt.clientY + "px";
        });
        remRect.addEventListener("mouseleave", () => {
            tooltip.style.display = "none";
        });
        svg.appendChild(remRect);

        const nonVal = nonProk[i];
        const yNonTop = yScale(remVal + nonVal);
        const nonHeight = yRemTop - yNonTop;
        const nonRect = document.createElementNS(svgns, "rect");
        nonRect.setAttribute("x", x + 1);
        nonRect.setAttribute("y", yNonTop);
        nonRect.setAttribute("width", Math.max(1, barW - 2));
        nonRect.setAttribute("height", nonHeight);
        nonRect.setAttribute("fill", "#b0bec5");
        nonRect.style.cursor = "pointer";

        nonRect.addEventListener("mouseenter", (evt) => {
            tooltip.style.display = "block";
            tooltip.textContent = `${samples[i]}\nNon-prokaryotic QC-passing: ${fmtInt(nonVal)}`;
            tooltip.style.left = evt.clientX + "px";
            tooltip.style.top = evt.clientY + "px";
        });
        nonRect.addEventListener("mousemove", (evt) => {
            tooltip.style.left = evt.clientX + "px";
            tooltip.style.top = evt.clientY + "px";
        });
        nonRect.addEventListener("mouseleave", () => {
            tooltip.style.display = "none";
        });
        svg.appendChild(nonRect);

        const prokVal = prok[i];
        const yProkTop = yScale(remVal + nonVal + prokVal);
        const prokHeight = yNonTop - yProkTop;
        const prokRect = document.createElementNS(svgns, "rect");
        prokRect.setAttribute("x", x + 1);
        prokRect.setAttribute("y", yProkTop);
        prokRect.setAttribute("width", Math.max(1, barW - 2));
        prokRect.setAttribute("height", prokHeight);
        prokRect.setAttribute("fill", "#66bb6a");
        prokRect.style.cursor = "pointer";

        prokRect.addEventListener("mouseenter", (evt) => {
            tooltip.style.display = "block";
            tooltip.textContent = `${samples[i]}\nProkaryotic QC-passing: ${fmtInt(prokVal)}`;
            tooltip.style.left = evt.clientX + "px";
            tooltip.style.top = evt.clientY + "px";
        });
        prokRect.addEventListener("mousemove", (evt) => {
            tooltip.style.left = evt.clientX + "px";
            tooltip.style.top = evt.clientY + "px";
        });
        prokRect.addEventListener("mouseleave", () => {
            tooltip.style.display = "none";
        });
        svg.appendChild(prokRect);

        const showAll = n <= 40;
        const show = showAll || (i % 5 === 0);
        if (show) {
            const lab = document.createElementNS(svgns, "text");
            lab.setAttribute("x", x + barW / 2);
            lab.setAttribute("y", margin.top + plotH + 14);
            lab.setAttribute("font-size", "9");
            lab.setAttribute("text-anchor", "end");
            lab.setAttribute(
                "transform",
                `rotate(-60 ${x + barW / 2} ${margin.top + plotH + 14})`
            );
            lab.textContent = samples[i];
            svg.appendChild(lab);
        }
    }

    const yLabel = document.createElementNS(svgns, "text");
    yLabel.setAttribute("x", 16);
    yLabel.setAttribute("y", margin.top + plotH / 2);
    yLabel.setAttribute("font-size", "11");
    yLabel.setAttribute("text-anchor", "middle");
    yLabel.setAttribute("transform", `rotate(-90 16 ${margin.top + plotH / 2})`);
    yLabel.textContent = "Reads (per sample)";
    svg.appendChild(yLabel);
}

/* ---------- Section 4: Overall metagenomic coverage (Nonpareil reads) ---------- */
function addRedundancyReadsSection(parent, data, depthPerSample) {
    if (!data) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(data.flag_redundancy);

    const msg = data.message_redundancy || "";

    const meanK = data.mean_kappa_total;
    const medianK = data.median_kappa_total;
    const cvK = data.cv_kappa_total;
    const nKappa = data.n_samples_kappa;

    const nWithLR = data.n_samples_with_lr;
    const nExceeds = data.n_samples_lr_exceeds_depth;
    const lrTarget = data.lr_target_used;

    const status = sectionStatus("Overall metagenomic coverage", data.flag_redundancy);

    div.innerHTML = `
        <h2 class="section-title">Overall metagenomic coverage</h2>
        <p class="section-intro">
            This section summarises Nonpareil-based redundancy estimates from reads and compares required vs. observed sequencing
            effort to reach a given diversity target.
        </p>
        <details>
            <summary>
                <span class="status-emoji">${status.emoji}</span>
                <span class="status-text">${status.text}</span>
            </summary>
            <div class="content">
                <p class="summary-message">${msg}</p>

                <div class="coverage-stats">
                    <div class="coverage-stat-item">
                        <div class="coverage-stat-label">Samples with Nonpareil (reads)</div>
                        <div class="coverage-stat-value">${fmtInt(nKappa)}</div>
                        <div class="coverage-stat-note">Samples with redundancy estimates</div>
                    </div>
                    <div class="coverage-stat-item">
                        <div class="coverage-stat-label">Mean redundancy (kappa)</div>
                        <div class="coverage-stat-value">${fmtFloat(meanK, 3)}</div>
                        <div class="coverage-stat-note">Average Nonpareil kappa across samples</div>
                    </div>
                    <div class="coverage-stat-item">
                        <div class="coverage-stat-label">LR target coverage</div>
                        <div class="coverage-stat-value">${fmtInt(nWithLR - nExceeds)} / ${fmtInt(nWithLR)}</div>
                        <div class="coverage-stat-note">Samples meeting the LR target</div>
                    </div>
                </div>

                <div class="coverage-plot-container">
                    <svg id="coverage-reads-svg" class="coverage-svg" viewBox="0 0 1000 360" preserveAspectRatio="none"></svg>
                </div>
                <p class="small-note">
                    X axis: samples; Y axis: fold change relative to the Nonpareil LR target depth (1X). Bars above the mid-line
                    indicate oversampling; bars below indicate undersampling. The black dashed line marks the target; orange and red
                    dashed lines show undersampling thresholds.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const svg = div.querySelector("#coverage-reads-svg");
    if (!svg) return;

    drawCoverageFoldPlot(svg, "reads");
}

/* ---------- Section 5: Prokaryotic coverage (Nonpareil markers) ---------- */
function addRedundancyMarkersSection(parent, data, redBiplotPerSample) {
    if (!data) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(data.flag_redundancy_markers);

    const msg = data.message_redundancy_markers || "";

    const meanK = data.mean_kappa_total;
    const medianK = data.median_kappa_total;
    const cvK = data.cv_kappa_total;
    const nKappa = data.n_samples_kappa;

    const nWithLR = data.n_samples_with_lr;
    const nExceeds = data.n_samples_lr_exceeds_depth;
    const lrTarget = data.lr_target_used;

    const status = sectionStatus("Prokaryotic coverage", data.flag_redundancy_markers);

    div.innerHTML = `
        <h2 class="section-title">Prokaryotic coverage</h2>
        <p class="section-intro">
            This section summarises Nonpareil-based redundancy estimates from marker genes, capturing coverage of the prokaryotic
            fraction of the community.
        </p>
        <details>
            <summary>
                <span class="status-emoji">${status.emoji}</span>
                <span class="status-text">${status.text}</span>
            </summary>
            <div class="content">
                <p class="summary-message">${msg}</p>

                <div class="coverage-stats">
                    <div class="coverage-stat-item">
                        <div class="coverage-stat-label">Samples with Nonpareil (markers)</div>
                        <div class="coverage-stat-value">${fmtInt(nKappa)}</div>
                        <div class="coverage-stat-note">Samples with redundancy estimates</div>
                    </div>
                    <div class="coverage-stat-item">
                        <div class="coverage-stat-label">Mean redundancy (kappa)</div>
                        <div class="coverage-stat-value">${fmtFloat(meanK, 3)}</div>
                        <div class="coverage-stat-note">Average Nonpareil kappa across samples</div>
                    </div>
                    <div class="coverage-stat-item">
                        <div class="coverage-stat-label">LR target coverage</div>
                        <div class="coverage-stat-value">${fmtInt(nWithLR - nExceeds)} / ${fmtInt(nWithLR)}</div>
                        <div class="coverage-stat-note">Samples meeting the LR target</div>
                    </div>
                </div>

                <div class="coverage-plot-container">
                    <svg id="coverage-markers-svg" class="coverage-svg" viewBox="0 0 1000 360" preserveAspectRatio="none"></svg>
                </div>
                <p class="small-note">
                    X axis: samples; Y axis: fold change relative to the Nonpareil LR target depth (1X). Bars above the mid-line
                    indicate oversampling; bars below indicate undersampling. The black dashed line marks the target; orange and red
                    dashed lines show undersampling thresholds.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const svg = div.querySelector("#coverage-markers-svg");
    if (!svg) return;

    drawCoverageFoldPlot(svg, "markers");
}

/* Coverage fold-change plot (shared between reads/markers) */
function drawCoverageFoldPlot(svg, kind) {
    const tooltip = getOrCreateTooltip();
    const svgns = "http://www.w3.org/2000/svg";

    const perSample = FIGURES_DATA &&
                      FIGURES_DATA.figures &&
                      FIGURES_DATA.figures.redundancy_fold_change &&
                      FIGURES_DATA.figures.redundancy_fold_change.per_sample
        ? FIGURES_DATA.figures.redundancy_fold_change.per_sample
        : [];

    if (!perSample.length) {
        svg.outerHTML = '<div class="small-note">Per-sample coverage fold-change data not available.</div>';
        return;
    }

    const samples = [];
    const folds = [];

    perSample.forEach(d => {
        const s = d.sample || "NA";
        let v = null;
        if (kind === "reads") {
            v = d.reads_fold_change;
        } else {
            v = d.markers_fold_change;
        }
        if (v == null || isNaN(v)) return;
        samples.push(s);
        folds.push(Number(v));
    });

    if (!samples.length) {
        svg.outerHTML = '<div class="small-note">No usable fold-change values available for this dataset.</div>';
        return;
    }

    const n = samples.length;
    const margin = {left: 80, right: 20, top: 40, bottom: 90};
    const width = 1000;
    const height = 360;
    const plotW = width - margin.left - margin.right;
    const plotH = height - margin.top - margin.bottom;

    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

    const maxAbove = Math.max(...folds.map(v => v > 1 ? v : 1));
    const maxFactor = Math.max(2, Math.ceil(maxAbove));

    const minBelow = Math.min(...folds.map(v => v < 1 ? v : 1));
    const minFactor = Math.min(0.1, minBelow);
    const maxBelowAbs = 1 / Math.min(1, minFactor);
    const maxBelowDisplay = Math.max(3, Math.ceil(maxBelowAbs));

    const yTop = maxFactor;
    const yBottom = -maxBelowDisplay;

    function yToDisplay(v) {
        if (v >= 1) {
            return v;
        } else {
            return -(1 / v);
        }
    }

    const displayValues = folds.map(yToDisplay);
    const yMin = yBottom;
    const yMax = yTop;

    function yScaleDisp(dv) {
        const frac = (dv - yMin) / (yMax - yMin);
        return margin.top + plotH - frac * plotH;
    }

    const barW = plotW / Math.max(n, 1);

    const midY = yScaleDisp(0);
    const x0 = margin.left;
    const x1 = margin.left + plotW;
    const midLine = document.createElementNS(svgns, "line");
    midLine.setAttribute("x1", x0);
    midLine.setAttribute("y1", midY);
    midLine.setAttribute("x2", x1);
    midLine.setAttribute("y2", midY);
    midLine.setAttribute("stroke", "#000000");
    midLine.setAttribute("stroke-width", "1.2");
    midLine.setAttribute("stroke-dasharray", "4 4");
    svg.appendChild(midLine);

    const yTargets = [1, 2, 3, -2, -3];
    yTargets.forEach(val => {
        if (val === 0) return;
        const y = yScaleDisp(val);
        const grid = document.createElementNS(svgns, "line");
        grid.setAttribute("x1", x0);
        grid.setAttribute("y1", y);
        grid.setAttribute("x2", x1);
        grid.setAttribute("y2", y);
        grid.setAttribute("stroke", "#e0e0e0");
        grid.setAttribute("stroke-width", "1");
        svg.appendChild(grid);
    });

    for (let factor = 1; factor <= maxFactor; factor++) {
        const dv = factor;
        const y = yScaleDisp(dv);
        const label = document.createElementNS(svgns, "text");
        label.setAttribute("x", margin.left - 6);
        label.setAttribute("y", y + 3);
        label.setAttribute("font-size", "9");
        label.setAttribute("text-anchor", "end");
        label.textContent = factor === 1 ? "1X" : factor + "X";
        svg.appendChild(label);
    }

    for (let factor = 2; factor <= maxBelowDisplay; factor++) {
        const dv = -factor;
        const y = yScaleDisp(dv);
        const label = document.createElementNS(svgns, "text");
        label.setAttribute("x", margin.left - 6);
        label.setAttribute("y", y + 3);
        label.setAttribute("font-size", "9");
        label.setAttribute("text-anchor", "end");
        label.textContent = `-${factor}X`;
        svg.appendChild(label);
    }

    const undersamplingThresholds = [-2, -3];
    undersamplingThresholds.forEach(th => {
        const y = yScaleDisp(th);
        const line = document.createElementNS(svgns, "line");
        line.setAttribute("x1", x0);
        line.setAttribute("y1", y);
        line.setAttribute("x2", x1);
        line.setAttribute("y2", y);
        line.setAttribute("stroke", th === -2 ? "#fb8c00" : "#c62828");
        line.setAttribute("stroke-width", "1.5");
        line.setAttribute("stroke-dasharray", "4 4");
        svg.appendChild(line);
    });

    const xAxis = document.createElementNS(svgns, "line");
    xAxis.setAttribute("x1", margin.left);
    xAxis.setAttribute("y1", margin.top + plotH);
    xAxis.setAttribute("x2", margin.left);
    xAxis.setAttribute("y2", margin.top);
    xAxis.setAttribute("stroke", "#444");
    xAxis.setAttribute("stroke-width", "1");
    svg.appendChild(xAxis);

    for (let i = 0; i < n; i++) {
        const dv = displayValues[i];
        const v = folds[i];

        const x = margin.left + i * barW;
        const yVal = yScaleDisp(dv);
        const yBase = yScaleDisp(0);
        const barHeight = Math.abs(yBase - yVal);

        let color = "#66bb6a";
        if (dv < -3) {
            color = "#c62828";
        } else if (dv < -2) {
            color = "#fb8c00";
        }

        const bar = document.createElementNS(svgns, "rect");
        bar.setAttribute("x", x + 1);
        bar.setAttribute("width", Math.max(1, barW - 2));
        bar.setAttribute("fill", color);
        bar.style.cursor = "pointer";

        if (dv >= 0) {
            bar.setAttribute("y", yVal);
            bar.setAttribute("height", Math.max(1, barHeight));
        } else {
            bar.setAttribute("y", yBase);
            bar.setAttribute("height", Math.max(1, barHeight));
        }

        bar.addEventListener("mouseenter", (evt) => {
            tooltip.style.display = "block";
            const direction = v >= 1 ? "times more" : "times less";
            const foldAbs = v >= 1 ? v.toFixed(2) : (1 / v).toFixed(2);
            tooltip.textContent = `${samples[i]}\nCoverage: ${foldAbs}X ${direction} than required`;
            tooltip.style.left = evt.clientX + "px";
            tooltip.style.top = evt.clientY + "px";
        });
        bar.addEventListener("mousemove", (evt) => {
            tooltip.style.left = evt.clientX + "px";
            tooltip.style.top = evt.clientY + "px";
        });
        bar.addEventListener("mouseleave", () => {
            tooltip.style.display = "none";
        });

        svg.appendChild(bar);

        const showAll = n <= 40;
        const show = showAll || (i % 5 === 0);
        if (show) {
            const lab = document.createElementNS(svgns, "text");
            lab.setAttribute("x", x + barW / 2);
            lab.setAttribute("y", margin.top + plotH + 14);
            lab.setAttribute("font-size", "9");
            lab.setAttribute("text-anchor", "end");
            lab.setAttribute(
                "transform",
                `rotate(-60 ${x + barW / 2} ${margin.top + plotH + 14})`
            );
            lab.textContent = samples[i];
            svg.appendChild(lab);
        }
    }

    const yLabel = document.createElementNS(svgns, "text");
    yLabel.setAttribute("x", 16);
    yLabel.setAttribute("y", margin.top + plotH / 2);
    yLabel.setAttribute("font-size", "11");
    yLabel.setAttribute("text-anchor", "middle");
    yLabel.setAttribute("transform", `rotate(-90 16 ${margin.top + plotH / 2})`);
    yLabel.textContent = "Fold-change vs LR target";
    svg.appendChild(yLabel);
}

/* ---------- Section 6: Sample clusters (Mash-based) ---------- */
function addClustersSection(parent, clusters) {
    if (!clusters) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(clusters.flag_clusters);

    const msg = clusters.message_clusters || "";
    const markers = clusters.markers || {};
    const reads = clusters.reads || {};

    const markersStruct = markers.structure || {};
    const readsStruct = reads.structure || {};

    const mMeanWithin = markersStruct.mean_within_distance;
    const mMeanBetween = markersStruct.mean_between_distance;
    const rMeanWithin = readsStruct.mean_within_distance;
    const rMeanBetween = readsStruct.mean_between_distance;

    const nClustersMarkers = markers.n_clusters != null ? markers.n_clusters : "NA";
    const nClustersReads = reads.n_clusters != null ? reads.n_clusters : "NA";

    const status = sectionStatus("Sample clusters", clusters.flag_clusters);

    div.innerHTML = `
        <h2 class="section-title">Sample clusters</h2>
        <p class="section-intro">
            This section summarises Mash-based clustering of samples from both marker genes and reads, giving an overview
            of sample similarity structure.
        </p>
        <details>
            <summary>
                <span class="status-emoji">${status.emoji}</span>
                <span class="status-text">${status.text}</span>
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
                        <div class="cluster-stat-label">Mean within-cluster distance</div>
                        <div class="cluster-stat-value">
                            Markers: ${fmtFloat(mMeanWithin, 3)}<br/>
                            Reads: ${fmtFloat(rMeanWithin, 3)}
                        </div>
                        <div class="cluster-stat-note">Average Mash distance among samples within clusters</div>
                    </div>
                    <div class="cluster-stat-item">
                        <div class="cluster-stat-label">Mean between-cluster distance</div>
                        <div class="cluster-stat-value">
                            Markers: ${fmtFloat(mMeanBetween, 3)}<br/>
                            Reads: ${fmtFloat(rMeanBetween, 3)}
                        </div>
                        <div class="cluster-stat-note">Average Mash distance between clusters</div>
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

                <div class="pairwise-heatmap-container">
                    <h3>Pairwise Mash distances</h3>
                    <div class="pairwise-tabs">
                        <button type="button" class="pairwise-tab active" data-kind="markers">Marker genes</button>
                        <button type="button" class="pairwise-tab" data-kind="reads">Reads</button>
                    </div>
                    <div class="pairwise-heatmap-scroll">
                        <svg id="pairwise-heatmap-svg" class="pairwise-heatmap-svg" viewBox="0 0 1000 420" preserveAspectRatio="none"></svg>
                    </div>
                    <p class="small-note">
                        Heatmap shows pairwise Mash distances between samples. Use the tabs to switch between marker-based and read-based estimates.
                    </p>
                </div>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const svg = div.querySelector("#clusters-heatmap-svg");
    if (!svg) return;

    const tooltip = getOrCreateTooltip();
    const svgns = "http://www.w3.org/2000/svg";

    const markersPS = markers.per_sample || [];
    const readsPS = reads.per_sample || [];

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

    const height = 210;
    const margin = {left: 80, right: 20, top: 20, bottom: 80};
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
                    lab.setAttribute("y", height - 22);
                    lab.setAttribute("font-size", "9");
                    lab.setAttribute("text-anchor", "end");
                    lab.setAttribute(
                        "transform",
                        `rotate(-60 ${x + cellW / 2} ${height - 22})`
                    );
                    lab.textContent = sampleName;
                    svg.appendChild(lab);
                }
            }
        });
    }

    drawRow(0, "Markers", markersMap, markerColors, "#9ecae1");
    drawRow(1, "Reads", readsMap, readColors, "#fcae91");

    // Pairwise Mash distance heatmap (markers vs reads)
    const pairwiseSvg = div.querySelector("#pairwise-heatmap-svg");
    const markersPairs = clusters.pairwise_markers || [];
    const readsPairs = clusters.pairwise_reads || [];

    if (pairwiseSvg && (markersPairs.length || readsPairs.length)) {
        const tabButtons = Array.from(div.querySelectorAll(".pairwise-tab"));

        function buildPairwiseMatrix(pairs) {
            if (!pairs || !pairs.length) return null;
            const sampleSet2 = new Set();
            pairs.forEach(p => {
                if (p.sample1 != null) sampleSet2.add(p.sample1);
                if (p.sample2 != null) sampleSet2.add(p.sample2);
            });
            const samples2 = Array.from(sampleSet2);
            samples2.sort();
            const n2 = samples2.length;
            const index = {};
            samples2.forEach((s, i) => { index[s] = i; });

            const mat = Array.from({length: n2}, () => new Array(n2).fill(null));
            let minD = Infinity;
            let maxD = -Infinity;

            pairs.forEach(p => {
                const s1 = p.sample1;
                const s2 = p.sample2;
                const d = Number(p.distance);
                if (!(s1 in index) || !(s2 in index) || !isFinite(d)) return;
                const i = index[s1];
                const j = index[s2];
                mat[i][j] = d;
                mat[j][i] = d;
                if (i !== j) {
                    if (d < minD) minD = d;
                    if (d > maxD) maxD = d;
                }
            });

            if (!isFinite(minD) || !isFinite(maxD)) {
                minD = 0;
                maxD = 1;
            }
            return { samples: samples2, matrix: mat, min: minD, max: maxD };
        }

        const markersMatrix = buildPairwiseMatrix(markersPairs);
        const readsMatrix = buildPairwiseMatrix(readsPairs);

        function pairwiseColor(d, minD, maxD, kind) {
            if (!isFinite(d)) return "#ffffff";
            const span = maxD - minD || 1;
            const t = (d - minD) / span;
            if (kind === "markers") {
                const r = 240 + Math.round(15 * t);
                const g = 249 - Math.round(80 * t);
                const b = 255 - Math.round(180 * t);
                return `rgb(${r},${g},${b})`;
            } else {
                const r = 254 - Math.round(130 * (1 - t));
                const g = 229 - Math.round(150 * t);
                const b = 217 - Math.round(180 * t);
                return `rgb(${r},${g},${b})`;
            }
        }

        function drawPairwise(kind) {
            const data = (kind === "reads") ? readsMatrix : markersMatrix;
            if (!data) {
                pairwiseSvg.outerHTML = '<div class="small-note">Pairwise Mash distances not available for ' + (kind === "reads" ? 'reads' : 'marker genes') + '.</div>';
                return;
            }

            while (pairwiseSvg.firstChild) {
                pairwiseSvg.removeChild(pairwiseSvg.firstChild);
            }

            const samples2 = data.samples;
            const mat = data.matrix;
            const n2 = samples2.length;
            const minD = data.min;
            const maxD = data.max;

            const svgns2 = "http://www.w3.org/2000/svg";
            const margin2 = {left: 80, right: 20, top: 40, bottom: 80};
            const baseCell = 20;
            const width2 = Math.max(1000, margin2.left + margin2.right + n2 * baseCell);
            const height2 = margin2.top + margin2.bottom + n2 * baseCell;
            pairwiseSvg.setAttribute("viewBox", `0 0 ${width2} ${height2}`);

            const tooltip2 = getOrCreateTooltip();
            const plotX0 = margin2.left;
            const plotY0 = margin2.top;
            const cellSize = (width2 - margin2.left - margin2.right) / n2;

            samples2.forEach((rowName, i) => {
                samples2.forEach((colName, j) => {
                    const d = mat[i][j];
                    const fill = (i === j) ? "#ffffff" : pairwiseColor(d, minD, maxD, kind);
                    const x = plotX0 + j * cellSize;
                    const y = plotY0 + i * cellSize;

                    const rect = document.createElementNS(svgns2, "rect");
                    rect.setAttribute("x", x);
                    rect.setAttribute("y", y);
                    rect.setAttribute("width", cellSize);
                    rect.setAttribute("height", cellSize);
                    rect.setAttribute("fill", fill);
                    rect.setAttribute("stroke", "#f0f0f0");
                    rect.setAttribute("stroke-width", "0.5");

                    if (i !== j) {
                        const tt = `${rowName} vs ${colName}\nMash distance: ${d != null ? d.toFixed(4) : 'NA'}`;
                        rect.style.cursor = "pointer";
                        rect.addEventListener("mouseenter", (evt) => {
                            rect.setAttribute("stroke", "#000");
                            rect.setAttribute("stroke-width", "1");
                            tooltip2.style.display = "block";
                            tooltip2.textContent = tt;
                            tooltip2.style.left = evt.clientX + "px";
                            tooltip2.style.top = evt.clientY + "px";
                        });
                        rect.addEventListener("mousemove", (evt) => {
                            tooltip2.style.left = evt.clientX + "px";
                            tooltip2.style.top = evt.clientY + "px";
                        });
                        rect.addEventListener("mouseleave", () => {
                            rect.setAttribute("stroke", "#f0f0f0");
                            rect.setAttribute("stroke-width", "0.5");
                            tooltip2.style.display = "none";
                        });
                    }

                    pairwiseSvg.appendChild(rect);
                });
            });

            samples2.forEach((name, idx) => {
                const xCenter = plotX0 + idx * cellSize + cellSize / 2;
                const yCenter = plotY0 + idx * cellSize + cellSize / 2;

                const yLab = document.createElementNS(svgns2, "text");
                yLab.setAttribute("x", margin2.left - 6);
                yLab.setAttribute("y", yCenter + 3);
                yLab.setAttribute("font-size", "9");
                yLab.setAttribute("text-anchor", "end");
                yLab.textContent = name;
                pairwiseSvg.appendChild(yLab);

                const xLab = document.createElementNS(svgns2, "text");
                xLab.setAttribute("x", xCenter);
                xLab.setAttribute("y", height2 - margin2.bottom + 12);
                xLab.setAttribute("font-size", "9");
                xLab.setAttribute("text-anchor", "end");
                xLab.setAttribute("transform", `rotate(-60 ${xCenter} ${height2 - margin2.bottom + 12})`);
                xLab.textContent = name;
                pairwiseSvg.appendChild(xLab);
            });
        }

        function setActiveTab(kind) {
            tabButtons.forEach(btn => {
                const k = btn.getAttribute("data-kind");
                btn.classList.toggle("active", k === kind);
            });
        }

        let initialKind = markersMatrix ? "markers" : "reads";
        if (!markersMatrix && !readsMatrix) {
            pairwiseSvg.outerHTML = '<div class="small-note">Pairwise Mash distances not available.</div>';
        } else {
            setActiveTab(initialKind);
            drawPairwise(initialKind);

            tabButtons.forEach(btn => {
                btn.addEventListener("click", () => {
                    const kind = btn.getAttribute("data-kind");
                    setActiveTab(kind);
                    drawPairwise(kind);
                });
            });
        }
    } else if (pairwiseSvg) {
        pairwiseSvg.outerHTML = '<div class="small-note">Pairwise Mash distances not available.</div>';
    }
}

/* Main JS entry */
function main() {
    const distill = DISTILL_DATA;
    const figures = FIGURES_DATA;

    const summaryDiv = document.getElementById("summary-sections");
    const globalDiv = document.getElementById("global-summary");

    const S = distill.summary || {};

    const depthFig = figures.figures && figures.figures.dna_depth_fractions
        ? figures.figures.dna_depth_fractions
        : null;
    const depthPerSample = depthFig ? (depthFig.per_sample || []) : [];

    const redBiplot = figures.figures && figures.figures.redundancy_biplot
        ? figures.figures.redundancy_biplot
        : null;
    const redBiplotPerSample = redBiplot ? (redBiplot.per_sample || []) : [];

    addGlobalSummary(globalDiv, distill, depthPerSample);
    addScreeningOverviewSection(summaryDiv, S.screening_overview, depthPerSample);
    addLowQualitySection(summaryDiv, S.low_quality_reads, depthPerSample);
    addProkFractionSection(summaryDiv, S.prokaryotic_fraction, depthPerSample);
    addRedundancyReadsSection(summaryDiv, S.redundancy_reads, depthPerSample);
    addRedundancyMarkersSection(summaryDiv, S.redundancy_markers, redBiplotPerSample);
    addClustersSection(summaryDiv, S.clusters);
}

main();
</script>

</body>
</html>
"""

def main():
    ap = argparse.ArgumentParser(
        description="Create an interactive HTML summary report from distill.json and figures.json."
    )
    ap.add_argument(
        "--distill-json",
        required=True,
        help="Path to distill.json (distilled summary).",
    )
    ap.add_argument(
        "--figures-json",
        required=True,
        help="Path to figures.json (figure-friendly data).",
    )
    ap.add_argument(
        "-o",
        "--output",
        required=True,
        help="Path to output HTML report.",
    )
    args = ap.parse_args()

    distill_path = Path(args.distill_json)
    figures_path = Path(args.figures_json)

    if not distill_path.is_file():
        raise FileNotFoundError(f"distill.json not found: {distill_path}")
    if not figures_path.is_file():
        raise FileNotFoundError(f"figures.json not found: {figures_path}")

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
