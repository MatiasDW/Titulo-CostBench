import React, { useMemo, useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Line } from 'react-chartjs-2';
import { FaUserTie } from 'react-icons/fa';
import AssetIcon from './AssetIcon';

/**
 * ChartCarousel - Continuous smooth scrolling carousel with REAL data
 * Includes Scloda analysis for each chart (Dynamic LLM generated)
 */
const ChartCarousel = ({ macro }) => {
    // Dynamic insights state
    const [insights, setInsights] = useState({});

    // All available charts configuration - TRANSLATED TO SPANISH
    const allCharts = useMemo(() => [
        {
            key: 'gold',
            title: '🥇 Oro',
            subtitle: 'USD/oz',
            color: '#bf8700',
            colorClass: 'text-warning',
            fallback: 'Activo refugio tradicional. Inversamente correlacional al riesgo.'
        },
        {
            key: 'copper',
            title: '⛏️ Cobre',
            subtitle: 'USD/lb',
            color: '#da3633',
            colorClass: 'text-danger',
            fallback: 'Sueldo de Chile. Indicador clave de demanda industrial global.'
        },
        {
            key: 'btc',
            title: '🪙 Bitcoin',
            subtitle: 'CLP',
            color: '#f2a900',
            colorClass: 'text-warning',
            fallback: 'Activo digital volátil. Proxy de riesgo.'
        },
        {
            key: 'eth',
            title: '💠 Ethereum',
            subtitle: 'CLP',
            color: '#627eea',
            colorClass: 'text-primary',
            fallback: 'Plataforma de contratos inteligentes. Alta exposición DeFi.'
        },
        {
            key: 'oil',
            title: '🛢️ Petróleo WTI',
            subtitle: 'USD/bbl',
            color: '#c9d1d9',
            colorClass: 'text-light',
            fallback: 'Referencia energética. Afecta inflación y transporte.'
        },
        {
            key: 'cpi',
            title: '📊 IPC EE.UU.',
            subtitle: 'Índice',
            color: '#f78166',
            colorClass: 'text-danger',
            fallback: 'Inflación USA. Clave para decisiones de la Fed.'
        },
        {
            key: 'yields',
            title: '📈 Treasury 10Y',
            subtitle: 'Tasa %',
            color: '#58a6ff',
            colorClass: 'text-primary',
            fallback: 'Tasa libre de riesgo. Presiona monedas emergentes al subir.'
        },
    ], []);

    // Calculate trend from REAL data helper
    const getTrend = (data) => {
        if (!data || data.length < 2) return { symbol: '—', color: '#8b949e', percent: 0, trend: 'stable' };
        const last = data[data.length - 1]?.value || 0;
        const first = data[0]?.value || last;
        const percentChange = ((last - first) / first * 100);

        let trend = 'stable';
        if (percentChange > 0.5) trend = 'up';
        if (percentChange < -0.5) trend = 'down';

        if (last > first) return { symbol: '▲', color: '#238636', percent: percentChange.toFixed(2), trend };
        if (last < first) return { symbol: '▼', color: '#da3633', percent: percentChange.toFixed(2), trend };
        return { symbol: '—', color: '#8b949e', percent: '0.00', trend };
    };

    // Fetch dynamic insights - PARALLELIZED for speed
    useEffect(() => {
        const fetchInsights = async () => {
            // Map over all charts to create an array of promises
            const promises = allCharts.map(async (chart) => {
                const data = macro?.[chart.key]?.slice(-25) || [];
                if (data.length === 0) return null;

                const currentValue = data[data.length - 1]?.value;
                const trendInfo = getTrend(data);

                // Check cache first (valid for 12 hours)
                const cacheKey = `scloda_insight_v2_${chart.key}`;
                const cached = localStorage.getItem(cacheKey);

                if (cached) {
                    const { insight, timestamp } = JSON.parse(cached);
                    // Use cache if < 12h old
                    if (Date.now() - timestamp < 12 * 60 * 60 * 1000) {
                        return { key: chart.key, insight };
                    }
                }

                // Fetch fresh insight
                try {
                    const response = await fetch('/api/v1/scloda/insight', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            asset: chart.key,
                            current_value: currentValue,
                            change_percent: parseFloat(trendInfo.percent),
                            trend: trendInfo.trend
                        })
                    });

                    if (response.ok) {
                        const result = await response.json();
                        // Save to cache
                        localStorage.setItem(cacheKey, JSON.stringify({
                            insight: result.insight,
                            timestamp: Date.now()
                        }));
                        return { key: chart.key, insight: result.insight };
                    }
                } catch (error) {
                    console.error(`Error fetching insight for ${chart.key}:`, error);
                }
                return null;
            });

            // Execute all requests in parallel
            const results = await Promise.all(promises);

            // Update state with valid results
            const newInsights = {};
            results.forEach(res => {
                if (res) newInsights[res.key] = res.insight;
            });

            setInsights(prev => ({ ...prev, ...newInsights }));
        };

        if (macro && Object.keys(macro).length > 0) {
            fetchInsights();
        }
    }, [macro, allCharts]);

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
        const insightText = insights[chart.key] || chart.fallback;

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
                            <FaUserTie size={14} style={{ marginRight: '6px', color: '#8b949e', marginTop: '2px' }} />
                            <p
                                className="mb-0 text-secondary"
                                style={{
                                    fontSize: '0.7rem',
                                    lineHeight: '1.4',
                                    fontStyle: 'italic'
                                }}
                            >
                                {insightText}
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
