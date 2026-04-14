import React, { useMemo, memo } from 'react';
import useSclodaInsights from '../../hooks/useSclodaInsights';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
} from 'chart.js';
import { Bar, Line } from 'react-chartjs-2';
import AIInsight from './AIInsight';

// Register Chart.js components
ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

const MarketDashboard = ({ items, macro, analytics }) => {
    // ── Fix #1: Single-flight insights via shared hook (no duplicate LLM calls) ──
    const { insights } = useSclodaInsights(macro);

    // Chart Global Options
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 1200, easing: 'easeOutQuart' },
        plugins: { legend: { display: false } },
        elements: { point: { radius: 0 } },
        scales: {
            x: {
                grid: { color: '#2a2f38' },
                ticks: {
                    color: '#8b949e',
                    maxTicksLimit: 6,
                    autoSkip: true,
                    callback: (v, i, ticks) => {
                        const label = ticks[i]?.label || '';
                        // shorten YYYY-MM-DD -> YYYY or MMM YY when possible
                        if (label.length >= 10) return label.slice(2, 7); // YY-MM
                        return label;
                    }
                }
            },
            y: { grid: { color: '#2a2f38' }, ticks: { color: '#8b949e', maxTicksLimit: 6 } }
        }
    };

    const horizontalOptions = {
        ...commonOptions,
        indexAxis: 'y',
        scales: {
            x: { grid: { color: '#30363d' }, ticks: { color: '#8b949e' } },
            y: { grid: { display: false }, ticks: { color: '#c9d1d9', font: { size: 11 } } }
        }
    };

    // Data Processing
    const { top5Cheap, top5Expensive, distribution, summary } = useMemo(() => {
        if (!items || items.length === 0) return { top5Cheap: [], top5Expensive: [], distribution: {}, summary: {} };

        // Sort by cost
        const sorted = [...items].sort((a, b) => a.cost - b.cost);
        const top5Cheap = sorted.slice(0, 5);
        const top5Expensive = [...sorted].reverse().slice(0, 5); // Descending for Chart

        // Stats
        const costs = sorted.map(i => i.cost);
        const min = costs[0];
        const max = costs[costs.length - 1];
        const avg = costs.reduce((a, b) => a + b, 0) / costs.length;
        const median = costs[Math.floor(costs.length / 2)];
        const savings = max - min;

        const leader = top5Cheap[0];
        const laggard = top5Expensive[0];

        return {
            top5Cheap,
            top5Expensive,
            distribution: { min, avg, max, savings, median },
            summary: {
                leaderLabel: leader ? `${leader.product} (${leader.institution})` : '—',
                laggardLabel: laggard ? `${laggard.institution}` : '—',
                savings,
                median,
                count: items.length,
            }
        };
    }, [items]);

    // Chart Data Configs
    const cheapData = {
        labels: top5Cheap.map(i => i.product),
        datasets: [{
            label: 'ATC',
            data: top5Cheap.map(i => i.cost),
            backgroundColor: '#238636',
            borderColor: '#2ea043',
            borderWidth: 1
        }]
    };

    const expensiveData = {
        labels: top5Expensive.map(i => i.institution),
        datasets: [{
            label: 'ATC',
            data: top5Expensive.map(i => i.cost),
            backgroundColor: '#a40e26',
            borderColor: '#da3633',
            borderWidth: 1
        }]
    };

    const distData = {
        labels: ['Lowest', 'Average', 'Highest'],
        datasets: [{
            label: 'Cost Spread',
            data: [distribution.min, distribution.avg, distribution.max],
            backgroundColor: ['#238636', '#d29922', '#a40e26'],
            borderColor: ['#2ea043', '#dbab09', '#da3633'],
            borderWidth: 1
        }]
    };

    const fmtClp = (n) => n != null ? `$${Math.round(n).toLocaleString('es-CL')}` : '—';
    const fmtNum = (n, unit) => {
        if (unit === '%') return `${n?.toFixed(2)}%`;
        if (unit?.includes('USD') || unit === 'CLP/USD')
            return `$${(n ?? 0).toLocaleString('en-US', { maximumFractionDigits: 2 })}`;
        if (unit === 'Index') return (n ?? 0).toLocaleString('en-US', { maximumFractionDigits: 1 });
        return (n ?? 0).toLocaleString('en-US', { maximumFractionDigits: 2 });
    };

    // Build line chart config with moving average overlay & gradient fill
    const buildLineConfig = (series = [], color = '#58a6ff', label = '', unit = '') => {
        const data = series.slice(-260); // keep recent points to unclutter
        const labels = data.map(d => new Date(d.date).toLocaleDateString());
        const values = data.map(d => d.value);
        // simple moving average window 7
        const ma = values.map((v, i, arr) => {
            const start = Math.max(0, i - 6);
            const slice = arr.slice(start, i + 1);
            return slice.reduce((a, b) => a + b, 0) / slice.length;
        });
        const last = values.at(-1);
        const prev = values.at(-2) ?? last;
        const change = prev ? ((last - prev) / prev) * 100 : 0;
        return {
            chart: {
                labels,
                datasets: [
                    {
                        label,
                        data: values,
                        borderColor: color,
                        backgroundColor: `${color}20`,
                        fill: true,
                        tension: 0.35,
                        borderWidth: 2,
                    },
                    {
                        label: `${label} (MA7)`,
                        data: ma,
                        borderColor: '#9ca3af',
                        borderDash: [6, 4],
                        fill: false,
                        tension: 0.2,
                        borderWidth: 1,
                    }
                ]
            },
            last,
            change,
            unit
        };
    };

    // Prebuilt line configs
    const cpiCfg = buildLineConfig(macro?.cpi, '#f78166', 'CPI', 'Index');
    const yieldCfg = buildLineConfig(macro?.yields, '#58a6ff', '10Y Yield', '%');
    const goldCfg = buildLineConfig(macro?.gold, '#bf8700', 'Gold', 'USD/oz');
    const copperCfg = buildLineConfig(macro?.copper, '#da3633', 'Copper', 'USD/lb');
    const oilCfg = buildLineConfig(macro?.oil, '#c9d1d9', 'Oil WTI', 'USD/bbl');
    const btcCfg = buildLineConfig(macro?.btc, '#f2a900', 'Bitcoin', 'CLP');
    const ethCfg = buildLineConfig(macro?.eth, '#627eea', 'Ethereum', 'CLP');

    const renderLineCard = (title, flag, cfg, colorClass = 'text-light') => (
        <div className="card card-custom h-100 p-3 animate-in">
            <div className="d-flex justify-content-between align-items-center mb-1">
                <h6 className="mb-0" style={{ color: '#e6edf3' }}>{flag} {title}</h6>
                <div className="badge bg-dark border border-secondary">
                    {fmtNum(cfg.last, cfg.unit)} ({cfg.change >= 0 ? '▲' : '▼'} {Math.abs(cfg.change).toFixed(2)}%)
                </div>
            </div>
            <div style={{ height: '220px' }}>
                <Line data={cfg.chart} options={commonOptions} />
            </div>
            <AIInsight
                insight={insights[title.toLowerCase()] || null}
                text={`Latest value: ${fmtNum(cfg.last, cfg.unit)} • Δ ${cfg.change.toFixed(2)}% vs prev.`}
                colorClass={colorClass}
            />
        </div>
    );

    return (
        <div className="modal fade" id="chartsModal" tabIndex="-1" aria-hidden="true">
            <div className="modal-dialog modal-xl modal-dialog-scrollable">
                <div className="modal-content">
                    <div className="modal-header">
                        <h5 className="modal-title">Market Analysis Panel</h5>
                        <button type="button" className="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div className="modal-body bg-dark">
                        <div className="container-fluid">

                            {/* Row 0: Quick badges */}
                            <div className="row g-3 mb-3">
                                <div className="col-md-3">
                                    <div className="card card-custom p-3 h-100 d-flex justify-content-center" style={{ borderColor: '#2ea04355' }}>
                                        <div className="text-light small">Leader</div>
                                        <div className="fw-bold text-success" style={{ fontSize: '0.95rem' }}>{summary.leaderLabel || '—'}</div>
                                        <div className="text-white-50" style={{ fontSize: '0.85rem' }}>{fmtClp(distribution.min)} / year</div>
                                    </div>
                                </div>
                                <div className="col-md-3">
                                    <div className="card card-custom p-3 h-100 d-flex justify-content-center" style={{ borderColor: '#a40e2655' }}>
                                        <div className="text-light small">Laggard</div>
                                        <div className="fw-bold text-danger" style={{ fontSize: '0.95rem' }}>{summary.laggardLabel || '—'}</div>
                                        <div className="text-white-50" style={{ fontSize: '0.85rem' }}>{fmtClp(distribution.max)} / year</div>
                                    </div>
                                </div>
                                <div className="col-md-3">
                                    <div className="card card-custom p-3 h-100 d-flex justify-content-center" style={{ borderColor: '#d2992255' }}>
                                        <div className="text-light small">Median</div>
                                        <div className="fw-bold text-warning" style={{ fontSize: '1rem' }}>{fmtClp(distribution.median)}</div>
                                        <div className="text-white-50" style={{ fontSize: '0.85rem' }}>Across {summary.count || 0} products</div>
                                    </div>
                                </div>
                                <div className="col-md-3">
                                    <div className="card card-custom p-3 h-100 d-flex justify-content-center" style={{ borderColor: '#58a6ff55' }}>
                                        <div className="text-light small">Gap (max - min)</div>
                                        <div className="fw-bold text-primary" style={{ fontSize: '1rem' }}>{fmtClp(distribution.savings)}</div>
                                        <div className="text-white-50" style={{ fontSize: '0.85rem' }}>Potential annual savings</div>
                                    </div>
                                </div>
                            </div>

                            {/* Row 1: Ranking Analysis */}
                            <div className="row g-3 mb-4">
                                <div className="col-md-4">
                                    <div className="card card-custom h-100 p-3 animate-in" style={{ animationDelay: '0.1s' }}>
                                        <h6 className="text-success">🇨🇱 Top 5 Most Affordable (Annual)</h6>
                                        <div style={{ height: '200px' }}>
                                            <Bar data={cheapData} options={horizontalOptions} />
                                        </div>
                                        <AIInsight
                                            insight={
                                                insights['cheap'] ||
                                                analytics?.insight_cheap ||
                                                `Cheapest: ${summary.leaderLabel || '—'} (${fmtClp(distribution.min)}).`
                                            }
                                            colorClass="text-success"
                                        />
                                    </div>
                                </div>
                                <div className="col-md-4">
                                    <div className="card card-custom h-100 p-3 animate-in" style={{ animationDelay: '0.2s' }}>
                                        <h6 className="text-danger">🇨🇱 Top 5 Most Expensive</h6>
                                        <div style={{ height: '200px' }}>
                                            <Bar data={expensiveData} options={horizontalOptions} />
                                        </div>
                                        <AIInsight
                                            insight={
                                                insights['expensive'] ||
                                                analytics?.insight_expensive ||
                                                `Most expensive: ${summary.laggardLabel || '—'} (${fmtClp(distribution.max)}).`
                                            }
                                            colorClass="text-danger"
                                        />
                                    </div>
                                </div>
                                <div className="col-md-4">
                                    <div className="card card-custom h-100 p-3 animate-in" style={{ animationDelay: '0.3s' }}>
                                        <h6 className="text-info">🇨🇱 Cost Distribution</h6>
                                        <div style={{ height: '200px' }}>
                                            <Bar data={distData} options={commonOptions} />
                                        </div>
                                        <AIInsight
                                            insight={
                                                insights['distribution'] ||
                                                analytics?.insight_distribution ||
                                                `Annual range: ${fmtClp(distribution.min)} to ${fmtClp(distribution.max)} (gap ${fmtClp(distribution.savings)}).`
                                            }
                                            colorClass="text-info"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Row 2: Macro Trends */}
                            <div className="row g-3 mt-1">
                                <div className="col-md-6">
                                    {renderLineCard('US CPI', '🇺🇸', cpiCfg, 'text-danger')}
                                </div>
                                <div className="col-md-6">
                                    {renderLineCard('10Y Bonds', '🇺🇸', yieldCfg, 'text-primary')}
                                </div>
                            </div>

                            {/* Row 3: Commodities */}
                            <div className="row g-3 mt-3">
                                <div className="col-md-4">
                                    {renderLineCard('Gold', '🥇', goldCfg, 'text-warning')}
                                </div>
                                <div className="col-md-4">
                                    {renderLineCard('Copper', '⛏️', copperCfg, 'text-danger')}
                                </div>
                                <div className="col-md-4">
                                    {renderLineCard('Oil WTI', '🛢️', oilCfg, 'text-light')}
                                </div>
                            </div>

                            {/* Row 4: Crypto */}
                            <div className="row g-3 mt-3">
                                <div className="col-md-6">
                                    {renderLineCard('Bitcoin', '🪙', btcCfg, 'text-warning')}
                                </div>
                                <div className="col-md-6">
                                    {renderLineCard('Ethereum', '💠', ethCfg, 'text-primary')}
                                </div>
                            </div>

                        </div>
                    </div>
                    <div className="modal-footer">
                        <small className="text-muted me-auto">*Sources: CMF Chile, BLS, US Treasury</small>
                        <button type="button" className="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default memo(MarketDashboard);
