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

    .section {
        margin-bottom: 24px;
        border-radius: 8px;
        padding: 12px 16px 18px 16px;
        border: 1px solid #ccc;
        background: #fff;
    }

    details > summary {
        font-size: 1.05em;
        cursor: pointer;
        padding: 4px 0;
        font-weight: bold;
        list-style: none;
    }

    details[open] > summary {
        margin-bottom: 8px;
    }

    /* Flag-based background colours */
    .flag-1 {
        background-color: #d7f5dd; /* greenish */
    }
    .flag-2 {
        background-color: #fff9c4; /* yellow */
    }
    .flag-3 {
        background-color: #ffd2d2; /* red/pink */
    }

    .summary-message {
        margin-bottom: 12px;
    }

    .small-note {
        font-size: 0.85em;
        color: #666;
        margin-top: 8px;
    }

    /* Generic highlight tiles (for stats) */
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

    /* Clusters heatmap */
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
        height: 210px; /* more vertical room for labels */
    }

    /* Tooltip for interactive charts */
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

<div id="summary-sections"></div>

<script>
// Embedded data from Python.
const DISTILL_DATA = __DISTILL_JSON__;
const FIGURES_DATA = __FIGURES_JSON__;

function flagClass(flag) {
    if (flag === 1) return "flag-1";
    if (flag === 2) return "flag-2";
    return "flag-3";
}

/* ---------- Formatting helpers ---------- */

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

/* Shared tooltip for charts */
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

