import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

/**
 * AnimatedBackground - Enhanced Finance-themed continuous animation
 * Features: Candlesticks, flowing chart lines, ticker tape, particles
 */
const AnimatedBackground = () => {
    const [lines, setLines] = useState([]);
    const [candlesticks, setCandlesticks] = useState([]);

    useEffect(() => {
        // Generate chart lines
        const generateLines = () => {
            return Array.from({ length: 6 }, (_, i) => ({
                id: i,
                points: generateChartPoints(),
                color: ['#238636', '#58a6ff', '#f78166', '#bf8700', '#627eea', '#da3633'][i],
                delay: i * 0.5,
            }));
        };

        // Generate candlesticks
        const generateCandlesticks = () => {
            return Array.from({ length: 30 }, (_, i) => ({
                id: i,
                x: (i / 30) * 100,
                open: 40 + Math.random() * 60,
                close: 40 + Math.random() * 60,
                high: 20 + Math.random() * 30,
                low: 10 + Math.random() * 20,
            }));
        };

        setLines(generateLines());
        setCandlesticks(generateCandlesticks());
    }, []);

    // Generate random "chart-like" path points
    const generateChartPoints = () => {
        const points = [];
        const segments = 20;
        const height = 200;
        let y = height / 2;

        for (let i = 0; i <= segments; i++) {
            const x = (i / segments) * 100;
            y = Math.max(20, Math.min(height - 20, y + (Math.random() - 0.48) * 35));
            points.push(`${x},${y}`);
        }
        return `M ${points.join(' L ')}`;
    };

    return (
        <div className="animated-background">
            {/* Floating Particles - More visible */}
            <div className="particles">
                {Array.from({ length: 40 }, (_, i) => (
                    <motion.div
                        key={i}
                        className="particle"
                        initial={{
                            x: Math.random() * (typeof window !== 'undefined' ? window.innerWidth : 1920),
                            y: Math.random() * (typeof window !== 'undefined' ? window.innerHeight : 1080),
                            opacity: 0,
                        }}
                        animate={{
                            y: [null, -1200],
                            opacity: [0, 0.8, 0],
                        }}
                        transition={{
                            duration: 6 + Math.random() * 6,
                            repeat: Infinity,
                            delay: Math.random() * 4,
                            ease: 'linear',
                        }}
                        style={{
                            position: 'absolute',
                            width: 3 + Math.random() * 8,
                            height: 3 + Math.random() * 8,
                            borderRadius: '50%',
                            background: ['#238636', '#58a6ff', '#f78166', '#bf8700', '#627eea', '#da3633'][
                                Math.floor(Math.random() * 6)
                            ],
                            boxShadow: '0 0 10px currentColor',
                        }}
                    />
                ))}
            </div>

            {/* Candlestick Pattern - Background */}
            <svg
                className="candlestick-bg"
                viewBox="0 0 100 150"
                preserveAspectRatio="none"
                style={{
                    position: 'absolute',
                    top: '10%',
                    left: 0,
                    width: '100%',
                    height: '60%',
                    opacity: 0.08,
                }}
            >
                {candlesticks.map((candle, i) => {
                    const isGreen = candle.close > candle.open;
                    const color = isGreen ? '#238636' : '#da3633';
                    const top = Math.min(candle.open, candle.close);
                    const bodyHeight = Math.abs(candle.close - candle.open);

                    return (
                        <motion.g
                            key={candle.id}
                            initial={{ opacity: 0, scaleY: 0 }}
                            animate={{ opacity: 1, scaleY: 1 }}
                            transition={{ delay: i * 0.05, duration: 0.5 }}
                        >
                            {/* Wick */}
                            <line
                                x1={candle.x + 1}
                                y1={top - candle.high}
                                x2={candle.x + 1}
                                y2={top + bodyHeight + candle.low}
                                stroke={color}
                                strokeWidth="0.15"
                            />
                            {/* Body */}
                            <rect
                                x={candle.x}
                                y={top}
                                width="2"
                                height={Math.max(bodyHeight, 2)}
                                fill={color}
                            />
                        </motion.g>
                    );
                })}
            </svg>

            {/* Flowing Chart Lines - More visible */}
            <svg
                className="chart-lines"
                viewBox="0 0 100 200"
                preserveAspectRatio="none"
                style={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    width: '100%',
                    height: '50%',
                    opacity: 0.25,
                }}
            >
                {lines.map((line) => (
                    <motion.path
                        key={line.id}
                        d={line.points}
                        fill="none"
                        stroke={line.color}
                        strokeWidth="0.4"
                        initial={{ pathLength: 0, opacity: 0 }}
                        animate={{ pathLength: 1, opacity: 1 }}
                        transition={{
                            duration: 2.5,
                            delay: line.delay,
                            ease: 'easeOut',
                        }}
                        style={{
                            filter: 'drop-shadow(0 0 3px ' + line.color + ')',
                        }}
                    />
                ))}
            </svg>

            {/* Ticker Tape Animation */}
            <div className="ticker-tape">
                <motion.div
                    className="ticker-content"
                    animate={{ x: [0, -2000] }}
                    transition={{
                        duration: 30,
                        repeat: Infinity,
                        ease: 'linear',
                    }}
                >
                    {['BTC ▲ +2.4%', 'ETH ▼ -0.8%', 'GOLD ▲ +0.3%', 'COPPER ▲ +1.2%', 'USD/CLP ▼ -0.5%', 'UF ▲ +0.1%', 'OIL ▼ -1.8%', 'S&P500 ▲ +0.6%'].map((item, i) => (
                        <span key={i} style={{ marginRight: '80px', opacity: 0.4, fontSize: '0.85rem', fontFamily: 'monospace' }}>
                            {item}
                        </span>
                    ))}
                    {['BTC ▲ +2.4%', 'ETH ▼ -0.8%', 'GOLD ▲ +0.3%', 'COPPER ▲ +1.2%', 'USD/CLP ▼ -0.5%', 'UF ▲ +0.1%', 'OIL ▼ -1.8%', 'S&P500 ▲ +0.6%'].map((item, i) => (
                        <span key={`dup-${i}`} style={{ marginRight: '80px', opacity: 0.4, fontSize: '0.85rem', fontFamily: 'monospace' }}>
                            {item}
                        </span>
                    ))}
                </motion.div>
            </div>

            {/* Dollar Signs Floating */}
            {Array.from({ length: 8 }, (_, i) => (
                <motion.div
                    key={`dollar-${i}`}
                    initial={{
                        x: Math.random() * (typeof window !== 'undefined' ? window.innerWidth : 1920),
                        y: (typeof window !== 'undefined' ? window.innerHeight : 1080) + 50,
                        opacity: 0,
                        rotate: Math.random() * 360
                    }}
                    animate={{
                        y: -100,
                        opacity: [0, 0.15, 0],
                        rotate: 360 + Math.random() * 180
                    }}
                    transition={{
                        duration: 15 + Math.random() * 10,
                        repeat: Infinity,
                        delay: Math.random() * 10,
                        ease: 'linear'
                    }}
                    style={{
                        position: 'absolute',
                        fontSize: '2rem',
                        color: '#58a6ff',
                        fontWeight: 'bold',
                        pointerEvents: 'none',
                    }}
                >
                    $
                </motion.div>
            ))}

            {/* Gradient Overlay - Enhanced */}
            <div
                className="gradient-overlay"
                style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: `
                        radial-gradient(ellipse at 20% 20%, rgba(88, 166, 255, 0.1) 0%, transparent 50%),
                        radial-gradient(ellipse at 80% 80%, rgba(35, 134, 54, 0.08) 0%, transparent 50%),
                        radial-gradient(ellipse at 50% 50%, rgba(191, 135, 0, 0.05) 0%, transparent 60%)
                    `,
                    pointerEvents: 'none',
                }}
            />

            {/* Grid Pattern - Slightly more visible */}
            <motion.div
                className="grid-pattern"
                initial={{ opacity: 0 }}
                animate={{ opacity: 0.05 }}
                transition={{ duration: 2 }}
                style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    backgroundImage: `
                        linear-gradient(rgba(88, 166, 255, 0.08) 1px, transparent 1px),
                        linear-gradient(90deg, rgba(88, 166, 255, 0.08) 1px, transparent 1px)
                    `,
                    backgroundSize: '60px 60px',
                    pointerEvents: 'none',
                }}
            />

            <style>{`
                .animated-background {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100vw;
                    height: 100vh;
                    overflow: hidden;
                    z-index: -1;
                    background: linear-gradient(145deg, #0a0e14 0%, #0d1117 40%, #161b22 70%, #0d1117 100%);
                }

                .particles {
                    position: absolute;
                    width: 100%;
                    height: 100%;
                }

                .ticker-tape {
                    position: absolute;
                    bottom: 15%;
                    left: 0;
                    width: 100%;
                    overflow: hidden;
                    white-space: nowrap;
                }

                .ticker-content {
                    display: inline-flex;
                    color: #8b949e;
                }
            `}</style>
        </div>
    );
};

export default AnimatedBackground;
