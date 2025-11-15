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
    h2 {
        margin-top: 40px;
        margin-bottom: 15px;
    }

    .section {
        margin-bottom: 20px;
        border-radius: 8px;
        padding: 10px 15px 15px 15px;
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
        margin-bottom: 5px;
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
        margin-bottom: 6px;
    }

    .summary-metrics {
        margin: 0;
        padding-left: 18px;
        font-size: 0.95em;
    }

    .summary-metrics li {
        margin-bottom: 2px;
    }

    .small-note {
        font-size: 0.85em;
        color: #666;
        margin-top: 4px;
    }

    /* Depth fractions legend colours */
    .depth-legend {
        font-size: 0.9em;
        margin-bottom: 6px;
    }
    .depth-legend span.box {
        display: inline-block;
        width: 12px;
        height: 10px;
        margin-right: 4px;
        border-radius: 2px;
        vertical-align: middle;
    }
    .seg-lowq   { background: #f44336; }  /* red */
    .seg-prok   { background: #4caf50; }  /* green */
    .seg-other  { background: #9e9e9e; }  /* grey */

    /* Redundancy biplot */
    .biplot-container {
        overflow-x: auto;
    }
    .biplot-svg {
        border: 1px solid #ddd;
        background: #fcfcfc;
    }

    /* Summary stat tiles (Sequencing, Prok, Redundancy) */
    .seq-depth-stats, .prok-stats, .redundancy-stats {
        display: flex;
        gap: 16px;
        justify-content: space-between;
        margin-bottom: 10px;
        flex-wrap: wrap;
    }
    .seq-depth-stat-item, .prok-stat-item, .redundancy-stat-item {
        flex: 1;
        min-width: 160px;
    }
    .seq-depth-stat-label, .prok-stat-label, .redundancy-stat-label {
        font-size: 0.9em;
        color: #555;
        margin-bottom: 2px;
    }
    .seq-depth-stat-value, .prok-stat-value, .redundancy-stat-value {
        font-size: 1.4em;
        font-weight: 600;
    }
    .seq-depth-stat-note, .prok-stat-note, .redundancy-stat-note {
        font-size: 0.8em;
        color: #666;
        margin-top: 2px;
    }

    .seq-depth-plot-container,
    .prok-depth-plot-container,
    .lr-target-plot-container {
        width: 100%;
        border: 1px solid #ddd;
        border-radius: 4px;
        background: #fcfcfc;
        padding: 4px 4px 0 4px;
        box-sizing: border-box;
    }
    .seq-depth-svg,
    .prok-depth-svg,
    .lr-target-svg {
        display: block;
        width: 100%;
        height: 320px;
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

<h2>Figures</h2>
<div id="figure-sections"></div>

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

/* ---------- Summary sections ---------- */

function addScreeningSection(parent, data) {
    if (!data) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(data.flag_reads_threshold);

    const msg = data.message_reads_threshold || "";

    div.innerHTML = `
        <details open>
            <summary>Screening Threshold</summary>
            <div class="content">
                <p class="summary-message">${msg}</p>
                <ul class="summary-metrics">
                    <li>Total samples in data.json: ${fmtInt(data.n_samples_total)}</li>
                    <li>Samples above threshold: ${fmtInt(data.n_samples_above_threshold)} (${fmtFloat(data.percent_above_threshold, 1)}%)</li>
                    <li>Read threshold used: ${fmtInt(data.reads_threshold)} reads</li>
                </ul>
            </div>
        </details>
    `;
    parent.appendChild(div);
}

function addSequencingDepthSection(parent, data, depthPerSample) {
    if (!data) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(data.flag_sequencing_depth);

    const msg = data.message_sequencing_depth || "";

    div.innerHTML = `
        <details>
            <summary>Sequencing Depth</summary>
            <div class="content">
                <p class="summary-message">${msg}</p>
                <div class="seq-depth-stats">
                    <div class="seq-depth-stat-item">
                        <div class="seq-depth-stat-label">Mean depth</div>
                        <div class="seq-depth-stat-value">${fmtMillions(data.mean_reads)}</div>
                        <div class="seq-depth-stat-note">Average reads per sample</div>
                    </div>
                    <div class="seq-depth-stat-item">
                        <div class="seq-depth-stat-label">Median depth</div>
                        <div class="seq-depth-stat-value">${fmtMillions(data.median_reads)}</div>
                        <div class="seq-depth-stat-note">Median reads per sample</div>
                    </div>
                    <div class="seq-depth-stat-item">
                        <div class="seq-depth-stat-label">Variation</div>
                        <div class="seq-depth-stat-value">${fmtFloat(data.cv_reads, 3)}</div>
                        <div class="seq-depth-stat-note">Coefficient of variation (CV)</div>
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

    // Logical drawing size (viewBox); SVG will scale to full width via CSS.
    const width = 1000;
    const height = 320;
    const margin = {left: 60, right: 20, top: 20, bottom: 80};
    const plotW = width - margin.left - margin.right;
    const plotH = height - margin.top - margin.bottom;
    const svgns = "http://www.w3.org/2000/svg";

    // Determine max depth for scaling
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

    // Axes
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

    // Y ticks
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

    // Axis labels
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

    // Shared tooltip
    const tooltip = getOrCreateTooltip();

    // Bars
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

    // Median line only (mean removed as requested)
    const medianDepth = Number(data.median_reads) || 0;

    function addHorizontalLine(val, color, dash, labelText) {
        const y = yForValue(val);
        const line = document.createElementNS(svgns, "line");
        line.setAttribute("x1", x0);
        line.setAttribute("y1", y);
        line.setAttribute("x2", x0 + plotW);
        line.setAttribute("y2", y);
        line.setAttribute("stroke", color);
        line.setAttribute("stroke-width", "1.2");
        line.setAttribute("stroke-dasharray", dash);
        svg.appendChild(line);

        const lab = document.createElementNS(svgns, "text");
        lab.setAttribute("x", x0 + plotW - 4);
        lab.setAttribute("y", y - 2);
        lab.setAttribute("font-size", "10");
        lab.setAttribute("text-anchor", "end");
        lab.setAttribute("fill", color);
        lab.textContent = `${labelText} (${fmtMillions(val)})`;
        svg.appendChild(lab);
    }

    if (medianDepth > 0) {
        addHorizontalLine(medianDepth, "#43a047", "3,2", "median");
    }
}

function addLowQualitySection(parent, data) {
    if (!data) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(data.flag_low_quality);

    const msg = data.message_low_quality || "";

    div.innerHTML = `
        <details>
            <summary>Low-quality Reads (fastp)</summary>
            <div class="content">
                <p class="summary-message">${msg}</p>
                <ul class="summary-metrics">
                    <li>Samples with fastp metrics: ${fmtInt(data.n_samples)}</li>
                    <li>Total reads across these samples: ${fmtMillions(data.total_reads)}</li>
                    <li>Total reads removed: ${fmtMillions(data.total_removed_reads)}</li>
                    <li>Overall fraction removed: ${fmtFloat(data.percent_removed_reads_overall, 3)}%</li>
                    <li>Mean fraction removed per sample: ${fmtFloat(100*data.mean_fraction_removed, 2)}%</li>
                    <li>Median fraction removed per sample: ${fmtFloat(100*data.median_fraction_removed, 2)}%</li>
                </ul>
            </div>
        </details>
    `;
    parent.appendChild(div);
}

function addProkFractionSection(parent, data, depthPerSample) {
    if (!data) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(data.flag_prokaryotic_fraction);

    const msg = data.message_prokaryotic_fraction || "";

    div.innerHTML = `
        <details>
            <summary>Prokaryotic Fraction (SingleM & depth components)</summary>
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

    // Axes
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

    // Y ticks (0–100%)
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

    // Dashed median line for prokaryotic fraction (as fraction 0–1)
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

function addRedundancyReadsSection(parent, data, depthPerSample, redBiplotPerSample) {
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
            <summary>Redundancy (Reads, Nonpareil)</summary>
            <div class="content">
                <p class="summary-message">${msg}</p>
                <div class="redundancy-stats">
                    <div class="redundancy-stat-item">
                        <div class="redundancy-stat-label">Mean kappa_total</div>
                        <div class="redundancy-stat-value">${fmtFloat(data.mean_kappa_total, 3)}</div>
                        <div class="redundancy-stat-note">Average Nonpareil redundancy estimate</div>
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
                <ul class="summary-metrics">
                    <li>Samples with kappa estimates: ${fmtInt(data.n_samples_kappa)}</li>
                    <li>Median kappa_total: ${fmtFloat(data.median_kappa_total, 3)}</li>
                    <li>Standard deviation of kappa_total: ${fmtFloat(data.sd_kappa_total, 3)}</li>
                    <li>Samples where LR_reads &gt; observed depth: ${fmtInt(data.n_samples_lr_exceeds_depth)}</li>
                    <li>LR target used (if any): ${data.lr_target_used || "NA"}%</li>
                </ul>
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
    const depthBySample = {};
    (depthPerSample || []).forEach(d => {
        depthBySample[d.sample] = d;
    });

    const combined = (redBiplotPerSample || []).map(r => {
        const name = r.sample;
        const depthRec = depthBySample[name];
        const observed = depthRec && depthRec.total_reads != null ? Number(depthRec.total_reads) : null;
        let target = null;
        if (r.target_reads_95_LR_reads != null) {
            target = Number(r.target_reads_95_LR_reads);
        } else if (depthRec && depthRec.target_reads_95_LR_reads != null) {
            target = Number(depthRec.target_reads_95_LR_reads);
        }
        let ratio = null;
        if (observed != null && target && target > 0) {
            ratio = observed / target;
        }
        return {
            sample: name,
            observed,
            target,
            ratio
        };
    }).filter(d => d.ratio != null);

    if (!combined.length) {
        svg.outerHTML = `<div class="small-note">No per-sample LR_reads and depth information available to compare against LR targets.</div>`;
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
    const baselineY = yTop + plotH / 2; // 0 (1×) in the middle

    // Transform ratio -> signed value v:
    //  - ratio >= 1: v = ratio - 1  (times extra)
    //  - ratio < 1:  v = -(1/ratio - 1)  (negative, times missing)
    function transformRatio(r) {
        if (r >= 1) return r - 1;
        return -(1 / r - 1);
    }

    // Inverse transform for tick labels: v -> ratio
    function inverseTransform(v) {
        if (v >= 0) return 1 + v;
        return 1 / (1 - v);
    }

    const values = combined.map(d => transformRatio(d.ratio));
    let maxAbs = 0;
    values.forEach(v => {
        const a = Math.abs(v);
        if (a > maxAbs) maxAbs = a;
    });
    if (maxAbs <= 0) maxAbs = 1;

    // Add a bit of headroom
    maxAbs *= 1.1;

    function yForVal(v) {
        // v in [-maxAbs, maxAbs], baseline at 0 -> baselineY
        const f = v / maxAbs;
        return baselineY - f * (plotH / 2);
    }

    // Axes
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

    // Baseline (1× target) in the middle, red dashed
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

    // Y ticks symmetrically around 0 (baseline), integer v from -ceil(maxAbs) to +ceil(maxAbs)
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

        const ratio = inverseTransform(v);
        let labelStr;
        if (Math.abs(ratio - 1) < 1e-6) {
            labelStr = "1×";
        } else {
            labelStr = ratio.toFixed(1) + "×";
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
            // Above baseline
            yRect = yVal;
            hRect = baselineY - yVal;
        } else {
            // Below baseline
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

function addRedundancyMarkersSection(parent, data) {
    if (!data) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(data.flag_redundancy_markers);

    const msg = data.message_redundancy_markers || "";

    div.innerHTML = `
        <details>
            <summary>Redundancy (Marker genes, Nonpareil)</summary>
            <div class="content">
                <p class="summary-message">${msg}</p>
                <ul class="summary-metrics">
                    <li>Samples with kappa estimates: ${fmtInt(data.n_samples_kappa)}</li>
                    <li>Mean kappa_total: ${fmtFloat(data.mean_kappa_total, 3)}</li>
                    <li>Median kappa_total: ${fmtFloat(data.median_kappa_total, 3)}</li>
                    <li>Standard deviation: ${fmtFloat(data.sd_kappa_total, 3)}</li>
                    <li>CV of kappa_total: ${fmtFloat(data.cv_kappa_total, 3)}</li>
                    <li>Samples with LR_reads target: ${fmtInt(data.n_samples_with_lr)}</li>
                    <li>Samples where LR_reads &gt; observed depth: ${fmtInt(data.n_samples_lr_exceeds_depth)}</li>
                    <li>LR target used (if any): ${data.lr_target_used || "NA"}%</li>
                </ul>
            </div>
        </details>
    `;
    parent.appendChild(div);
}

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
            <summary>Sample Clusters (Mash-based)</summary>
            <div class="content">
                <p class="summary-message">${msg}</p>
                <ul class="summary-metrics">
                    <li>Marker-based clusters: ${nClustersMarkers}</li>
                    <li>Read-based clusters: ${nClustersReads}</li>
                </ul>
                <p class="small-note">
                    Cluster assignments and distances are available in the JSON output and can be explored programmatically.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);
}

/* ---------- Figures: redundancy biplot ---------- */

function addFigureRedundancyBiplot(parent, fig) {
    if (!fig) return;
    const data = (fig.per_sample || []).filter(d =>
        d.kappa_reads !== null && d.kappa_reads !== undefined &&
        d.kappa_markers !== null && d.kappa_markers !== undefined
    );
    if (!data.length) return;

    const div = document.createElement("div");
    div.className = "section";

    div.innerHTML = `
        <details open>
            <summary>Redundancy Biplot (Nonpareil kappa)</summary>
            <div class="figure-container">
                <div class="biplot-container">
                    <svg id="biplot-svg" class="biplot-svg" width="380" height="380"></svg>
                </div>
                <p class="small-note">
                    Scatterplot of read-based vs marker-based Nonpareil kappa_total.
                    Points are samples (hover for sample names). Axes are fixed to [0, 1].
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const svg = div.querySelector("#biplot-svg");
    const w = 380, h = 380;
    const margin = {left: 50, right: 10, top: 20, bottom: 40};
    const plotW = w - margin.left - margin.right;
    const plotH = h - margin.top - margin.bottom;

    const svgns = "http://www.w3.org/2000/svg";

    const x0 = margin.left;
    const y0 = h - margin.bottom;
    const x1 = margin.left + plotW;
    const y1 = margin.top;

    const xAxis = document.createElementNS(svgns, "line");
    xAxis.setAttribute("x1", x0);
    xAxis.setAttribute("y1", y0);
    xAxis.setAttribute("x2", x1);
    xAxis.setAttribute("y2", y0);
    xAxis.setAttribute("stroke", "#555");
    svg.appendChild(xAxis);

    const yAxis = document.createElementNS(svgns, "line");
    yAxis.setAttribute("x1", x0);
    yAxis.setAttribute("y1", y0);
    yAxis.setAttribute("x2", x0);
    yAxis.setAttribute("y2", y1);
    yAxis.setAttribute("stroke", "#555");
    svg.appendChild(yAxis);

    const xlabel = document.createElementNS(svgns, "text");
    xlabel.setAttribute("x", margin.left + plotW / 2);
    xlabel.setAttribute("y", h - 8);
    xlabel.setAttribute("text-anchor", "middle");
    xlabel.setAttribute("font-size", "11");
    xlabel.textContent = "kappa_total (reads)";
    svg.appendChild(xlabel);

    const ylabel = document.createElementNS(svgns, "text");
    ylabel.setAttribute("x", 14);
    ylabel.setAttribute("y", margin.top + plotH / 2);
    ylabel.setAttribute("text-anchor", "middle");
    ylabel.setAttribute("font-size", "11");
    ylabel.setAttribute("transform", `rotate(-90 14 ${margin.top + plotH / 2})`);
    ylabel.textContent = "kappa_total (markers)";
    svg.appendChild(ylabel);

    [0.5, 1.0].forEach(t => {
        const xt = x0 + t * plotW;
        const yt = y0 - t * plotH;

        const xtick = document.createElementNS(svgns, "line");
        xtick.setAttribute("x1", xt);
        xtick.setAttribute("y1", y0);
        xtick.setAttribute("x2", xt);
        xtick.setAttribute("y2", y0 + 4);
        xtick.setAttribute("stroke", "#555");
        svg.appendChild(xtick);

        const xtlab = document.createElementNS(svgns, "text");
        xtlab.setAttribute("x", xt);
        xtlab.setAttribute("y", y0 + 15);
        xtlab.setAttribute("font-size", "10");
        xtlab.setAttribute("text-anchor", "middle");
        xtlab.textContent = t.toFixed(1);
        svg.appendChild(xtlab);

        const ytick = document.createElementNS(svgns, "line");
        ytick.setAttribute("x1", x0 - 4);
        ytick.setAttribute("y1", yt);
        ytick.setAttribute("x2", x0);
        ytick.setAttribute("y2", yt);
        ytick.setAttribute("stroke", "#555");
        svg.appendChild(ytick);

        const ytlab = document.createElementNS(svgns, "text");
        ytlab.setAttribute("x", x0 - 7);
        ytlab.setAttribute("y", yt + 3);
        ytlab.setAttribute("font-size", "10");
        ytlab.setAttribute("text-anchor", "end");
        ytlab.textContent = t.toFixed(1);
        svg.appendChild(ytlab);
    });

    data.forEach(d => {
        const xr = Number(d.kappa_reads);
        const yr = Number(d.kappa_markers);
        if (!isFinite(xr) || !isFinite(yr)) return;

        const cx = x0 + Math.max(0, Math.min(1, xr)) * plotW;
        const cy = y0 - Math.max(0, Math.min(1, yr)) * plotH;

        const circle = document.createElementNS(svgns, "circle");
        circle.setAttribute("cx", cx);
        circle.setAttribute("cy", cy);
        circle.setAttribute("r", 4);
        circle.setAttribute("fill", "#1976d2");
        circle.setAttribute("fill-opacity", "0.8");

        const title = document.createElementNS(svgns, "title");
        title.textContent =
            `${d.sample}\n` +
            `kappa_reads = ${xr.toFixed(3)}\n` +
            `kappa_markers = ${yr.toFixed(3)}`;
        circle.appendChild(title);

        svg.appendChild(circle);
    });
}

/* ---------- Main ---------- */

function main() {
    const distill = DISTILL_DATA;
    const figures = FIGURES_DATA;

    const summaryDiv = document.getElementById("summary-sections");
    const figureDiv = document.getElementById("figure-sections");

    const S = distill.summary || {};

    const depthFig = figures.figures && figures.figures.dna_depth_fractions
        ? figures.figures.dna_depth_fractions
        : null;
    const depthPerSample = depthFig ? (depthFig.per_sample || []) : [];

    const redBiplot = figures.figures && figures.figures.redundancy_biplot
        ? figures.figures.redundancy_biplot
        : null;
    const redBiplotPerSample = redBiplot ? (redBiplot.per_sample || []) : [];

    addScreeningSection(summaryDiv, S.screening_threshold);
    addSequencingDepthSection(summaryDiv, S.sequencing_depth, depthPerSample);
    addLowQualitySection(summaryDiv, S.low_quality_reads);
    addProkFractionSection(summaryDiv, S.prokaryotic_fraction, depthPerSample);
    addRedundancyReadsSection(summaryDiv, S.redundancy_reads, depthPerSample, redBiplotPerSample);
    addRedundancyMarkersSection(summaryDiv, S.redundancy_markers);
    addClustersSection(summaryDiv, S.clusters);

    // Figures section: keep the biplot here
    if (redBiplot) {
        addFigureRedundancyBiplot(figureDiv, redBiplot);
    }
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
        help="Path to figures.json (figure-friendly data, e.g. depth fractions, redundancy biplot).",
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
