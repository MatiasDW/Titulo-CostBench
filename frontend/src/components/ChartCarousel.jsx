import React, { memo } from 'react';
import { motion } from 'framer-motion';
import ChartCard from './ChartCard';
import useSclodaInsights, { ASSET_CHARTS } from '../hooks/useSclodaInsights';

/**
 * ChartCarousel – Continuous smooth scrolling carousel with REAL data.
 *
 * Optimisations (v2):
 *   • Insight fetching moved to shared `useSclodaInsights` hook (deduped).
 *   • `ChartCard` is a standalone `React.memo()` component.
 *   • Chart configs live in `ASSET_CHARTS` (single source of truth).
 */
const ChartCarousel = ({ macro }) => {
    const { insights, loading: insightsLoading } = useSclodaInsights(macro);

    // Duplicate chart list for seamless infinite scroll
    const duplicated = [...ASSET_CHARTS, ...ASSET_CHARTS];

    return (
        <div className="chart-carousel-wrapper" style={{ overflow: 'hidden', position: 'relative' }}>
            {/* Gradient fade edges */}
            <div
                style={{
                    position: 'absolute', left: 0, top: 0, bottom: 0, width: '60px',
                    background: 'linear-gradient(to right, #0d1117, transparent)',
                    zIndex: 10, pointerEvents: 'none',
                }}
            />
            <div
                style={{
                    position: 'absolute', right: 0, top: 0, bottom: 0, width: '60px',
                    background: 'linear-gradient(to left, #0d1117, transparent)',
                    zIndex: 10, pointerEvents: 'none',
                }}
            />

            {/* Scrolling container */}
            <motion.div
                className="chart-scroll-track"
                animate={{ x: [0, -(ASSET_CHARTS.length * 336)] }}
                transition={{
                    x: { duration: 50, repeat: Infinity, ease: 'linear' },
                }}
                style={{ display: 'flex', width: 'fit-content' }}
            >
                {duplicated.map((chart, i) => (
                    <ChartCard
                        key={`${chart.key}-${i}`}
                        chart={chart}
                        data={macro?.[chart.key]?.slice(-25) || []}
                        insightText={insights[chart.key] || null}
                        isLoading={insightsLoading}
                    />
                ))}
            </motion.div>

            <style>{`
                .chart-carousel-wrapper { padding: 10px 0; }
                .chart-scroll-track:hover { animation-play-state: paused; }
            `}</style>
        </div>
    );
};

export default memo(ChartCarousel);
