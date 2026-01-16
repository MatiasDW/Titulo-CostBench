import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { Line } from 'react-chartjs-2';

/**
 * ChartCarousel - Continuous smooth scrolling carousel with REAL data
 * Includes Scloda analysis for each chart
 */
const ChartCarousel = ({ macro }) => {
    // All available charts with their data keys and Scloda insights
    const allCharts = useMemo(() => [
        {
            key: 'gold',
            title: '🥇 Gold',
            subtitle: 'USD/oz',
            color: '#bf8700',
            colorClass: 'text-warning',
            insight: 'Traditional safe-haven asset. Inversely correlated with risk appetite and USD strength.'
        },
        {
            key: 'copper',
            title: '⛏️ Copper',
            subtitle: 'USD/lb',
            color: '#da3633',
            colorClass: 'text-danger',
            insight: 'Chile\'s key export commodity. Strong indicator of global industrial demand and economic health.'
        },
        {
            key: 'btc',
            title: '🪙 Bitcoin',
            subtitle: 'CLP',
            color: '#f2a900',
            colorClass: 'text-warning',
            insight: 'Digital store of value. High volatility, increasingly correlated with tech equities.'
        },
        {
            key: 'eth',
            title: '💠 Ethereum',
            subtitle: 'CLP',
            color: '#627eea',
            colorClass: 'text-primary',
            insight: 'Smart contract platform. Tracks BTC with higher beta exposure to DeFi sentiment.'
        },
        {
            key: 'oil',
            title: '🛢️ WTI Oil',
            subtitle: 'USD/bbl',
            color: '#c9d1d9',
            colorClass: 'text-light',
            insight: 'Energy benchmark. Impacts Chilean fuel costs and transportation inflation directly.'
        },
        {
            key: 'cpi',
            title: '📊 US CPI',
            subtitle: 'Index',
            color: '#f78166',
            colorClass: 'text-danger',
            insight: 'US inflation measure. Key driver of Fed policy and global interest rate expectations.'
        },
        {
            key: 'yields',
            title: '📈 10Y Treasury',
            subtitle: 'Yield %',
            color: '#58a6ff',
            colorClass: 'text-primary',
            insight: 'Risk-free rate benchmark. Higher yields pressure emerging market currencies like CLP.'
        },
    ], []);

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: { legend: { display: false } },
        scales: {
            x: { display: false },
            y: {
                grid: { color: '#30363d' },
                ticks: { color: '#8b949e', maxTicksLimit: 3, font: { size: 9 } }
            }
        },
        elements: {
            point: { radius: 0 },
            line: { tension: 0.4 }
        }
    };

    // Calculate trend from REAL data
    const getTrend = (data) => {
        if (!data || data.length < 2) return { symbol: '—', color: '#8b949e', percent: '0.00' };
        const last = data[data.length - 1]?.value || 0;
        const first = data[0]?.value || last;
        const percentChange = ((last - first) / first * 100).toFixed(2);
        if (last > first) return { symbol: '▲', color: '#238636', percent: `+${percentChange}` };
        if (last < first) return { symbol: '▼', color: '#da3633', percent: percentChange };
        return { symbol: '—', color: '#8b949e', percent: '0.00' };
    };

    // Format value
    const formatValue = (value, key) => {
        if (!value) return '—';
        const decimals = (key === 'yields' || key === 'cpi') ? 2 : 0;
        return value.toLocaleString('es-CL', { maximumFractionDigits: decimals });
    };

    // Chart card with Scloda insight
    const ChartCard = ({ chart }) => {
        const data = macro?.[chart.key]?.slice(-25) || [];
        const trend = getTrend(data);
        const currentValue = data[data.length - 1]?.value;

        return (
            <div
                className="chart-card"
                style={{
                    flex: '0 0 320px',
                    minWidth: '320px',
                    marginRight: '16px',
                }}
            >
                <div
                    className="card card-custom h-100 p-3"
                    style={{
                        background: 'rgba(22, 27, 34, 0.92)',
                        backdropFilter: 'blur(12px)',
                        border: `1px solid ${chart.color}40`,
                        boxShadow: `0 4px 24px ${chart.color}15`,
                        minHeight: '220px',
                    }}
                >
                    {/* Header */}
                    <div className="d-flex justify-content-between align-items-start mb-1">
                        <div>
                            <h6 className={`${chart.colorClass} mb-0`} style={{ fontSize: '0.95rem' }}>
                                {chart.title}
                            </h6>
                            <small className="text-muted" style={{ fontSize: '0.65rem' }}>
                                {chart.subtitle}
                            </small>
                        </div>
                        <div className="text-end">
                            <div style={{
                                color: trend.color,
                                fontWeight: 'bold',
                                fontSize: '0.8rem',
                                fontFamily: 'monospace'
                            }}>
                                {trend.symbol} {trend.percent}%
                            </div>
                            <span style={{
                                fontSize: '1rem',
                                color: '#e6edf3',
                                fontFamily: 'monospace',
                                fontWeight: '700'
                            }}>
                                {formatValue(currentValue, chart.key)}
                            </span>
                        </div>
                    </div>

                    {/* Chart - REAL DATA */}
                    <div style={{ height: '70px', marginBottom: '8px' }}>
                        {data.length > 0 ? (
                            <Line
                                data={{
                                    labels: data.map((_, idx) => idx),
                                    datasets: [{
                                        data: data.map(d => d.value),
                                        borderColor: chart.color,
                                        backgroundColor: `${chart.color}15`,
                                        fill: true,
                                        borderWidth: 2
                                    }]
                                }}
                                options={chartOptions}
                            />
                        ) : (
                            <div className="text-center text-muted" style={{ paddingTop: '25px', fontSize: '0.75rem' }}>
                                Loading...
                            </div>
                        )}
                    </div>

                    {/* Scloda Insight */}
                    <div
                        style={{
                            borderTop: '1px solid #30363d',
                            paddingTop: '8px',
                        }}
                    >
                        <div className="d-flex align-items-start">
                            <span style={{ fontSize: '0.9rem', marginRight: '6px' }}>🧠</span>
                            <p
                                className="mb-0 text-secondary"
                                style={{
                                    fontSize: '0.7rem',
                                    lineHeight: '1.4',
                                    fontStyle: 'italic'
                                }}
                            >
                                {chart.insight}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    // Duplicate charts for seamless infinite scroll
    const duplicatedCharts = [...allCharts, ...allCharts];

    return (
        <div className="chart-carousel-wrapper" style={{ overflow: 'hidden', position: 'relative' }}>
            {/* Gradient fade edges */}
            <div style={{
                position: 'absolute',
                left: 0,
                top: 0,
                bottom: 0,
                width: '60px',
                background: 'linear-gradient(to right, #0d1117, transparent)',
                zIndex: 10,
                pointerEvents: 'none'
            }} />
            <div style={{
                position: 'absolute',
                right: 0,
                top: 0,
                bottom: 0,
                width: '60px',
                background: 'linear-gradient(to left, #0d1117, transparent)',
                zIndex: 10,
                pointerEvents: 'none'
            }} />

            {/* Scrolling container */}
            <motion.div
                className="chart-scroll-track"
                animate={{ x: [0, -(allCharts.length * 336)] }}
                transition={{
                    x: {
                        duration: 50, // 50 seconds for full cycle
                        repeat: Infinity,
                        ease: 'linear',
                    }
                }}
                style={{
                    display: 'flex',
                    width: 'fit-content',
                }}
            >
                {duplicatedCharts.map((chart, i) => (
                    <ChartCard key={`${chart.key}-${i}`} chart={chart} />
                ))}
            </motion.div>

            <style>{`
                .chart-carousel-wrapper {
                    padding: 10px 0;
                }
                
                .chart-scroll-track:hover {
                    animation-play-state: paused;
                }
            `}</style>
        </div>
    );
};

export default ChartCarousel;