/* ---------- Screening overview (merged) ---------- */

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

    div.innerHTML = `
        <details open>
            <summary>Screening overview</summary>
            <div class="content">
                <p class="summary-message">${msg}</p>
                <div class="screen-overview-stats">
                    <div class="screen-overview-stat-item">
                        <div class="screen-overview-stat-label">Total samples</div>
                        <div class="screen-overview-stat-value">${fmtInt(total)}</div>
                        <div class="screen-overview-stat-note">Samples in data.json</div>
                    </div>
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
                    X axis: samples; Y axis: sequencing depth in reads. Bars show per-sample total read counts.
                    A horizontal dashed line indicates the median sequencing depth across samples.
                    Hover over bars for exact values.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const svg = div.querySelector("#seq-depth-svg");
    const perSample = (depthPerSample || [])
        .filter(d => d.total_reads !== null && d.total_reads !== undefined);

    if (!perSample.length) {
        svg.outerHTML = `<div class="small-note">Per-sample read counts not available for sequencing depth barplot.</div>`;
        return;
    }

    const width = 1000;
    const height = 320;
    const margin = {left: 60, right: 20, top: 20, bottom: 80};
    const plotW = width - margin.left - margin.right;
    const plotH = height - margin.top - margin.bottom;
    const svgns = "http://www.w3.org/2000/svg";

    let maxDepth = 0;
    perSample.forEach(d => {
        const v = Number(d.total_reads) || 0;
        if (v > maxDepth) maxDepth = v;
    });
    if (maxDepth <= 0) maxDepth = 1;

    const x0 = margin.left;
    const y0 = height - margin.bottom;

    function yForValue(v) {
        const ratio = Math.max(0, Math.min(1, v / maxDepth));
        return y0 - ratio * plotH;
    }

    const xAxis = document.createElementNS(svgns, "line");
    xAxis.setAttribute("x1", x0);
    xAxis.setAttribute("y1", y0);
    xAxis.setAttribute("x2", x0 + plotW);
    xAxis.setAttribute("y2", y0);
    xAxis.setAttribute("stroke", "#555");
    svg.appendChild(xAxis);

    const yAxis = document.createElementNS(svgns, "line");
    yAxis.setAttribute("x1", x0);
    yAxis.setAttribute("y1", y0);
    yAxis.setAttribute("x2", x0);
    yAxis.setAttribute("y2", margin.top);
    yAxis.setAttribute("stroke", "#555");
    svg.appendChild(yAxis);

    [0, 0.25, 0.5, 0.75, 1].forEach(frac => {
        const val = frac * maxDepth;
        const y = yForValue(val);

        const tick = document.createElementNS(svgns, "line");
        tick.setAttribute("x1", x0 - 4);
        tick.setAttribute("y1", y);
        tick.setAttribute("x2", x0);
        tick.setAttribute("y2", y);
        tick.setAttribute("stroke", "#555");
        svg.appendChild(tick);

        const lab = document.createElementNS(svgns, "text");
        lab.setAttribute("x", x0 - 6);
        lab.setAttribute("y", y + 3);
        lab.setAttribute("font-size", "10");
        lab.setAttribute("text-anchor", "end");
        lab.textContent = fmtMillions(val);
        svg.appendChild(lab);
    });

    const ylabel = document.createElementNS(svgns, "text");
    ylabel.setAttribute("x", 16);
    ylabel.setAttribute("y", margin.top + plotH / 2);
    ylabel.setAttribute("text-anchor", "middle");
    ylabel.setAttribute("font-size", "11");
    ylabel.setAttribute("transform", `rotate(-90 16 ${margin.top + plotH / 2})`);
    ylabel.textContent = "Sequencing depth (reads)";
    svg.appendChild(ylabel);

    const xlabel = document.createElementNS(svgns, "text");
    xlabel.setAttribute("x", margin.left + plotW / 2);
    xlabel.setAttribute("y", height - 8);
    xlabel.setAttribute("text-anchor", "middle");
    xlabel.setAttribute("font-size", "11");
    xlabel.textContent = "Samples";
    svg.appendChild(xlabel);

    const tooltip = getOrCreateTooltip();

    const n = perSample.length;
    const step = plotW / n;
    const barWidth = Math.min(16, step * 0.8);

    perSample.forEach((d, i) => {
        const val = Number(d.total_reads) || 0;
        const xCenter = x0 + step * i + step / 2;
        const x = xCenter - barWidth / 2;
        const y = yForValue(val);
        const hBar = y0 - y;

        const rect = document.createElementNS(svgns, "rect");
        rect.setAttribute("x", x);
        rect.setAttribute("y", y);
        rect.setAttribute("width", barWidth);
        rect.setAttribute("height", hBar);
        rect.setAttribute("fill", "#1976d2");
        rect.setAttribute("fill-opacity", "0.85");
        rect.style.cursor = "pointer";

        rect.addEventListener("mouseenter", (evt) => {
            rect.setAttribute("fill", "#0d47a1");
            rect.setAttribute("fill-opacity", "1.0");
            tooltip.style.display = "block";
            tooltip.textContent = `${d.sample}: ${fmtMillions(val)} reads`;
            tooltip.style.left = evt.clientX + "px";
            tooltip.style.top = evt.clientY + "px";
        });
        rect.addEventListener("mousemove", (evt) => {
            tooltip.style.left = evt.clientX + "px";
            tooltip.style.top = evt.clientY + "px";
        });
        rect.addEventListener("mouseleave", () => {
            rect.setAttribute("fill", "#1976d2");
            rect.setAttribute("fill-opacity", "0.85");
            tooltip.style.display = "none";
        });

        svg.appendChild(rect);

        const showAll = n <= 40;
        const show = showAll || (i % 5 === 0);
        if (show) {
            const lab = document.createElementNS(svgns, "text");
            lab.setAttribute("x", xCenter);
            lab.setAttribute("y", y0 + 10);
            lab.setAttribute("font-size", "9");
            lab.setAttribute("text-anchor", "end");
            lab.setAttribute("transform", `rotate(-60 ${xCenter} ${y0 + 10})`);
            lab.textContent = d.sample;
            svg.appendChild(lab);
        }
    });

    const medianDepth = Number(medianReads) || 0;

    if (medianDepth > 0) {
        const y = yForValue(medianDepth);
        const line = document.createElementNS(svgns, "line");
        line.setAttribute("x1", x0);
        line.setAttribute("y1", y);
        line.setAttribute("x2", x0 + plotW);
        line.setAttribute("y2", y);
        line.setAttribute("stroke", "#43a047");
        line.setAttribute("stroke-width", "1.2");
        line.setAttribute("stroke-dasharray", "3,2");
        svg.appendChild(line);

        const lab = document.createElementNS(svgns, "text");
        lab.setAttribute("x", x0 + plotW - 4);
        lab.setAttribute("y", y - 2);
        lab.setAttribute("font-size", "10");
        lab.setAttribute("text-anchor", "end");
        lab.setAttribute("fill", "#43a047");
        lab.textContent = `median (${fmtMillions(medianDepth)})`;
        svg.appendChild(lab);
    }
}

/* Sequencing quality (fastp) – per-sample barplot */
function addLowQualitySection(parent, data, depthPerSample) {
    if (!data) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(data.flag_low_quality);

    const msg = data.message_low_quality || "";

    const overall = data.percent_removed_reads_overall;
    const meanFrac = data.mean_fraction_removed;
    const medianFrac = data.median_fraction_removed;

    div.innerHTML = `
        <details>
            <summary>Sequencing quality</summary>
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
                    <svg id="quality-svg" class="quality-svg" viewBox="0 0 1000 320" preserveAspectRatio="none"></svg>
                </div>
                <p class="small-note">
                    X axis: samples; Y axis: fraction of reads removed by quality filtering (fastp).
                    Bars show per-sample removed fractions. Horizontal dashed lines mark 5% (yellow-orange)
                    and 20% (red) thresholds. Hover over bars for exact values.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const svg = div.querySelector("#quality-svg");
    const perSample = (depthPerSample || [])
        .filter(d => d.fraction_low_quality_of_total !== null &&
                     d.fraction_low_quality_of_total !== undefined);

    if (!perSample.length) {
        svg.outerHTML = `<div class="small-note">Per-sample removed fractions not available for sequencing quality plot.</div>`;
        return;
    }

    const width = 1000;
    const height = 320;
    const margin = {left: 60, right: 20, top: 20, bottom: 80};
    const plotW = width - margin.left - margin.right;
    const plotH = height - margin.top - margin.bottom;
    const svgns = "http://www.w3.org/2000/svg";

    const x0 = margin.left;
    const y0 = height - margin.bottom;

    // Determine max fraction; ensure thresholds visible.
    let maxFrac = 0;
    perSample.forEach(d => {
        const f = Number(d.fraction_low_quality_of_total) || 0;
        if (f > maxFrac) maxFrac = f;
    });
    maxFrac = Math.max(maxFrac * 1.1, 0.25, 0.22); // at least 25% so 20% line is well inside

    function yForFrac(f) {
        const frac = Math.max(0, Math.min(maxFrac, f));
        return y0 - (frac / maxFrac) * plotH;
    }

    const xAxis = document.createElementNS(svgns, "line");
    xAxis.setAttribute("x1", x0);
    xAxis.setAttribute("y1", y0);
    xAxis.setAttribute("x2", x0 + plotW);
    xAxis.setAttribute("y2", y0);
    xAxis.setAttribute("stroke", "#555");
    svg.appendChild(xAxis);

    const yAxis = document.createElementNS(svgns, "line");
    yAxis.setAttribute("x1", x0);
    yAxis.setAttribute("y1", y0);
    yAxis.setAttribute("x2", x0);
    yAxis.setAttribute("y2", margin.top);
    yAxis.setAttribute("stroke", "#555");
    svg.appendChild(yAxis);

    // Y ticks at 0, 5, 10, 15, 20, 25% (or up to maxFrac)
    const tickPercs = [0, 0.05, 0.10, 0.15, 0.20, 0.25].filter(p => p <= maxFrac + 1e-9);
    tickPercs.forEach(frac => {
        const y = yForFrac(frac);
        const tick = document.createElementNS(svgns, "line");
        tick.setAttribute("x1", x0 - 4);
        tick.setAttribute("y1", y);
        tick.setAttribute("x2", x0);
        tick.setAttribute("y2", y);
        tick.setAttribute("stroke", "#555");
        svg.appendChild(tick);

        const lab = document.createElementNS(svgns, "text");
        lab.setAttribute("x", x0 - 6);
        lab.setAttribute("y", y + 3);
        lab.setAttribute("font-size", "10");
        lab.setAttribute("text-anchor", "end");
        lab.textContent = (frac * 100).toFixed(0) + "%";
        svg.appendChild(lab);
    });

    const ylabel = document.createElementNS(svgns, "text");
    ylabel.setAttribute("x", 16);
    ylabel.setAttribute("y", margin.top + plotH / 2);
    ylabel.setAttribute("text-anchor", "middle");
    ylabel.setAttribute("font-size", "11");
    ylabel.setAttribute("transform", `rotate(-90 16 ${margin.top + plotH / 2})`);
    ylabel.textContent = "Reads removed by fastp (%)";
    svg.appendChild(ylabel);

    const xlabel = document.createElementNS(svgns, "text");
    xlabel.setAttribute("x", margin.left + plotW / 2);
    xlabel.setAttribute("y", height - 8);
    xlabel.setAttribute("text-anchor", "middle");
    xlabel.setAttribute("font-size", "11");
    xlabel.textContent = "Samples";
    svg.appendChild(xlabel);

    const tooltip = getOrCreateTooltip();

    const n = perSample.length;
    const step = plotW / n;
    const barWidth = Math.min(16, step * 0.8);

    perSample.forEach((d, i) => {
        const frac = Number(d.fraction_low_quality_of_total) || 0;
        const xCenter = x0 + step * i + step / 2;
        const x = xCenter - barWidth / 2;
        const y = yForFrac(frac);
        const hBar = y0 - y;

        const rect = document.createElementNS(svgns, "rect");
        rect.setAttribute("x", x);
        rect.setAttribute("y", y);
        rect.setAttribute("width", barWidth);
        rect.setAttribute("height", hBar);
        rect.setAttribute("fill", "#1976d2");
        rect.setAttribute("fill-opacity", "0.9");
        rect.style.cursor = "pointer";

        const tooltipText =
            `${d.sample}\n` +
            `Removed: ${(frac * 100).toFixed(2)}%`;

        rect.addEventListener("mouseenter", (evt) => {
            rect.setAttribute("fill", "#0d47a1");
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
            rect.setAttribute("fill", "#1976d2");
            tooltip.style.display = "none";
        });

        svg.appendChild(rect);

        const showAll = n <= 40;
        const show = showAll || (i % 5 === 0);
        if (show) {
            const lab = document.createElementNS(svgns, "text");
            lab.setAttribute("x", xCenter);
            lab.setAttribute("y", y0 + 10);
            lab.setAttribute("font-size", "9");
            lab.setAttribute("text-anchor", "end");
            lab.setAttribute("transform", `rotate(-60 ${xCenter} ${y0 + 10})`);
            lab.textContent = d.sample;
            svg.appendChild(lab);
        }
    });

    // Horizontal threshold lines at 5% and 20%
    const thresholds = [
        {frac: 0.05, color: "#ffb300", label: "5%"},
        {frac: 0.20, color: "#d32f2f", label: "20%"}
    ];
    thresholds.forEach(t => {
        if (t.frac > maxFrac + 1e-9) return;
        const y = yForFrac(t.frac);
        const line = document.createElementNS(svgns, "line");
        line.setAttribute("x1", x0);
        line.setAttribute("y1", y);
        line.setAttribute("x2", x0 + plotW);
        line.setAttribute("y2", y);
        line.setAttribute("stroke", t.color);
        line.setAttribute("stroke-width", "1.4");
        line.setAttribute("stroke-dasharray", "4,2");
        svg.appendChild(line);

        const lab = document.createElementNS(svgns, "text");
        lab.setAttribute("x", x0 + plotW - 4);
        lab.setAttribute("y", y - 2);
        lab.setAttribute("font-size", "10");
        lab.setAttribute("text-anchor", "end");
        lab.setAttribute("fill", t.color);
        lab.textContent = t.label;
        svg.appendChild(lab);
    });
}

