import React, { memo } from 'react';
import { Line } from 'react-chartjs-2';
import { FaUserTie } from 'react-icons/fa';

// ── Shared chart.js options ──
const CHART_OPTIONS = {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: { legend: { display: false } },
    scales: {
        x: {
            display: false,
        },
        y: {
            grid: { color: '#30363d' },
            ticks: { color: '#8b949e', maxTicksLimit: 3, font: { size: 9 } },
        },
    },
    elements: {
        point: { radius: 0 },
        line: { tension: 0.4 },
    },
};

// Short month names
const MONTH_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/** Max recent observations to display */
const MAX_POINTS = 30;

/** Format "2026-02-15" → "15 Feb" (day-based, avoids duplicate month labels) */
function formatDateLabel(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    if (isNaN(d)) return dateStr;
    const day = String(d.getDate()).padStart(2, '0');
    const month = MONTH_SHORT[d.getMonth()];
    return `${day} ${month}`;
}

// ── Helpers ──

function getTrend(data) {
    if (!data || data.length < 2)
        return { symbol: '—', color: '#8b949e', percent: '0.00' };
    const last = data[data.length - 1]?.value || 0;
    const first = data[0]?.value || last;
    const pct = ((last - first) / first) * 100;
    if (last > first)
        return { symbol: '▲', color: '#238636', percent: pct.toFixed(2) };
    if (last < first)
        return { symbol: '▼', color: '#da3633', percent: pct.toFixed(2) };
    return { symbol: '—', color: '#8b949e', percent: '0.00' };
}

function formatValue(value, key) {
    if (!value) return '—';
    const decimals = key === 'yields' || key === 'cpi' ? 2 : 0;
    return value.toLocaleString('es-CL', { maximumFractionDigits: decimals });
}

// ── Component ──

/**
 * ChartCard – single asset card for the carousel.
 *
 * Props (all primitives / shallow-stable objects → memo works):
 *   chart       { key, title, subtitle, color, colorClass, fallback }
 *   data        observation[] from macro (already sliced to last 25)
 *   insightText string | null  (resolved by useSclodaInsights)
 *   isLoading   boolean        (insight still fetching)
 */
const ChartCard = ({ chart, data: rawData, insightText, isLoading }) => {
    // Safety net: only show recent data (fixes ancient Copper observations, etc.)
    const data = rawData.length > MAX_POINTS ? rawData.slice(-MAX_POINTS) : rawData;
    const trend = getTrend(data);
    const currentValue = data[data.length - 1]?.value;
    const displayInsight = insightText || chart.fallback;

    // Date range for subtitle badge
    const firstDate = data[0]?.date || data[0]?.observation_date;
    const lastDate = data[data.length - 1]?.date || data[data.length - 1]?.observation_date;
    const rangeLabel = firstDate && lastDate
        ? `${formatDateLabel(firstDate)} → ${formatDateLabel(lastDate)}`
        : null;

    return (
        <div
            className="chart-card"
            style={{ flex: '0 0 320px', minWidth: '320px', marginRight: '16px' }}
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
                        <small style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.6)' }}>
                            {chart.subtitle}
                        </small>
                    </div>
                    <div className="text-end">
                        <div
                            style={{
                                color: trend.color,
                                fontWeight: 'bold',
                                fontSize: '0.8rem',
                                fontFamily: 'monospace',
                            }}
                        >
                            {trend.symbol} {trend.percent}%
                        </div>
                        <span
                            style={{
                                fontSize: '1rem',
                                color: '#e6edf3',
                                fontFamily: 'monospace',
                                fontWeight: '700',
                            }}
                        >
                            {formatValue(currentValue, chart.key)}
                        </span>
                    </div>
                </div>

                {/* Date range badge */}
                {rangeLabel && (
                    <div style={{
                        textAlign: 'center',
                        marginBottom: '2px',
                    }}>
                        <span style={{
                            fontSize: '0.6rem',
                            fontFamily: 'monospace',
                            color: `${chart.color}99`,
                            background: `${chart.color}10`,
                            border: `1px solid ${chart.color}20`,
                            borderRadius: '10px',
                            padding: '1px 8px',
                            letterSpacing: '0.3px',
                        }}>
                            {rangeLabel}
                        </span>
                    </div>
                )}

                {/* Chart (REAL DATA) */}
                <div style={{ height: '80px', marginBottom: '6px' }}>
                    {data.length > 0 ? (
                        <Line
                            data={{
                                labels: data.map((d) => formatDateLabel(d.date || d.observation_date)),
                                datasets: [
                                    {
                                        data: data.map((d) => d.value),
                                        borderColor: chart.color,
                                        backgroundColor: `${chart.color}15`,
                                        fill: true,
                                        borderWidth: 2,
                                    },
                                ],
                            }}
                            options={CHART_OPTIONS}
                        />
                    ) : (
                        <div
                            className="text-center text-muted"
                            style={{ paddingTop: '25px', fontSize: '0.75rem' }}
                        >
                            Loading...
                        </div>
                    )}
                </div>

                {/* Scloda Insight – skeleton → fade-in */}
                <div style={{ borderTop: '1px solid #30363d', paddingTop: '8px' }}>
                    <div className="d-flex align-items-start">
                        <FaUserTie
                            size={14}
                            style={{ marginRight: '6px', color: '#8b949e', marginTop: '2px', flexShrink: 0 }}
                        />

                        {isLoading && !insightText ? (
                            /* Skeleton pulse */
                            <div className="insight-skeleton">
                                <div className="skeleton-line" style={{ width: '90%' }} />
                                <div className="skeleton-line" style={{ width: '60%' }} />
                            </div>
                        ) : (
                            /* Actual insight with fade-in */
                            <p
                                className="mb-0 text-secondary insight-fade-in"
                                style={{
                                    fontSize: '0.7rem',
                                    lineHeight: '1.4',
                                    fontStyle: 'italic',
                                }}
                            >
                                {displayInsight}
                            </p>
                        )}
                    </div>
                </div>
            </div>

            {/* Skeleton + fade-in CSS (scoped) */}
            <style>{`
                .insight-skeleton {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    gap: 4px;
                }
                .skeleton-line {
                    height: 8px;
                    border-radius: 4px;
                    background: linear-gradient(
                        90deg,
                        rgba(48,54,61,0.6) 25%,
                        rgba(88,166,255,0.08) 50%,
                        rgba(48,54,61,0.6) 75%
                    );
                    background-size: 200% 100%;
                    animation: shimmer 1.5s ease-in-out infinite;
                }
                @keyframes shimmer {
                    0%   { background-position: 200% 0; }
                    100% { background-position: -200% 0; }
                }
                .insight-fade-in {
                    animation: fadeInInsight 0.4s ease-out;
                }
                @keyframes fadeInInsight {
                    from { opacity: 0; transform: translateY(4px); }
                    to   { opacity: 1; transform: translateY(0); }
                }
            `}</style>
        </div>
    );
};

export default memo(ChartCard);
