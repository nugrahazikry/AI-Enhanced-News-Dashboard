// Global chart instances
let newsOverTimeChart = null;
let sentimentOverTimeChart = null;
let topSourcesChart = null;
let topTopicsChart = null;
let topEntitiesChart = null;
let topicShareChart = null;
let entityTrendChart = null;
let sourceBubbleChart = null;
let radarPositifChart = null;
let radarNetralChart = null;
let radarNegatifChart = null;
let sourceTrendChart = null;
let radarSrcPositifChart = null;
let radarSrcNetralChart  = null;
let radarSrcNegatifChart = null;
// New overview chart instances
let sentimentTrendChart = null;
let sovPieChart = null;
let entityPieChart = null;

// Doughnut centre-text plugin (shows total + label inside the hole)
const doughnutCenterPlugin = {
    id: 'doughnutCenter',
    afterDraw(chart) {
        if (chart.config.type !== 'doughnut') return;
        const { ctx, chartArea, data } = chart;
        if (!chartArea) return;
        const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
        const cx = (chartArea.left + chartArea.right) / 2;
        const cy = (chartArea.top + chartArea.bottom) / 2;
        ctx.save();
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.font = 'bold 26px Inter, sans-serif';
        ctx.fillStyle = '#1e293b';
        ctx.fillText(total.toLocaleString(), cx, cy - 10);
        ctx.font = '11px Inter, sans-serif';
        ctx.fillStyle = '#64748b';
        ctx.fillText('Total', cx, cy + 12);
        ctx.restore();
    }
};
Chart.register(doughnutCenterPlugin);

// Palette for multi-series charts
const palette = [
    '#4f46e5', '#0ea5e9', '#f59e0b', '#22c55e', '#ef4444',
    '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#84cc16'
];

// Global news data for filtering
let allNewsData = [];
let filteredNewsData = [];

// Chart colors
const chartColors = {
    positive: '#22c55e',
    neutral: '#64748b',
    negative: '#ef4444',
    primary: '#4f46e5',
    primaryLight: 'rgba(79, 70, 229, 0.2)'
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Set current date
    const dateDisplay = document.getElementById('current-date');
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    dateDisplay.textContent = new Date().toLocaleDateString('en-US', options);

    // ── Scraper sidebar date constraints ─────────────────────────────────────
    const today = new Date();
    const oneMonthAgo = new Date(today);
    oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);

    const toISO = d => d.toISOString().split('T')[0];

    const startDateInput = document.getElementById('scraper-start-date');
    const endDateInput   = document.getElementById('scraper-end-date');

    if (startDateInput && endDateInput) {
        startDateInput.min   = toISO(oneMonthAgo);
        startDateInput.max   = toISO(today);
        startDateInput.value = toISO(oneMonthAgo);

        endDateInput.min     = toISO(oneMonthAgo);
        endDateInput.max     = toISO(today);
        endDateInput.value   = toISO(today);

        // Keep end date >= start date dynamically
        startDateInput.addEventListener('change', () => {
            endDateInput.min = startDateInput.value;
            if (endDateInput.value < startDateInput.value) {
                endDateInput.value = startDateInput.value;
            }
        });
        endDateInput.addEventListener('change', () => {
            startDateInput.max = endDateInput.value;
        });
    }

    // ── Run scraper button (placeholder) ─────────────────────────────────────
    const runBtn = document.getElementById('scraper-run-btn');
    if (runBtn) {
        runBtn.addEventListener('click', () => {
            // Require login before running analysis
            if (!window.isLoggedIn) {
                if (typeof openMustLoginPopup === 'function') openMustLoginPopup();
                return;
            }

            const keyword   = document.getElementById('scraper-keyword').value.trim();
            const startDate = startDateInput ? startDateInput.value : '';
            const endDate   = endDateInput   ? endDateInput.value   : '';
            const language  = document.getElementById('scraper-language').value;
            const countryEl = document.getElementById('scraper-country');
            const country   = countryEl ? countryEl.value : 'ID';

            // Validate required fields
            let hasError = false;
            const warnKeyword   = document.getElementById('warn-keyword');
            const warnStartDate = document.getElementById('warn-start-date');
            const warnEndDate   = document.getElementById('warn-end-date');

            if (!keyword) {
                if (warnKeyword) warnKeyword.style.display = 'block';
                hasError = true;
            } else {
                if (warnKeyword) warnKeyword.style.display = 'none';
            }
            if (!startDate) {
                if (warnStartDate) warnStartDate.style.display = 'block';
                hasError = true;
            } else {
                if (warnStartDate) warnStartDate.style.display = 'none';
            }
            if (!endDate) {
                if (warnEndDate) warnEndDate.style.display = 'block';
                hasError = true;
            } else {
                if (warnEndDate) warnEndDate.style.display = 'none';
            }
            if (hasError) return;

            // Show loading overlay
            const overlay      = document.getElementById('main-loading-overlay');
            const loadingTitle = document.getElementById('main-loading-title');
            if (overlay)      overlay.style.display = 'flex';
            if (loadingTitle) loadingTitle.textContent = `Scraping news for "${keyword}"...`;

            // Stream scraping progress via Server-Sent Events
            const params = new URLSearchParams({
                keyword, start_date: startDate, end_date: endDate, language, country
            });
            const evtSource = new EventSource(`/api/scrape?${params}`);

            evtSource.onmessage = (event) => {
                const msg = JSON.parse(event.data);
                if (msg.type === 'progress') {
                    if (loadingTitle) loadingTitle.textContent = msg.message;
                } else if (msg.type === 'done') {
                    evtSource.close();
                    if (loadingTitle) loadingTitle.textContent = `✓ Processed ${msg.count} articles. Loading dashboard...`;
                    setTimeout(() => {
                        if (overlay) overlay.style.display = 'none';
                        loadDashboardData(keyword);
                    }, 1200);
                } else if (msg.type === 'error') {
                    evtSource.close();
                    if (loadingTitle) loadingTitle.textContent = '❌ ' + msg.message;
                    setTimeout(() => { if (overlay) overlay.style.display = 'none'; }, 3000);
                }
            };

            evtSource.onerror = () => {
                evtSource.close();
                if (overlay) overlay.style.display = 'none';
            };
        });
    }

    // Load initial data using the server-provided default keyword
    const defaultKeyword = document.body.dataset.defaultKeyword || '';
    loadDashboardData(defaultKeyword);

    // Wire up download button
    const downloadBtn = document.getElementById('download-excel-btn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', () => {
            const kw = window._currentKeyword || defaultKeyword;
            if (kw) window.location.href = `/api/download/${encodeURIComponent(kw)}`;
        });
    }

    // ── Choose Keyword dropdown ────────────────────────────────────────────
    const keywordSelect = document.getElementById('keyword-select');

    if (keywordSelect) {
        keywordSelect.addEventListener('change', () => {
            const kw = keywordSelect.value;
            if (kw) loadDashboardData(kw);
        });
    }

    // Initialize news filters
    initializeNewsFilters();
});

