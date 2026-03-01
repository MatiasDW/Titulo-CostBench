import React, { useEffect, useState, memo } from 'react';
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
                    animate={{ x: [0, -3000] }}
                    transition={{
                        duration: 40,
                        repeat: Infinity,
                        ease: 'linear',
                    }}
                >
                    {['BTC ▲ +2.4%', 'ETH ▼ -0.8%', 'GOLD ▲ +0.3%', 'COPPER ▲ +1.2%', 'USD/CLP ▼ -0.5%', 'UF ▲ +0.1%', 'OIL ▼ -1.8%', 'S&P500 ▲ +0.6%', '🏠 Hipotecario ▼ -0.2%', '🏢 M² Santiago ▲ +1.1%', '📊 CAE ▼ -0.3%', '🏗️ PIB Construcción ▲ +0.8%'].map((item, i) => (
                        <span key={i} style={{ marginRight: '80px', opacity: 0.4, fontSize: '0.85rem', fontFamily: 'monospace' }}>
                            {item}
                        </span>
                    ))}
                    {['BTC ▲ +2.4%', 'ETH ▼ -0.8%', 'GOLD ▲ +0.3%', 'COPPER ▲ +1.2%', 'USD/CLP ▼ -0.5%', 'UF ▲ +0.1%', 'OIL ▼ -1.8%', 'S&P500 ▲ +0.6%', '🏠 Hipotecario ▼ -0.2%', '🏢 M² Santiago ▲ +1.1%', '📊 CAE ▼ -0.3%', '🏗️ PIB Construcción ▲ +0.8%'].map((item, i) => (
                        <span key={`dup-${i}`} style={{ marginRight: '80px', opacity: 0.4, fontSize: '0.85rem', fontFamily: 'monospace' }}>
                            {item}
                        </span>
                    ))}
                </motion.div>
            </div>

            {/* Dollar Signs + Real Estate Icons Floating */}
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

            {/* Floating Real Estate Icons */}
            {['🏠', '🏢', '🏗️', '🔑', '📐', '🏘️'].map((icon, i) => (
                <motion.div
                    key={`realty-${i}`}
                    initial={{
                        x: (i * 280) + Math.random() * 150,
                        y: (typeof window !== 'undefined' ? window.innerHeight : 1080) + 80,
                        opacity: 0,
                    }}
                    animate={{
                        y: -120,
                        opacity: [0, 0.12, 0.12, 0],
                    }}
                    transition={{
                        duration: 18 + Math.random() * 12,
                        repeat: Infinity,
                        delay: 2 + Math.random() * 8,
                        ease: 'linear'
                    }}
                    style={{
                        position: 'absolute',
                        fontSize: '1.6rem',
                        pointerEvents: 'none',
                        filter: 'grayscale(0.3)',
                    }}
                >
                    {icon}
                </motion.div>
            ))}

            {/* City Skyline Silhouette */}
            <svg
                className="skyline-bg"
                viewBox="0 0 1200 200"
                preserveAspectRatio="none"
                style={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    width: '100%',
                    height: '18%',
                    opacity: 0.06,
                    pointerEvents: 'none',
                }}
            >
                <motion.path
                    d="M0,200 L0,160 L40,160 L40,120 L55,120 L55,100 L70,100 L70,120 L90,120 L90,140 L120,140 L120,90 L135,90 L135,70 L145,70 L145,50 L155,50 L155,70 L165,70 L165,90 L180,90 L180,130 L210,130 L210,110 L225,110 L225,80 L235,80 L235,60 L245,60 L245,80 L260,80 L260,110 L290,110 L290,150 L320,150 L320,100 L335,100 L335,65 L345,65 L345,45 L360,35 L375,45 L375,65 L385,65 L385,100 L420,100 L420,130 L460,130 L460,85 L475,85 L475,55 L490,55 L490,40 L510,40 L510,55 L525,55 L525,85 L560,85 L560,120 L590,120 L590,95 L610,95 L610,70 L625,70 L625,50 L640,45 L655,50 L655,70 L670,70 L670,95 L700,95 L700,140 L740,140 L740,110 L755,110 L755,75 L770,75 L770,55 L785,55 L785,35 L800,30 L815,35 L815,55 L830,55 L830,75 L845,75 L845,110 L880,110 L880,130 L920,130 L920,100 L940,100 L940,70 L955,70 L955,90 L975,90 L975,120 L1010,120 L1010,145 L1050,145 L1050,110 L1070,110 L1070,80 L1085,80 L1085,60 L1100,55 L1115,60 L1115,80 L1130,80 L1130,110 L1160,110 L1160,140 L1200,140 L1200,200 Z"
                    fill="#58a6ff"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 2, delay: 1 }}
                />
                {/* Window lights */}
                {Array.from({ length: 25 }, (_, i) => (
                    <motion.rect
                        key={`win-${i}`}
                        x={50 + (i * 46) % 1100}
                        y={80 + (i * 17) % 90}
                        width="4"
                        height="5"
                        fill="#ffc107"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: [0.3, 0.8, 0.3] }}
                        transition={{
                            duration: 2 + Math.random() * 3,
                            repeat: Infinity,
                            delay: Math.random() * 4,
                        }}
                    />
                ))}
            </svg>

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

export default memo(AnimatedBackground);
