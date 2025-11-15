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

    /* Depth fractions figure */
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
    .seg-other  { background: #2196f3; }  /* blue */

    .depth-table {
        max-height: 350px;
        overflow-y: auto;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 4px 6px;
        background: #fcfcfc;
    }
    .depth-row {
        display: flex;
        align-items: center;
        padding: 3px 0;
        font-size: 0.9em;
    }
    .depth-label {
        width: 120px;
        flex-shrink: 0;
        font-weight: 500;
    }
    .depth-bar-wrapper {
        flex: 1;
        margin: 0 8px;
    }
    .depth-bar {
        position: relative;
        height: 12px;
        width: 100%;
        background: #eee;
        border-radius: 6px;
        overflow: hidden;
    }
    .depth-bar-seg {
        height: 100%;
        display: inline-block;
    }
    .depth-info {
        width: 200px;
        flex-shrink: 0;
        font-size: 0.8em;
        text-align: right;
    }

    /* Redundancy biplot */
    .biplot-container {
        overflow-x: auto;
    }
    .biplot-svg {
        border: 1px solid #ddd;
        background: #fcfcfc;
    }

    /* Sequencing depth barplot */
    .seq-depth-stats {
        display: flex;
        gap: 16px;
        justify-content: space-between;
        margin-bottom: 10px;
        flex-wrap: wrap;
    }
    .seq-depth-stat-item {
        flex: 1;
        min-width: 160px;
    }
    .seq-depth-stat-label {
        font-size: 0.9em;
        color: #555;
        margin-bottom: 2px;
    }
    .seq-depth-stat-value {
        font-size: 1.4em;
        font-weight: 600;
    }
    .seq-depth-stat-note {
        font-size: 0.8em;
        color: #666;
        margin-top: 2px;
    }

    .seq-depth-plot-container {
        overflow-x: auto;
        border: 1px solid #ddd;
        border-radius: 4px;
        background: #fcfcfc;
        padding: 4px 4px 0 4px;
    }
    .seq-depth-svg {
        display: block;
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

    // container with stats + plot placeholder
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
                    <svg id="seq-depth-svg" class="seq-depth-svg" width="600" height="320"></svg>
                </div>
                <p class="small-note">
                    X axis: samples; Y axis: sequencing depth in reads. Bars show per-sample total read counts.
                    Horizontal dashed lines indicate mean and median sequencing depth across samples.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    // Build barplot using depthPerSample (from figures.json)
    const svg = div.querySelector("#seq-depth-svg");
    const perSample = (depthPerSample || [])
        .filter(d => d.total_reads !== null && d.total_reads !== undefined);

    if (!perSample.length) {
        // show message in place of the plot
        const msgNode = document.createElement("text");
        msgNode.textContent = "Per-sample read counts not available for barplot.";
        // quick hack: use foreignObject-like display via innerHTML
        svg.outerHTML = `<div class="small-note">Per-sample read counts not available for sequencing depth barplot.</div>`;
        return;
    }

    // If many samples, make SVG wider; container will scroll horizontally
    const n = perSample.length;
    const margin = {left: 60, right: 10, top: 20, bottom: 80};
    const baseWidth = 400;
    const barWidth = 14;
    const minPlotWidth = n * (barWidth + 4);
    const width = Math.max(baseWidth, margin.left + margin.right + minPlotWidth);
    const height = 320;
    svg.setAttribute("width", width);
    svg.setAttribute("height", height);

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

    // y-scale: 0..maxDepth maps to bottom..top
    const x0 = margin.left;
    const y0 = height - margin.bottom;

    function yForValue(v) {
        const ratio = Math.max(0, Math.min(1, v / maxDepth));
        return y0 - ratio * plotH;
    }

    // Draw axes
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

    // Y-ticks at 0, 25, 50, 75, 100% of max
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

    // Bars
    const step = plotW / n;
    const barActualWidth = Math.min(barWidth, step * 0.8);

    perSample.forEach((d, i) => {
        const val = Number(d.total_reads) || 0;
        const xCenter = x0 + step * i + step / 2;
        const x = xCenter - barActualWidth / 2;
        const y = yForValue(val);
        const hBar = y0 - y;

        const rect = document.createElementNS(svgns, "rect");
        rect.setAttribute("x", x);
        rect.setAttribute("y", y);
        rect.setAttribute("width", barActualWidth);
        rect.setAttribute("height", hBar);
        rect.setAttribute("fill", "#1976d2");
        rect.setAttribute("fill-opacity", "0.85");

        const title = document.createElementNS(svgns, "title");
        title.textContent = `${d.sample}\n${fmtMillions(val)} reads`;
        rect.appendChild(title);

        svg.appendChild(rect);

        // Sample labels: only show if not too many samples, or every 5th one
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

    // Mean & median lines (from distill section data)
    const meanDepth = Number(data.mean_reads) || 0;
    const medianDepth = Number(data.median_reads) || 0;

    function addHorizontalLine(val, color, dash, labelText, dx) {
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
        lab.setAttribute("x", x0 + plotW + (dx || 0));
        lab.setAttribute("y", y - 2);
        lab.setAttribute("font-size", "10");
        lab.setAttribute("text-anchor", "end");
        lab.setAttribute("fill", color);
        lab.textContent = `${labelText} (${fmtMillions(val)})`;
        svg.appendChild(lab);
    }

    if (meanDepth > 0) {
        addHorizontalLine(meanDepth, "#e53935", "4,2", "mean", -2);
    }
    if (medianDepth > 0) {
        addHorizontalLine(medianDepth, "#43a047", "3,2", "median", -2);
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

function addProkFractionSection(parent, data) {
    if (!data) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(data.flag_prokaryotic_fraction);

    const msg = data.message_prokaryotic_fraction || "";

    div.innerHTML = `
        <details>
            <summary>Prokaryotic Fraction (SingleM)</summary>
            <div class="content">
                <p class="summary-message">${msg}</p>
                <ul class="summary-metrics">
                    <li>Samples with SingleM estimates: ${fmtInt(data.n_samples)}</li>
                    <li>Mean prokaryotic fraction: ${fmtFloat(data.mean_prokaryotic_fraction, 2)}%</li>
                    <li>Median prokaryotic fraction: ${fmtFloat(data.median_prokaryotic_fraction, 2)}%</li>
                    <li>Standard deviation: ${fmtFloat(data.sd_prokaryotic_fraction, 2)}</li>
                    <li>Coefficient of variation (CV): ${fmtFloat(data.cv_prokaryotic_fraction, 3)}</li>
                    <li>Samples with warnings: ${fmtInt(data.n_warnings)}</li>
                </ul>
            </div>
        </details>
    `;
    parent.appendChild(div);
}

function addRedundancyReadsSection(parent, data) {
    if (!data) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(data.flag_redundancy);

    const msg = data.message_redundancy || "";

    div.innerHTML = `
        <details>
            <summary>Redundancy (Reads, Nonpareil)</summary>
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

/* ---------- Figures: depth fractions ---------- */

function addFigureDepthFractions(parent, fig) {
    if (!fig) return;
    const data = fig.per_sample || [];
    if (!data.length) return;

    const div = document.createElement("div");
    div.className = "section";

    div.innerHTML = `
        <details open>
            <summary>Sequencing Depth Components</summary>
            <div class="figure-container">
                <div class="depth-legend">
                    <span class="box seg-lowq"></span> low-quality &nbsp;
                    <span class="box seg-prok"></span> prokaryotic &nbsp;
                    <span class="box seg-other"></span> other (non-prokaryotic, QC-passing)
                </div>
                <div id="depth-bars" class="depth-table"></div>
                <p class="small-note">
                    Bars show per-sample relative contributions of low-quality reads, prokaryotic reads, "
                    and other QC-passing reads. Tooltip values and right-hand text give approximate counts.
                    Nonpareil 95% LR_reads thresholds are indicated in text for use as dashed horizontal
                    lines in custom plots.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const container = div.querySelector("#depth-bars");

    const maxSamples = 50; // keep UI manageable
    const rows = data.slice(0, maxSamples);
    const truncated = data.length > maxSamples;

    rows.forEach(d => {
        const row = document.createElement("div");
        row.className = "depth-row";

        const fracLow = d.fraction_low_quality_of_total || 0;
        const fracProk = d.fraction_prokaryotic_of_total || 0;
        const fracOther = d.fraction_non_prokaryotic_of_total || 0;

        const lowPct = (100 * fracLow).toFixed(2);
        const prokPct = (100 * fracProk).toFixed(2);
        const otherPct = (100 * fracOther).toFixed(2);

        const totalReads = d.total_reads;
        const targetReads95 = d.target_reads_95_LR_reads;

        row.innerHTML = `
            <div class="depth-label">${d.sample}</div>
            <div class="depth-bar-wrapper">
                <div class="depth-bar" title="Low-Q: ${lowPct}%, Prok: ${prokPct}%, Other: ${otherPct}%">
                    <span class="depth-bar-seg seg-lowq" style="width: ${lowPct}%;"></span>
                    <span class="depth-bar-seg seg-prok" style="width: ${prokPct}%;"></span>
                    <span class="depth-bar-seg seg-other" style="width: ${otherPct}%;"></span>
                </div>
            </div>
            <div class="depth-info">
                ${fmtMillions(totalReads)} reads<br/>
                95% LR (reads): ${fmtMillions(targetReads95)}
            </div>
        `;
        container.appendChild(row);
    });

    if (truncated) {
        const note = document.createElement("div");
        note.className = "small-note";
        note.textContent = `Showing first ${maxSamples} samples of ${data.length}.`;
        container.appendChild(note);
    }
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

    addScreeningSection(summaryDiv, S.screening_threshold);
    addSequencingDepthSection(summaryDiv, S.sequencing_depth, depthPerSample);
    addLowQualitySection(summaryDiv, S.low_quality_reads);
    addProkFractionSection(summaryDiv, S.prokaryotic_fraction);
    addRedundancyReadsSection(summaryDiv, S.redundancy_reads);
    addRedundancyMarkersSection(summaryDiv, S.redundancy_markers);
    addClustersSection(summaryDiv, S.clusters);

    if (figures.figures && figures.figures.dna_depth_fractions) {
        addFigureDepthFractions(figureDiv, figures.figures.dna_depth_fractions);
    }
    if (figures.figures && figures.figures.redundancy_biplot) {
        addFigureRedundancyBiplot(figureDiv, figures.figures.redundancy_biplot);
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
