#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>ScreenM Summary Report</title>
<style>
    body {
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        margin: 0;
        padding: 20px 30px 40px 30px;
        background: #f6f7fb;
        color: #222;
    }

    h1 {
        font-size: 2.0em;
        margin-bottom: 10px;
    }

    #summary-sections {
        margin-top: 10px;
    }

    .section {
        border-radius: 6px;
        margin-bottom: 18px;
        padding: 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        background: #ffffff;
        border-left: 6px solid transparent;
    }

    .section.flag-1 {
        border-left-color: #2e7d32;
        background: #f1f8e9;
    }
    .section.flag-2 {
        border-left-color: #f9a825;
        background: #fffde7;
    }
    .section.flag-3 {
        border-left-color: #c62828;
        background: #ffebee;
    }

    .section-title {
        margin: 0;
        padding: 10px 16px 2px 16px;
        font-size: 1.35em;
    }

    .section-intro {
        margin: 0;
        padding: 0 16px 8px 16px;
        font-size: 0.95em;
        color: #444;
    }

    details {
        margin: 0;
        padding: 0 0 10px 0;
    }

    details > summary {
        cursor: pointer;
        padding: 8px 16px;
        font-weight: 500;
        list-style: none;
    }

    details > summary::-webkit-details-marker {
        display: none;
    }

    details[open] > summary {
        border-bottom: 1px solid rgba(0,0,0,0.08);
    }

    .content {
        padding: 10px 16px 14px 16px;
    }

    .summary-message {
        margin-top: 0;
        margin-bottom: 12px;
        font-size: 0.95em;
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
    .quality-stats,
    .pairwise-stats {
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
    .quality-stat-item,
    .pairwise-stat-item {
        flex: 1;
        min-width: 160px;
    }

    .screen-overview-stat-label,
    .seq-depth-stat-label,
    .prok-stat-label,
    .redundancy-stat-label,
    .cluster-stat-label,
    .quality-stat-label,
    .pairwise-stat-label {
        font-size: 0.9em;
        color: #555;
        margin-bottom: 2px;
    }

    .screen-overview-stat-value,
    .seq-depth-stat-value,
    .prok-stat-value,
    .redundancy-stat-value,
    .cluster-stat-value,
    .quality-stat-value,
    .pairwise-stat-value {
        font-size: 1.4em;
        font-weight: 600;
    }

    .screen-overview-stat-note,
    .seq-depth-stat-note,
    .prok-stat-note,
    .redundancy-stat-note,
    .cluster-stat-note,
    .quality-stat-note,
    .pairwise-stat-note {
        font-size: 0.8em;
        color: #666;
        margin-top: 2px;
    }

    .seq-depth-plot-container,
    .prok-depth-plot-container,
    .lr-target-plot-container,
    .lr-target-markers-plot-container,
    .quality-plot-container,
    .pairwise-heatmap-scroll,
    .clusters-heatmap-scroll {
        width: 100%;
        border: 1px solid #ddd;
        border-radius: 4px;
        background: #fcfcfc;
        padding: 6px 6px 2px 6px;
        box-sizing: border-box;
        margin-top: 10px;
        overflow-x: auto;
    }

    .seq-depth-svg,
    .prok-depth-svg,
    .lr-target-svg,
    .lr-target-markers-svg,
    .quality-svg,
    .pairwise-heatmap-svg,
    .clusters-heatmap-svg {
        display: block;
        width: 100%;
        height: 320px;
    }

    .clusters-heatmap-svg {
        height: 210px;
    }

    .pairwise-heatmap-controls {
        margin-top: 8px;
        font-size: 0.9em;
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
                        <div class="screen-overview-stat-label">Median depth</div>
                        <div class="screen-overview-stat-value">${fmtMillions(medianReads)}</div>
                        <div class="screen-overview-stat-note">Typical sequencing depth per sample</div>
                    </div>
                </div>
                <div class="seq-depth-plot-container">
                    <svg id="seq-depth-svg" class="seq-depth-svg" viewBox="0 0 1000 320" preserveAspectRatio="none"></svg>
                </div>
                <p class="small-note">
                    X axis: samples; Y axis: total sequencing depth (reads). Bars show per-sample depth.
                    The blue dashed line marks the median depth; a grey dashed line marks the read threshold.
                    Bars above the threshold are coloured green, and bars below the threshold red.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const svg = div.querySelector("#seq-depth-svg");
    const perSample = (depthPerSample || [])
        .filter(d => d.total_reads !== null && d.total_reads !== undefined);

    if (!perSample.length) {
        svg.outerHTML = `<div class="small-note">Per-sample read counts not available for sequencing depth plot.</div>`;
        return;
    }

    const svgns = "http://www.w3.org/2000/svg";
    const tooltip = getOrCreateTooltip();

    const samples = perSample.map(d => d.sample);
    const depths = perSample.map(d => Number(d.total_reads) || 0);

    const n = samples.length;
    const maxDepth = Math.max(...depths, 1);

    const height = 320;
    const margin = {left: 60, right: 20, top: 20, bottom: 90};
    const baseBarW = 24;
    const width = Math.max(1000, margin.left + margin.right + n * baseBarW);
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

    const plotW = width - margin.left - margin.right;
    const plotH = height - margin.top - margin.bottom;
    const x0 = margin.left;
    const y0 = margin.top;

    function yForValue(v) {
        if (maxDepth <= 0) return y0 + plotH;
        const frac = v / maxDepth;
        return y0 + (1 - frac) * plotH;
    }

    const barW = plotW / n;

    depths.forEach((d, i) => {
        const x = x0 + i * barW;
        const y = yForValue(d);
        const h = y0 + plotH - y;

        const thrReads = data.reads_threshold || 0;
        const barColor = (thrReads > 0 && d < thrReads) ? "#c62828" : "#2e7d32";

        const rect = document.createElementNS(svgns, "rect");
        rect.setAttribute("x", x + 2);
        rect.setAttribute("y", y);
        rect.setAttribute("width", Math.max(barW - 4, 2));
        rect.setAttribute("height", Math.max(h, 1));
        rect.setAttribute("fill", barColor);
        rect.setAttribute("stroke", "#ffffff");
        rect.setAttribute("stroke-width", "0.5");

        rect.addEventListener("mousemove", (ev) => {
            const t = tooltip;
            t.textContent = `${samples[i]}: ${fmtMillions(d)} reads`;
            t.style.left = ev.clientX + "px";
            t.style.top = ev.clientY + "px";
            t.style.display = "block";
        });
        rect.addEventListener("mouseleave", () => {
            tooltip.style.display = "none";
        });

        svg.appendChild(rect);

        const showAll = n <= 40;
        const show = showAll || (i % 5 === 0);
        if (show) {
            const lab = document.createElementNS(svgns, "text");
            const xCenter = x + barW / 2;
            lab.setAttribute("x", xCenter);
            lab.setAttribute("y", y0 + plotH + 10);
            lab.setAttribute("font-size", "9");
            lab.setAttribute("text-anchor", "end");
            lab.setAttribute("transform", `rotate(-60 ${xCenter} ${y0 + plotH + 10})`);
            lab.textContent = samples[i];
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

    const thresholdReads = data.reads_threshold;
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

/* ---------- Sequencing quality ---------- */
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

    const svgns = "http://www.w3.org/2000/svg";
    const tooltip = getOrCreateTooltip();

    const samples = perSample.map(d => d.sample);
    const fracs = perSample.map(d => Number(d.fraction_low_quality_of_total) || 0);

    const n = samples.length;
    const maxFrac = Math.max(...fracs, 0.25);

    const height = 320;
    const margin = {left: 60, right: 20, top: 20, bottom: 90};
    const baseBarW = 24;
    const width = Math.max(1000, margin.left + margin.right + n * baseBarW);
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

    const plotW = width - margin.left - margin.right;
    const plotH = height - margin.top - margin.bottom;
    const x0 = margin.left;
    const y0 = margin.top;

    function yForValue(v) {
        if (maxFrac <= 0) return y0 + plotH;
        const frac = v / maxFrac;
        return y0 + (1 - frac) * plotH;
    }

    const barW = plotW / n;

    fracs.forEach((v, i) => {
        const x = x0 + i * barW;
        const y = yForValue(v);
        const h = y0 + plotH - y;

        let barColor = "#2e7d32"; // green
        if (v > 0.20) {
            barColor = "#c62828"; // red
        } else if (v > 0.05) {
            barColor = "#f9a825"; // yellow-orange
        }

        const rect = document.createElementNS(svgns, "rect");
        rect.setAttribute("x", x + 2);
        rect.setAttribute("y", y);
        rect.setAttribute("width", Math.max(barW - 4, 2));
        rect.setAttribute("height", Math.max(h, 1));
        rect.setAttribute("fill", barColor);
        rect.setAttribute("stroke", "#ffffff");
        rect.setAttribute("stroke-width", "0.5");

        rect.addEventListener("mousemove", (ev) => {
            const t = tooltip;
            t.textContent = `${samples[i]}: ${(v*100).toFixed(2)}% removed`;
            t.style.left = ev.clientX + "px";
            t.style.top = ev.clientY + "px";
            t.style.display = "block";
        });
        rect.addEventListener("mouseleave", () => {
            tooltip.style.display = "none";
        });

        svg.appendChild(rect);

        const showAll = n <= 40;
        const show = showAll || (i % 5 === 0);
        if (show) {
            const lab = document.createElementNS(svgns, "text");
            const xCenter = x + barW / 2;
            lab.setAttribute("x", xCenter);
            lab.setAttribute("y", y0 + plotH + 10);
            lab.setAttribute("font-size", "9");
            lab.setAttribute("text-anchor", "end");
            lab.setAttribute("transform", `rotate(-60 ${xCenter} ${y0 + plotH + 10})`);
            lab.textContent = samples[i];
            svg.appendChild(lab);
        }
    });

    // Threshold lines at 5% and 20%
    [0.05, 0.20].forEach((thr, idx) => {
        const y = yForValue(thr);
        const line = document.createElementNS(svgns, "line");
        line.setAttribute("x1", x0);
        line.setAttribute("y1", y);
        line.setAttribute("x2", x0 + plotW);
        line.setAttribute("y2", y);
        line.setAttribute("stroke", idx === 0 ? "#f9a825" : "#c62828");
        line.setAttribute("stroke-width", "1.2");
        line.setAttribute("stroke-dasharray", "4,2");
        svg.appendChild(line);
    });

    const medianRemoved = Number(medianFrac) || 0;
    if (medianRemoved > 0) {
        const y = yForValue(medianRemoved);
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
        lab.textContent = `median (${(medianRemoved*100).toFixed(2)}%)`;
        svg.appendChild(lab);
    }
}

/* ---------- Prokaryotic fraction + DNA depth components ----------
   (not reworked here – assumed to already exist in your version)
   You can keep your previous addProkFractionSection implementation.
   For brevity, we omit reprinting that function here, but it should
   remain unchanged in your file except for previous tweaks.
*/

/* ---------- Redundancy sections ----------
   Similarly, existing addRedundancyReadsSection and
   addRedundancyMarkersSection are assumed to be present and
   unchanged from your latest working version.
*/

/* ---------- Sample clusters section ----------
   We reuse your existing implementation; only the order in main()
   will change so that the pairwise section appears before this.
*/

/* ---------- Pairwise Mash distances heatmap ---------- */

function addMashPairwiseSection(parent, pairwiseData, clustersData) {
    if (!pairwiseData || ( !pairwiseData.markers && !pairwiseData.reads )) return;

    const flag = clustersData && clustersData.reads
        ? clustersData.reads.flag_clusters
        : 2;

    const div = document.createElement("div");
    div.className = "section " + flagClass(flag);

    const status = sectionStatus("Pairwise Mash distances", flag);

    const markers = pairwiseData.markers || null;
    const reads = pairwiseData.reads || null;

    const markersPairs = markers ? markers.n_pairs : 0;
    const readsPairs = reads ? reads.n_pairs : 0;

    const nSamplesMarkers = markers && markers.samples ? markers.samples.length : 0;
    const nSamplesReads = reads && reads.samples ? reads.samples.length : 0;

    const nSamples = Math.max(nSamplesMarkers, nSamplesReads);

    div.innerHTML = `
        <h2 class="section-title">Pairwise Mash distances</h2>
        <p class="section-intro">
            This section shows the full pairwise distance matrix between samples based on Mash,
            using either marker genes or whole-read signatures.
        </p>
        <details>
            <summary>
                <span class="status-emoji">${status.emoji}</span>
                <span class="status-text">${status.text}</span>
            </summary>
            <div class="content">
                <p class="summary-message">
                    Pairwise Mash distances help visualise how similar or different samples are
                    before clustering. Darker tiles correspond to larger distances (more divergent pairs).
                </p>
                <div class="pairwise-stats">
                    <div class="pairwise-stat-item">
                        <div class="pairwise-stat-label">Samples (max)</div>
                        <div class="pairwise-stat-value">${fmtInt(nSamples)}</div>
                        <div class="pairwise-stat-note">Unique samples across markers and reads</div>
                    </div>
                    <div class="pairwise-stat-item">
                        <div class="pairwise-stat-label">Marker pairs</div>
                        <div class="pairwise-stat-value">${fmtInt(markersPairs)}</div>
                        <div class="pairwise-stat-note">Pairwise distances from Mash markers</div>
                    </div>
                    <div class="pairwise-stat-item">
                        <div class="pairwise-stat-label">Read pairs</div>
                        <div class="pairwise-stat-value">${fmtInt(readsPairs)}</div>
                        <div class="pairwise-stat-note">Pairwise distances from Mash reads</div>
                    </div>
                </div>
                <div class="pairwise-heatmap-controls">
                    <label><input type="radio" name="pairwise-mode" value="markers" checked> Marker-based distances</label>
                    &nbsp;&nbsp;
                    <label><input type="radio" name="pairwise-mode" value="reads"> Read-based distances</label>
                </div>
                <div class="pairwise-heatmap-scroll">
                    <svg id="pairwise-heatmap-svg" class="pairwise-heatmap-svg" viewBox="0 0 1000 320" preserveAspectRatio="none"></svg>
                </div>
                <p class="small-note">
                    Heatmap shows sample-by-sample distances. X and Y axes are samples; tiles are coloured by
                    Mash distance (white = small distance, dark = larger distance). Use the radio buttons to
                    switch between marker-based and read-based distance matrices. Hover over tiles to see exact
                    distances for each sample pair.
                </p>
            </div>
        </details>
    `;
    parent.appendChild(div);

    const svg = div.querySelector("#pairwise-heatmap-svg");
    const svgns = "http://www.w3.org/2000/svg";
    const tooltip = getOrCreateTooltip();

    function buildMatrix(block) {
        if (!block || !block.pairwise || !block.samples) return null;
        const samples = block.samples.slice();
        samples.sort();
        const n = samples.length;

        const distMap = {};
        (block.pairwise || []).forEach(rec => {
            const s1 = rec.sample1;
            const s2 = rec.sample2;
            const d  = Number(rec.distance);
            if (!isFinite(d)) return;
            const k1 = s1 + "||" + s2;
            const k2 = s2 + "||" + s1;
            distMap[k1] = d;
            distMap[k2] = d;
        });

        const matrix = [];
        const distances = [];
        for (let i = 0; i < n; i++) {
            const row = [];
            for (let j = 0; j < n; j++) {
                let val;
                if (i === j) {
                    val = 0.0;
                } else {
                    const key = samples[i] + "||" + samples[j];
                    if (distMap.hasOwnProperty(key)) {
                        val = distMap[key];
                    } else {
                        val = null;
                    }
                }
                row.push(val);
                if (val !== null) distances.push(val);
            }
            matrix.push(row);
        }

        let minD = 0;
        let maxD = 1;
        if (distances.length) {
            minD = Math.min(...distances);
            maxD = Math.max(...distances);
            if (maxD === minD) {
                maxD = minD + 1e-6;
            }
        }

        return {samples, matrix, minD, maxD};
    }

    const markersMatrix = buildMatrix(markers);
    const readsMatrix = buildMatrix(reads);

    function colorForValue(v, minD, maxD) {
        if (v === null) return "#eeeeee";
        if (!isFinite(v)) return "#000000";
        const t = (v - minD) / (maxD - minD);
        const clamped = Math.max(0, Math.min(1, t));
        const r = 255;
        const g = Math.round(255 * (1 - clamped * 0.7));
        const b = Math.round(255 * (1 - clamped));
        return `rgb(${r},${g},${b})`;
    }

    function drawMatrix(which) {
        while (svg.firstChild) svg.removeChild(svg.firstChild);

        const block = (which === "markers") ? markersMatrix : readsMatrix;
        if (!block) {
            const text = document.createElementNS(svgns, "text");
            text.setAttribute("x", 20);
            text.setAttribute("y", 30);
            text.setAttribute("font-size", "12");
            text.textContent = `No ${which}-based pairwise distances available.`;
            svg.appendChild(text);
            return;
        }

        const samples = block.samples;
        const matrix = block.matrix;
        const n = samples.length;
        const minD = block.minD;
        const maxD = block.maxD;

        const height = 320;
        const margin = {left: 120, right: 10, top: 40, bottom: 110};
        const baseCell = 20;
        const width = Math.max(1000, margin.left + margin.right + n * baseCell);
        const innerH = height - margin.top - margin.bottom;
        const cellSize = Math.min(baseCell, innerH / Math.max(n, 1));

        svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

        const plotW = n * cellSize;
        const plotH = n * cellSize;
        const x0 = margin.left;
        const y0 = margin.top;

        const title = document.createElementNS(svgns, "text");
        title.setAttribute("x", x0);
        title.setAttribute("y", 22);
        title.setAttribute("font-size", "12");
        title.setAttribute("font-weight", "600");
        title.textContent = (which === "markers")
            ? "Marker-based Mash distances"
            : "Read-based Mash distances";
        svg.appendChild(title);

        for (let i = 0; i < n; i++) {
            for (let j = 0; j < n; j++) {
                const v = matrix[i][j];
                const x = x0 + j * cellSize;
                const y = y0 + i * cellSize;

                const rect = document.createElementNS(svgns, "rect");
                rect.setAttribute("x", x);
                rect.setAttribute("y", y);
                rect.setAttribute("width", cellSize);
                rect.setAttribute("height", cellSize);
                rect.setAttribute("fill", colorForValue(v, minD, maxD));
                rect.setAttribute("stroke", "#ffffff");
                rect.setAttribute("stroke-width", "0.3");

                rect.addEventListener("mousemove", (ev) => {
                    const s1 = samples[i];
                    const s2 = samples[j];
                    const valTxt = (v === null) ? "NA" : v.toFixed(4);
                    tooltip.textContent = `${s1} vs ${s2}: ${valTxt}`;
                    tooltip.style.left = ev.clientX + "px";
                    tooltip.style.top = ev.clientY + "px";
                    tooltip.style.display = "block";
                });
                rect.addEventListener("mouseleave", () => {
                    tooltip.style.display = "none";
                });

                svg.appendChild(rect);
            }
        }

        // Axis labels
        for (let i = 0; i < n; i++) {
            const s = samples[i];

            // y-axis label
            const ty = document.createElementNS(svgns, "text");
            ty.setAttribute("x", margin.left - 4);
            ty.setAttribute("y", y0 + i * cellSize + cellSize / 2 + 3);
            ty.setAttribute("font-size", "9");
            ty.setAttribute("text-anchor", "end");
            ty.textContent = s;
            svg.appendChild(ty);

            // x-axis label
            const tx = document.createElementNS(svgns, "text");
            const xCenter = x0 + i * cellSize + cellSize / 2;
            tx.setAttribute("x", xCenter);
            tx.setAttribute("y", y0 + plotH + 12);
            tx.setAttribute("font-size", "9");
            tx.setAttribute("text-anchor", "end");
            tx.setAttribute("transform", `rotate(-60 ${xCenter} ${y0 + plotH + 12})`);
            tx.textContent = s;
            svg.appendChild(tx);
        }
    }

    const radios = div.querySelectorAll('input[name="pairwise-mode"]');
    radios.forEach(r => {
        r.addEventListener("change", () => {
            const val = div.querySelector('input[name="pairwise-mode"]:checked').value;
            drawMatrix(val);
        });
    });

    // Initial draw (prefer markers if available)
    if (markersMatrix) {
        drawMatrix("markers");
    } else if (readsMatrix) {
        div.querySelector('input[value="markers"]').disabled = true;
        div.querySelector('input[value="reads"]').checked = true;
        drawMatrix("reads");
    } else {
        drawMatrix("markers");
    }
}

/* ---------- Sample clusters (existing implementation) ---------- */
function addClustersSection(parent, data) {
    if (!data) return;

    const markers = data.markers || {};
    const reads = data.reads || {};

    const flag = reads.flag_clusters || markers.flag_clusters || 3;
    const div = document.createElement("div");
    div.className = "section " + flagClass(flag);

    const status = sectionStatus("Sample clusters", flag);

    const nClustersMarkers = markers.n_clusters;
    const nClustersReads = reads.n_clusters;

    div.innerHTML = `
        <h2 class="section-title">Sample clusters</h2>
        <p class="section-intro">
            This section summarises Mash-based sample clusters, which can be used to define coassemblies.
        </p>
        <details>
            <summary>
                <span class="status-emoji">${status.emoji}</span>
                <span class="status-text">${status.text}</span>
            </summary>
            <div class="content">
                <p class="summary-message">${data.message_clusters_overall || ""}</p>
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
    const y0 = margin.top;

    function drawRow(rowIndex, label, map, colorMap, defaultColor) {
        const y = y0 + rowIndex * cellH;
        const labelText = document.createElementNS(svgns, "text");
        labelText.setAttribute("x", 10);
        labelText.setAttribute("y", y + cellH / 2 + 3);
        labelText.setAttribute("font-size", "11");
        labelText.setAttribute("font-weight", "600");
        labelText.textContent = label;
        svg.appendChild(labelText);

        const cellW = plotW / nSamples;
        samples.forEach((sampleName, i) => {
            const x = x0 + i * cellW;
            const clusterId = map[sampleName];
            const color = (clusterId !== undefined && clusterId !== null)
                ? colorMap[clusterId] || defaultColor
                : "#e0e0e0";

            const rect = document.createElementNS(svgns, "rect");
            rect.setAttribute("x", x);
            rect.setAttribute("y", y);
            rect.setAttribute("width", cellW);
            rect.setAttribute("height", cellH);
            rect.setAttribute("fill", color);
            rect.setAttribute("stroke", "#ffffff");
            rect.setAttribute("stroke-width", "0.5");

            rect.addEventListener("mousemove", (ev) => {
                const cidTxt = (clusterId === undefined || clusterId === null)
                    ? "none"
                    : clusterId;
                tooltip.textContent = `${label} – ${sampleName}: cluster ${cidTxt}`;
                tooltip.style.left = ev.clientX + "px";
                tooltip.style.top = ev.clientY + "px";
                tooltip.style.display = "block";
            });

            rect.addEventListener("mouseleave", () => {
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

/* ---------- Main JS entry ---------- */
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
    // Your existing Prokaryotic fraction section (not reprinted here)
    if (typeof addProkFractionSection === "function") {
        addProkFractionSection(summaryDiv, S.prokaryotic_fraction, depthPerSample);
    }
    if (typeof addRedundancyReadsSection === "function") {
        addRedundancyReadsSection(summaryDiv, S.redundancy_reads, depthPerSample);
    }
    if (typeof addRedundancyMarkersSection === "function") {
        addRedundancyMarkersSection(summaryDiv, S.redundancy_markers, redBiplotPerSample);
    }

    // NEW: Pairwise Mash distances heatmap, before clusters
    addMashPairwiseSection(summaryDiv, S.mash_pairwise, S.clusters);

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

    # Escape closing script tags in the JSON
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