/* Prokaryotic fraction + depth components */
function addProkFractionSection(parent, data, depthPerSample) {
    if (!data) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(data.flag_prokaryotic_fraction);

    const msg = data.message_prokaryotic_fraction || "";

    div.innerHTML = `
        <details>
            <summary>Prokaryotic fraction</summary>
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
                    <svg id="prok-depth-svg" class="prok-depth-svg" viewBox="0 0 1000 320" preserveAspectRatio="none"></svg>
                </div>
                <p class="small-note">
                    X axis: samples; Y axis: fraction of total reads. Bars are stacked into low-quality (red),
                    prokaryotic (green), and other QC-passing reads (grey). Hover over bars for exact fractions
                    and estimated read counts of each component. A dashed horizontal line indicates the median
                    prokaryotic fraction across samples.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const svg = div.querySelector("#prok-depth-svg");
    const dataPerSample = (depthPerSample || []).filter(d =>
        d.total_reads !== null &&
        d.total_reads !== undefined
    );

    if (!dataPerSample.length) {
        svg.outerHTML = `<div class="small-note">Per-sample depth component data not available.</div>`;
        return;
    }

    const width = 1000;
    const height = 320;
    const margin = {left: 60, right: 20, top: 20, bottom: 80};
    const plotW = width - margin.left - margin.right;
    const plotH = height - margin.top - margin.bottom;
    const svgns = "http://www.w3.org/2000/svg";

    const x0 = margin.left;
    const y0 = height - margin.bottom;

    function yForFrac(frac) {
        const f = Math.max(0, Math.min(1, frac));
        return y0 - f * plotH;
    }

    const xAxis = document.createElementNS(svgns, "line");
    xAxis.setAttribute("x1", x0);
    xAxis.setAttribute("y1", y0);
    xAxis.setAttribute("x2", x0 + plotW);
    xAxis.setAttribute("y2", y0);
    xAxis.setAttribute("stroke", "#555");
    svg.appendChild(xAxis);

    const yAxis = document.createElementNS(svgns, "line");
    yAxis.setAttribute("x1", x0);
    yAxis.setAttribute("y1", y0);
    yAxis.setAttribute("x2", x0);
    yAxis.setAttribute("y2", margin.top);
    yAxis.setAttribute("stroke", "#555");
    svg.appendChild(yAxis);

    [0, 0.25, 0.5, 0.75, 1].forEach(frac => {
        const y = yForFrac(frac);
        const tick = document.createElementNS(svgns, "line");
        tick.setAttribute("x1", x0 - 4);
        tick.setAttribute("y1", y);
        tick.setAttribute("x2", x0);
        tick.setAttribute("y2", y);
        tick.setAttribute("stroke", "#555");
        svg.appendChild(tick);

        const lab = document.createElementNS(svgns, "text");
        lab.setAttribute("x", x0 - 6);
        lab.setAttribute("y", y + 3);
        lab.setAttribute("font-size", "10");
        lab.setAttribute("text-anchor", "end");
        lab.textContent = (frac * 100).toFixed(0) + "%";
        svg.appendChild(lab);
    });

    const ylabel = document.createElementNS(svgns, "text");
    ylabel.setAttribute("x", 16);
    ylabel.setAttribute("y", margin.top + plotH / 2);
    ylabel.setAttribute("text-anchor", "middle");
    ylabel.setAttribute("font-size", "11");
    ylabel.setAttribute("transform", `rotate(-90 16 ${margin.top + plotH / 2})`);
    ylabel.textContent = "Fraction of total reads";
    svg.appendChild(ylabel);

    const xlabel = document.createElementNS(svgns, "text");
    xlabel.setAttribute("x", margin.left + plotW / 2);
    xlabel.setAttribute("y", height - 8);
    xlabel.setAttribute("text-anchor", "middle");
    xlabel.setAttribute("font-size", "11");
    xlabel.textContent = "Samples";
    svg.appendChild(xlabel);

    const tooltip = getOrCreateTooltip();

    const n = dataPerSample.length;
    const step = plotW / n;
    const barWidth = Math.min(16, step * 0.8);

    dataPerSample.forEach((d, i) => {
        const fracLow = d.fraction_low_quality_of_total || 0;
        const fracProk = d.fraction_prokaryotic_of_total || 0;
        const fracOther = d.fraction_non_prokaryotic_of_total || 0;

        const totalReads = d.total_reads || 0;
        const lowReads = d.low_quality_reads_est || 0;
        const prokReads = d.prokaryotic_reads_est || 0;
        const otherReads = d.non_prokaryotic_reads_est || 0;

        const xCenter = x0 + step * i + step / 2;
        const x = xCenter - barWidth / 2;

        const hLow = fracLow * plotH;
        const hProk = fracProk * plotH;
        const hOther = fracOther * plotH;

        let currentTop = y0;

        function makeSeg(height, color) {
            if (height <= 0) return null;
            const y = currentTop - height;
            currentTop = y;

            const rect = document.createElementNS(svgns, "rect");
            rect.setAttribute("x", x);
            rect.setAttribute("y", y);
            rect.setAttribute("width", barWidth);
            rect.setAttribute("height", height);
            rect.setAttribute("fill", color);
            rect.setAttribute("fill-opacity", "0.9");
            rect.style.cursor = "pointer";
            return rect;
        }

        const segLow = makeSeg(hLow, "#f44336");
        const segProk = makeSeg(hProk, "#4caf50");
        const segOther = makeSeg(hOther, "#9e9e9e");

        const tooltipText =
            `${d.sample}\n` +
            `Total: ${fmtMillions(totalReads)} reads\n` +
            `Low-quality: ${(100*fracLow).toFixed(2)}% (${fmtMillions(lowReads)} reads)\n` +
            `Prokaryotic: ${(100*fracProk).toFixed(2)}% (${fmtMillions(prokReads)} reads)\n` +
            `Other: ${(100*fracOther).toFixed(2)}% (${fmtMillions(otherReads)} reads)`;

        [segLow, segProk, segOther].forEach(seg => {
            if (!seg) return;
            seg.addEventListener("mouseenter", (evt) => {
                seg.setAttribute("stroke", "#000");
                seg.setAttribute("stroke-width", "1");
                tooltip.style.display = "block";
                tooltip.textContent = tooltipText;
                tooltip.style.left = evt.clientX + "px";
                tooltip.style.top = evt.clientY + "px";
            });
            seg.addEventListener("mousemove", (evt) => {
                tooltip.style.left = evt.clientX + "px";
                tooltip.style.top = evt.clientY + "px";
            });
            seg.addEventListener("mouseleave", () => {
                seg.removeAttribute("stroke");
                seg.removeAttribute("stroke-width");
                tooltip.style.display = "none";
            });
            svg.appendChild(seg);
        });

        const showAll = n <= 40;
        const show = showAll || (i % 5 === 0);
        if (show) {
            const lab = document.createElementNS(svgns, "text");
            lab.setAttribute("x", xCenter);
            lab.setAttribute("y", y0 + 10);
            lab.setAttribute("font-size", "9");
            lab.setAttribute("text-anchor", "end");
            lab.setAttribute("transform", `rotate(-60 ${xCenter} ${y0 + 10})`);
            lab.textContent = d.sample;
            svg.appendChild(lab);
        }
    });

    const medianProkFrac = (Number(data.median_prokaryotic_fraction) || 0) / 100;
    if (medianProkFrac > 0) {
        const y = yForFrac(medianProkFrac);
        const line = document.createElementNS(svgns, "line");
        line.setAttribute("x1", x0);
        line.setAttribute("y1", y);
        line.setAttribute("x2", x0 + plotW);
        line.setAttribute("y2", y);
        line.setAttribute("stroke", "#43a047");
        line.setAttribute("stroke-width", "1.2");
        line.setAttribute("stroke-dasharray", "3,2");
        svg.appendChild(line);

        const lab = document.createElementNS(svgns, "text");
        lab.setAttribute("x", x0 + plotW - 4);
        lab.setAttribute("y", y - 2);
        lab.setAttribute("font-size", "10");
        lab.setAttribute("text-anchor", "end");
        lab.setAttribute("fill", "#43a047");
        lab.textContent = `median prok (${fmtFloat(data.median_prokaryotic_fraction, 1)}%)`;
        svg.appendChild(lab);
    }
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

    div.innerHTML = `
        <details>
            <summary>Overall metagenomic coverage</summary>
            <div class="content">
                <p class="summary-message">${msg}</p>
                <div class="redundancy-stats">
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Mean kappa_total</div>
                        <div class="redundancy-stat-value">${fmtFloat(data.mean_kappa_total, 3)}</div>
                        <div class="redundancy-stat-note">Average Nonpareil redundancy estimate (reads)</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Variation in kappa_total</div>
                        <div class="redundancy-stat-value">${fmtFloat(data.cv_kappa_total, 3)}</div>
                        <div class="redundancy-stat-note">Coefficient of variation (CV)</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Samples at / above LR target</div>
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
                    The red dashed midline corresponds to the LR target (1×). Bars projecting above the
                    line indicate how many times more than necessary has been sequenced; bars projecting
                    below the line indicate how many times more sequencing would be needed to reach the target.
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
    if (maxAbs <= 0) maxAbs = 1;
    maxAbs *= 1.1;

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
    baseLine.setAttribute("stroke", "#e53935");
    baseLine.setAttribute("stroke-width", "1.4");
    baseLine.setAttribute("stroke-dasharray", "4,2");
    svg.appendChild(baseLine);

    const baseLabel = document.createElementNS(svgns, "text");
    baseLabel.setAttribute("x", x0 + plotW - 4);
    baseLabel.setAttribute("y", baselineY - 4);
    baseLabel.setAttribute("font-size", "10");
    baseLabel.setAttribute("text-anchor", "end");
    baseLabel.setAttribute("fill", "#e53935");
    baseLabel.textContent = "LR target (1×)";
    svg.appendChild(baseLabel);

    const maxTick = Math.max(1, Math.ceil(maxAbs));
    for (let v = -maxTick; v <= maxTick; v++) {
        const y = yForVal(v);
        const tick = document.createElementNS(svgns, "line");
        tick.setAttribute("x1", x0 - 4);
        tick.setAttribute("y1", y);
        tick.setAttribute("x2", x0);
        tick.setAttribute("y2", y);
        tick.setAttribute("stroke", "#555");
        svg.appendChild(tick);

        const lab = document.createElementNS(svgns, "text");
        lab.setAttribute("x", x0 - 6);
        lab.setAttribute("y", y + 3);
        lab.setAttribute("font-size", "10");
        lab.setAttribute("text-anchor", "end");

        let labelStr;
        if (v === 0) {
            labelStr = "1×";
        } else if (v > 0) {
            labelStr = (1 + v).toFixed(0) + "×";
        } else {
            labelStr = "-" + Math.abs(v).toFixed(0) + "×";
        }
        lab.textContent = labelStr;
        svg.appendChild(lab);
    }

    const ylabel = document.createElementNS(svgns, "text");
    ylabel.setAttribute("x", 16);
    ylabel.setAttribute("y", margin.top + plotH / 2);
    ylabel.setAttribute("text-anchor", "middle");
    ylabel.setAttribute("font-size", "11");
    ylabel.setAttribute("transform", `rotate(-90 16 ${margin.top + plotH / 2})`);
    ylabel.textContent = "Sequenced depth relative to LR target (95%)";
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

        const rect = document.createElementNS(svgns, "rect");
        rect.setAttribute("x", x);
        rect.setAttribute("y", yRect);
        rect.setAttribute("width", barWidth);
        rect.setAttribute("height", hRect);
        rect.setAttribute("fill", v >= 0 ? "#4caf50" : "#ffa000");
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

    div.innerHTML = `
        <details>
            <summary>Prokaryotic coverage</summary>
            <div class="content">
                <p class="summary-message">${msg}</p>
                <div class="redundancy-stats">
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Mean kappa_total</div>
                        <div class="redundancy-stat-value">${fmtFloat(data.mean_kappa_total, 3)}</div>
                        <div class="redundancy-stat-note">Average Nonpareil redundancy estimate (markers)</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Variation in kappa_total</div>
                        <div class="redundancy-stat-value">${fmtFloat(data.cv_kappa_total, 3)}</div>
                        <div class="redundancy-stat-note">Coefficient of variation (CV)</div>
                    </div>
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Samples at / above LR target</div>
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
                    The red dashed midline corresponds to the 95% coverage target (1×). Bars projecting above the
                    line indicate samples exceeding the target; bars projecting below indicate how many times more
                    coverage would be needed to reach it.
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
    if (maxAbs <= 0) maxAbs = 1;
    maxAbs *= 1.1;

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
    baseLine.setAttribute("stroke", "#e53935");
    baseLine.setAttribute("stroke-width", "1.4");
    baseLine.setAttribute("stroke-dasharray", "4,2");
    svg.appendChild(baseLine);

    const baseLabel = document.createElementNS(svgns, "text");
    baseLabel.setAttribute("x", x0 + plotW - 4);
    baseLabel.setAttribute("y", baselineY - 4);
    baseLabel.setAttribute("font-size", "10");
    baseLabel.setAttribute("text-anchor", "end");
    baseLabel.setAttribute("fill", "#e53935");
    baseLabel.textContent = "95% coverage target (1×)";
    svg.appendChild(baseLabel);

    const maxTick = Math.max(1, Math.ceil(maxAbs));
    for (let v = -maxTick; v <= maxTick; v++) {
        const y = yForVal(v);
        const tick = document.createElementNS(svgns, "line");
        tick.setAttribute("x1", x0 - 4);
        tick.setAttribute("y1", y);
        tick.setAttribute("x2", x0);
        tick.setAttribute("y2", y);
        tick.setAttribute("stroke", "#555");
        svg.appendChild(tick);

        const lab = document.createElementNS(svgns, "text");
        lab.setAttribute("x", x0 - 6);
        lab.setAttribute("y", y + 3);
        lab.setAttribute("font-size", "10");
        lab.setAttribute("text-anchor", "end");

        let labelStr;
        if (v === 0) {
            labelStr = "1×";
        } else if (v > 0) {
            labelStr = (1 + v).toFixed(0) + "×";
        } else {
            labelStr = "-" + Math.abs(v).toFixed(0) + "×";
        }
        lab.textContent = labelStr;
        svg.appendChild(lab);
    }

    const ylabel = document.createElementNS(svgns, "text");
    ylabel.setAttribute("x", 16);
    ylabel.setAttribute("y", margin.top + plotH / 2);
    ylabel.setAttribute("text-anchor", "middle");
    ylabel.setAttribute("font-size", "11");
    ylabel.setAttribute("transform", `rotate(-90 16 ${margin.top + plotH / 2})`);
    ylabel.textContent = "Marker coverage relative to 95% target";
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

        const rect = document.createElementNS(svgns, "rect");
        rect.setAttribute("x", x);
        rect.setAttribute("y", yRect);
        rect.setAttribute("width", barWidth);
        rect.setAttribute("height", hRect);
        rect.setAttribute("fill", v >= 0 ? "#4caf50" : "#ffa000");
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

/* Sample clusters (Mash-based) */
function addClustersSection(parent, clusters) {
    if (!clusters) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(clusters.flag_clusters);

    const msg = clusters.message_clusters || "";
    const markers = clusters.markers || {};
    const reads = clusters.reads || {};

    const nClustersMarkers = markers.n_clusters != null ? markers.n_clusters : "NA";
    const nClustersReads = reads.n_clusters != null ? reads.n_clusters : "NA";

    div.innerHTML = `
        <details>
            <summary>Sample clusters</summary>
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

    // Build sample->cluster maps from clusters[].members
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

    /* High-contrast palettes: cold blues/teals for markers, warm reds/oranges/magentas for reads */
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

    const height = 210;  // more vertical space for labels
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
        const labelY = yRowTop + cellH / 2 + 4;
        const labelText = document.createElementNS(svgns, "text");
        labelText.setAttribute("x", labelX);
        labelText.setAttribute("y", labelY);
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
                    lab.setAttribute("y", height - 22);  // closer to tiles, further from bottom edge
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
}

/* Main JS entry */
function main() {
    const distill = DISTILL_DATA;
    const figures = FIGURES_DATA;

    const summaryDiv = document.getElementById("summary-sections");

    const S = distill.summary || {};

    const depthFig = figures.figures && figures.figures.dna_depth_fractions
        ? figures.figures.dna_depth_fractions
        : null;
    const depthPerSample = depthFig ? (depthFig.per_sample || []) : [];

    const redBiplot = figures.figures && figures.figures.redundancy_biplot
        ? figures.figures.redundancy_biplot
        : null;
    const redBiplotPerSample = redBiplot ? (redBiplot.per_sample || []) : [];

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

    # Avoid breaking the <script> tag if JSON contains "</script>"
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