// Load all dashboard data
async function loadDashboardData(keyword) {
    window._currentKeyword = keyword;
    // Update header keyword label
    const headerKw = document.getElementById('header-keyword');
    if (headerKw) headerKw.textContent = keyword ? `— ${keyword}` : '';
    // Reset AI insight section when keyword changes
    const aiContent = document.getElementById('ai-insight-content');
    if (aiContent) {
        aiContent.innerHTML = '<p class="ai-insight-placeholder">Generating AI-powered analysis of the news data...</p>';
    }
    try {
        // Show loading state
        showLoading();
        
        // Fetch data
        const [dataResponse, newsResponse] = await Promise.all([
            fetch(`/api/data/${encodeURIComponent(keyword)}`),
            fetch(`/api/news/${encodeURIComponent(keyword)}`)
        ]);
        
        const data = await dataResponse.json();
        const news = await newsResponse.json();
        
        // Hide loading state
        hideLoading();
        
        // Update summary cards with week-over-week
        updateSummaryCards(data.summary, data.week_over_week, data.comparison_label);

        // Overview Row 1: combined sentiment trend + two pies
        updateSentimentTrendChart(data.sentiment_over_time);
        updateSOVPieChart(data.source_sov);
        updateEntityPieChart(data.entity_sov);

        // (sentimentTrendChart is ApexCharts — no Chart.js date-range padding needed)

        // Overview Row 2: horizontal bar charts
        updateTopSourcesChart(data.top_sources);
        updateTopTopicsChart(data.top_topics);
        updateTopEntitiesChart(data.top_entities);

        // Analytics section charts
        updateTopicShareChart(data.topic_share);
        updateEntityTrendChart(data.entity_trend);
        updateSourceTrendChart(data.source_trend);
        updateSourceBubbleChart(data.source_bubble);
        renderActivityHeatmap(data.heatmap);
        renderTopicEntityHeatmap(data.topic_entity_heatmap);
        updateRadarCharts(data.radar);
        updateSankeyChart(data.sankey);

        // Update news list
        updateNewsListAndFilters(news);

        // Auto-generate AI insights after dashboard data is loaded
        loadAIInsight(keyword);
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        hideLoading();
    }
}

// Load and display AI insights for the given keyword
async function loadAIInsight(keyword) {
    const loadingEl = document.getElementById('ai-insight-loading');
    const contentEl = document.getElementById('ai-insight-content');

    if (!contentEl) return;

    // Show spinner, hide old content
    if (loadingEl) loadingEl.style.display = 'block';
    contentEl.style.display = 'none';

    try {
        const response = await fetch(`/api/ai_insight/${encodeURIComponent(keyword)}`);
        if (!response.ok) throw new Error(`Request failed: ${response.status}`);
        const data = await response.json();
        const html = marked.parse(data.insight || '');
        contentEl.innerHTML = html;
    } catch (error) {
        console.error('Error loading AI insight:', error);
        contentEl.innerHTML = '<p class="ai-insight-placeholder" style="color:#ef4444;">Failed to generate insights. Please try again.</p>';
    } finally {
        if (loadingEl) loadingEl.style.display = 'none';
        contentEl.style.display = 'block';
    }
}

// Show loading state - preserve canvas elements
function showLoading() {
    // Don't destroy canvas elements, just show loading overlay
    document.querySelectorAll('.chart-container, .chart-container-bar, .chart-container-radar-lg').forEach(container => {
        // Remove existing loading overlay if any
        const existingOverlay = container.querySelector('.loading-overlay');
        if (existingOverlay) {
            existingOverlay.remove();
        }
        
        // Add loading overlay without destroying canvas
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.innerHTML = '<i class="fas fa-spinner"></i>';
        container.style.position = 'relative';
        container.appendChild(overlay);
    });
}

// Hide loading state
function hideLoading() {
    document.querySelectorAll('.loading-overlay').forEach(overlay => {
        overlay.remove();
    });
}

// Update summary cards with animation
function updateSummaryCards(summary, weekOverWeek, comparisonLabel) {
    animateNumber('total-news', summary.total);
    animateNumber('positive-news', summary.positive);
    animateNumber('neutral-news', summary.neutral);
    animateNumber('negative-news', summary.negative);

    if (weekOverWeek) {
        const label = comparisonLabel || 'last week';
        updateChangeIndicator('total-change',    weekOverWeek.total,    label);
        updateChangeIndicator('positive-change', weekOverWeek.positive, label);
        updateChangeIndicator('neutral-change',  weekOverWeek.neutral,  label);
        updateChangeIndicator('negative-change', weekOverWeek.negative, label);
    }
}

// Render % vs last-week indicator
function updateChangeIndicator(elementId, pct, label) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const vsLabel = label || 'last week';
    if (pct === null || pct === undefined) {
        el.innerHTML = `<i class="fas fa-minus"></i><span>&nbsp;N/A vs ${vsLabel}</span>`;
        el.className = 'card-change flat';
        return;
    }
    const sign   = pct >= 0 ? '+' : '';
    const icon   = pct >  0.05 ? 'fa-arrow-up'
                 : pct < -0.05 ? 'fa-arrow-down'
                 : 'fa-minus';
    const cls    = pct >  0.05 ? 'up'
                 : pct < -0.05 ? 'down'
                 : 'flat';
    el.innerHTML = `<i class="fas ${icon}"></i><span>&nbsp;${sign}${pct}% vs ${vsLabel}</span>`;
    el.className = `card-change ${cls}`;
}

