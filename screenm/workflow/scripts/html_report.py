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
        white-space: nowrap;
        transform: translate(8px, -20px);
    }

    .highlight-summary {
        display: flex;
        gap: 24px;
        justify-content: center;
        margin: 12px 0 24px 0;
        flex-wrap: wrap;
    }

    .highlight-item {
        min-width: 180px;
        padding: 10px 14px;
        border-radius: 8px;
        background: #ffffff;
        border: 1px solid #dddddd;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        text-align: center;
    }

    .highlight-label {
        font-size: 0.85em;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        color: #666;
        margin-bottom: 4px;
    }

    .highlight-value {
        font-size: 1.6em;
        font-weight: 650;
    }

    .report-footer {
        margin-top: 32px;
        padding-top: 12px;
        border-top: 1px solid #ddd;
        font-size: 0.85em;
        color: #555;
    }
</style>

</head>
<body>

<h1>ScreenM Summary Report</h1>

<p class="section-intro" id="report-intro">
    This report summarises metagenomic screening results across samples. CheckM is typically used downstream
    to evaluate the completeness and contamination of metagenome-assembled genomes (MAGs); it is not run
    here, but its genome-quality estimates provide useful context when interpreting the depth and coverage
    metrics below.
</p>

<div id="top-highlights"></div>

<div id="summary-sections"></div>

<footer class="report-footer">
    <p>
        Report generated by ScreenM from <code>distill.json</code> and <code>figures.json</code>.
        Coverage estimates rely on Nonpareil; prokaryotic fractions are based on SingleM; genome bin quality
        should be assessed separately with tools such as CheckM.
    </p>
</footer>


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

