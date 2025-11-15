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

    .section-title {
        margin: 2px 0 4px 0;
        font-size: 1.25em;
    }

    .section-intro {
        margin: 0 0 8px 0;
        font-size: 0.9em;
        color: #555;
    }

    .small-note {
        font-size: 0.85em;
        color: #666;
        margin: 6px 0 10px 0;
    }

    details {
        margin-top: 4px;
    }

    summary {
        cursor: pointer;
        font-weight: bold;
        list-style: none;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    summary::-webkit-details-marker {
        display: none;
    }

    .content {
        margin-top: 8px;
    }

    .summary-message {
        font-size: 0.9em;
        line-height: 1.4;
        margin-bottom: 10px;
    }

    .flag-1 {
        background-color: #e8f5e9;
        border-color: #c8e6c9;
    }

    .flag-2 {
        background-color: #fffde7;
        border-color: #fff9c4;
    }

    .flag-3 {
        background-color: #ffebee;
        border-color: #ffcdd2;
    }

    .status-emoji {
        font-size: 1.2em;
    }

    .status-text {
        font-size: 0.95em;
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
        flex: 1 1 180px;
        min-width: 180px;
        background: #f9f9f9;
        border-radius: 6px;
        padding: 8px 10px;
        border: 1px solid #e0e0e0;
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
        color: #777;
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

    .pairwise-container {
        margin-top: 14px;
    }
    .pairwise-tabs {
        display: inline-flex;
        border-radius: 999px;
        overflow: hidden;
        border: 1px solid #ccc;
        margin-bottom: 8px;
    }
    .pairwise-tab {
        border: none;
        padding: 4px 12px;
        font-size: 0.85em;
        cursor: pointer;
        background: #f0f0f0;
        color: #444;
    }
    .pairwise-tab.active {
        background: #1976d2;
        color: #fff;
    }
    .pairwise-heatmap {
        width: 100%;
        overflow-x: auto;
        border: 1px solid #ddd;
        border-radius: 4px;
        background: #fcfcfc;
        padding: 6px 6px 2px 6px;
        box-sizing: border-box;
        margin-top: 8px;
    }

    .chart-tooltip {
        position: fixed;
        pointer-events: none;
        background: rgba(0,0,0,0.85);
        color: #fff;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8em;
        z-index: 9999;
        white-space: pre;
    }
</style>

</head>
<body>

<h1>ScreenM Summary Report</h1>

<div id="global-overview" class="screen-overview-stats"></div>

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

function fmtPercent(x, digits) {
    if (x === null || x === undefined) return "NA";
    return Number(x).toFixed(digits) + "%";
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

/* ---------- Global overview (top) ---------- */
function addGlobalOverview(distill, figures) {
    const container = document.getElementById("global-overview");
    if (!container) return;

    const meta = distill.meta || {};
    const nSamples = meta.n_samples_in_results != null ? meta.n_samples_in_results : null;

    let totalReadsAll = null;
    try {
        const depthFig = figures.figures && figures.figures.dna_depth_fractions
            ? figures.figures.dna_depth_fractions
            : null;
        const perSample = depthFig ? (depthFig.per_sample || []) : [];
        let total = 0;
        perSample.forEach(d => {
            if (!d) return;
            if (d.total_reads != null) {
                const v = Number(d.total_reads);
                if (!isNaN(v)) total += v;
            }
        });
        totalReadsAll = total;
    } catch (e) {
        totalReadsAll = null;
    }

    container.innerHTML = `
        <div class="screen-overview-stat-item">
            <div class="screen-overview-stat-label">Samples</div>
            <div class="screen-overview-stat-value">${fmtInt(nSamples)}</div>
            <div class="screen-overview-stat-note">Samples with results</div>
        </div>
        <div class="screen-overview-stat-item">
            <div class="screen-overview-stat-label">Total reads</div>
            <div class="screen-overview-stat-value">${fmtMillions(totalReadsAll)}</div>
            <div class="screen-overview-stat-note">Sum of per-sample read counts</div>
        </div>
    `;
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
                    X axis: samples; Y axis: sequencing depth in reads. Bars show per-sample total read counts,
                    and a dashed line marks the read threshold used for screening.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const svg = div.querySelector("#seq-depth-svg");
    const svgns = "http://www.w3.org/2000/svg";
    const tooltip = getOrCreateTooltip();

    const samples = depthPerSample.map(d => d.sample);
    const reads   = depthPerSample.map(d => d.total_reads);

    if (!samples.length) {
        svg.outerHTML = `<div class="small-note">Sequencing depths per sample not available.</div>`;
        return;
    }

    const width = 1000;
    const height = 320;
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

    const marginLeft = 70;
    const marginRight = 20;
    const marginTop = 20;
    const marginBottom = 80;

    const plotWidth = width - marginLeft - marginRight;
    const plotHeight = height - marginTop - marginBottom;

    const maxY = Math.max(...reads, thr || 0);
    const yMax = maxY * 1.05;

    function xScale(i) {
        const n = samples.length;
        return marginLeft + (i + 0.5) * (plotWidth / n);
    }

    function yScale(val) {
        return marginTop + plotHeight - (val / yMax) * plotHeight;
    }

    const axisY = document.createElementNS(svgns, "line");
    axisY.setAttribute("x1", marginLeft);
    axisY.setAttribute("y1", marginTop);
    axisY.setAttribute("x2", marginLeft);
    axisY.setAttribute("y2", marginTop + plotHeight);
    axisY.setAttribute("stroke", "#333");
    axisY.setAttribute("stroke-width", "1");
    svg.appendChild(axisY);

    const axisX = document.createElementNS(svgns, "line");
    axisX.setAttribute("x1", marginLeft);
    axisX.setAttribute("y1", marginTop + plotHeight);
    axisX.setAttribute("x2", marginLeft + plotWidth);
    axisX.setAttribute("y2", marginTop + plotHeight);
    axisX.setAttribute("stroke", "#333");
    axisX.setAttribute("stroke-width", "1");
    svg.appendChild(axisX);

    const nTicks = 5;
    for (let t = 0; t <= nTicks; t++) {
        const val = (t / nTicks) * yMax;
        const y = yScale(val);

        const tick = document.createElementNS(svgns, "line");
        tick.setAttribute("x1", marginLeft - 5);
        tick.setAttribute("y1", y);
        tick.setAttribute("x2", marginLeft);
        tick.setAttribute("y2", y);
        tick.setAttribute("stroke", "#333");
        svg.appendChild(tick);

        const label = document.createElementNS(svgns, "text");
        label.setAttribute("x", marginLeft - 8);
        label.setAttribute("y", y + 3);
        label.setAttribute("text-anchor", "end");
        label.setAttribute("font-size", "10");
        label.textContent = fmtMillions(val);
        svg.appendChild(label);
    }

    if (thr != null) {
        const yThr = yScale(thr);
        const line = document.createElementNS(svgns, "line");
        line.setAttribute("x1", marginLeft);
        line.setAttribute("y1", yThr);
        line.setAttribute("x2", marginLeft + plotWidth);
        line.setAttribute("y2", yThr);
        line.setAttribute("stroke", "#d32f2f");
        line.setAttribute("stroke-width", "1.5");
        line.setAttribute("stroke-dasharray", "4,3");
        svg.appendChild(line);
    }

    const n = samples.length;
    const barWidth = (plotWidth / n) * 0.7;

    reads.forEach((val, i) => {
        const xCenter = xScale(i);
        const x0 = xCenter - barWidth / 2;
        const y0 = yScale(val);
        const bar = document.createElementNS(svgns, "rect");
        bar.setAttribute("x", x0);
        bar.setAttribute("y", y0);
        bar.setAttribute("width", barWidth);
        bar.setAttribute("height", (marginTop + plotHeight) - y0);
        bar.setAttribute("fill", "#90caf9");
        bar.setAttribute("stroke", "#1976d2");
        bar.setAttribute("stroke-width", "0.5");
        bar.style.cursor = "pointer";

        const tooltipText = `${samples[i]}\nReads: ${fmtMillions(val)}`;

        bar.addEventListener("mouseenter", (evt) => {
            bar.setAttribute("fill", "#64b5f6");
            tooltip.style.display = "block";
            tooltip.textContent = tooltipText;
            tooltip.style.left = evt.clientX + "px";
            tooltip.style.top = evt.clientY + "px";
        });
        bar.addEventListener("mousemove", (evt) => {
            tooltip.style.left = evt.clientX + "px";
            tooltip.style.top = evt.clientY + "px";
        });
        bar.addEventListener("mouseleave", () => {
            bar.setAttribute("fill", "#90caf9");
            tooltip.style.display = "none";
        });

        svg.appendChild(bar);
    });

    const showAll = n <= 40;
    samples.forEach((s, i) => {
        const show = showAll || (i % 5 === 0);
        if (!show) return;
        const x = xScale(i);
        const y = marginTop + plotHeight + 55;
        const text = document.createElementNS(svgns, "text");
        text.setAttribute("x", x);
        text.setAttribute("y", y);
        text.setAttribute("font-size", "9");
        text.setAttribute("text-anchor", "end");
        text.setAttribute("transform", `rotate(-60 ${x} ${y})`);
        text.textContent = s;
        svg.appendChild(text);
    });

    const yLabel = document.createElementNS(svgns, "text");
    yLabel.setAttribute("x", 14);
    yLabel.setAttribute("y", marginTop + plotHeight / 2);
    yLabel.setAttribute("font-size", "10");
    yLabel.setAttribute("transform", `rotate(-90 14 ${marginTop + plotHeight / 2})`);
    yLabel.textContent = "Reads";
    svg.appendChild(yLabel);
}

/* ---------- Sequencing quality (low-quality reads) ---------- */
function addLowQualitySection(parent, data, depthPerSample) {
    if (!data) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(data.flag_low_quality);

    const msg = data.message_low_quality || "";

    const meanFrac = data.mean_fraction_removed;
    const medianFrac = data.median_fraction_removed;

    const status = sectionStatus("Sequencing quality", data.flag_low_quality);

    div.innerHTML = `
        <h2 class="section-title">Sequencing quality</h2>
        <p class="section-intro">
            This section summarises the fraction of reads removed by quality filtering and how this varies across samples.
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
                        <div class="quality-stat-label">Mean removed fraction</div>
                        <div class="quality-stat-value">${fmtPercent(meanFrac * 100, 1)}</div>
                        <div class="quality-stat-note">Average across samples</div>
                    </div>
                    <div class="quality-stat-item">
                        <div class="quality-stat-label">Median removed fraction</div>
                        <div class="quality-stat-value">${fmtPercent(medianFrac * 100, 1)}</div>
                        <div class="quality-stat-note">Typical sample</div>
                    </div>
                </div>
                <div class="quality-plot-container">
                    <svg id="quality-svg" class="quality-svg" viewBox="0 0 1000 320" preserveAspectRatio="none"></svg>
                </div>
                <p class="small-note">
                    X axis: samples; Y axis: percentage of reads removed by fastp (low quality, Ns, length/complexity filters).
                    A dashed yellow line marks 5% and a dashed red line marks 20% removal thresholds.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const svg = div.querySelector("#quality-svg");
    const svgns = "http://www.w3.org/2000/svg";
    const tooltip = getOrCreateTooltip();

    const samples = depthPerSample.map(d => d.sample);
    const removedFrac = depthPerSample.map(d =>
        (d.fraction_low_quality_of_total != null)
            ? d.fraction_low_quality_of_total
            : (d.removed_fraction_fastp != null ? d.removed_fraction_fastp : 0)
    );

    if (!samples.length) {
        svg.outerHTML = `<div class="small-note">Per-sample quality metrics not available.</div>`;
        return;
    }

    const width = 1000;
    const height = 320;
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

    const marginLeft = 70;
    const marginRight = 20;
    const marginTop = 20;
    const marginBottom = 80;

    const plotWidth = width - marginLeft - marginRight;
    const plotHeight = height - marginTop - marginBottom;

    const removedPct = removedFrac.map(v => v * 100);
    const maxY = Math.max(...removedPct, 20);
    const yMax = maxY * 1.1;

    function xScale(i) {
        const n = samples.length;
        return marginLeft + (i + 0.5) * (plotWidth / n);
    }
    function yScale(val) {
        return marginTop + plotHeight - (val / yMax) * plotHeight;
    }

    const axisY = document.createElementNS(svgns, "line");
    axisY.setAttribute("x1", marginLeft);
    axisY.setAttribute("y1", marginTop);
    axisY.setAttribute("x2", marginLeft);
    axisY.setAttribute("y2", marginTop + plotHeight);
    axisY.setAttribute("stroke", "#333");
    axisY.setAttribute("stroke-width", "1");
    svg.appendChild(axisY);

    const axisX = document.createElementNS(svgns, "line");
    axisX.setAttribute("x1", marginLeft);
    axisX.setAttribute("y1", marginTop + plotHeight);
    axisX.setAttribute("x2", marginLeft + plotWidth);
    axisX.setAttribute("y2", marginTop + plotHeight);
    axisX.setAttribute("stroke", "#333");
    axisX.setAttribute("stroke-width", "1");
    svg.appendChild(axisX);

    const nTicks = 5;
    for (let t = 0; t <= nTicks; t++) {
        const val = (t / nTicks) * yMax;
        const y = yScale(val);

        const tick = document.createElementNS(svgns, "line");
        tick.setAttribute("x1", marginLeft - 5);
        tick.setAttribute("y1", y);
        tick.setAttribute("x2", marginLeft);
        tick.setAttribute("y2", y);
        tick.setAttribute("stroke", "#333");
        svg.appendChild(tick);

        const label = document.createElementNS(svgns, "text");
        label.setAttribute("x", marginLeft - 8);
        label.setAttribute("y", y + 3);
        label.setAttribute("text-anchor", "end");
        label.setAttribute("font-size", "10");
        label.textContent = fmtFloat(val, 1) + "%";
        svg.appendChild(label);
    }

    const y5 = yScale(5);
    const line5 = document.createElementNS(svgns, "line");
    line5.setAttribute("x1", marginLeft);
    line5.setAttribute("y1", y5);
    line5.setAttribute("x2", marginLeft + plotWidth);
    line5.setAttribute("y2", y5);
    line5.setAttribute("stroke", "#f9a825");
    line5.setAttribute("stroke-width", "1.5");
    line5.setAttribute("stroke-dasharray", "4,3");
    svg.appendChild(line5);

    const y20 = yScale(20);
    const line20 = document.createElementNS(svgns, "line");
    line20.setAttribute("x1", marginLeft);
    line20.setAttribute("y1", y20);
    line20.setAttribute("x2", marginLeft + plotWidth);
    line20.setAttribute("y2", y20);
    line20.setAttribute("stroke", "#d32f2f");
    line20.setAttribute("stroke-width", "1.5");
    line20.setAttribute("stroke-dasharray", "4,3");
    svg.appendChild(line20);

    const n = samples.length;
    const barWidth = (plotWidth / n) * 0.7;

    removedPct.forEach((val, i) => {
        const xCenter = xScale(i);
        const x0 = xCenter - barWidth / 2;
        const y0 = yScale(val);
        const bar = document.createElementNS(svgns, "rect");
        bar.setAttribute("x", x0);
        bar.setAttribute("y", y0);
        bar.setAttribute("width", barWidth);
        bar.setAttribute("height", (marginTop + plotHeight) - y0);
        bar.setAttribute("fill", "#90caf9");
        bar.setAttribute("stroke", "#1976d2");
        bar.setAttribute("stroke-width", "0.5");
        bar.style.cursor = "pointer";

        const tooltipText = `${samples[i]}\nRemoved: ${fmtFloat(val, 1)}%`;

        bar.addEventListener("mouseenter", (evt) => {
            bar.setAttribute("fill", "#64b5f6");
            tooltip.style.display = "block";
            tooltip.textContent = tooltipText;
            tooltip.style.left = evt.clientX + "px";
            tooltip.style.top = evt.clientY + "px";
        });
        bar.addEventListener("mousemove", (evt) => {
            tooltip.style.left = evt.clientX + "px";
            tooltip.style.top = evt.clientY + "px";
        });
        bar.addEventListener("mouseleave", () => {
            bar.setAttribute("fill", "#90caf9");
            tooltip.style.display = "none";
        });

        svg.appendChild(bar);
    });

    const showAll = n <= 40;
    samples.forEach((s, i) => {
        const show = showAll || (i % 5 === 0);
        if (!show) return;
        const x = xScale(i);
        const y = marginTop + plotHeight + 55;
        const text = document.createElementNS(svgns, "text");
        text.setAttribute("x", x);
        text.setAttribute("y", y);
        text.setAttribute("font-size", "9");
        text.setAttribute("text-anchor", "end");
        text.setAttribute("transform", `rotate(-60 ${x} ${y})`);
        text.textContent = s;
        svg.appendChild(text);
    });

    const yLabel = document.createElementNS(svgns, "text");
    yLabel.setAttribute("x", 14);
    yLabel.setAttribute("y", marginTop + plotHeight / 2);
    yLabel.setAttribute("font-size", "10");
    yLabel.setAttribute("transform", `rotate(-90 14 ${marginTop + plotHeight / 2})`);
    yLabel.textContent = "% reads removed";
    svg.appendChild(yLabel);
}

/* ---------- Prokaryotic fraction & depth components ---------- */
/* (existing implementation here, unchanged from your current script) */

/* ---------- Redundancy (reads) ---------- */
/* (existing implementation here, unchanged from your current script) */

/* ---------- Redundancy (markers) ---------- */
/* (existing implementation here, unchanged from your current script) */

/* ---------- Sample clusters ---------- */
function addClustersSection(parent, clusters) {
    if (!clusters) return;
    const div = document.createElement("div");
    div.className = "section " + flagClass(clusters.flag_clusters);

    const msg = clusters.message_clusters || "";
    const markers = clusters.markers || {};
    const reads = clusters.reads || {};

    const nClustersMarkers = markers.n_clusters != null ? markers.n_clusters : "NA";
    const nClustersReads = reads.n_clusters != null ? reads.n_clusters : "NA";

    const markersWithin = markers.mean_within_distance;
    const markersBetween = markers.mean_between_distance;
    const readsWithin = reads.mean_within_distance;
    const readsBetween = reads.mean_between_distance;

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
                        <div class="cluster-stat-label">Marker mean distances</div>
                        <div class="cluster-stat-value">
                            ${fmtFloat(markersWithin, 3)} / ${fmtFloat(markersBetween, 3)}
                        </div>
                        <div class="cluster-stat-note">Within / between clusters (Mash markers)</div>
                    </div>
                    <div class="cluster-stat-item">
                        <div class="cluster-stat-label">Read mean distances</div>
                        <div class="cluster-stat-value">
                            ${fmtFloat(readsWithin, 3)} / ${fmtFloat(readsBetween, 3)}
                        </div>
                        <div class="cluster-stat-note">Within / between clusters (Mash reads)</div>
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
                <div class="pairwise-container">
                    <p class="small-note">
                        Pairwise Mash distances between samples can be inspected below, separately for marker-based and read-based estimates.
                    </p>
                    <div class="pairwise-tabs">
                        <button class="pairwise-tab active" data-kind="markers">Markers distances</button>
                        <button class="pairwise-tab" data-kind="reads">Reads distances</button>
                    </div>
                    <div id="pairwise-heatmap-markers" class="pairwise-heatmap"></div>
                    <div id="pairwise-heatmap-reads" class="pairwise-heatmap" style="display:none;"></div>
                </div>
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

    svg.setAttribute("viewBox", "0 0 1000 210");

    const width = 1000;
    const height = 210;
    const marginLeft = 90;
    const marginRight = 20;
    const marginTop = 18;
    const marginBottom = 70;
    const plotW = width - marginLeft - marginRight;
    const plotH = height - marginTop - marginBottom;

    const nRows = 2;
    const cellH = plotH / nRows;
    const nSamples = samples.length;

    function assignColours(map, palette) {
        const colourMap = {};
        let idx = 0;
        const clustersSeen = new Set(Object.values(map).filter(v => v !== null && v !== undefined));
        clustersSeen.forEach(clid => {
            colourMap[clid] = palette[idx % palette.length];
            idx += 1;
        });
        return colourMap;
    }

    const markerPalette = ["#08306b", "#08519c", "#2171b5", "#4292c6", "#6baed6", "#9ecae1", "#c6dbef"];
    const readPalette   = ["#7f0000", "#b30000", "#d7301f", "#ef6548", "#fc8d59", "#fdbb84", "#fdd0a2"];

    const markerColors = assignColours(markersMap, markerPalette);
    const readColors   = assignColours(readsMap, readPalette);

    function drawRow(rowIndex, label, map, colorMap, defaultColor) {
        const yRowTop = marginTop + rowIndex * cellH;
        const labelText = document.createElementNS(svgns, "text");
        labelText.setAttribute("x", marginLeft - 10);
        labelText.setAttribute("y", yRowTop + cellH / 2 + 4);
        labelText.setAttribute("text-anchor", "end");
        labelText.setAttribute("font-size", "11");
        labelText.textContent = label;
        svg.appendChild(labelText);

        const cellW = plotW / nSamples;

        samples.forEach((sampleName, i) => {
            const cluster = map[sampleName];
            const hasCluster = cluster !== null && cluster !== undefined;
            const fill = hasCluster ? (colorMap[cluster] || defaultColor) : "#eeeeee";

            const x = marginLeft + i * cellW;
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

            if (rowIndex === nRows - 1) {
                const showAll = nSamples <= 40;
                const show = showAll || (i % 5 === 0);
                if (show) {
                    const lab = document.createElementNS(svgns, "text");
                    lab.setAttribute("x", x + cellW / 2);
                    lab.setAttribute("y", marginTop + plotH + 50);
                    lab.setAttribute("font-size", "9");
                    lab.setAttribute("text-anchor", "end");
                    lab.setAttribute("transform", `rotate(-60 ${x + cellW / 2} ${marginTop + plotH + 50})`);
                    lab.textContent = sampleName;
                    svg.appendChild(lab);
                }
            }
        });
    }

    drawRow(0, "Markers", markersMap, markerColors, "#9ecae1");
    drawRow(1, "Reads", readsMap, readColors, "#fcae91");

    // Pairwise Mash distance heatmaps (markers vs reads)
    const pairwiseMarkers = clusters.pairwise_markers || [];
    const pairwiseReads = clusters.pairwise_reads || [];

    function buildPairwiseMatrix(pairs) {
        const sampleSet = new Set();
        pairs.forEach(p => {
            if (!p) return;
            if (p.sample1 != null) sampleSet.add(p.sample1);
            if (p.sample2 != null) sampleSet.add(p.sample2);
        });
        const samplesArr = Array.from(sampleSet).sort();
        const n = samplesArr.length;
        const index = {};
        samplesArr.forEach((s, i) => { index[s] = i; });

        const matrix = [];
        for (let i = 0; i < n; i++) {
            const row = new Array(n).fill(null);
            matrix.push(row);
        }

        let minD = Infinity;
        let maxD = -Infinity;

        pairs.forEach(p => {
            if (!p) return;
            const s1 = p.sample1;
            const s2 = p.sample2;
            if (!(s1 in index) || !(s2 in index)) return;
            const i = index[s1];
            const j = index[s2];
            const d = Number(p.distance);
            if (isNaN(d)) return;
            matrix[i][j] = d;
            matrix[j][i] = d;
            if (d < minD) minD = d;
            if (d > maxD) maxD = d;
        });

        if (!isFinite(minD) || !isFinite(maxD)) {
            minD = 0;
            maxD = 1;
        }

        for (let i = 0; i < n; i++) {
            if (matrix[i][i] === null) matrix[i][i] = 0.0;
        }

        return { samples: samplesArr, matrix, min: minD, max: maxD };
    }

    function distanceColor(d, minD, maxD) {
        if (d === null || d === undefined) return "#f5f5f5";
        const t = (d - minD) / ((maxD - minD) || 1);
        const clamped = Math.min(1, Math.max(0, t));
        const r = Math.round(255 * clamped);
        const g = Math.round(255 * (1 - clamped));
        const b = 80;
        return `rgb(${r},${g},${b})`;
    }

    function drawPairwiseHeatmap(containerSelector, matrixInfo, title) {
        const container = div.querySelector(containerSelector);
        if (!container) return;
        container.innerHTML = "";

        const samplesArr = matrixInfo.samples || [];
        const n = samplesArr.length;
        if (!n) {
            container.innerHTML = '<div class="small-note">Pairwise Mash distances not available.</div>';
            return;
        }

        const marginLeft = 110;
        const marginRight = 20;
        const marginTop = 30;
        const marginBottom = 110;
        const baseCell = 16;

        const plotW = Math.max(200, n * baseCell);
        const plotH = Math.max(200, n * baseCell);

        const width = marginLeft + plotW + marginRight;
        const height = marginTop + plotH + marginBottom;

        const svgPW = document.createElementNS(svgns, "svg");
        svgPW.setAttribute("width", width);
        svgPW.setAttribute("height", height);
        svgPW.setAttribute("viewBox", `0 0 ${width} ${height}`);
        svgPW.style.display = "block";

        container.appendChild(svgPW);

        const cellW = plotW / n;
        const cellH = plotH / n;

        const z = matrixInfo.matrix;
        const minD = matrixInfo.min;
        const maxD = matrixInfo.max;

        for (let i = 0; i < n; i++) {
            for (let j = 0; j < n; j++) {
                const d = z[i][j];
                const fill = distanceColor(d, minD, maxD);
                const x = marginLeft + j * cellW;
                const y = marginTop + i * cellH;

                const rect = document.createElementNS(svgns, "rect");
                rect.setAttribute("x", x);
                rect.setAttribute("y", y);
                rect.setAttribute("width", cellW);
                rect.setAttribute("height", cellH);
                rect.setAttribute("fill", fill);
                rect.setAttribute("stroke", "#ffffff");
                rect.setAttribute("stroke-width", "0.3");
                rect.style.cursor = "pointer";

                const s1 = samplesArr[i];
                const s2 = samplesArr[j];
                const tooltipText = `${s1} vs ${s2}\nMash distance: ${fmtFloat(d, 3)}`;

                rect.addEventListener("mouseenter", (evt) => {
                    rect.setAttribute("stroke", "#000");
                    rect.setAttribute("stroke-width", "0.8");
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
                    rect.setAttribute("stroke-width", "0.3");
                    tooltip.style.display = "none";
                });

                svgPW.appendChild(rect);
            }
        }

        samplesArr.forEach((s, i) => {
            const y = marginTop + i * cellH + cellH / 2 + 4;
            const text = document.createElementNS(svgns, "text");
            text.setAttribute("x", marginLeft - 4);
            text.setAttribute("y", y);
            text.setAttribute("font-size", "9");
            text.setAttribute("text-anchor", "end");
            text.textContent = s;
            svgPW.appendChild(text);
        });

        const showAll = n <= 40;
        samplesArr.forEach((s, j) => {
            const show = showAll || (j % 4 === 0);
            if (!show) return;
            const x = marginLeft + j * cellW + cellW / 2;
            const y = marginTop + plotH + 60;
            const text = document.createElementNS(svgns, "text");
            text.setAttribute("x", x);
            text.setAttribute("y", y);
            text.setAttribute("font-size", "9");
            text.setAttribute("text-anchor", "end");
            text.setAttribute("transform", `rotate(-60 ${x} ${y})`);
            text.textContent = s;
            svgPW.appendChild(text);
        });

        const titleText = document.createElementNS(svgns, "text");
        titleText.setAttribute("x", marginLeft);
        titleText.setAttribute("y", 16);
        titleText.setAttribute("font-size", "11");
        titleText.setAttribute("font-weight", "bold");
        titleText.textContent = title;
        svgPW.appendChild(titleText);
    }

    const markersMatrix = buildPairwiseMatrix(pairwiseMarkers);
    const readsMatrix = buildPairwiseMatrix(pairwiseReads);

    drawPairwiseHeatmap("#pairwise-heatmap-markers", markersMatrix, "Pairwise Mash distances (markers)");
    drawPairwiseHeatmap("#pairwise-heatmap-reads", readsMatrix, "Pairwise Mash distances (reads)");

    const tabButtons = div.querySelectorAll(".pairwise-tab");
    const markersDiv = div.querySelector("#pairwise-heatmap-markers");
    const readsDiv = div.querySelector("#pairwise-heatmap-reads");

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            tabButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const kind = btn.getAttribute("data-kind");
            if (kind === "markers") {
                markersDiv.style.display = "";
                readsDiv.style.display = "none";
            } else {
                markersDiv.style.display = "none";
                readsDiv.style.display = "";
            }
        });
    });
}

/* Main JS entry */
function main() {
    const distill = DISTILL_DATA;
    const figures = FIGURES_DATA;

    const summaryDiv = document.getElementById("summary-sections");

    const S = distill.summary || {};

    addGlobalOverview(distill, figures);

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
