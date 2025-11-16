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
        padding: 20px;
        background-color: #f7f7f7;
        color: #222;
    }

    h1 {
        text-align: center;
    }

    h2 {
        margin-top: 1.5em;
        margin-bottom: 0.4em;
    }

    .section {
        margin-bottom: 1.5em;
    }

    details.section-details {
        border-radius: 4px;
        padding: 8px 12px 12px 12px;
        margin-bottom: 12px;
        background-color: #ffffff;
        border: 1px solid #ccc;
    }

    details.section-details summary {
        cursor: pointer;
        font-weight: bold;
        outline: none;
    }

    .section-flag-1 {
        border-left: 8px solid #4caf50;
    }

    .section-flag-2 {
        border-left: 8px solid #ff9800;
    }

    .section-flag-3 {
        border-left: 8px solid #f44336;
    }

    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .section-header-left {
        display: flex;
        flex-direction: column;
    }

    .section-header-right {
        text-align: right;
        font-size: 0.9em;
        color: #555;
    }

    .section-badge {
        border-radius: 999px;
        padding: 2px 8px;
        font-size: 0.8em;
        display: inline-block;
        margin-top: 4px;
    }

    .flag-1 {
        background-color: #e8f5e9;
        color: #1b5e20;
    }

    .flag-2 {
        background-color: #fff9e6;
        color: #f57f17;
    }

    .flag-3 {
        background-color: #ffebee;
        color: #b71c1c;
    }

    .small-note {
        font-size: 0.9em;
        color: #555;
        margin-top: 0.6em;
    }

    .summary-stat {
        display: inline-block;
        margin-right: 18px;
        margin-top: 8px;
        font-size: 0.95em;
    }

    .summary-stat span.label {
        font-weight: 600;
    }

    .summary-stat span.value {
        font-family: "Courier New", monospace;
        margin-left: 4px;
    }

    .summary-text {
        margin-top: 0.6em;
        margin-bottom: 0.6em;
    }

    .chart-container {
        margin-top: 10px;
        margin-bottom: 5px;
        background-color: #fafafa;
        border-radius: 4px;
        padding: 8px;
        border: 1px solid #ddd;
    }

    .chart-title {
        font-size: 0.95em;
        margin-bottom: 4px;
        color: #333;
    }

    .chart-caption {
        font-size: 0.85em;
        color: #555;
        margin-top: 4px;
    }

    svg.chart {
        width: 100%;
        height: 300px;
        background: #ffffff;
    }

    .legend {
        font-size: 0.85em;
        color: #333;
        margin-top: 4px;
    }

    .legend span {
        display: inline-block;
        margin-right: 12px;
    }

    .legend-color-box {
        width: 12px;
        height: 12px;
        display: inline-block;
        vertical-align: middle;
        margin-right: 4px;
        border-radius: 2px;
    }

    .flex-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
    }

    .flex-col {
        flex: 1 1 0;
        min-width: 0;
    }

    .badge-pill {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 999px;
        font-size: 0.8em;
        background: #eee;
        margin-right: 4px;
        margin-bottom: 4px;
    }

    .sample-list {
        font-size: 0.9em;
        margin: 0;
        padding-left: 1.2em;
    }

    .sample-list li {
        margin-bottom: 2px;
    }

    .lr-target-circle {
        opacity: 0.15;
    }

    .lr-target-line {
        stroke-dasharray: 4, 4;
    }

    .clusters-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 6px;
        font-size: 0.9em;
    }

    .clusters-table th,
    .clusters-table td {
        border: 1px solid #ccc;
        padding: 4px 6px;
    }

    .clusters-table th {
        background: #f0f0f0;
    }

    .clusters-table td.samples-cell {
        font-size: 0.85em;
    }

    .tooltip-row {
        margin: 0;
        padding: 0;
    }

    .tooltip-row span.label {
        font-weight: 600;
    }

    .tooltip-row span.value {
        font-family: "Courier New", monospace;
        margin-left: 4px;
    }

    .inline-highlight {
        background: #fff9c4;
        padding: 1px 3px;
        border-radius: 3px;
    }

    .inline-code {
        font-family: "Courier New", monospace;
        background: #f5f5f5;
        border-radius: 3px;
        padding: 0 3px;
    }

    .bottom-note {
        margin-top: 30px;
        font-size: 0.85em;
        color: #555;
    }

    .bottom-note code {
        font-family: "Courier New", monospace;
        background: #f5f5f5;
        padding: 0 3px;
        border-radius: 3px;
    }

    .heatmap-svg {
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
        white-space: nowrap;
        transform: translate(8px, -20px);
    }

    .report-header {
        margin-bottom: 24px;
        border-radius: 8px;
        padding: 12px 16px 16px 16px;
        border: 1px solid #ccc;
        background: #fff;
    }

    .report-title-sub {
        text-align: center;
        margin: 0 0 10px 0;
        font-size: 1.05em;
        color: #555;
    }

    .report-meta-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        justify-content: space-between;
    }

    .report-meta-item {
        flex: 1;
        min-width: 200px;
    }

    .report-meta-label {
        font-size: 0.9em;
        color: #555;
        margin-bottom: 2px;
    }

    .report-meta-value {
        font-size: 1.1em;
        font-weight: 600;
    }
</style>

</head>
<body>

<h1>ScreenM Summary Report</h1>

<div id="report-header"></div>
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
    if (x === null || x === undefined) return "NA"
    const factor = Math.pow(10, digits);
    const rounded = Math.round(x * factor) / factor;
    return rounded.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

function fmtPercent(x, digits) {
    if (x === null || x === undefined) return "NA";
    const factor = Math.pow(10, digits);
    const rounded = Math.round(x * factor) / factor;
    return rounded.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits }) + "%";
}

function fmtMillions(x) {
    if (x === null || x === undefined) return "NA";
    const v = Number(x);
    if (!isFinite(v)) return "∞";
    if (v >= 1e9) return (v / 1e9).toFixed(2) + " B";
    if (v >= 1e6) return (v / 1e6).toFixed(2) + " M";
    if (v >= 1e3) return (v / 1e3).toFixed(2) + " K";
    return v.toLocaleString();
}

function mkSummaryStat(label, value) {
    const span = document.createElement("span");
    span.className = "summary-stat";
    span.innerHTML = `<span class="label">${label}:</span><span class="value">${value}</span>`;
    return span;
}

function mkSmallNote(text) {
    const div = document.createElement("div");
    div.className = "small-note";
    div.textContent = text;
    return div;
}

function mkInlineHighlight(text) {
    const span = document.createElement("span");
    span.className = "inline-highlight";
    span.textContent = text;
    return span;
}