// Animate number counting
function animateNumber(elementId, target) {
    const element = document.getElementById(elementId);
    const start = parseInt(element.textContent) || 0;
    const duration = 500;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(start + (target - start) * easeOut);
        
        element.textContent = current.toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

// Apply a padded date range to a time-category chart so a single-date dataset isn't squeezed
function applyDateRange(chartInstance, dateRange) {
    if (!chartInstance || !dateRange.min || !dateRange.max) return;
    const min = new Date(dateRange.min);
    const max = new Date(dateRange.max);
    // Always show at least a 2-day window centred on the data
    if (min.getTime() === max.getTime()) {
        min.setDate(min.getDate() - 1);
        max.setDate(max.getDate() + 1);
    } else {
        min.setDate(min.getDate() - 1);
        max.setDate(max.getDate() + 1);
    }
    const fmt = d => d.toISOString().slice(0, 10);
    // Inject min/max into the category-scale labels array boundaries
    const labels = chartInstance.data.labels;
    if (!labels.includes(fmt(min))) labels.unshift(fmt(min));
    if (!labels.includes(fmt(max))) labels.push(fmt(max));
    // Pad the datasets to match
    chartInstance.data.datasets.forEach(ds => {
        if (ds.data.length < labels.length) {
            while (ds.data.length < labels.length) ds.data.unshift(null);
        }
    });
    chartInstance.update();
}

// ── NEW: Combined Sentiment Trend Chart — ApexCharts ─────────────────────
function updateSentimentTrendChart(data) {
    const el = document.getElementById('sentimentTrendChart');
    if (!el) return;
    if (sentimentTrendChart) { sentimentTrendChart.destroy(); sentimentTrendChart = null; }
    if (!data || data.length === 0) return;

    const categories = data.map(d => d.date);

    sentimentTrendChart = new ApexCharts(el, {
        chart: {
            type: 'area',
            height: '100%',
            toolbar: { show: false },
            zoom: { enabled: false },
            fontFamily: 'Inter, sans-serif',
            background: 'transparent',
            animations: { enabled: true, speed: 600 },
            sparkline: { enabled: false },
            parentHeightOffset: 0
        },
        series: [
            { name: 'Positive', data: data.map(d => d.positive || 0) },
            { name: 'Neutral',  data: data.map(d => d.neutral  || 0) },
            { name: 'Negative', data: data.map(d => d.negative || 0) }
        ],
        colors: [chartColors.positive, chartColors.neutral, chartColors.negative],
        fill: {
            type: ['gradient', 'gradient', 'gradient'],
            gradient: {
                shade: 'light',
                type: 'vertical',
                shadeIntensity: 0.4,
                opacityFrom: 0.45,
                opacityTo: 0.02,
                stops: [0, 90, 100]
            }
        },
        stroke: { curve: 'smooth', width: 1.5 },
        markers: { size: 2, hover: { size: 5 } },
        xaxis: {
            categories,
            tickAmount: 12,
            labels: { rotate: -30, style: { colors: '#64748b', fontSize: '10px' } },
            axisBorder: { show: false },
            axisTicks: { show: false }
        },
        yaxis: {
            min: 0,
            labels: { style: { colors: '#64748b', fontSize: '10px' } }
        },
        grid: { borderColor: 'rgba(148,163,184,0.15)', strokeDashArray: 4, padding: { bottom: 0 } },
        legend: {
            position: 'bottom',
            horizontalAlign: 'center',
            offsetY: 0,
            markers: { radius: 12, width: 10, height: 10 },
            labels: { colors: '#1e293b' },
            fontSize: '11px'
        },
        tooltip: {
            shared: true,
            intersect: false,
            theme: 'dark',
            x: { format: 'yyyy-MM-dd' }
        },
        dataLabels: { enabled: false }
    });
    sentimentTrendChart.render();
}

// ── NEW: Overall Sentiment Pie / Donut ────────────────────────────────────
// ── Share-of-Voice Pie / Donut ───────────────────────────────────────────
function updateSOVPieChart(sourceSOV) {
    const ctx = document.getElementById('sovPieChart');
    if (!ctx) return;
    if (sovPieChart) sovPieChart.destroy();
    if (!sourceSOV || sourceSOV.length === 0) return;

    // Sort descending and take top 6
    const sorted = [...sourceSOV].sort((a, b) => b.count - a.count);
    const displayItems = sorted.slice(0, 6);

    const labels = displayItems.map(d => d.source);
    const values = displayItems.map(d => d.count);
    const total  = values.reduce((a, b) => a + b, 0);
    // Generate enough colors by cycling the palette
    const baseColors = ['#4f46e5','#0ea5e9','#f59e0b','#22c55e','#ef4444','#8b5cf6','#ec4899','#14b8a6','#fb923c','#84cc16'];
    const colors = labels.map((_, i) => baseColors[i % baseColors.length]);
    const otherDetail = [];

    sovPieChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderColor: '#ffffff',
                borderWidth: 3,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            layout: { padding: { right: 4, top: 0, bottom: 0 } },
            animation: { animateRotate: true, duration: 800 },
            plugins: {
                legend: {
                    display: true,
                    position: 'right',
                    align: 'center',
                    maxWidth: 140,
                    labels: {
                        usePointStyle: true,
                        pointStyle: 'circle',
                        padding: 12,
                        color: '#64748b',
                        font: { size: 10 },
                        generateLabels(chart) {
                            const d = chart.data;
                            return d.labels.map((lbl, i) => {
                                const val = d.datasets[0].data[i];
                                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : '0.0';
                                return {
                                    text: `${lbl} ${pct}%`,
                                    fillStyle: d.datasets[0].backgroundColor[i],
                                    strokeStyle: '#fff',
                                    lineWidth: 0,
                                    hidden: false,
                                    index: i
                                };
                            });
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(30,41,59,0.9)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label(ctx) {
                            const val = ctx.raw;
                            const pct = total > 0 ? ((val / total) * 100).toFixed(1) : '0.0';
                            return ` ${ctx.label}: ${val.toLocaleString()} (${pct}%)`;
                        }
                    }
                }
            }
        }
    });
}

