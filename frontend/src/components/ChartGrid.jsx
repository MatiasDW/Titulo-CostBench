import React, { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Line } from 'react-chartjs-2';

/**
 * ChartGrid - Animated chart cards with LIVE simulated movement
 * Charts continuously update to simulate real-time trading data
 */
const ChartGrid = ({ macro }) => {
    const [liveData, setLiveData] = useState({});
    const intervalRef = useRef(null);

    // Chart configuration
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 500, easing: 'linear' },
        plugins: { legend: { display: false } },
        scales: {
            x: { display: false },
            y: {
                grid: { color: '#30363d' },
                ticks: { color: '#8b949e', maxTicksLimit: 4, font: { size: 10 } }
            }
        },
        elements: {
            point: { radius: 0 },
            line: { tension: 0.4 }
        }
    };

    const charts = [
        { key: 'gold', title: '🥇 Gold (USD)', color: '#bf8700', colorClass: 'text-warning' },
        { key: 'copper', title: '⛏️ Copper (USD)', color: '#da3633', colorClass: 'text-danger' },
        { key: 'btc', title: '🪙 Bitcoin (CLP)', color: '#f2a900', colorClass: 'text-warning' },
        { key: 'eth', title: '💠 Ethereum (CLP)', color: '#627eea', colorClass: 'text-primary' },
    ];

    // Initialize live data from macro prop
    useEffect(() => {
        if (macro) {
            const initialData = {};
            charts.forEach(chart => {
                const sourceData = macro[chart.key]?.slice(-30) || [];
                initialData[chart.key] = sourceData.map(d => ({
                    date: d.date,
                    value: d.value,
                    originalValue: d.value
                }));
            });
            setLiveData(initialData);
        }
    }, [macro]);

    // Continuous live simulation - update values every 1.5 seconds
    useEffect(() => {
        intervalRef.current = setInterval(() => {
            setLiveData(prev => {
                const updated = {};
                Object.keys(prev).forEach(key => {
                    const data = prev[key];
                    if (data && data.length > 0) {
                        updated[key] = data.map((point, i) => {
                            // Add small random fluctuation (±0.5% of original value)
                            const fluctuation = point.originalValue * (Math.random() - 0.5) * 0.01;
                            // More movement for recent points
                            const recentMultiplier = i > data.length - 5 ? 2 : 1;
                            return {
                                ...point,
                                value: point.originalValue + (fluctuation * recentMultiplier)
                            };
                        });

                        // Occasionally shift the data to simulate new data coming in
                        if (Math.random() > 0.7 && updated[key].length > 0) {
                            const lastVal = updated[key][updated[key].length - 1];
                            const newVal = {
                                date: new Date().toISOString(),
                                value: lastVal.originalValue * (1 + (Math.random() - 0.5) * 0.005),
                                originalValue: lastVal.originalValue
                            };
                            updated[key] = [...updated[key].slice(1), newVal];
                        }
                    } else {
                        updated[key] = data;
                    }
                });
                return updated;
            });
        }, 1500);

        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
        };
    }, []);

    const cardVariants = {
        hidden: { opacity: 0, y: 40, scale: 0.95 },
        visible: (i) => ({
            opacity: 1,
            y: 0,
            scale: 1,
            transition: {
                delay: i * 0.15,
                duration: 0.6,
                ease: [0.25, 0.46, 0.45, 0.94]
            }
        })
    };

    // Calculate trend indicator
    const getTrend = (data) => {
        if (!data || data.length < 2) return { symbol: '—', color: '#8b949e' };
        const last = data[data.length - 1]?.value || 0;
        const prev = data[data.length - 2]?.value || 0;
        if (last > prev) return { symbol: '▲', color: '#238636' };
        if (last < prev) return { symbol: '▼', color: '#da3633' };
        return { symbol: '—', color: '#8b949e' };
    };

    return (
        <div className="row g-4 mb-4">
            {charts.map((chart, i) => {
                const data = liveData[chart.key] || [];
                const trend = getTrend(data);
                const currentValue = data[data.length - 1]?.value;

                return (
                    <motion.div
                        key={chart.key}
                        className="col-md-6 col-lg-3"
                        custom={i}
                        initial="hidden"
                        animate="visible"
                        variants={cardVariants}
                    >
                        <div
                            className="card card-custom h-100 p-3"
                            style={{
                                background: 'rgba(22, 27, 34, 0.85)',
                                backdropFilter: 'blur(10px)',
                                border: `1px solid ${chart.color}33`,
                                boxShadow: `0 4px 20px ${chart.color}15`,
                            }}
                        >
                            <div className="d-flex justify-content-between align-items-center mb-2">
                                <h6 className={`${chart.colorClass} mb-0`} style={{ fontSize: '0.85rem' }}>
                                    {chart.title}
                                </h6>
                                <motion.span
                                    key={trend.symbol + currentValue}
                                    initial={{ scale: 1.3, opacity: 0 }}
                                    animate={{ scale: 1, opacity: 1 }}
                                    style={{
                                        color: trend.color,
                                        fontWeight: 'bold',
                                        fontSize: '0.9rem'
                                    }}
                                >
                                    {trend.symbol}
                                </motion.span>
                            </div>

                            {/* Live indicator */}
                            <div className="d-flex align-items-center mb-2">
                                <motion.div
                                    animate={{ opacity: [1, 0.3, 1] }}
                                    transition={{ duration: 1.5, repeat: Infinity }}
                                    style={{
                                        width: 8,
                                        height: 8,
                                        borderRadius: '50%',
                                        backgroundColor: '#238636',
                                        marginRight: 6
                                    }}
                                />
                                <span style={{ fontSize: '0.7rem', color: '#8b949e' }}>LIVE</span>
                                {currentValue && (
                                    <motion.span
                                        key={currentValue}
                                        initial={{ opacity: 0.5 }}
                                        animate={{ opacity: 1 }}
                                        style={{
                                            marginLeft: 'auto',
                                            fontSize: '0.75rem',
                                            color: '#c9d1d9',
                                            fontFamily: 'monospace'
                                        }}
                                    >
                                        {currentValue.toLocaleString('es-CL', {
                                            maximumFractionDigits: chart.key.includes('btc') || chart.key.includes('eth') ? 0 : 2
                                        })}
                                    </motion.span>
                                )}
                            </div>

                            <div style={{ height: '120px' }}>
                                <Line
                                    data={{
                                        labels: data.map((_, idx) => idx),
                                        datasets: [{
                                            data: data.map(d => d.value),
                                            borderColor: chart.color,
                                            backgroundColor: `${chart.color}20`,
                                            fill: true,
                                            borderWidth: 2
                                        }]
                                    }}
                                    options={chartOptions}
                                />
                            </div>
                        </div>
                    </motion.div>
                );
            })}
        </div>
    );
};

export default ChartGrid;