function mkInlineCode(text) {
    const span = document.createElement("span");
    span.className = "inline-code";
    span.textContent = text;
    return span;
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


function addReportHeader(distill, depthPerSample) {
    const meta = distill.meta || {};
    const mergedMeta = meta.metadata || {};

    const projectName = mergedMeta.project || "Unnamed project";
    const softwareVersion = mergedMeta.software_version || "NA";
    const createdAt = mergedMeta.created_at || mergedMeta.creation_date || "NA";

    const S = distill.summary || {};
    const screen = S.screening_overview || {};

    let nSamples = meta.n_samples_in_results;
    if (nSamples === undefined || nSamples === null) {
        if (screen.n_samples_total !== undefined && screen.n_samples_total !== null) {
            nSamples = screen.n_samples_total;
        }
    }

    let totalDepth = null;
    if (Array.isArray(depthPerSample) && depthPerSample.length > 0) {
        totalDepth = depthPerSample.reduce((acc, d) => {
            const v = Number(d.total_reads);
            if (!isNaN(v)) {
                return acc + v;
            }
            return acc;
        }, 0);
    }

    const headerDiv = document.getElementById("report-header");
    if (!headerDiv) return;

    headerDiv.className = "report-header";

    const titleHtml = (projectName && projectName !== "Unnamed project")
        ? '<p class="report-title-sub">' + projectName + '</p>'
        : "";

    headerDiv.innerHTML = `
        ${titleHtml}
        <div class="report-meta-grid">
            <div class="report-meta-item">
                <div class="report-meta-label">Software version</div>
                <div class="report-meta-value">${softwareVersion}</div>
            </div>
            <div class="report-meta-item">
                <div class="report-meta-label">Report created</div>
                <div class="report-meta-value">${createdAt}</div>
            </div>
            <div class="report-meta-item">
                <div class="report-meta-label">Number of samples</div>
                <div class="report-meta-value">${fmtInt(nSamples)}</div>
            </div>
            <div class="report-meta-item">
                <div class="report-meta-label">Total sequencing depth</div>
                <div class="report-meta-value">${fmtMillions(totalDepth)}</div>
            </div>
        </div>
    `;

    if (projectName && projectName !== "Unnamed project") {
        const h1 = document.querySelector("h1");
        if (h1) {
            h1.textContent = `ScreenM Summary Report – ${projectName}`;
        }
        document.title = `ScreenM Report – ${projectName}`;
    }
}

/* ---------- Section-level status (emoji + short text) ---------- */
function sectionStatus(sectionLabel, flag) {
    let emoji, descriptor;
    if (flag === 1) {
        emoji = "😊";
        descriptor = "good";
    } else if (flag === 2) {
        emoji = "⚠️";
        descriptor = "caution";
    } else {
        emoji = "❌";
        descriptor = "warning";
    }
    return `${emoji} Overall status for ${sectionLabel}: ${descriptor}.`;
}

/* ---------- 01. Screening overview ---------- */

function addScreeningOverviewSection(parent, overview, depthPerSample) {
    if (!overview) {
        const div = document.createElement("div");
        div.className = "section";
        div.innerHTML = "<h2>1. Screening overview</h2><p class='small-note'>No overview data available.</p>";
        parent.appendChild(div);
        return;
    }

    const flag = overview.flag_reads_threshold;
    const message = overview.message_overall || overview.message_reads_threshold || "";

    const details = document.createElement("details");
    details.className = `section-details section-flag-${flagClass(flag)}`;
    details.open = true;

    const summary = document.createElement("summary");
    summary.innerHTML = `
        <div class="section-header">
            <div class="section-header-left">
                <span>1. Screening overview</span>
                <span class="section-badge ${flagClass(flag)}">Reads threshold</span>
            </div>
            <div class="section-header-right">
                <span>${sectionStatus("screening overview", flag)}</span>
            </div>
        </div>
    `;
    details.appendChild(summary);

    const content = document.createElement("div");
    content.className = "section-content";

    const statsDiv = document.createElement("div");
    statsDiv.appendChild(mkSummaryStat("Number of samples", fmtInt(overview.n_samples_total)));
    statsDiv.appendChild(mkSummaryStat("Reads threshold", fmtMillions(overview.reads_threshold)));
    statsDiv.appendChild(mkSummaryStat("Samples above threshold", fmtInt(overview.n_samples_above_threshold)));
    statsDiv.appendChild(mkSummaryStat("Above threshold (%)", fmtPercent(overview.percent_above_threshold, 1)));
    statsDiv.appendChild(mkSummaryStat("Samples with depth estimation", fmtInt(overview.n_samples_depth)));
    statsDiv.appendChild(mkSummaryStat("Estimated total depth (M reads)", fmtFloat(overview.est_total_mreads || 0, 2)));
    statsDiv.appendChild(mkSummaryStat("Mean depth (M reads)", fmtFloat(overview.mean_depth_mreads || 0, 2)));
    statsDiv.appendChild(mkSummaryStat("CV of depth", fmtFloat(overview.cv_depth || 0, 2)));

    content.appendChild(statsDiv);

    const msgP = document.createElement("p");
    msgP.className = "summary-text";
    msgP.textContent = message;
    content.appendChild(msgP);

    const figContainer = document.createElement("div");
    figContainer.className = "chart-container";

    const figTitle = document.createElement("div");
    figTitle.className = "chart-title";
    figTitle.textContent = "Sequencing depth per sample";
    figContainer.appendChild(figTitle);

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.classList.add("chart");
    svg.setAttribute("id", "seq-depth-svg");
    figContainer.appendChild(svg);

    const caption = document.createElement("div");
    caption.className = "chart-caption";
    caption.textContent = "Bars show reads per sample. Horizontal line indicates screening reads threshold.";
    figContainer.appendChild(caption);

    content.appendChild(figContainer);

    const note = mkSmallNote("If some samples are far below the threshold, they may not be suitable for deep analyses.");
    content.appendChild(note);

    details.appendChild(content);
    parent.appendChild(details);

    const perSample = (depthPerSample || [])
        .filter(d => d.total_reads !== null && d.total_reads !== undefined);

    if (!perSample.length) {
        svg.outerHTML = `<div class="small-note">Per-sample read counts not available for sequencing depth barplot.</div>`;
        return;
    }

    const margin = { top: 18, right: 8, bottom: 88, left: 60 };
    const innerWidth = svg.clientWidth || 800;
    const innerHeight = svg.clientHeight || 320;
    const width = innerWidth - margin.left - margin.right;
    const height = innerHeight - margin.top - margin.bottom;

    const maxDepth = perSample.reduce((max, d) => {
        const v = Number(d.total_reads) || 0;
        return v > max ? v : max;
    }, 0);

    const threshold = overview.reads_threshold || 0;
    const maxY = Math.max(maxDepth, threshold * 1.05);

    const barWidth = Math.max(4, width / Math.max(1, perSample.length));
    const xStep = width / Math.max(1, perSample.length);

    const maxLabelChars = 12;
    const truncatedNames = perSample.map(d => {
        const s = String(d.sample || "");
        if (s.length <= maxLabelChars) return s;
        return s.slice(0, maxLabelChars - 1) + "…";
    });

    while (svg.firstChild) svg.removeChild(svg.firstChild);

    svg.setAttribute("viewBox", `0 0 ${innerWidth} ${innerHeight}`);

    const svgns = "http://www.w3.org/2000/svg";

    const xAxis = document.createElementNS(svgns, "g");
    xAxis.setAttribute("transform", `translate(${margin.left}, ${innerHeight - margin.bottom})`);

    truncatedNames.forEach((name, i) => {
        const x = i * xStep + xStep / 2;
        const tick = document.createElementNS(svgns, "line");
        tick.setAttribute("x1", x);
        tick.setAttribute("y1", 0);
        tick.setAttribute("x2", x);
        tick.setAttribute("y2", 5);
        tick.setAttribute("stroke", "#555");
        xAxis.appendChild(tick);

        const label = document.createElementNS(svgns, "text");
        label.setAttribute("x", x);
        label.setAttribute("y", 20);
        label.setAttribute("text-anchor", "end");
        label.setAttribute("transform", `rotate(-60 ${x} 20)`);
        label.setAttribute("font-size", "10");
        label.textContent = name;
        xAxis.appendChild(label);
    });

    const axisLine = document.createElementNS(svgns, "line");
    axisLine.setAttribute("x1", 0);
    axisLine.setAttribute("y1", 0);
    axisLine.setAttribute("x2", width);
    axisLine.setAttribute("y2", 0);
    axisLine.setAttribute("stroke", "#333");
    axisLine.setAttribute("stroke-width", "1.5");
    xAxis.appendChild(axisLine);

    svg.appendChild(xAxis);

    const yAxis = document.createElementNS(svgns, "g");
    yAxis.setAttribute("transform", `translate(${margin.left}, ${margin.top})`);

    const nTicks = 5;
    for (let i = 0; i <= nTicks; i++) {
        const t = i / nTicks;
        const yVal = t * maxY;
        const y = height - t * height;

        const grid = document.createElementNS(svgns, "line");
        grid.setAttribute("x1", 0);
        grid.setAttribute("y1", y);
        grid.setAttribute("x2", width);
        grid.setAttribute("y2", y);
        grid.setAttribute("stroke", "#ddd");
        grid.setAttribute("stroke-width", "1");
        yAxis.appendChild(grid);

        const tick = document.createElementNS(svgns, "line");
        tick.setAttribute("x1", 0);
        tick.setAttribute("y1", y);
        tick.setAttribute("x2", -5);
        tick.setAttribute("y2", y);
        tick.setAttribute("stroke", "#555");
        tick.setAttribute("stroke-width", "1");
        yAxis.appendChild(tick);

        const label = document.createElementNS(svgns, "text");
        label.setAttribute("x", -8);
        label.setAttribute("y", y + 3);
        label.setAttribute("text-anchor", "end");
        label.setAttribute("font-size", "10");
        label.textContent = fmtMillions(yVal);
        yAxis.appendChild(label);
    }

    const yAxisLine = document.createElementNS(svgns, "line");
    yAxisLine.setAttribute("x1", 0);
    yAxisLine.setAttribute("y1", 0);
    yAxisLine.setAttribute("x2", 0);
    yAxisLine.setAttribute("y2", height);
    yAxisLine.setAttribute("stroke", "#333");
    yAxisLine.setAttribute("stroke-width", "1.5");
    yAxis.appendChild(yAxisLine);

    svg.appendChild(yAxis);

    const barsGroup = document.createElementNS(svgns, "g");
    barsGroup.setAttribute("transform", `translate(${margin.left}, ${margin.top})`);

    const tooltip = getOrCreateTooltip();

    perSample.forEach((d, i) => {
        const value = Number(d.total_reads) || 0;
        const x0 = i * xStep + (xStep - barWidth) / 2;
        const barHeight = maxY > 0 ? (value / maxY) * height : 0;
        const y0 = height - barHeight;

        const rect = document.createElementNS(svgns, "rect");
        rect.setAttribute("x", x0);
        rect.setAttribute("y", y0);
        rect.setAttribute("width", barWidth);
        rect.setAttribute("height", barHeight);
        rect.setAttribute("fill", "#2196f3");
        rect.setAttribute("opacity", "0.8");

        rect.addEventListener("mousemove", (ev) => {
            tooltip.style.left = ev.clientX + "px";
            tooltip.style.top = ev.clientY + "px";
            tooltip.innerHTML = `
                <div class="tooltip-row"><span class="label">Sample</span><span class="value">${d.sample}</span></div>
                <div class="tooltip-row"><span class="label">Total reads</span><span class="value">${fmtMillions(value)}</span></div>
            `;
            tooltip.style.display = "block";
        });
        rect.addEventListener("mouseleave", () => {
            tooltip.style.display = "none";
        });

        barsGroup.appendChild(rect);
    });

    svg.appendChild(barsGroup);

    if (threshold > 0) {
        const t = threshold / maxY;
        const y = margin.top + (height - t * height);

        const line = document.createElementNS(svgns, "line");
        line.setAttribute("x1", margin.left);
        line.setAttribute("y1", y);
        line.setAttribute("x2", margin.left + width);
        line.setAttribute("y2", y);
        line.setAttribute("stroke", "#f44336");
        line.setAttribute("stroke-width", "2");
        line.setAttribute("stroke-dasharray", "4,4");

        svg.appendChild(line);

        const label = document.createElementNS(svgns, "text");
        label.setAttribute("x", margin.left + width - 4);
        label.setAttribute("y", y - 4);
        label.setAttribute("text-anchor", "end");
        label.setAttribute("font-size", "10");
        label.setAttribute("fill", "#f44336");
        label.textContent = "Threshold";
        svg.appendChild(label);
    }
}

/* ---------- 02. Low-quality reads ---------- */

function addLowQualitySection(parent, lowQuality, depthPerSample) {
    if (!lowQuality) {
        const div = document.createElement("div");
        div.className = "section";
        div.innerHTML = "<h2>2. Low-quality reads</h2><p class='small-note'>No low-quality read metrics available.</p>";
        parent.appendChild(div);
        return;
    }

    const flag = lowQuality.flag_low_quality;
    const message = lowQuality.message_low_quality || "";

    const details = document.createElement("details");
    details.className = `section-details section-flag-${flagClass(flag)}`;
    details.open = true;

    const summary = document.createElement("summary");
    summary.innerHTML = `
        <div class="section-header">
            <div class="section-header-left">
                <span>2. Low-quality reads</span>
                <span class="section-badge ${flagClass(flag)}">Low-quality fraction</span>
            </div>
            <div class="section-header-right">
                <span>${sectionStatus("low-quality reads", flag)}</span>
            </div>
        </div>
    `;
    details.appendChild(summary);

    const content = document.createElement("div");
    content.className = "section-content";

    const statsDiv = document.createElement("div");
    statsDiv.appendChild(mkSummaryStat("Samples with low-quality estimates", fmtInt(lowQuality.n_samples_with_data || 0)));
    statsDiv.appendChild(mkSummaryStat("Mean low-quality fraction", fmtPercent(lowQuality.mean_fraction_removed || 0, 2)));
    statsDiv.appendChild(mkSummaryStat("Median low-quality fraction", fmtPercent(lowQuality.median_fraction_removed || 0, 2)));
    statsDiv.appendChild(mkSummaryStat("SD of low-quality fraction", fmtFloat(lowQuality.sd_fraction_removed || 0, 2)));

    content.appendChild(statsDiv);

    const msgP = document.createElement("p");
    msgP.className = "summary-text";
    msgP.textContent = message;
    content.appendChild(msgP);

    const figContainer = document.createElement("div");
    figContainer.className = "chart-container";

    const figTitle = document.createElement("div");
    figTitle.className = "chart-title";
    figTitle.textContent = "Low-quality reads vs. total depth";
    figContainer.appendChild(figTitle);

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.classList.add("chart");
    svg.setAttribute("id", "low-quality-scatter-svg");
    figContainer.appendChild(svg);

    const caption = document.createElement("div");
    caption.className = "chart-caption";
    caption.textContent = "Each point is a sample, positioned by total reads and number of reads estimated to be low quality.";
    figContainer.appendChild(caption);

    content.appendChild(figContainer);

    const note = mkSmallNote("High fractions of low-quality reads can indicate issues with library preparation or sequencing.");
    content.appendChild(note);

    details.appendChild(content);
    parent.appendChild(details);

    const dataPerSample = (depthPerSample || []).filter(d =>
        d.total_reads !== null &&
        d.total_reads !== undefined &&
        d.low_quality_reads_est !== null &&
        d.low_quality_reads_est !== undefined
    );

    if (!dataPerSample.length) {
        svg.outerHTML = `<div class="small-note">Per-sample low-quality read estimates not available for scatter plot.</div>`;
        return;
    }

    const margin = { top: 18, right: 8, bottom: 50, left: 60 };
    const innerWidth = svg.clientWidth || 800;
    const innerHeight = svg.clientHeight || 320;
    const width = innerWidth - margin.left - margin.right;
    const height = innerHeight - margin.top - margin.bottom;

    let maxTotal = 0;
    let maxLow = 0;
    dataPerSample.forEach(d => {
        const total = Number(d.total_reads) || 0;
        const low = Number(d.low_quality_reads_est) || 0;
        if (total > maxTotal) maxTotal = total;
        if (low > maxLow) maxLow = low;
    });

    if (maxTotal <= 0 || maxLow <= 0) {
        svg.outerHTML = `<div class="small-note">Low-quality read estimates are all zero or missing.</div>`;
        return;
    }

    const xMax = maxTotal * 1.05;
    const yMax = maxLow * 1.05;

    while (svg.firstChild) svg.removeChild(svg.firstChild);
    svg.setAttribute("viewBox", `0 0 ${innerWidth} ${innerHeight}`);
    const svgns = "http://www.w3.org/2000/svg";

    const g = document.createElementNS(svgns, "g");
    g.setAttribute("transform", `translate(${margin.left}, ${margin.top})`);

    const xTicks = 5;
    for (let i = 0; i <= xTicks; i++) {
        const t = i / xTicks;
        const x = t * width;
        const y = height;

        const grid = document.createElementNS(svgns, "line");
        grid.setAttribute("x1", x);
        grid.setAttribute("y1", 0);
        grid.setAttribute("x2", x);
        grid.setAttribute("y2", y);
        grid.setAttribute("stroke", "#eee");
        grid.setAttribute("stroke-width", "1");
        g.appendChild(grid);

        const tick = document.createElementNS(svgns, "line");
        tick.setAttribute("x1", x);
        tick.setAttribute("y1", y);
        tick.setAttribute("x2", x);
        tick.setAttribute("y2", y + 5);
        tick.setAttribute("stroke", "#555");
        tick.setAttribute("stroke-width", "1");
        g.appendChild(tick);

        const label = document.createElementNS(svgns, "text");
        label.setAttribute("x", x);
        label.setAttribute("y", y + 18);
        label.setAttribute("text-anchor", "middle");
        label.setAttribute("font-size", "10");
        label.textContent = fmtMillions(t * xMax);
        g.appendChild(label);
    }

    const yTicks = 5;
    for (let i = 0; i <= yTicks; i++) {
        const t = i / yTicks;
        const y = height - t * height;

        const grid = document.createElementNS(svgns, "line");
        grid.setAttribute("x1", 0);
        grid.setAttribute("y1", y);
        grid.setAttribute("x2", width);
        grid.setAttribute("y2", y);
        grid.setAttribute("stroke", "#eee");
        grid.setAttribute("stroke-width", "1");
        g.appendChild(grid);

        const tick = document.createElementNS(svgns, "line");
        tick.setAttribute("x1", 0);
        tick.setAttribute("y1", y);
        tick.setAttribute("x2", -5);
        tick.setAttribute("y2", y);
        tick.setAttribute("stroke", "#555");
        tick.setAttribute("stroke-width", "1");
        g.appendChild(tick);

        const label = document.createElementNS(svgns, "text");
        label.setAttribute("x", -8);
        label.setAttribute("y", y + 3);
        label.setAttribute("text-anchor", "end");
        label.setAttribute("font-size", "10");
        label.textContent = fmtMillions(t * yMax);
        g.appendChild(label);
    }

    const xAxisLine = document.createElementNS(svgns, "line");
    xAxisLine.setAttribute("x1", 0);
    xAxisLine.setAttribute("y1", height);
    xAxisLine.setAttribute("x2", width);
    xAxisLine.setAttribute("y2", height);
    xAxisLine.setAttribute("stroke", "#333");
    xAxisLine.setAttribute("stroke-width", "1.5");
    g.appendChild(xAxisLine);

    const yAxisLine = document.createElementNS(svgns, "line");
    yAxisLine.setAttribute("x1", 0);
    yAxisLine.setAttribute("y1", 0);
    yAxisLine.setAttribute("x2", 0);
    yAxisLine.setAttribute("y2", height);
    yAxisLine.setAttribute("stroke", "#333");
    yAxisLine.setAttribute("stroke-width", "1.5");
    g.appendChild(yAxisLine);

    const tooltip = getOrCreateTooltip();

    dataPerSample.forEach(d => {
        const total = Number(d.total_reads) || 0;
        const low = Number(d.low_quality_reads_est) || 0;
        const x = (total / xMax) * width;
        const y = height - (low / yMax) * height;

        const circle = document.createElementNS(svgns, "circle");
        circle.setAttribute("cx", x);
        circle.setAttribute("cy", y);
        circle.setAttribute("r", 4);
        circle.setAttribute("fill", "#f44336");
        circle.setAttribute("opacity", "0.8");

        circle.addEventListener("mousemove", (ev) => {
            tooltip.style.left = ev.clientX + "px";
            tooltip.style.top = ev.clientY + "px";
            tooltip.innerHTML = `
                <div class="tooltip-row"><span class="label">Sample</span><span class="value">${d.sample}</span></div>
                <div class="tooltip-row"><span class="label">Total reads</span><span class="value">${fmtMillions(total)}</span></div>
                <div class="tooltip-row"><span class="label">Low-quality reads (est.)</span><span class="value">${fmtMillions(low)}</span></div>
                <div class="tooltip-row"><span class="label">Fraction removed</span><span class="value">${fmtPercent(low / Math.max(1, total), 2)}</span></div>
            `;
            tooltip.style.display = "block";
        });
        circle.addEventListener("mouseleave", () => {
            tooltip.style.display = "none";
        });

        g.appendChild(circle);
    });

    svg.appendChild(g);

    const xLabel = document.createElementNS(svgns, "text");
    xLabel.setAttribute("x", margin.left + width / 2);
    xLabel.setAttribute("y", innerHeight - 8);
    xLabel.setAttribute("text-anchor", "middle");
    xLabel.setAttribute("font-size", "11");
    xLabel.textContent = "Total reads per sample";
    svg.appendChild(xLabel);

    const yLabel = document.createElementNS(svgns, "text");
    yLabel.setAttribute("x", 14);
    yLabel.setAttribute("y", margin.top + height / 2);
    yLabel.setAttribute("text-anchor", "middle");
    yLabel.setAttribute("font-size", "11");
    yLabel.setAttribute("transform", `rotate(-90 14 ${margin.top + height / 2})`);
    yLabel.textContent = "Estimated low-quality reads";
    svg.appendChild(yLabel);
}

/* ---------- 03. Prokaryotic fraction ---------- */

function addProkFractionSection(parent, prokFraction, depthPerSample) {
    if (!prokFraction) {
        const div = document.createElement("div");
        div.className = "section";
        div.innerHTML = "<h2>3. Prokaryotic fraction</h2><p class='small-note'>No prokaryotic fraction metrics available.</p>";
        parent.appendChild(div);
        return;
    }

    const flag = prokFraction.flag_prokaryotic_fraction;
    const message = prokFraction.message_prokaryotic_fraction || "";

    const details = document.createElement("details");
    details.className = `section-details section-flag-${flagClass(flag)}`;
    details.open = true;

    const summary = document.createElement("summary");
    summary.innerHTML = `
        <div class="section-header">
            <div class="section-header-left">
                <span>3. Prokaryotic fraction</span>
                <span class="section-badge ${flagClass(flag)}">Prokaryotic content</span>
            </div>
            <div class="section-header-right">
                <span>${sectionStatus("prokaryotic fraction", flag)}</span>
            </div>
        </div>
    `;
    details.appendChild(summary);

    const content = document.createElement("div");
    content.className = "section-content";

    const statsDiv = document.createElement("div");
    statsDiv.appendChild(mkSummaryStat("Samples with prokaryotic fraction", fmtInt(prokFraction.n_samples || 0)));
    statsDiv.appendChild(mkSummaryStat("Mean prokaryotic fraction", fmtPercent(prokFraction.mean_prokaryotic_fraction || 0, 2)));
    statsDiv.appendChild(mkSummaryStat("Median prokaryotic fraction", fmtPercent(prokFraction.median_prokaryotic_fraction || 0, 2)));
    statsDiv.appendChild(mkSummaryStat("SD of prokaryotic fraction", fmtFloat(prokFraction.sd_prokaryotic_fraction || 0, 2)));
    statsDiv.appendChild(mkSummaryStat("Number of warnings", fmtInt(prokFraction.n_warnings || 0)));

    content.appendChild(statsDiv);

    const msgP = document.createElement("p");
    msgP.className = "summary-text";
    msgP.textContent = message;
    content.appendChild(msgP);

    const figContainer = document.createElement("div");
    figContainer.className = "chart-container";

    const figTitle = document.createElement("div");
    figTitle.className = "chart-title";
    figTitle.textContent = "Prokaryotic fraction vs. depth";
    figContainer.appendChild(figTitle);

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.classList.add("chart");
    svg.setAttribute("id", "prok-fraction-scatter-svg");
    figContainer.appendChild(svg);

    const caption = document.createElement("div");
    caption.className = "chart-caption";
    caption.textContent = "Each point is a sample, positioned by total reads and estimated prokaryotic fraction.";
    figContainer.appendChild(caption);

    content.appendChild(figContainer);

    const note = mkSmallNote("Low prokaryotic fractions can indicate that a substantial portion of reads comes from host or other non-prokaryotic DNA.");
    content.appendChild(note);

    details.appendChild(content);
    parent.appendChild(details);

    const dataPerSample = (depthPerSample || []).filter(d =>
        d.total_reads !== null &&
        d.total_reads !== undefined &&
        d.prokaryotic_fraction !== null &&
        d.prokaryotic_fraction !== undefined
    );

    if (!dataPerSample.length) {
        svg.outerHTML = `<div class="small-note">Per-sample prokaryotic fraction estimates not available for scatter plot.</div>`;
        return;
    }

    const margin = { top: 18, right: 8, bottom: 50, left: 60 };
    const innerWidth = svg.clientWidth || 800;
    const innerHeight = svg.clientHeight || 320;
    const width = innerWidth - margin.left - margin.right;
    const height = innerHeight - margin.top - margin.bottom;

    let maxTotal = 0;
    dataPerSample.forEach(d => {
        const total = Number(d.total_reads) || 0;
        if (total > maxTotal) maxTotal = total;
    });

    if (maxTotal <= 0) {
        svg.outerHTML = `<div class="small-note">Total reads are zero or missing for all samples; cannot draw prokaryotic fraction plot.</div>`;
        return;
    }

    const xMax = maxTotal * 1.05;
    const yMax = 100;

    while (svg.firstChild) svg.removeChild(svg.firstChild);
    svg.setAttribute("viewBox", `0 0 ${innerWidth} ${innerHeight}`);
    const svgns = "http://www.w3.org/2000/svg";

    const g = document.createElementNS(svgns, "g");
    g.setAttribute("transform", `translate(${margin.left}, ${margin.top})`);

    const xTicks = 5;
    for (let i = 0; i <= xTicks; i++) {
        const t = i / xTicks;
        const x = t * width;
        const y = height;

        const grid = document.createElementNS(svgns, "line");
        grid.setAttribute("x1", x);
        grid.setAttribute("y1", 0);
        grid.setAttribute("x2", x);
        grid.setAttribute("y2", y);
        grid.setAttribute("stroke", "#eee");
        grid.setAttribute("stroke-width", "1");
        g.appendChild(grid);

        const tick = document.createElementNS(svgns, "line");
        tick.setAttribute("x1", x);
        tick.setAttribute("y1", y);
        tick.setAttribute("x2", x);
        tick.setAttribute("y2", y + 5);
        tick.setAttribute("stroke", "#555");
        tick.setAttribute("stroke-width", "1");
        g.appendChild(tick);

        const label = document.createElementNS(svgns, "text");
        label.setAttribute("x", x);
        label.setAttribute("y", y + 18);
        label.setAttribute("text-anchor", "middle");
        label.setAttribute("font-size", "10");
        label.textContent = fmtMillions(t * xMax);
        g.appendChild(label);
    }

    const yTicks = 5;
    for (let i = 0; i <= yTicks; i++) {
        const t = i / yTicks;
        const y = height - t * height;

        const grid = document.createElementNS(svgns, "line");
        grid.setAttribute("x1", 0);
        grid.setAttribute("y1", y);
        grid.setAttribute("x2", width);
        grid.setAttribute("y2", y);
        grid.setAttribute("stroke", "#eee");
        grid.setAttribute("stroke-width", "1");
        g.appendChild(grid);

        const tick = document.createElementNS(svgns, "line");
        tick.setAttribute("x1", 0);
        tick.setAttribute("y1", y);
        tick.setAttribute("x2", -5);
        tick.setAttribute("y2", y);
        tick.setAttribute("stroke", "#555");
        tick.setAttribute("stroke-width", "1");
        g.appendChild(tick);

        const label = document.createElementNS(svgns, "text");
        label.setAttribute("x", -8);
        label.setAttribute("y", y + 3);
        label.setAttribute("text-anchor", "end");
        label.setAttribute("font-size", "10");
        label.textContent = fmtPercent(t * yMax, 0);
        g.appendChild(label);
    }

    const xAxisLine = document.createElementNS(svgns, "line");
    xAxisLine.setAttribute("x1", 0);
    xAxisLine.setAttribute("y1", height);
    xAxisLine.setAttribute("x2", width);
    xAxisLine.setAttribute("y2", height);
    xAxisLine.setAttribute("stroke", "#333");
    xAxisLine.setAttribute("stroke-width", "1.5");
    g.appendChild(xAxisLine);

    const yAxisLine = document.createElementNS(svgns, "line");
    yAxisLine.setAttribute("x1", 0);
    yAxisLine.setAttribute("y1", 0);
    yAxisLine.setAttribute("x2", 0);
    yAxisLine.setAttribute("y2", height);
    yAxisLine.setAttribute("stroke", "#333");
    yAxisLine.setAttribute("stroke-width", "1.5");
    g.appendChild(yAxisLine);

    const tooltip = getOrCreateTooltip();

    dataPerSample.forEach(d => {
        const total = Number(d.total_reads) || 0;
        const frac = Number(d.prokaryotic_fraction) || 0;

        const x = (total / xMax) * width;
        const y = height - (frac / yMax) * height;

        const circle = document.createElementNS(svgns, "circle");
        circle.setAttribute("cx", x);
        circle.setAttribute("cy", y);
        circle.setAttribute("r", 4);
        circle.setAttribute("fill", "#4caf50");
        circle.setAttribute("opacity", "0.8");

        circle.addEventListener("mousemove", (ev) => {
            tooltip.style.left = ev.clientX + "px";
            tooltip.style.top = ev.clientY + "px";
            tooltip.innerHTML = `
                <div class="tooltip-row"><span class="label">Sample</span><span class="value">${d.sample}</span></div>
                <div class="tooltip-row"><span class="label">Total reads</span><span class="value">${fmtMillions(total)}</span></div>
                <div class="tooltip-row"><span class="label">Prokaryotic fraction</span><span class="value">${fmtPercent(frac, 2)}</span></div>
            `;
            tooltip.style.display = "block";
        });
        circle.addEventListener("mouseleave", () => {
            tooltip.style.display = "none";
        });

        g.appendChild(circle);
    });

    svg.appendChild(g);

    const xLabel = document.createElementNS(svgns, "text");
    xLabel.setAttribute("x", margin.left + width / 2);
    xLabel.setAttribute("y", innerHeight - 8);
    xLabel.setAttribute("text-anchor", "middle");
    xLabel.setAttribute("font-size", "11");
    xLabel.textContent = "Total reads per sample";
    svg.appendChild(xLabel);

    const yLabel = document.createElementNS(svgns, "text");
    yLabel.setAttribute("x", 14);
    yLabel.setAttribute("y", margin.top + height / 2);
    yLabel.setAttribute("text-anchor", "middle");
    yLabel.setAttribute("font-size", "11");
    yLabel.setAttribute("transform", `rotate(-90 14 ${margin.top + height / 2})`);
    yLabel.textContent = "Prokaryotic fraction (%)";
    svg.appendChild(yLabel);
}

/* ---------- 04. Redundancy (reads) ---------- */

function addRedundancyReadsSection(parent, redundancyReads, depthPerSample) {
    if (!redundancyReads) {
        const div = document.createElement("div");
        div.className = "section";
        div.innerHTML = "<h2>4. Redundancy based on read overlap</h2><p class='small-note'>No redundancy metrics based on reads available.</p>";
        parent.appendChild(div);
        return;
    }

    const flag = redundancyReads.flag_redundancy_reads;
    const message = redundancyReads.message_redundancy_reads || "";

    const details = document.createElement("details");
    details.className = `section-details section-flag-${flagClass(flag)}`;
    details.open = true;

    const summary = document.createElement("summary");
    summary.innerHTML = `
        <div class="section-header">
            <div class="section-header-left">
                <span>4. Redundancy based on read overlap</span>
                <span class="section-badge ${flagClass(flag)}">Redundancy (reads)</span>
            </div>
            <div class="section-header-right">
                <span>${sectionStatus("redundancy (reads)", flag)}</span>
            </div>
        </div>
    `;
    details.appendChild(summary);

    const content = document.createElement("div");
    content.className = "section-content";

    const statsDiv = document.createElement("div");
    statsDiv.appendChild(mkSummaryStat("Samples in Mash clustering", fmtInt(redundancyReads.n_samples_in_clustering || 0)));
    statsDiv.appendChild(mkSummaryStat("Number of clusters", fmtInt(redundancyReads.n_clusters || 0)));
    statsDiv.appendChild(mkSummaryStat("Max cluster size", fmtInt(redundancyReads.max_cluster_size || 0)));
    statsDiv.appendChild(mkSummaryStat("Number of samples above LR target depth", fmtInt(redundancyReads.n_samples_above_lr_target || 0)));

    content.appendChild(statsDiv);

    const msgP = document.createElement("p");
    msgP.className = "summary-text";
    msgP.textContent = message;
    content.appendChild(msgP);

    const figContainer = document.createElement("div");
    figContainer.className = "chart-container";

    const figTitle = document.createElement("div");
    figTitle.className = "chart-title";
    figTitle.textContent = "Depth vs. redundancy groups (reads)";
    figContainer.appendChild(figTitle);

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.classList.add("chart");
    svg.setAttribute("id", "redundancy-reads-svg");
    figContainer.appendChild(svg);

    const caption = document.createElement("div");
    caption.className = "chart-caption";
    caption.textContent = "Samples are grouped by Mash clusters (potential co-assemblies). Vertical lines highlight cluster spans in depth.";
    figContainer.appendChild(caption);

    content.appendChild(figContainer);

    const note = mkSmallNote("Redundancy based on reads indicates whether multiple samples may contain similar communities and could be co-assembled.");
    content.appendChild(note);

    details.appendChild(content);
    parent.appendChild(details);

    const dataPerSample = (depthPerSample || []).filter(d =>
        d.total_reads !== null && d.total_reads !== undefined
    );

    if (!dataPerSample.length) {
        svg.outerHTML = `<div class="small-note">Per-sample read counts not available for redundancy plots.</div>`;
        return;
    }

    const margin = { top: 18, right: 8, bottom: 50, left: 60 };
    const innerWidth = svg.clientWidth || 800;
    const innerHeight = svg.clientHeight || 320;
    const width = innerWidth - margin.left - margin.right;
    const height = innerHeight - margin.top - margin.bottom;

    const maxDepth = dataPerSample.reduce((max, d) => {
        const v = Number(d.total_reads) || 0;
        return v > max ? v : max;
    }, 0);

    if (maxDepth <= 0) {
        svg.outerHTML = `<div class="small-note">All total reads are zero or missing; cannot draw redundancy plot.</div>`;
        return;
    }

    while (svg.firstChild) svg.removeChild(svg.firstChild);
    svg.setAttribute("viewBox", `0 0 ${innerWidth} ${innerHeight}`);
    const svgns = "http://www.w3.org/2000/svg";

    const g = document.createElementNS(svgns, "g");
    g.setAttribute("transform", `translate(${margin.left}, ${margin.top})`);

    const sorted = dataPerSample.slice().sort((a, b) => {
        const ca = a.cluster_reads;
        const cb = b.cluster_reads;
        if (ca === null || ca === undefined) return 1;
        if (cb === null || cb === undefined) return -1;
        if (ca === cb) {
            const da = Number(a.total_reads) || 0;
            const db = Number(b.total_reads) || 0;
            return da - db;
        }
        return ca - cb;
    });

    const n = sorted.length;
    const xStep = width / Math.max(1, n);
    const barWidth = Math.max(4, xStep * 0.6);

    const xTicks = 5;
    for (let i = 0; i <= xTicks; i++) {
        const t = i / xTicks;
        const x = t * width;
        const y = height;

        const grid = document.createElementNS(svgns, "line");
        grid.setAttribute("x1", x);
        grid.setAttribute("y1", 0);
        grid.setAttribute("x2", x);
        grid.setAttribute("y2", y);
        grid.setAttribute("stroke", "#eee");
        grid.setAttribute("stroke-width", "1");
        g.appendChild(grid);

        const label = document.createElementNS(svgns, "text");
        label.setAttribute("x", x);
        label.setAttribute("y", y + 16);
        label.setAttribute("text-anchor", "middle");
        label.setAttribute("font-size", "10");
        label.textContent = `#${Math.round(t * (n - 1) + 1)}`;
        g.appendChild(label);
    }

    const yTicks = 5;
    for (let i = 0; i <= yTicks; i++) {
        const t = i / yTicks;
        const y = height - t * height;

        const grid = document.createElementNS(svgns, "line");
        grid.setAttribute("x1", 0);
        grid.setAttribute("y1", y);
        grid.setAttribute("x2", width);
        grid.setAttribute("y2", y);
        grid.setAttribute("stroke", "#eee");
        grid.setAttribute("stroke-width", "1");
        g.appendChild(grid);

        const tick = document.createElementNS(svgns, "line");
        tick.setAttribute("x1", 0);
        tick.setAttribute("y1", y);
        tick.setAttribute("x2", -5);
        tick.setAttribute("y2", y);
        tick.setAttribute("stroke", "#555");
        tick.setAttribute("stroke-width", "1");
        g.appendChild(tick);

        const label = document.createElementNS(svgns, "text");
        label.setAttribute("x", -8);
        label.setAttribute("y", y + 3);
        label.setAttribute("text-anchor", "end");
        label.setAttribute("font-size", "10");
        label.textContent = fmtMillions(t * maxDepth);
        g.appendChild(label);
    }

    const xAxisLine = document.createElementNS(svgns, "line");
    xAxisLine.setAttribute("x1", 0);
    xAxisLine.setAttribute("y1", height);
    xAxisLine.setAttribute("x2", width);
    xAxisLine.setAttribute("y2", height);
    xAxisLine.setAttribute("stroke", "#333");
    xAxisLine.setAttribute("stroke-width", "1.5");
    g.appendChild(xAxisLine);

    const yAxisLine = document.createElementNS(svgns, "line");
    yAxisLine.setAttribute("x1", 0);
    yAxisLine.setAttribute("y1", 0);
    yAxisLine.setAttribute("x2", 0);
    yAxisLine.setAttribute("y2", height);
    yAxisLine.setAttribute("stroke", "#333");
    yAxisLine.setAttribute("stroke-width", "1.5");
    g.appendChild(yAxisLine);

    const tooltip = getOrCreateTooltip();

    sorted.forEach((d, i) => {
        const v = Number(d.total_reads) || 0;
        const x = i * xStep + (xStep - barWidth) / 2;
        const barHeight = (v / maxDepth) * height;
        const y = height - barHeight;

        const rect = document.createElementNS(svgns, "rect");
        rect.setAttribute("x", x);
        rect.setAttribute("y", y);
        rect.setAttribute("width", barWidth);
        rect.setAttribute("height", barHeight);
        rect.setAttribute("fill", "#9c27b0");
        rect.setAttribute("opacity", "0.8");

        rect.addEventListener("mousemove", (ev) => {
            tooltip.style.left = ev.clientX + "px";
            tooltip.style.top = ev.clientY + "px";
            tooltip.innerHTML = `
                <div class="tooltip-row"><span class="label">Sample</span><span class="value">${d.sample}</span></div>
                <div class="tooltip-row"><span class="label">Cluster (reads)</span><span class="value">${d.cluster_reads}</span></div>
                <div class="tooltip-row"><span class="label">Total reads</span><span class="value">${fmtMillions(v)}</span></div>
            `;
            tooltip.style.display = "block";
        });
        rect.addEventListener("mouseleave", () => {
            tooltip.style.display = "none";
        });

        g.appendChild(rect);
    });

    svg.appendChild(g);

    const xLabel = document.createElementNS(svgns, "text");
    xLabel.setAttribute("x", margin.left + width / 2);
    xLabel.setAttribute("y", innerHeight - 8);
    xLabel.setAttribute("text-anchor", "middle");
    xLabel.setAttribute("font-size", "11");
    xLabel.textContent = "Samples ordered by cluster and depth";
    svg.appendChild(xLabel);

    const yLabel = document.createElementNS(svgns, "text");
    yLabel.setAttribute("x", 14);
    yLabel.setAttribute("y", margin.top + height / 2);
    yLabel.setAttribute("text-anchor", "middle");
    yLabel.setAttribute("font-size", "11");
    yLabel.setAttribute("transform", `rotate(-90 14 ${margin.top + height / 2})`);
    yLabel.textContent = "Total reads per sample";
    svg.appendChild(yLabel);
}

/* ---------- 05. Redundancy (marker genes) ---------- */

function addRedundancyMarkersSection(parent, redundancyMarkers, redBiplotPerSample) {
    if (!redundancyMarkers) {
        const div = document.createElement("div");
        div.className = "section";
        div.innerHTML = "<h2>5. Redundancy based on marker genes</h2><p class='small-note'>No redundancy metrics based on marker genes available.</p>";
        parent.appendChild(div);
        return;
    }

    const flag = redundancyMarkers.flag_redundancy_markers;
    const message = redundancyMarkers.message_redundancy_markers || "";

    const details = document.createElement("details");
    details.className = `section-details section-flag-${flagClass(flag)}`;
    details.open = true;

    const summary = document.createElement("summary");
    summary.innerHTML = `
        <div class="section-header">
            <div class="section-header-left">
                <span>5. Redundancy based on marker genes</span>
                <span class="section-badge ${flagClass(flag)}">Redundancy (markers)</span>
            </div>
            <div class="section-header-right">
                <span>${sectionStatus("redundancy (marker genes)", flag)}</span>
            </div>
        </div>
    `;
    details.appendChild(summary);

    const content = document.createElement("div");
    content.className = "section-content";

    const statsDiv = document.createElement("div");
    statsDiv.appendChild(mkSummaryStat("Samples in marker-based clustering", fmtInt(redundancyMarkers.n_samples_in_clustering || 0)));
    statsDiv.appendChild(mkSummaryStat("Number of clusters", fmtInt(redundancyMarkers.n_clusters || 0)));
    statsDiv.appendChild(mkSummaryStat("Max cluster size", fmtInt(redundancyMarkers.max_cluster_size || 0)));
    statsDiv.appendChild(mkSummaryStat("Number of samples above LR target depth", fmtInt(redundancyMarkers.n_samples_above_lr_target || 0)));

    content.appendChild(statsDiv);

    const msgP = document.createElement("p");
    msgP.className = "summary-text";
    msgP.textContent = message;
    content.appendChild(msgP);

    const figContainer = document.createElement("div");
    figContainer.className = "chart-container";

    const figTitle = document.createElement("div");
    figTitle.className = "chart-title";
    figTitle.textContent = "Marker-based redundancy and coverage vs. LR target";
    figContainer.appendChild(figTitle);

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.classList.add("chart");
    svg.setAttribute("id", "lr-target-markers-svg");
    figContainer.appendChild(svg);

    const caption = document.createElement("div");
    caption.className = "chart-caption";
    caption.textContent = "Each point is a sample, colored by cluster; the x-axis is estimated coverage from marker genes, and the y-axis is coverage relative to the LR target.";
    figContainer.appendChild(caption);

    content.appendChild(figContainer);

    const note = mkSmallNote("Redundancy based on marker genes considers deeper taxonomic/functional similarity and how close samples are to a long-read sequencing target.");
    content.appendChild(note);

    details.appendChild(content);
    parent.appendChild(details);

    const svgEl = svg;

    if (!redBiplotPerSample || !redBiplotPerSample.length) {
        svgEl.outerHTML = `<div class="small-note">Marker-based redundancy biplot data not available.</div>`;
        return;
    }

    const margin = { top: 20, right: 8, bottom: 45, left: 60 };
    const innerWidth = svgEl.clientWidth || 800;
    const innerHeight = svgEl.clientHeight || 320;
    const width = innerWidth - margin.left - margin.right;
    const height = innerHeight - margin.top - margin.bottom;

    let maxCoverage = 0;
    let maxRatio = 0;

    redBiplotPerSample.forEach(d => {
        const cov = d.coverage_markers != null ? Number(d.coverage_markers) : null;
        let ratio = null;
        if (cov != null && cov > 0) {
            ratio = cov / 0.95;
        }
        if (cov != null && cov > maxCoverage) maxCoverage = cov;
        if (ratio != null && ratio > maxRatio) maxRatio = ratio;
    });

    if (maxCoverage <= 0) {
        svgEl.outerHTML = `<div class="small-note">Coverage estimates from marker genes are zero or missing; cannot draw LR target plot.</div>`;
        return;
    }

    if (maxRatio <= 0) {
        maxRatio = 1;
    }

    while (svgEl.firstChild) svgEl.removeChild(svgEl.firstChild);
    svgEl.setAttribute("viewBox", `0 0 ${innerWidth} ${innerHeight}`);
    const svgns = "http://www.w3.org/2000/svg";

    const g = document.createElementNS(svgns, "g");
    g.setAttribute("transform", `translate(${margin.left}, ${margin.top})`);

    const xTicks = 5;
    for (let i = 0; i <= xTicks; i++) {
        const t = i / xTicks;
        const x = t * width;
        const y = height;

        const grid = document.createElementNS(svgns, "line");
        grid.setAttribute("x1", x);
        grid.setAttribute("y1", 0);
        grid.setAttribute("x2", x);
        grid.setAttribute("y2", y);
        grid.setAttribute("stroke", "#eee");
        grid.setAttribute("stroke-width", "1");
        g.appendChild(grid);

        const tick = document.createElementNS(svgns, "line");
        tick.setAttribute("x1", x);
        tick.setAttribute("y1", y);
        tick.setAttribute("x2", x);
        tick.setAttribute("y2", y + 5);
        tick.setAttribute("stroke", "#555");
        tick.setAttribute("stroke-width", "1");
        g.appendChild(tick);

        const label = document.createElementNS(svgns, "text");
        label.setAttribute("x", x);
        label.setAttribute("y", y + 18);
        label.setAttribute("text-anchor", "middle");
        label.setAttribute("font-size", "10");
        label.textContent = fmtPercent(t * maxCoverage, 1);
        g.appendChild(label);
    }

    const yTicks = 5;
    for (let i = 0; i <= yTicks; i++) {
        const t = i / yTicks;
        const y = height - t * height;

        const grid = document.createElementNS(svgns, "line");
        grid.setAttribute("x1", 0);
        grid.setAttribute("y1", y);
        grid.setAttribute("x2", width);
        grid.setAttribute("y2", y);
        grid.setAttribute("stroke", "#eee");
        grid.setAttribute("stroke-width", "1");
        g.appendChild(grid);

        const tick = document.createElementNS(svgns, "line");
        tick.setAttribute("x1", 0);
        tick.setAttribute("y1", y);
        tick.setAttribute("x2", -5);
        tick.setAttribute("y2", y);
        tick.setAttribute("stroke", "#555");
        tick.setAttribute("stroke-width", "1");
        g.appendChild(tick);

        const label = document.createElementNS(svgns, "text");
        label.setAttribute("x", -8);
        label.setAttribute("y", y + 3);
        label.setAttribute("text-anchor", "end");
        label.setAttribute("font-size", "10");
        label.textContent = fmtFloat(t * maxRatio, 2);
        g.appendChild(label);
    }

    const xAxisLine = document.createElementNS(svgns, "line");
    xAxisLine.setAttribute("x1", 0);
    xAxisLine.setAttribute("y1", height);
    xAxisLine.setAttribute("x2", width);
    xAxisLine.setAttribute("y2", height);
    xAxisLine.setAttribute("stroke", "#333");
    xAxisLine.setAttribute("stroke-width", "1.5");
    g.appendChild(xAxisLine);

    const yAxisLine = document.createElementNS(svgns, "line");
    yAxisLine.setAttribute("x1", 0);
    yAxisLine.setAttribute("y1", 0);
    yAxisLine.setAttribute("x2", 0);
    yAxisLine.setAttribute("y2", height);
    yAxisLine.setAttribute("stroke", "#333");
    yAxisLine.setAttribute("stroke-width", "1.5");
    g.appendChild(yAxisLine);

    const targetLine = document.createElementNS(svgns, "line");
    const targetY = height - (1 / maxRatio) * height;
    targetLine.setAttribute("x1", 0);
    targetLine.setAttribute("y1", targetY);
    targetLine.setAttribute("x2", width);
    targetLine.setAttribute("y2", targetY);
    targetLine.setAttribute("stroke", "#f44336");
    targetLine.setAttribute("stroke-width", "2");
    targetLine.setAttribute("stroke-dasharray", "4,4");
    g.appendChild(targetLine);

    const targetLabel = document.createElementNS(svgns, "text");
    targetLabel.setAttribute("x", width - 4);
    targetLabel.setAttribute("y", targetY - 4);
    targetLabel.setAttribute("text-anchor", "end");
    targetLabel.setAttribute("font-size", "10");
    targetLabel.setAttribute("fill", "#f44336");
    targetLabel.textContent = "LR target";
    g.appendChild(targetLabel);

    const tooltip = getOrCreateTooltip();

    const clusterColors = {};
    const clusterNames = [];
    let nextHue = 0;

    function getClusterColor(clusterId) {
        if (clusterId === null || clusterId === undefined) {
            return "#9e9e9e";
        }
        const key = String(clusterId);
        if (!(key in clusterColors)) {
            const hue = nextHue;
            nextHue = (nextHue + 137) % 360;
            clusterColors[key] = `hsl(${hue}, 70%, 50%)`;
            clusterNames.push(key);
        }
        return clusterColors[key];
    }

    redBiplotPerSample.forEach(d => {
        const cov = d.coverage_markers != null ? Number(d.coverage_markers) : null;
        let ratio = null;
        if (cov != null && cov > 0) {
            ratio = cov / 0.95;
        }

        if (cov == null || ratio == null) return;

        const x = (cov / maxCoverage) * width;
        const y = height - (ratio / maxRatio) * height;

        const clusterId = d.cluster_markers;
        const fillColor = getClusterColor(clusterId);

        const circle = document.createElementNS(svgns, "circle");
        circle.setAttribute("cx", x);
        circle.setAttribute("cy", y);
        circle.setAttribute("r", 4);
        circle.setAttribute("fill", fillColor);
        circle.setAttribute("opacity", "0.8");

        circle.addEventListener("mousemove", (ev) => {
            tooltip.style.left = ev.clientX + "px";
            tooltip.style.top = ev.clientY + "px";
            tooltip.innerHTML = `
                <div class="tooltip-row"><span class="label">Sample</span><span class="value">${d.sample}</span></div>
                <div class="tooltip-row"><span class="label">Cluster (markers)</span><span class="value">${clusterId == null ? "NA" : clusterId}</span></div>
                <div class="tooltip-row"><span class="label">Coverage (markers)</span><span class="value">${fmtPercent(cov, 1)}</span></div>
                <div class="tooltip-row"><span class="label">Coverage / LR target</span><span class="value">${fmtFloat(ratio, 2)}</span></div>
            `;
            tooltip.style.display = "block";
        });
        circle.addEventListener("mouseleave", () => {
            tooltip.style.display = "none";
        });

        g.appendChild(circle);
    });

    svgEl.appendChild(g);

    const legendGroup = document.createElementNS(svgns, "g");
    const legendX = margin.left + 4;
    let legendY = margin.top - 8;

    const legendTitle = document.createElementNS(svgns, "text");
    legendTitle.setAttribute("x", legendX);
    legendTitle.setAttribute("y", legendY);
    legendTitle.setAttribute("text-anchor", "start");
    legendTitle.setAttribute("font-size", "10");
    legendTitle.setAttribute("fill", "#333");
    legendTitle.textContent = "Clusters (markers):";
    legendGroup.appendChild(legendTitle);

    legendY += 12;

    const maxLegendItems = 8;
    const displayClusters = clusterNames.slice(0, maxLegendItems);
    const hasMoreClusters = clusterNames.length > maxLegendItems;

    displayClusters.forEach((clusterId, index) => {
        const group = document.createElementNS(svgns, "g");
        const rowY = legendY + index * 12;

        const rect = document.createElementNS(svgns, "rect");
        rect.setAttribute("x", legendX);
        rect.setAttribute("y", rowY - 8);
        rect.setAttribute("width", 10);
        rect.setAttribute("height", 10);
        rect.setAttribute("fill", clusterColors[clusterId]);
        rect.setAttribute("stroke", "#333");
        rect.setAttribute("stroke-width", "0.5");
        group.appendChild(rect);

        const text = document.createElementNS(svgns, "text");
        text.setAttribute("x", legendX + 14);
        text.setAttribute("y", rowY);
        text.setAttribute("text-anchor", "start");
        text.setAttribute("font-size", "10");
        text.textContent = `cluster ${clusterId}`;
        group.appendChild(text);

        legendGroup.appendChild(group);
    });

    if (hasMoreClusters) {
        const extraIndex = displayClusters.length;
        const rowY = legendY + extraIndex * 12;
        const text = document.createElementNS(svgns, "text");
        text.setAttribute("x", legendX);
        text.setAttribute("y", rowY);
        text.setAttribute("text-anchor", "start");
        text.setAttribute("font-size", "10");
        text.textContent = `(+ ${clusterNames.length - maxLegendItems} more clusters)`;
        legendGroup.appendChild(text);
    }

    svgEl.appendChild(legendGroup);

    const xLabel = document.createElementNS(svgns, "text");
    xLabel.setAttribute("x", margin.left + width / 2);
    xLabel.setAttribute("y", innerHeight - 8);
    xLabel.setAttribute("text-anchor", "middle");
    xLabel.setAttribute("font-size", "11");
    xLabel.textContent = "Coverage from marker genes (%)";
    svgEl.appendChild(xLabel);

    const yLabel = document.createElementNS(svgns, "text");
    yLabel.setAttribute("x", 14);
    yLabel.setAttribute("y", margin.top + height / 2);
    yLabel.setAttribute("text-anchor", "middle");
    yLabel.setAttribute("font-size", "11");
    yLabel.setAttribute("transform", `rotate(-90 14 ${margin.top + height / 2})`);
    yLabel.textContent = "Coverage / LR target";
    svgEl.appendChild(yLabel);
}

/* ---------- 06. Clusters table ---------- */

function addClustersSection(parent, clusters) {
    const details = document.createElement("details");
    details.className = "section-details section-flag-1";
    details.open = true;

    const summary = document.createElement("summary");
    summary.innerHTML = `
        <div class="section-header">
            <div class="section-header-left">
                <span>6. Mash clusters and potential co-assemblies</span>
                <span class="section-badge flag-1">Summary of candidate co-assemblies</span>
            </div>
            <div class="section-header-right">
                <span>😊 Overview: table of clusters based on Mash distance.</span>
            </div>
        </div>
    `;
    details.appendChild(summary);

    const content = document.createElement("div");
    content.className = "section-content";

    if (!clusters || !clusters.clusters || !clusters.clusters.length) {
        const note = mkSmallNote("No cluster information is available in the distilled JSON.");
        content.appendChild(note);
        details.appendChild(content);
        parent.appendChild(details);
        return;
    }

    const statsDiv = document.createElement("div");
    statsDiv.appendChild(mkSummaryStat("Number of clusters (reads)", fmtInt(clusters.n_clusters_reads || 0)));
    statsDiv.appendChild(mkSummaryStat("Number of clusters (markers)", fmtInt(clusters.n_clusters_markers || 0)));
    statsDiv.appendChild(mkSummaryStat("Max cluster size (reads)", fmtInt(clusters.max_cluster_size_reads || 0)));
    statsDiv.appendChild(mkSummaryStat("Max cluster size (markers)", fmtInt(clusters.max_cluster_size_markers || 0)));
    statsDiv.appendChild(mkSummaryStat("Total samples in clusters", fmtInt(clusters.n_samples_in_clusters || 0)));

    content.appendChild(statsDiv);

    const msg = clusters.message_clusters || "Clusters group samples that may be suitable for co-assembly, based on read similarity and/or marker gene profiles.";
    const msgP = document.createElement("p");
    msgP.className = "summary-text";
    msgP.textContent = msg;
    content.appendChild(msgP);

    const table = document.createElement("table");
    table.className = "clusters-table";

    const thead = document.createElement("thead");
    thead.innerHTML = `
        <tr>
            <th>Cluster ID</th>
            <th>Type</th>
            <th># Samples</th>
            <th>Total reads (M)</th>
            <th>Mean depth (M)</th>
            <th>Notes</th>
            <th>Samples</th>
        </tr>
    `;
    table.appendChild(thead);

    const tbody = document.createElement("tbody");

    clusters.clusters.forEach(cl => {
        const tr = document.createElement("tr");

        const tdId = document.createElement("td");
        tdId.textContent = cl.cluster_id != null ? cl.cluster_id : "NA";
        tr.appendChild(tdId);

        const tdType = document.createElement("td");
        tdType.textContent = cl.type || "NA";
        tr.appendChild(tdType);

        const tdNSamples = document.createElement("td");
        tdNSamples.textContent = fmtInt(cl.n_samples || 0);
        tr.appendChild(tdNSamples);

        const tdTotalReads = document.createElement("td");
        tdTotalReads.textContent = fmtFloat(cl.total_reads_m || 0, 2);
        tr.appendChild(tdTotalReads);

        const tdMeanDepth = document.createElement("td");
        tdMeanDepth.textContent = fmtFloat(cl.mean_depth_m || 0, 2);
        tr.appendChild(tdMeanDepth);

        const tdNotes = document.createElement("td");
        tdNotes.textContent = cl.notes || "";
        tr.appendChild(tdNotes);

        const tdSamples = document.createElement("td");
        tdSamples.className = "samples-cell";
        if (cl.samples && cl.samples.length) {
            tdSamples.textContent = cl.samples.join(", ");
        } else {
            tdSamples.textContent = "NA";
        }
        tr.appendChild(tdSamples);

        tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    content.appendChild(table);

    const note = mkSmallNote("Clusters are potential co-assembly groups. You may consider co-assembling samples within a cluster, especially if they share similar environments and show high redundancy.");
    content.appendChild(note);

    details.appendChild(content);
    parent.appendChild(details);
}

/* ---------- Main entry ---------- */

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

    addReportHeader(distill, depthPerSample);

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
        help="Path to distill.json (output of distill_results.py).",
    )
    parser.add_argument(
        "--figures-json",
        required=True,
        help="Path to figures.json (per-sample figure data).",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output HTML file.",
    )

    args = parser.parse_args()

    distill_path = Path(args.distill_json)
    figures_path = Path(args.figures_json)

    with distill_path.open("r", encoding="utf-8") as f:
        distill_data = json.load(f)

    with figures_path.open("r", encoding="utf-8") as f:
        figures_data = json.load(f)

    distill_json_str = json.dumps(distill_data, separators=(",", ":"), ensure_ascii=False)
    figures_json_str = json.dumps(figures_data, separators=(",", ":"), ensure_ascii=False)

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