// ── Entity Share Pie / Donut ──────────────────────────────────────────────
function updateEntityPieChart(entitySOV) {
    const ctx = document.getElementById('entityPieChart');
    if (!ctx) return;
    if (entityPieChart) entityPieChart.destroy();
    if (!entitySOV || entitySOV.length === 0) return;

    const sorted = [...entitySOV].sort((a, b) => b.count - a.count);
    const displayItems = sorted.slice(0, 6);

    const labels = displayItems.map(d => d.entity);
    const values = displayItems.map(d => d.count);
    const total  = values.reduce((a, b) => a + b, 0);
    const baseColors = ['#4f46e5','#0ea5e9','#f59e0b','#22c55e','#ef4444','#8b5cf6','#ec4899','#14b8a6','#fb923c','#84cc16'];
    const colors = labels.map((_, i) => baseColors[i % baseColors.length]);

    entityPieChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderColor: '#ffffff',
                borderWidth: 3,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            layout: { padding: { right: 4, top: 0, bottom: 0 } },
            animation: { animateRotate: true, duration: 800 },
            plugins: {
                legend: {
                    display: true,
                    position: 'right',
                    align: 'center',
                    maxWidth: 140,
                    labels: {
                        usePointStyle: true,
                        pointStyle: 'circle',
                        padding: 12,
                        color: '#64748b',
                        font: { size: 10 },
                        generateLabels(chart) {
                            const d = chart.data;
                            return d.labels.map((lbl, i) => {
                                const val = d.datasets[0].data[i];
                                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : '0.0';
                                // Capitalise first letter for display
                                const displayLbl = lbl.charAt(0).toUpperCase() + lbl.slice(1);
                                return {
                                    text: `${displayLbl} ${pct}%`,
                                    fillStyle: d.datasets[0].backgroundColor[i],
                                    strokeStyle: '#fff',
                                    lineWidth: 0,
                                    hidden: false,
                                    index: i
                                };
                            });
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(30,41,59,0.9)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label(ctx) {
                            const val = ctx.raw;
                            const pct = total > 0 ? ((val / total) * 100).toFixed(1) : '0.0';
                            return ` ${ctx.label}: ${val.toLocaleString()} (${pct}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Update News Over Time Chart
function updateNewsOverTimeChart(data) {
    const ctx = document.getElementById('newsOverTimeChart');
    if (!ctx) return;

    // Destroy existing chart
    if (newsOverTimeChart) {
        newsOverTimeChart.destroy();
    }
    
    // Prepare data
    const labels = data.map(item => item.date);
    const values = data.map(item => item.count);
    
    newsOverTimeChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'News Count',
                data: values,
                borderColor: chartColors.primary,
                backgroundColor: chartColors.primaryLight,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6,
                pointBackgroundColor: chartColors.primary,
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(30, 41, 59, 0.9)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    padding: 12,
                    cornerRadius: 8,
                    displayColors: false
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxTicksLimit: 10,
                        color: '#64748b'
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    },
                    ticks: {
                        color: '#64748b'
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

// Update Sentiment Over Time Chart
function updateSentimentOverTimeChart(data) {
    const ctx = document.getElementById('sentimentOverTimeChart');
    if (!ctx) return;

    if (sentimentOverTimeChart) {
        sentimentOverTimeChart.destroy();
    }
    
    const labels = data.map(item => item.date);
    
    sentimentOverTimeChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Positive',
                    data: data.map(item => item.positive || 0),
                    borderColor: chartColors.positive,
                    backgroundColor: 'rgba(34, 197, 94, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 5
                },
                {
                    label: 'Neutral',
                    data: data.map(item => item.neutral || 0),
                    borderColor: chartColors.neutral,
                    backgroundColor: 'rgba(100, 116, 139, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 5
                },
                {
                    label: 'Negative',
                    data: data.map(item => item.negative || 0),
                    borderColor: chartColors.negative,
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 5
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    align: 'end',
                    labels: {
                        usePointStyle: true,
                        padding: 20,
                        color: '#64748b'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(30, 41, 59, 0.9)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    padding: 12,
                    cornerRadius: 8
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxTicksLimit: 10,
                        color: '#64748b'
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    },
                    ticks: {
                        color: '#64748b'
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

// ── Entity Treemap (D3) ────────────────────────────────────────────────────
function updateEntityTreemap(data) {
    const container = document.getElementById('entityTreemap');
    if (!container) return;
    container.innerHTML = '';
    if (!data || data.length === 0) return;

    const w = container.clientWidth || 300;
    const h = container.clientHeight || 130;

    const root = d3.hierarchy({ children: data.map(d => ({ name: d.entitas, value: (d.positive||0)+(d.neutral||0)+(d.negative||0), positive: d.positive||0, neutral: d.neutral||0, negative: d.negative||0 })) })
        .sum(d => d.value)
        .sort((a, b) => b.value - a.value);

    d3.treemap().size([w, h]).paddingInner(2).paddingOuter(1)(root);

    const colorScale = d3.scaleOrdinal()
        .domain(data.map(d => d.entitas))
        .range(['#4f46e5','#0ea5e9','#22c55e','#f59e0b','#ef4444','#8b5cf6','#ec4899','#14b8a6','#f97316','#84cc16','#6366f1','#38bdf8']);

    const svg = d3.select(container).append('svg')
        .attr('width', w).attr('height', h).style('font-family', 'Inter, sans-serif');

    const cell = svg.selectAll('g')
        .data(root.leaves())
        .join('g')
        .attr('transform', d => `translate(${d.x0},${d.y0})`);

    cell.append('rect')
        .attr('width', d => Math.max(0, d.x1 - d.x0))
        .attr('height', d => Math.max(0, d.y1 - d.y0))
        .attr('fill', d => colorScale(d.data.name))
        .attr('rx', 3)
        .attr('opacity', 0.85);

    cell.append('title')
        .text(d => `${d.data.name}\nTotal: ${d.data.value}\n+${d.data.positive} ~${d.data.neutral} -${d.data.negative}`);

    cell.filter(d => (d.x1 - d.x0) > 28 && (d.y1 - d.y0) > 14)
        .append('text')
        .attr('x', 4)
        .attr('y', 11)
        .attr('fill', '#fff')
        .attr('font-size', '9px')
        .attr('font-weight', '600')
        .text(d => {
            const cellW = d.x1 - d.x0;
            const maxChar = Math.floor(cellW / 5.5);
            return d.data.name.length > maxChar ? d.data.name.slice(0, maxChar - 1) + '…' : d.data.name;
        });

    cell.filter(d => (d.x1 - d.x0) > 28 && (d.y1 - d.y0) > 26)
        .append('text')
        .attr('x', 4)
        .attr('y', 22)
        .attr('fill', 'rgba(255,255,255,0.85)')
        .attr('font-size', '8px')
        .text(d => d.data.value);
}

// Update Top Sources Chart
function updateTopSourcesChart(data) {
    const ctx = document.getElementById('topSourcesChart');
    if (!ctx) return;
    if (topSourcesChart) topSourcesChart.destroy();
    if (!data || data.length === 0) return;

    const labels = data.map(item => item.source_news);

    topSourcesChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Positive',
                    data: data.map(item => item.positive || 0),
                    backgroundColor: chartColors.positive,
                    borderRadius: 4
                },
                {
                    label: 'Neutral',
                    data: data.map(item => item.neutral || 0),
                    backgroundColor: chartColors.neutral,
                    borderRadius: 4
                },
                {
                    label: 'Negative',
                    data: data.map(item => item.negative || 0),
                    backgroundColor: chartColors.negative,
                    borderRadius: 4
                }
            ]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    align: 'center',
                    labels: { usePointStyle: true, padding: 14, color: '#1e293b', font: { size: 10 } }
                },
                tooltip: {
                    backgroundColor: 'rgba(30,41,59,0.9)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    padding: 12,
                    cornerRadius: 8
                }
            },
            scales: {
                x: { stacked: true, grid: { color: 'rgba(148,163,184,0.1)' }, ticks: { color: '#1e293b', font: { size: 9 } } },
                y: { stacked: true, grid: { display: false }, ticks: { color: '#1e293b', font: { size: 9 } } }
            }
        }
    });
}

// Update Top Topics Chart
function updateTopTopicsChart(data) {
    const ctx = document.getElementById('topTopicsChart');
    if (!ctx) return;
    if (topTopicsChart) topTopicsChart.destroy();
    if (!data || data.length === 0) return;

    const labels = data.map(item => item.topik_berita);

    topTopicsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Positive',
                    data: data.map(item => item.positive || 0),
                    backgroundColor: chartColors.positive,
                    borderRadius: 4
                },
                {
                    label: 'Neutral',
                    data: data.map(item => item.neutral || 0),
                    backgroundColor: chartColors.neutral,
                    borderRadius: 4
                },
                {
                    label: 'Negative',
                    data: data.map(item => item.negative || 0),
                    backgroundColor: chartColors.negative,
                    borderRadius: 4
                }
            ]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    align: 'center',
                    labels: { usePointStyle: true, padding: 14, color: '#1e293b', font: { size: 10 } }
                },
                tooltip: {
                    backgroundColor: 'rgba(30,41,59,0.9)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    padding: 12,
                    cornerRadius: 8
                }
            },
            scales: {
                x: { stacked: true, grid: { color: 'rgba(148,163,184,0.1)' }, ticks: { color: '#1e293b', font: { size: 9 } } },
                y: { stacked: true, grid: { display: false }, ticks: { color: '#1e293b', font: { size: 9 } } }
            }
        }
    });
}

// Update Top Entities Chart
function updateTopEntitiesChart(data) {
    const ctx = document.getElementById('topEntitiesChart');
    if (!ctx) return;
    if (topEntitiesChart) topEntitiesChart.destroy();
    if (!data || data.length === 0) return;

    const labels = data.map(item => item.entitas);

    topEntitiesChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Positive',
                    data: data.map(item => item.positive || 0),
                    backgroundColor: chartColors.positive,
                    borderRadius: 4
                },
                {
                    label: 'Neutral',
                    data: data.map(item => item.neutral || 0),
                    backgroundColor: chartColors.neutral,
                    borderRadius: 4
                },
                {
                    label: 'Negative',
                    data: data.map(item => item.negative || 0),
                    backgroundColor: chartColors.negative,
                    borderRadius: 4
                }
            ]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    align: 'center',
                    labels: { usePointStyle: true, padding: 14, color: '#1e293b', font: { size: 10 } }
                },
                tooltip: {
                    backgroundColor: 'rgba(30,41,59,0.9)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    padding: 12,
                    cornerRadius: 8
                }
            },
            scales: {
                x: { stacked: true, grid: { color: 'rgba(148,163,184,0.1)' }, ticks: { color: '#1e293b', font: { size: 9 } } },
                y: { stacked: true, grid: { display: false }, ticks: { color: '#1e293b', font: { size: 9 } } }
            }
        }
    });
}

// Update News List
function updateNewsList(news) {
    const container = document.getElementById('news-list');
    
    if (!news || news.length === 0) {
        container.innerHTML = '<p class="no-data">No news articles found.</p>';
        updateNewsCount(0);
        return;
    }
    
    container.innerHTML = news.map(item => `
        <div class="news-item fade-in">
            <div class="news-title">
                <a href="${item.url}" target="_blank" rel="noopener noreferrer">
                    ${escapeHtml(item.title)}
                </a>
            </div>
            <div class="news-meta">
                <span class="news-source">
                    <i class="fas fa-globe"></i> ${escapeHtml(item.source)}
                </span>
                <span class="news-date">
                    <i class="fas fa-clock"></i> ${item.date}
                </span>
                ${item.topic ? `<span class="news-topic"><i class="fas fa-tag"></i> ${escapeHtml(item.topic)}</span>` : ''}
                ${item.entities && item.entities.length > 0 ? item.entities.map(e => `<span class="news-entity">${escapeHtml(e)}</span>`).join('') : ''}
                <span class="news-sentiment sentiment-${item.sentiment}">
                    ${item.sentiment}
                </span>
            </div>
        </div>
    `).join('');
    
    updateNewsCount(news.length);
}

// Initialize news filters
function initializeNewsFilters() {
    const sourceFilter = document.getElementById('source-filter');
    const sentimentFilter = document.getElementById('sentiment-filter');
    const topicFilter = document.getElementById('topic-filter');

    const entityFilter = document.getElementById('entity-filter');

    if (sourceFilter)   sourceFilter.addEventListener('change', applyNewsFilters);
    if (sentimentFilter) sentimentFilter.addEventListener('change', applyNewsFilters);
    if (topicFilter)    topicFilter.addEventListener('change', applyNewsFilters);
    if (entityFilter)   entityFilter.addEventListener('change', applyNewsFilters);
}

// Populate source filter dropdown
function populateSourceFilter() {
    const sourceFilter = document.getElementById('source-filter');
    if (!sourceFilter || !allNewsData.length) return;
    
    // Get unique sources, sorted case-insensitively
    const sources = [...new Set(allNewsData.map(item => item.source))]
        .filter(Boolean)
        .sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));
    
    // Clear existing options except "All Sources"
    sourceFilter.innerHTML = '<option value="">All Sources</option>';
    
    // Add source options
    sources.forEach(source => {
        const option = document.createElement('option');
        option.value = source;
        option.textContent = source;
        sourceFilter.appendChild(option);
    });
}

// Populate entity filter dropdown
function populateEntityFilter() {
    const entityFilter = document.getElementById('entity-filter');
    if (!entityFilter || !allNewsData.length) return;

    const entitySet = new Set();
    allNewsData.forEach(item => {
        if (Array.isArray(item.entities)) {
            item.entities.forEach(e => { if (e) entitySet.add(e); });
        }
    });
    const entities = [...entitySet].sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));

    entityFilter.innerHTML = '<option value="">All Entities</option>';
    entities.forEach(entity => {
        const option = document.createElement('option');
        option.value = entity;
        option.textContent = entity;
        entityFilter.appendChild(option);
    });
}

// Populate topic filter dropdown
function populateTopicFilter() {
    const topicFilter = document.getElementById('topic-filter');
    if (!topicFilter || !allNewsData.length) return;

    const topics = [...new Set(allNewsData.map(item => item.topic))]
        .filter(Boolean)
        .sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));

    topicFilter.innerHTML = '<option value="">All Topics</option>';
    topics.forEach(topic => {
        const option = document.createElement('option');
        option.value = topic;
        option.textContent = topic;
        topicFilter.appendChild(option);
    });
}

// Apply filters to news data
function applyNewsFilters() {
    const sourceFilter = document.getElementById('source-filter');
    const sentimentFilter = document.getElementById('sentiment-filter');
    const topicFilter = document.getElementById('topic-filter');
    const entityFilter = document.getElementById('entity-filter');

    if (!allNewsData.length) return;

    let filtered = [...allNewsData];

    if (sourceFilter && sourceFilter.value)
        filtered = filtered.filter(item => item.source === sourceFilter.value);

    if (sentimentFilter && sentimentFilter.value)
        filtered = filtered.filter(item => item.sentiment === sentimentFilter.value);

    if (topicFilter && topicFilter.value)
        filtered = filtered.filter(item => item.topic === topicFilter.value);

    if (entityFilter && entityFilter.value)
        filtered = filtered.filter(item => Array.isArray(item.entities) && item.entities.includes(entityFilter.value));

    filteredNewsData = filtered;
    updateNewsList(filtered);
}

// Update news count display
function updateNewsCount(count) {
    const countElement = document.getElementById('filtered-news-count');
    if (countElement) {
        countElement.textContent = count;
    }
}

// Enhanced updateNewsList to populate filters on first load
function updateNewsListAndFilters(news) {
    allNewsData = news;
    filteredNewsData = news;
    updateNewsList(news);
    populateSourceFilter();
    populateTopicFilter();
    populateEntityFilter();
}

// ── Chart 5: Topic Share Over Time ────────────────────────────────────────
function updateTopicShareChart(payload) {
    const ctx = document.getElementById('topicShareChart');
    if (topicShareChart) topicShareChart.destroy();
    if (!payload || !payload.data || payload.data.length === 0) return;

    const { data, topics } = payload;
    const labels = data.map(d => d.date);

    topicShareChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: topics.map((topic, i) => ({
                label: topic,
                data: data.map(d => d[topic] || 0),
                borderColor: palette[i % palette.length],
                backgroundColor: palette[i % palette.length] + '33',
                fill: true,
                tension: 0.4,
                pointRadius: 2,
                pointHoverRadius: 5,
                borderWidth: 2
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', align: 'end', labels: { usePointStyle: true, padding: 14, color: '#64748b', font: { size: 11 } } },
                tooltip: { backgroundColor: 'rgba(30,41,59,0.9)', titleColor: '#fff', bodyColor: '#fff', padding: 12, cornerRadius: 8 }
            },
            scales: {
                x: { stacked: true, grid: { display: false }, ticks: { color: '#64748b', maxTicksLimit: 10 } },
                y: { stacked: true, beginAtZero: true, grid: { color: 'rgba(148,163,184,0.1)' }, ticks: { color: '#64748b' } }
            },
            interaction: { intersect: false, mode: 'index' }
        }
    });
}

// ── Chart 6: Entity Mention Trend ──────────────────────────────────────────
function updateEntityTrendChart(payload) {
    const ctx = document.getElementById('entityTrendChart');
    if (entityTrendChart) entityTrendChart.destroy();
    if (!payload || !payload.data || payload.data.length === 0) return;

    const { data, entities } = payload;
    const labels = data.map(d => d.date);

    entityTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: entities.map((entity, i) => ({
                label: entity,
                data: data.map(d => d[entity] || 0),
                borderColor: palette[i % palette.length],
                backgroundColor: 'transparent',
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 5,
                borderWidth: 2
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', align: 'end', labels: { usePointStyle: true, padding: 14, color: '#64748b', font: { size: 11 } } },
                tooltip: { backgroundColor: 'rgba(30,41,59,0.9)', titleColor: '#fff', bodyColor: '#fff', padding: 12, cornerRadius: 8 }
            },
            scales: {
                x: { grid: { display: false }, ticks: { color: '#64748b', maxTicksLimit: 10 } },
                y: { beginAtZero: true, grid: { color: 'rgba(148,163,184,0.1)' }, ticks: { color: '#64748b' } }
            },
            interaction: { intersect: false, mode: 'index' }
        }
    });
}

// ── Chart: Top 5 Sources News Count Over Time (Line) ──────────────────────
function updateSourceTrendChart(payload) {
    const ctx = document.getElementById('sourceTrendChart');
    if (!ctx) return;
    if (sourceTrendChart) sourceTrendChart.destroy();
    if (!payload || !payload.data || payload.data.length === 0) return;

    const { data, sources } = payload;
    const labels = data.map(d => d.date);

    sourceTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: sources.map((source, i) => ({
                label: source,
                data: data.map(d => d[source] || 0),
                borderColor: palette[i % palette.length],
                backgroundColor: 'transparent',
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 5,
                borderWidth: 2
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', align: 'end', labels: { usePointStyle: true, padding: 14, color: '#64748b', font: { size: 11 } } },
                tooltip: { backgroundColor: 'rgba(30,41,59,0.9)', titleColor: '#fff', bodyColor: '#fff', padding: 12, cornerRadius: 8 }
            },
            scales: {
                x: { grid: { display: false }, ticks: { color: '#64748b', maxTicksLimit: 10 } },
                y: { beginAtZero: true, grid: { color: 'rgba(148,163,184,0.1)' }, ticks: { color: '#64748b' } }
            },
            interaction: { intersect: false, mode: 'index' }
        }
    });
}

// ── Chart 7: Source Volume vs Negativity (Scatter) ─────────────────────────
function updateSourceBubbleChart(data) {
    const ctx = document.getElementById('sourceBubbleChart');
    if (!ctx) return;
    if (sourceBubbleChart) sourceBubbleChart.destroy();
    if (!data || data.length === 0) return;

    const pointColors = data.map(d => {
        if (d.neg_pct >= 60) return 'rgba(239,68,68,0.75)';
        if (d.neg_pct >= 30) return 'rgba(245,158,11,0.75)';
        return 'rgba(34,197,94,0.75)';
    });

    sourceBubbleChart = new Chart(ctx, {
        type: 'bubble',
        data: {
            datasets: [{
                label: 'Sources',
                data: data.map(d => ({ x: d.total, y: d.neg_pct, r: Math.min(Math.sqrt(d.total) * 2, 28), label: d.source })),
                backgroundColor: pointColors,
                borderColor: pointColors.map(c => c.replace('0.75', '1')),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(30,41,59,0.9)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: ctx => {
                            const d = data[ctx.dataIndex];
                            return [`Source: ${d.source}`, `Total: ${d.total}`, `Neg %: ${d.neg_pct}%`];
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Total Articles', color: '#64748b' },
                    grid: { color: 'rgba(148,163,184,0.1)' },
                    ticks: { color: '#64748b' }
                },
                y: {
                    title: { display: true, text: 'Negativity %', color: '#64748b' },
                    beginAtZero: true,
                    max: 100,
                    grid: { color: 'rgba(148,163,184,0.1)' },
                    ticks: { color: '#64748b', callback: v => v + '%' }
                }
            }
        }
    });
}

// ── Chart 8: Activity Heatmap (Weekday × Hour) ─────────────────────────────
function renderActivityHeatmap(data) {
    const container = document.getElementById('activityHeatmap');
    if (!container) return;
    container.innerHTML = '';

    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const hours = Array.from({ length: 24 }, (_, i) => i);

    // Build lookup: weekday → hour → count
    const lookup = {};
    (data || []).forEach(d => {
        if (!lookup[d.weekday]) lookup[d.weekday] = {};
        lookup[d.weekday][d.hour] = d.count;
    });
    const maxVal = Math.max(1, ...Object.values(lookup).flatMap(h => Object.values(h)));

    // Hour header row
    const spacer = document.createElement('div');
    spacer.className = 'heatmap-spacer';
    container.appendChild(spacer);
    hours.forEach(h => {
        const el = document.createElement('div');
        el.className = 'heatmap-hour-header';
        el.textContent = h % 3 === 0 ? h : '';
        container.appendChild(el);
    });

    // Data rows
    days.forEach((day, wi) => {
        const label = document.createElement('div');
        label.className = 'heatmap-row-label';
        label.textContent = day;
        container.appendChild(label);

        hours.forEach(h => {
            const count = (lookup[wi] && lookup[wi][h]) || 0;
            const intensity = count / maxVal;
            const cell = document.createElement('div');
            cell.className = 'heatmap-cell';
            if (count > 0) {
                // Interpolate from light indigo to deep indigo
                const r = Math.round(224 - (224 - 79) * intensity);
                const g = Math.round(231 - (231 - 70) * intensity);
                const b = Math.round(255 - (255 - 229) * intensity);
                cell.style.background = `rgb(${r},${g},${b})`;
            }
            cell.setAttribute('data-tip', `${day} ${h}:00 — ${count} articles`);
            container.appendChild(cell);
        });
    });
}

// ── Chart 9: Topic × Entity Heatmap ──────────────────────────────────────
function renderTopicEntityHeatmap(payload) {
    const container = document.getElementById('topicEntityHeatmap');
    if (!container) return;
    container.innerHTML = '';
    if (!payload || !payload.data || payload.data.length === 0) return;

    const { data, topics, entities } = payload;
    const nCols = entities.length;

    // Set dynamic grid columns: label column + N entity columns
    container.style.gridTemplateColumns = `180px repeat(${nCols}, 52px)`;

    // Build lookup for fast access
    const lookup = {};
    data.forEach(d => {
        if (!lookup[d.topic]) lookup[d.topic] = {};
        lookup[d.topic][d.entity] = d;
    });
    const maxTotal = Math.max(1, ...data.map(d => d.total));

    // Sentiment base colors [R, G, B]
    const sentRGB = {
        positive: [34, 197, 94],
        neutral:  [100, 116, 139],
        negative: [239, 68, 68],
    };

    // Header row: spacer + rotated entity labels
    const spacer = document.createElement('div');
    spacer.className = 'hm2-col-header-spacer';
    container.appendChild(spacer);
    entities.forEach(entity => {
        const lbl = document.createElement('div');
        lbl.className = 'hm2-col-label';
        lbl.textContent = entity;
        lbl.title = entity;
        container.appendChild(lbl);
    });

    // Data rows
    topics.forEach(topic => {
        const rowLabel = document.createElement('div');
        rowLabel.className = 'hm2-row-label';
        rowLabel.textContent = topic;
        rowLabel.title = topic;
        container.appendChild(rowLabel);

        entities.forEach(entity => {
            const cell = document.createElement('div');
            cell.className = 'hm2-cell';
            const d = lookup[topic] && lookup[topic][entity];
            if (d && d.total > 0) {
                const intensity = 0.15 + (d.total / maxTotal) * 0.75;
                const [r, g, b] = sentRGB[d.dominant] || [241, 245, 249];
                cell.style.background = `rgba(${r},${g},${b},${intensity})`;
                cell.setAttribute('data-tip',
                    `${topic}\n× ${entity}\n✅ ${d.positive}  ◾ ${d.neutral}  ❌ ${d.negative}`);
            }
            container.appendChild(cell);
        });
    });
}

// ── Chart 10: Radar Charts (3 × sentiment) ────────────────────────────────
function updateRadarCharts(data) {
    if (!data || !data.labels || data.labels.length === 0) return;

    function makeRadar(existingRef, canvasId, label, values, color) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;
        if (existingRef) existingRef.destroy();
        return new Chart(ctx, {
            type: 'radar',
            data: {
                labels: data.labels,
                datasets: [{
                    label,
                    data: values,
                    backgroundColor: color + '28',
                    borderColor: color,
                    borderWidth: 2,
                    pointBackgroundColor: color,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(30,41,59,0.9)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        padding: 10,
                        cornerRadius: 8
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        grid: { color: 'rgba(148,163,184,0.25)' },
                        ticks: { color: '#64748b', backdropColor: 'transparent', font: { size: 10 }, maxTicksLimit: 4 },
                        pointLabels: { color: '#64748b', font: { size: 10 } }
                    }
                }
            }
        });
    }

    radarPositifChart = makeRadar(radarPositifChart, 'radarPositifChart', 'Positive', data.positive, '#22c55e');
    radarNetralChart  = makeRadar(radarNetralChart,  'radarNetralChart',  'Neutral',  data.neutral,  '#64748b');
    radarNegatifChart = makeRadar(radarNegatifChart, 'radarNegatifChart', 'Negative', data.negative, '#ef4444');
}

// ── Radar: Sentiment by Top 10 Sources (Overview) ─────────────────────────
function updateRadarSourceCharts(data) {
    if (!data || !data.labels || data.labels.length === 0) return;

    // Shared max across all three datasets so axes are comparable
    const sharedMax = Math.max(...data.positive, ...data.neutral, ...data.negative);

    function makeRadarSrc(existingRef, canvasId, label, values, color) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;
        if (existingRef) existingRef.destroy();
        return new Chart(ctx, {
            type: 'radar',
            data: {
                labels: data.labels,
                datasets: [{
                    label,
                    data: values,
                    backgroundColor: color + '28',
                    borderColor: color,
                    borderWidth: 2,
                    pointBackgroundColor: color,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(30,41,59,0.9)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        padding: 10,
                        cornerRadius: 8
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        suggestedMax: sharedMax,
                        grid: { color: 'rgba(0,0,0,0.12)' },
                        angleLines: { color: 'rgba(0,0,0,0.15)' },
                        ticks: {
                            display: false
                        },
                        pointLabels: {
                            color: '#000000',
                            font: { size: 13, weight: 'bold' }
                        }
                    }
                }
            }
        });
    }

    radarSrcPositifChart = makeRadarSrc(radarSrcPositifChart, 'radarSrcPositifChart', 'Positive', data.positive, '#22c55e');
    radarSrcNetralChart  = makeRadarSrc(radarSrcNetralChart,  'radarSrcNetralChart',  'Neutral',  data.neutral,  '#64748b');
    radarSrcNegatifChart = makeRadarSrc(radarSrcNegatifChart, 'radarSrcNegatifChart', 'Negative', data.negative, '#ef4444');
}

// ── Chart 11: Sankey (D3) ──────────────────────────────────────────────────
function updateSankeyChart(rawData) {
    const container = document.getElementById('sankeyChart');
    if (!container) return;
    container.innerHTML = '';
    if (!rawData || rawData.length === 0) return;

    const sentColors = { positive: '#22c55e', neutral: '#94a3b8', negative: '#ef4444' };
    const width  = container.clientWidth  || 800;
    const height = 400;
    const margin = { top: 16, right: 180, bottom: 16, left: 100 };
    const innerW = width  - margin.left - margin.right;
    const innerH = height - margin.top  - margin.bottom;

    // Build unique node objects keyed by id
    const nodeMap = {};
    rawData.forEach(d => {
        if (!nodeMap[d.from]) nodeMap[d.from] = { id: d.from };
        if (!nodeMap[d.to])   nodeMap[d.to]   = { id: d.to };
    });
    const nodeList  = Object.values(nodeMap);
    const linksList = rawData.map(d => ({ source: d.from, target: d.to, value: d.flow }));

    const sankey = d3.sankey()
        .nodeId(d => d.id)
        .nodeWidth(18)
        .nodePadding(14)
        .extent([[0, 0], [innerW, innerH]]);

    const graph = sankey({ nodes: nodeList.map(n => ({ ...n })), links: linksList });

    const svg = d3.select(container)
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    // Gradient defs per link
    const defs = svg.append('defs');
    graph.links.forEach((link, i) => {
        const grad = defs.append('linearGradient')
            .attr('id', `sk-grad-${i}`)
            .attr('gradientUnits', 'userSpaceOnUse')
            .attr('x1', link.source.x1).attr('x2', link.target.x0);
        const col = sentColors[link.source.id] || '#4f46e5';
        grad.append('stop').attr('offset', '0%').attr('stop-color', col).attr('stop-opacity', 0.75);
        grad.append('stop').attr('offset', '100%').attr('stop-color', col).attr('stop-opacity', 0.3);
    });

    // Links
    svg.append('g')
        .attr('fill', 'none')
        .selectAll('path')
        .data(graph.links)
        .join('path')
        .attr('d', d3.sankeyLinkHorizontal())
        .attr('stroke', (d, i) => `url(#sk-grad-${i})`)
        .attr('stroke-width', d => Math.max(1, d.width))
        .append('title')
        .text(d => `${d.source.id} → ${d.target.id}\n${d.value} articles`);

    // Nodes
    svg.append('g')
        .selectAll('rect')
        .data(graph.nodes)
        .join('rect')
        .attr('x', d => d.x0).attr('y', d => d.y0)
        .attr('height', d => Math.max(1, d.y1 - d.y0))
        .attr('width',  d => d.x1 - d.x0)
        .attr('fill',   d => sentColors[d.id] || '#4f46e5')
        .attr('rx', 3).attr('opacity', 0.9)
        .append('title')
        .text(d => `${d.id}\n${d.value} articles`);

    // Labels
    svg.append('g')
        .style('font-size', '12px')
        .style('font-family', 'Inter, sans-serif')
        .style('fill', '#1e293b')
        .selectAll('text')
        .data(graph.nodes)
        .join('text')
        .attr('x', d => d.x0 < innerW / 2 ? d.x1 + 8 : d.x0 - 8)
        .attr('y', d => (d.y1 + d.y0) / 2)
        .attr('dy', '0.35em')
        .attr('text-anchor', d => d.x0 < innerW / 2 ? 'start' : 'end')
        .text(d => d.id.length > 26 ? d.id.slice(0, 24) + '…' : d.id);
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