function renderTopHighlights(parent, totalSamples, totalReads) {
    if (!parent) return;
    if (totalSamples == null && totalReads == null) return;

    const container = document.createElement("div");
    container.className = "highlight-summary";

    let innerHTML = "";
    if (totalSamples != null) {
        innerHTML += `
            <div class="highlight-item">
                <div class="highlight-label">Samples</div>
                <div class="highlight-value">${fmtInt(totalSamples)}</div>
            </div>
        `;
    }
    if (totalReads != null) {
        innerHTML += `
            <div class="highlight-item">
                <div class="highlight-label">Total reads</div>
                <div class="highlight-value">${fmtMillions(totalReads)}</div>
            </div>
        `;
    }

    container.innerHTML = innerHTML;
    parent.appendChild(container);
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
                    coloured green if above the screening threshold and red if below. A horizontal dashed line
                    indicates the median sequencing depth; another dashed line marks the read threshold.
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

    const thresholdReads = Number(data.reads_threshold) || null;

    const maxReads = Math.max(
        ...perSample.map(d => Number(d.total_reads) || 0),
        thresholdReads || 0,
        Number(data.median_reads) || 0
    );
    if (!(maxReads > 0)) {
        svg.outerHTML = `<div class="small-note">Sequencing depth summary is not available.</div>`;
        return;
    }

    const x0 = margin.left;
    const y0 = height - margin.bottom;

    function yForValue(v) {
        const frac = Math.max(0, Math.min(1, v / maxReads));
        return y0 - frac * plotH;
    }

    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

    const xAxis = document.createElementNS(svgns, "line");
    xAxis.setAttribute("x1", x0);
    xAxis.setAttribute("y1", y0);
    xAxis.setAttribute("x2", x0 + plotW);
    xAxis.setAttribute("y2", y0);
    xAxis.setAttribute("stroke", "#555");
    xAxis.setAttribute("stroke-width", "1");
    svg.appendChild(xAxis);

    const yAxis = document.createElementNS(svgns, "line");
    yAxis.setAttribute("x1", x0);
    yAxis.setAttribute("y1", margin.top);
    yAxis.setAttribute("x2", x0);
    yAxis.setAttribute("y2", y0);
    yAxis.setAttribute("stroke", "#555");
    yAxis.setAttribute("stroke-width", "1");
    svg.appendChild(yAxis);

    const ticks = 5;
    for (let i = 0; i <= ticks; i++) {
        const frac = i / ticks;
        const y = y0 - frac * plotH;
        const val = maxReads * frac;
        const line = document.createElementNS(svgns, "line");
        line.setAttribute("x1", x0 - 4);
        line.setAttribute("y1", y);
        line.setAttribute("x2", x0);
        line.setAttribute("y2", y);
        line.setAttribute("stroke", "#555");
        line.setAttribute("stroke-width", "1");
        svg.appendChild(line);

        const label = document.createElementNS(svgns, "text");
        label.setAttribute("x", x0 - 6);
        label.setAttribute("y", y + 4);
        label.setAttribute("font-size", "10");
        label.setAttribute("text-anchor", "end");
        label.textContent = fmtMillions(val);
        svg.appendChild(label);
    }

    const ylabel = document.createElementNS(svgns, "text");
    ylabel.setAttribute("x", 16);
    ylabel.setAttribute("y", margin.top + plotH / 2);
    ylabel.setAttribute("text-anchor", "middle");
    ylabel.setAttribute("font-size", "11");
    ylabel.setAttribute("transform", `rotate(-90 16 ${margin.top + plotH / 2})`);
    ylabel.textContent = "Reads per sample";
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
        const reads = Number(d.total_reads) || 0;
        const xCenter = x0 + step * i + step / 2;
        const x = xCenter - barWidth / 2;
        const y = yForValue(reads);
        const hBar = y0 - y;

        const aboveThr = thresholdReads ? reads >= thresholdReads : true;
        const color = aboveThr ? "#4caf50" : "#c62828";

        const rect = document.createElementNS(svgns, "rect");
        rect.setAttribute("x", x);
        rect.setAttribute("y", y);
        rect.setAttribute("width", barWidth);
        rect.setAttribute("height", hBar);
        rect.setAttribute("fill", color);
        rect.setAttribute("fill-opacity", "0.9");
        rect.style.cursor = "pointer";
        svg.appendChild(rect);

        const tooltipText =
            `${d.sample}\n` +
            `Total reads: ${fmtMillions(reads)}`;

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
        line.setAttribute("stroke", "#1976d2");
        line.setAttribute("stroke-width", "1.2");
        line.setAttribute("stroke-dasharray", "3,2");
        svg.appendChild(line);

        const lab = document.createElementNS(svgns, "text");
        lab.setAttribute("x", x0 + plotW - 4);
        lab.setAttribute("y", y - 2);
        lab.setAttribute("font-size", "10");
        lab.setAttribute("text-anchor", "end");
        lab.setAttribute("fill", "#1976d2");
        lab.textContent = `median (${fmtMillions(medianDepth)})`;
        svg.appendChild(lab);
    }

    if (thresholdReads && thresholdReads > 0) {
        const y = yForValue(thresholdReads);
        const line = document.createElementNS(svgns, "line");
        line.setAttribute("x1", x0);
        line.setAttribute("y1", y);
        line.setAttribute("x2", x0 + plotW);
        line.setAttribute("y2", y);
        line.setAttribute("stroke", "#424242");
        line.setAttribute("stroke-width", "1.2");
        line.setAttribute("stroke-dasharray", "4,2");
        svg.appendChild(line);

        const lab = document.createElementNS(svgns, "text");
        lab.setAttribute("x", x0 + plotW - 4);
        lab.setAttribute("y", y - 2);
        lab.setAttribute("font-size", "10");
        lab.setAttribute("text-anchor", "end");
        lab.setAttribute("fill", "#424242");
        lab.textContent = `threshold (${fmtMillions(thresholdReads)})`;
        svg.appendChild(lab);
    }
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
                    Bars show per-sample removed fractions, coloured green (&le; 5%), yellow (5–20%) or
                    red (&gt; 20%). Horizontal dashed lines mark 5% and 20% thresholds, and the median
                    removed fraction is shown as a blue dashed line.
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

    const maxFrac = Math.max(
        ...perSample.map(d => Number(d.fraction_low_quality_of_total) || 0),
        Number(meanFrac) || 0,
        Number(medianFrac) || 0,
    );
    if (!(maxFrac > 0)) {
        svg.outerHTML = `<div class="small-note">Sequencing quality summary is not available.</div>`;
        return;
    }

    const THRESH_GOOD = 0.05;
    const THRESH_MOD = 0.20;

    function yForFrac(frac) {
        const f = Math.max(0, Math.min(maxFrac, frac));
        return y0 - (f / maxFrac) * plotH;
    }

    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

    const xAxis = document.createElementNS(svgns, "line");
    xAxis.setAttribute("x1", x0);
    xAxis.setAttribute("y1", y0);
    xAxis.setAttribute("x2", x0 + plotW);
    xAxis.setAttribute("y2", y0);
    xAxis.setAttribute("stroke", "#555");
    xAxis.setAttribute("stroke-width", "1");
    svg.appendChild(xAxis);

    const yAxis = document.createElementNS(svgns, "line");
    yAxis.setAttribute("x1", x0);
    yAxis.setAttribute("y1", margin.top);
    yAxis.setAttribute("x2", x0);
    yAxis.setAttribute("y2", y0);
    yAxis.setAttribute("stroke", "#555");
    yAxis.setAttribute("stroke-width", "1");
    svg.appendChild(yAxis);

    const ticks = 5;
    for (let i = 0; i <= ticks; i++) {
        const frac = i / ticks;
        const y = y0 - frac * plotH;
        const val = maxFrac * frac;
        const line = document.createElementNS(svgns, "line");
        line.setAttribute("x1", x0 - 4);
        line.setAttribute("y1", y);
        line.setAttribute("x2", x0);
        line.setAttribute("y2", y);
        line.setAttribute("stroke", "#555");
        line.setAttribute("stroke-width", "1");
        svg.appendChild(line);

        const label = document.createElementNS(svgns, "text");
        label.setAttribute("x", x0 - 6);
        label.setAttribute("y", y + 4);
        label.setAttribute("font-size", "10");
        label.setAttribute("text-anchor", "end");
        label.textContent = (val * 100).toFixed(1) + "%";
        svg.appendChild(label);
    }

    const ylabel = document.createElementNS(svgns, "text");
    ylabel.setAttribute("x", 16);
    ylabel.setAttribute("y", margin.top + plotH / 2);
    ylabel.setAttribute("text-anchor", "middle");
    ylabel.setAttribute("font-size", "11");
    ylabel.setAttribute("transform", `rotate(-90 16 ${margin.top + plotH / 2})`);
    ylabel.textContent = "Removed reads (% of total)";
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

        let color;
        if (frac <= THRESH_GOOD) {
            color = "#2e7d32";
        } else if (frac <= THRESH_MOD) {
            color = "#f9a825";
        } else {
            color = "#c62828";
        }

        const rect = document.createElementNS(svgns, "rect");
        rect.setAttribute("x", x);
        rect.setAttribute("y", y);
        rect.setAttribute("width", barWidth);
        rect.setAttribute("height", hBar);
        rect.setAttribute("fill", color);
        rect.setAttribute("fill-opacity", "0.9");
        rect.style.cursor = "pointer";

        const tooltipText =
            `${d.sample}\n` +
            `Removed: ${(frac * 100).toFixed(2)}%`;

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
            lab.setAttribute("y", y0 + 10);
            lab.setAttribute("font-size", "9");
            lab.setAttribute("text-anchor", "end");
            lab.setAttribute("transform", `rotate(-60 ${xCenter} ${y0 + 10})`);
            lab.textContent = d.sample;
            svg.appendChild(lab);
        }
    });

    const thresholds = [
        {frac: THRESH_GOOD, color: "#2e7d32", label: "5%"},
        {frac: THRESH_MOD,  color: "#c62828", label: "20%"}
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

    const medianRemoved = Number(medianFrac) || 0;
    if (medianRemoved > 0) {
        const y = yForFrac(medianRemoved);
        const line = document.createElementNS(svgns, "line");
        line.setAttribute("x1", x0);
        line.setAttribute("y1", y);
        line.setAttribute("x2", x0 + plotW);
        line.setAttribute("y2", y);
        line.setAttribute("stroke", "#1976d2");
        line.setAttribute("stroke-width", "1.2");
        line.setAttribute("stroke-dasharray", "3,2");
        svg.appendChild(line);

        const lab = document.createElementNS(svgns, "text");
        lab.setAttribute("x", x0 + plotW - 4);
        lab.setAttribute("y", y - 2);
        lab.setAttribute("font-size", "10");
        lab.setAttribute("text-anchor", "end");
        lab.setAttribute("fill", "#1976d2");
        lab.textContent = `median (${(medianRemoved * 100).toFixed(1)}%)`;
        svg.appendChild(lab);
    }
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
                    <svg id="prok-depth-svg" class="prok-depth-svg" viewBox="0 0 1000 320" preserveAspectRatio="none"></svg>
                </div>
                <p class="small-note">
                    X axis: samples; Y axis: fraction of total reads. Bars are stacked into low-quality (red),
                    prokaryotic (green/yellow/red depending on the fraction), and other QC-passing reads (grey).
                    Horizontal dashed lines mark 50% (yellow) and 90% (green) prokaryotic fraction; the blue dashed line
                    shows the median prokaryotic fraction. Hover over bars for exact fractions and estimated read counts.
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

    const THRESH_PROK_MOD = 0.50;
    const THRESH_PROK_HIGH = 0.90;

    function yForFrac(frac) {
        const f = Math.max(0, Math.min(1, frac));
        return y0 - f * plotH;
    }

    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

    const xAxis = document.createElementNS(svgns, "line");
    xAxis.setAttribute("x1", x0);
    xAxis.setAttribute("y1", y0);
    xAxis.setAttribute("x2", x0 + plotW);
    xAxis.setAttribute("y2", y0);
    xAxis.setAttribute("stroke", "#555");
    xAxis.setAttribute("stroke-width", "1");
    svg.appendChild(xAxis);

    const yAxis = document.createElementNS(svgns, "line");
    yAxis.setAttribute("x1", x0);
    yAxis.setAttribute("y1", margin.top);
    yAxis.setAttribute("x2", x0);
    yAxis.setAttribute("y2", y0);
    yAxis.setAttribute("stroke", "#555");
    yAxis.setAttribute("stroke-width", "1");
    svg.appendChild(yAxis);

    const ticks = 5;
    for (let i = 0; i <= ticks; i++) {
        const frac = i / ticks;
        const y = y0 - frac * plotH;
        const line = document.createElementNS(svgns, "line");
        line.setAttribute("x1", x0 - 4);
        line.setAttribute("y1", y);
        line.setAttribute("x2", x0);
        line.setAttribute("y2", y);
        line.setAttribute("stroke", "#555");
        line.setAttribute("stroke-width", "1");
        svg.appendChild(line);

        const label = document.createElementNS(svgns, "text");
        label.setAttribute("x", x0 - 6);
        label.setAttribute("y", y + 4);
        label.setAttribute("font-size", "10");
        label.setAttribute("text-anchor", "end");
        label.textContent = (frac * 100).toFixed(0) + "%";
        svg.appendChild(label);
    }

    const ylabel = document.createElementNS(svgns, "text");
    ylabel.setAttribute("x", 16);
    ylabel.setAttribute("y", margin.top + plotH / 2);
    ylabel.setAttribute("text-anchor", "middle");
    ylabel.setAttribute("font-size", "11");
    ylabel.setAttribute("transform", `rotate(-90 16 ${margin.top + plotH / 2})`);
    ylabel.textContent = "Fraction of reads";
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

        let prokColor;
        if (fracProk >= THRESH_PROK_HIGH) {
            prokColor = "#2e7d32";
        } else if (fracProk >= THRESH_PROK_MOD) {
            prokColor = "#f9a825";
        } else {
            prokColor = "#c62828";
        }
        const segProk = makeSeg(hProk, prokColor);

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
        });

        [segLow, segProk, segOther].forEach(seg => {
            if (seg) svg.appendChild(seg);
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

    const thresholds = [
        {frac: THRESH_PROK_MOD,  color: "#f9a825", label: "50%"},
        {frac: THRESH_PROK_HIGH, color: "#2e7d32", label: "90%"}
    ];
    thresholds.forEach(t => {
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

    const medianProkFrac = (Number(data.median_prokaryotic_fraction) || 0) / 100;
    if (medianProkFrac > 0) {
        const y = yForFrac(medianProkFrac);
        const line = document.createElementNS(svgns, "line");
        line.setAttribute("x1", x0);
        line.setAttribute("y1", y);
        line.setAttribute("x2", x0 + plotW);
        line.setAttribute("y2", y);
        line.setAttribute("stroke", "#1976d2");
        line.setAttribute("stroke-width", "1.2");
        line.setAttribute("stroke-dasharray", "3,2");
        svg.appendChild(line);

        const lab = document.createElementNS(svgns, "text");
        lab.setAttribute("x", x0 + plotW - 4);
        lab.setAttribute("y", y - 2);
        lab.setAttribute("font-size", "10");
        lab.setAttribute("text-anchor", "end");
        lab.setAttribute("fill", "#1976d2");
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

    const status = sectionStatus("Overall metagenomic coverage", data.flag_redundancy);

    div.innerHTML = `
        <h2 class="section-title">Overall metagenomic coverage</h2>
        <p class="section-intro">
            This section evaluates how close the sequencing depth is to the Nonpareil LR target for metagenomic reads.
        </p>
        <details>
            <summary>
                <span class="status-emoji">${status.emoji}</span>
                <span class="status-text">${status.text}</span>
            </summary>
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
    const perSample = (depthPerSample || [])
        .filter(d => d.total_reads !== null && d.total_reads !== undefined);

    if (!perSample.length) {
        svg.outerHTML = `<div class="small-note">Per-sample read counts not available for LR-versus-depth plot.</div>`;
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

    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

    const combined = perSample.map(d => {
        const observed = d.total_reads || 0;
        const target = d.lr_target_reads || 0;
        const ratio = (target > 0 && observed > 0) ? (observed / target) : null;
        let coverage = d.lr_coverage_fraction || null;
        if (coverage == null || coverage === undefined) {
            coverage = null;
        }
        return { sample: d.sample, observed, target, ratio, coverage };
    }).filter(d => d.ratio !== null);

    if (!combined.length) {
        svg.outerHTML = `<div class="small-note">LR-versus-depth information not available for metagenomic reads.</div>`;
        return;
    }

    function transformRatio(ratio) {
        if (ratio >= 1) {
            return Math.log10(ratio);
        } else {
            return -Math.log10(1 / ratio);
        }
    }

    let maxAbs = 0;
    combined.forEach(d => {
        const v = transformRatio(d.ratio);
        maxAbs = Math.max(maxAbs, Math.abs(v));
    });
    maxAbs = Math.max(maxAbs, 1);

    function yForVal(v) {
        const frac = (v + maxAbs) / (2 * maxAbs);
        return y0 - frac * plotH;
    }

    const baselineY = yForVal(0);

    const xAxis = document.createElementNS(svgns, "line");
    xAxis.setAttribute("x1", x0);
    xAxis.setAttribute("y1", baselineY);
    xAxis.setAttribute("x2", x0 + plotW);
    xAxis.setAttribute("y2", baselineY);
    xAxis.setAttribute("stroke", "#555");
    xAxis.setAttribute("stroke-width", "1");
    svg.appendChild(xAxis);

    for (let sign of [1, -1]) {
        for (let i = 1; i <= Math.ceil(maxAbs); i++) {
            const v = sign * i;
            const y = yForVal(v);
            const line = document.createElementNS(svgns, "line");
            line.setAttribute("x1", x0);
            line.setAttribute("y1", y);
            line.setAttribute("x2", x0 + plotW);
            line.setAttribute("y2", y);
            line.setAttribute("stroke", "#ddd");
            line.setAttribute("stroke-width", "1");
            line.setAttribute("stroke-dasharray", "2,2");
            svg.appendChild(line);

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
    ylabel.textContent = "Depth vs 95% LR target (extra / missing ×)";
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
            lab.setAttribute("y", y0 + 10);
            lab.setAttribute("font-size", "9");
            lab.setAttribute("text-anchor", "end");
            lab.setAttribute("transform", `rotate(-60 ${xCenter} ${y0 + 10})`);
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

    const status = sectionStatus("Prokaryotic coverage", data.flag_redundancy_markers);

    div.innerHTML = `
        <h2 class="section-title">Prokaryotic coverage</h2>
        <p class="section-intro">
            This section evaluates coverage of marker genes relative to the 95% Nonpareil target.
        </p>
        <details>
            <summary>
                <span class="status-emoji">${status.emoji}</span>
                <span class="status-text">${status.text}</span>
            </summary>
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
                    The black dashed midline corresponds to the 95% coverage target. Bars above it show excess
                    coverage (1×, 2×, ...), while bars below show how many times more coverage would be needed
                    (-1×, -2×, -3× etc.). Bars more than 3× short of the target are shown in red.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const svg = div.querySelector("#lr-target-markers-svg");
    const perSample = (redBiplotPerSample || [])
        .filter(d => d.coverage_fraction !== null && d.coverage_fraction !== undefined);

    if (!perSample.length) {
        svg.outerHTML = `<div class="small-note">Marker-based coverage information not available for LR-versus-depth plot.</div>`;
        return;
    }

    const width = 1000;
    const height = 320;
    const margin = {left: 60, right: 20, top: 20, bottom: 80};
    const plotW = width - margin.left - margin.right;
    const plotH = height - margin.top - margin.bottom;
    const svgns = "http://www.w3.org/2000/svg";

    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

    const x0 = margin.left;
    const y0 = height - margin.bottom;

    const combined = perSample.map(d => {
        const coverage = d.coverage_fraction || 0;
        const target = 0.95;
        const ratio = (target > 0 && coverage > 0) ? (coverage / target) : null;
        return { sample: d.sample, coverage, ratio };
    }).filter(d => d.ratio !== null);

    if (!combined.length) {
        svg.outerHTML = `<div class="small-note">Marker-based LR-versus-depth information not available.</div>`;
        return;
    }

    function transformRatio(ratio) {
        if (ratio >= 1) {
            return Math.log10(ratio);
        } else {
            return -Math.log10(1 / ratio);
        }
    }

    let maxAbs = 0;
    combined.forEach(d => {
        const v = transformRatio(d.ratio);
        maxAbs = Math.max(maxAbs, Math.abs(v));
    });
    maxAbs = Math.max(maxAbs, 1);

    function yForVal(v) {
        const frac = (v + maxAbs) / (2 * maxAbs);
        return y0 - frac * plotH;
    }

    const baselineY = yForVal(0);

    const xAxis = document.createElementNS(svgns, "line");
    xAxis.setAttribute("x1", x0);
    xAxis.setAttribute("y1", baselineY);
    xAxis.setAttribute("x2", x0 + plotW);
    xAxis.setAttribute("y2", baselineY);
    xAxis.setAttribute("stroke", "#555");
    xAxis.setAttribute("stroke-width", "1");
    svg.appendChild(xAxis);

    for (let sign of [1, -1]) {
        for (let i = 1; i <= Math.ceil(maxAbs); i++) {
            const v = sign * i;
            const y = yForVal(v);
            const line = document.createElementNS(svgns, "line");
            line.setAttribute("x1", x0);
            line.setAttribute("y1", y);
            line.setAttribute("x2", x0 + plotW);
            line.setAttribute("y2", y);
            line.setAttribute("stroke", "#ddd");
            line.setAttribute("stroke-width", "1");
            line.setAttribute("stroke-dasharray", "2,2");
            svg.appendChild(line);

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
            lab.setAttribute("y", y0 + 10);
            lab.setAttribute("font-size", "9");
            lab.setAttribute("text-anchor", "end");
            lab.setAttribute("transform", `rotate(-60 ${xCenter} ${y0 + 10})`);
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
        const plotTop = margin.top;
        const yRowTop = plotTop + rowIndex * cellH;

        const labelText = document.createElementNS(svgns, "text");
        labelText.setAttribute("x", x0 - 10);
        labelText.setAttribute("y", yRowTop + cellH / 2);
        labelText.setAttribute("font-size", "11");
        labelText.setAttribute("text-anchor", "end");
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
}

/* Main JS entry */
function main() {
    const distill = DISTILL_DATA;
    const figures = FIGURES_DATA;

    const summaryDiv = document.getElementById("summary-sections");
    const highlightsDiv = document.getElementById("top-highlights");

    const S = distill.summary || {};
    const meta = distill.meta || {};

    const depthFig = figures.figures && figures.figures.dna_depth_fractions
        ? figures.figures.dna_depth_fractions
        : null;
    const depthPerSample = depthFig ? (depthFig.per_sample || []) : [];

    const redBiplot = figures.figures && figures.figures.redundancy_biplot
        ? figures.figures.redundancy_biplot
        : null;
    const redBiplotPerSample = redBiplot ? (redBiplot.per_sample || []) : [];

    const totalSamples =
        meta.n_samples_in_results != null ? meta.n_samples_in_results
        : (S.screening_overview && S.screening_overview.n_samples_total != null ? S.screening_overview.n_samples_total
        : (S.low_quality_reads && S.low_quality_reads.n_samples != null ? S.low_quality_reads.n_samples
        : null));

    const totalReads = (S.low_quality_reads && S.low_quality_reads.total_reads != null)
        ? S.low_quality_reads.total_reads
        : null;

    renderTopHighlights(highlightsDiv, totalSamples, totalReads);

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
