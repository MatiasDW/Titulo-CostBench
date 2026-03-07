import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
    FaArrowLeft, FaExchangeAlt, FaCheck,
    FaExclamationTriangle, FaClock, FaBolt, FaQuestionCircle
} from 'react-icons/fa';
import axios from 'axios';
import AnimatedBackground from '../AnimatedBackground';
import useSounds from '../../hooks/useSounds';
import { createChart, ColorType } from 'lightweight-charts';
import SclodaChat from './SclodaChat';
import './Trading.css';

const tradingApi = axios.create({ baseURL: '/api/v1/trading', withCredentials: true });
const marketApi = axios.create({ baseURL: '/api/v1/market', withCredentials: true });

const ASSETS = [
    { key: 'gold', label: 'Gold (XAU)', unit: 'USD/oz', seriesId: 'GOLDAMGBD228NLBM' },
    { key: 'copper', label: 'Copper', unit: 'USD/lb', seriesId: 'PCOPPUSDM' },
    { key: 'oil', label: 'Crude Oil (WTI)', unit: 'USD/bbl', seriesId: 'DCOILWTICO' },
    { key: 'btc', label: 'Bitcoin (BTC)', unit: 'CLP', seriesId: 'BTC-CLP' },
    { key: 'eth', label: 'Ethereum (ETH)', unit: 'CLP', seriesId: 'ETH-CLP' },
    { key: 'usdclp', label: 'USD/CLP', unit: 'CLP/USD', seriesId: 'USDCLP' },
    { key: 'uf', label: 'UF', unit: 'CLP', seriesId: 'UF' },
];

const TIMEFRAMES = {
    '1W': 7,
    '1M': 30,
    '3M': 90,
    '6M': 180,
    '1Y': 365,
    '3Y': 1095,
};
const TIMEFRAME_ORDER = ['1W', '1M', '3M', '6M', '1Y', '3Y'];

const formatCLP = (v) => {
    if (v == null) return '$0';
    return '$' + Math.round(v).toLocaleString('es-CL');
};

const TradePage = () => {
    const navigate = useNavigate();

    const [asset, setAsset] = useState('gold');
    const [direction, setDirection] = useState('long');
    const [amount, setAmount] = useState('');
    const [livePrice, setLivePrice] = useState(null);
    const [walletBalance, setWalletBalance] = useState(null);
    const [orderType, setOrderType] = useState('market'); // market | conditional
    const [takeProfit, setTakeProfit] = useState('');
    const [stopLoss, setStopLoss] = useState('');
    const [timeframe, setTimeframe] = useState('3M');
    const [candles, setCandles] = useState([]);
    const [chartLoading, setChartLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [toast, setToast] = useState(null);
    const [showSclodaChat, setShowSclodaChat] = useState(false);
    const [showCoach, setShowCoach] = useState(false);
    const [coachType, setCoachType] = useState('chart');
    const [tipIndex, setTipIndex] = useState(0);

    const openCoach = (type) => {
        setCoachType(type);
        setTipIndex(0);
        setShowCoach(true);
    };

    const openFullChat = () => {
        setShowCoach(false);
        setShowSclodaChat(true);
    };

    const { playTrade, playError, playClick } = useSounds();
    const chartRef = useRef(null);
    const chartInstance = useRef(null);
    const resizeObserver = useRef(null);

    const showToast = (msg, type = 'success') => {
        setToast({ msg, type });
        setTimeout(() => setToast(null), 3000);
    };

    const selectedAsset = ASSETS.find(a => a.key === asset);

    // Fetch live price from latest macro snapshot
    const fetchPrice = useCallback(async () => {
        try {
            const res = await marketApi.get('/latest');
            const items = res.data.items || [];
            const map = {};
            items.forEach(it => { map[it.series_id] = it.value; });
            const seriesId = selectedAsset?.seriesId;
            setLivePrice(seriesId ? map[seriesId] || null : null);
        } catch (err) {
            console.error('Price fetch error:', err);
            setLivePrice(null);
        }
    }, [selectedAsset]);

    // Fetch wallet balance
    const fetchWallet = useCallback(async () => {
        try {
            const res = await tradingApi.get('/wallet');
            setWalletBalance(res.data.available_cash);
        } catch (err) {
            console.error('Wallet fetch error:', err);
        }
    }, []);

    // Fetch history for chart
    const fetchHistory = useCallback(async () => {
        const seriesId = selectedAsset?.seriesId;
        if (!seriesId) return;
        setChartLoading(true);
        try {
            const res = await marketApi.get('/history', { params: { series_id: seriesId } });
            const obs = res.data.observations || [];

            // To allow scrolling back in time, we load up to 10 years of data (approx 3650 days)
            // instead of just the selected timeframe.
            const sliced = obs.slice(-3650);

            const candlesData = [];
            let prevClose = null;
            sliced.forEach((d) => {
                const close = Number(d.value);
                const open = prevClose ?? close;
                const high = Math.max(open, close);
                const low = Math.min(open, close);
                const dt = new Date(d.date);
                const yr = dt.getUTCFullYear();
                const mo = String(dt.getUTCMonth() + 1).padStart(2, '0');
                const da = String(dt.getUTCDate()).padStart(2, '0');

                candlesData.push({
                    time: `${yr}-${mo}-${da}`,
                    open,
                    high,
                    low,
                    close,
                });
                prevClose = close;
            });
            setCandles(candlesData);
        } catch (err) {
            console.error('History fetch error:', err);
            setCandles([]);
        } finally {
            setChartLoading(false);
        }
    }, [selectedAsset]); // Removed 'timeframe' from deps so we don't refetch on tab change

    useEffect(() => { fetchPrice(); fetchWallet(); fetchHistory(); }, [fetchPrice, fetchWallet, fetchHistory]);

    // Build chart with Lightweight Charts
    useEffect(() => {
        if (!chartRef.current) return;
        if (!candles.length) return;

        // Create chart once
        if (!chartInstance.current) {
            if (typeof ResizeObserver === 'undefined') {
                console.warn('ResizeObserver not available; chart resize disabled');
            }
            chartInstance.current = createChart(chartRef.current, {
                width: chartRef.current.clientWidth,
                height: 320,
                layout: {
                    background: { type: ColorType.Solid, color: '#0f172a' },
                    textColor: '#cbd5e1',
                },
                grid: {
                    vertLines: { color: '#1e293b' },
                    horzLines: { color: '#1e293b' },
                },
                crosshair: { mode: 1 },
                timeScale: {
                    timeVisible: true,
                    secondsVisible: false,
                    rightOffset: 2,
                    borderColor: '#1e293b',
                },
                handleScroll: {
                    mouseWheel: true,
                    pressedMouseMove: true,
                    horzTouchDrag: true,
                    vertTouchDrag: true,
                },
                handleScale: {
                    mouseWheel: true,
                    pinch: true,
                    axisPressedMouseMove: {
                        time: true,
                        price: true,
                    },
                },
            });
            if (typeof ResizeObserver !== 'undefined') {
                resizeObserver.current = new ResizeObserver(entries => {
                    for (const entry of entries) {
                        const { width } = entry.contentRect;
                        chartInstance.current.applyOptions({ width });
                    }
                });
                resizeObserver.current.observe(chartRef.current);
            }
        }

        const series = chartInstance.current.addCandlestickSeries({
            upColor: '#16a34a',
            downColor: '#dc2626',
            borderVisible: false,
            wickUpColor: '#16a34a',
            wickDownColor: '#dc2626',
        });
        series.setData(candles);

        // Autoscale view to selected timeframe window (allowing user to pan back later)
        const lastCandle = candles[candles.length - 1];
        if (lastCandle) {
            const limitDays = TIMEFRAMES[timeframe] || 30; // Default to 1M if not found
            // Convert calendar days to approximate trading days (since weekends are now skipped)
            const tradeDays = Math.ceil(limitDays * (5 / 7));
            const firstCandle = candles[Math.max(0, candles.length - tradeDays)];

            chartInstance.current.timeScale().setVisibleRange({ from: firstCandle.time, to: lastCandle.time });
        } else {
            chartInstance.current.timeScale().fitContent();
        }
        series.priceScale().applyOptions({ autoScale: true });

        // Price line for live price
        if (livePrice) {
            series.createPriceLine({
                price: Number(livePrice),
                color: '#60a5fa',
                lineWidth: 2,
                lineStyle: 2,
                axisLabelVisible: true,
                title: 'Live',
            });
        }

        return () => {
            chartInstance.current?.removeSeries(series);
        };
    }, [candles, livePrice, timeframe]);

    useEffect(() => () => {
        resizeObserver.current?.disconnect();
        chartInstance.current?.remove();
        chartInstance.current = null;
    }, []);

    // localStorage safe helpers
    const safeLSGet = (k) => {
        try { return localStorage.getItem(k); } catch { return null; }
    };
    const safeLSSet = (k, v) => {
        try { localStorage.setItem(k, v); } catch { /* ignore */ }
    };

    const chartTips = useMemo(() => ([
        "Timeframes 1W/1M/3M/1Y auto-frame the chart. You can also use your mouse wheel or trackpad pinch to adjust it.",
        "The chart supports zooming with the wheel/trackpad and dragging to pan across the price series."
    ]), []);

    const tradeTips = useMemo(() => ([
        "Market vs Conditional: 'Market' executes immediately at the current price; 'Conditional' sets automatic Take Profit and Stop Loss levels.",
        "Risk Controls: Take Profit secures your gains; Stop Loss limits your losses. The risk bot checks prices every 5 minutes.",
        "Estimated Qty = CLP amount / live price. You can adjust the amount quickly using the pre-defined interval buttons below."
    ]), []);

    const currentTips = coachType === 'chart' ? chartTips : tradeTips;

    useEffect(() => {
        const seen = safeLSGet('scloda_trading_chat_seen');
        if (!seen) {
            setShowSclodaChat(true);
            safeLSSet('scloda_trading_chat_seen', '1');
        }
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!amount || !livePrice) return;

        setSubmitting(true);
        try {
            const endpoint = direction === 'long' ? '/buy' : '/sell';
            const payload = {
                asset,
                amount: parseFloat(amount),
                price: livePrice,
            };
            if (orderType === 'conditional') {
                payload.take_profit_price = takeProfit ? parseFloat(takeProfit) : null;
                payload.stop_loss_price = stopLoss ? parseFloat(stopLoss) : null;
            }
            const res = await tradingApi.post(endpoint, payload);
            showToast(`${direction === 'long' ? 'Bought' : 'Sold'} ${selectedAsset.label}!`);
            playTrade();
            setAmount('');
            setTakeProfit('');
            setStopLoss('');
            setWalletBalance(res.data.wallet_balance);
        } catch (err) {
            playError();
            showToast(err.response?.data?.error || 'Trade failed', 'error');
        } finally {
            setSubmitting(false);
        }
    };

    const amountNum = parseFloat(amount) || 0;
    const qty = livePrice && amountNum > 0 ? (amountNum / livePrice) : 0;

    const chartStats = useMemo(() => {
        if (!candles.length) return { last: null, changePct: 0 };
        const last = candles[candles.length - 1].close;
        const prev = candles.length > 1 ? candles[candles.length - 2].close : last;
        const changePct = prev ? ((last - prev) / prev) * 100 : 0;
        return { last, changePct };
    }, [candles]);

    return (
        <div className="trading-page">
            <AnimatedBackground />

            <div className="trade-top-bar">
                <button className="trading-back" onClick={() => navigate('/wallet')}>
                    <FaArrowLeft size={12} /> Back to Wallet
                </button>
                <div className="trading-header">
                    <h2><FaExchangeAlt /> New Trade</h2>
                    <p>Available: <strong className="text-success">
                        {walletBalance != null ? formatCLP(walletBalance) : '...'}
                    </strong> CLP</p>
                </div>
            </div>

            <div className="trade-grid wide">
                {/* Chart column */}
                <div className="trade-chart-card">
                    <div className="chart-head">
                        <div>
                            <div className="chart-asset">{selectedAsset?.label}</div>
                            <div className="chart-price">
                                {livePrice != null ? livePrice.toLocaleString('en-US', { maximumFractionDigits: 2 }) : '—'} <span className="unit">{selectedAsset?.unit}</span>
                            </div>
                            <div className={`chart-change ${chartStats.changePct >= 0 ? 'pos' : 'neg'}`}>
                                {chartStats.changePct >= 0 ? '▲' : '▼'} {Math.abs(chartStats.changePct).toFixed(2)}%
                            </div>
                        </div>
                        <div className="timeframe-tabs">
                            {TIMEFRAME_ORDER.map(tf => (
                                <button
                                    key={tf}
                                    className={`tf-btn ${timeframe === tf ? 'active' : ''}`}
                                    onClick={() => { playClick(); setTimeframe(tf); }}
                                >
                                    <FaClock size={12} /> {tf}
                                </button>
                            ))}
                        </div>
                    </div>
                    <div className="chart-container">
                        {chartLoading && <div className="chart-loading">Loading chart...</div>}
                        <div ref={chartRef} className="lw-chart" />
                    </div>
                    <div className="chart-hints">
                        <span>🖱️ / 🖐️  Zoom with wheel/trackpad pinch, drag to pan</span>
                        <span>MA7 overlay for trend</span>
                    </div>
                    <div className="chart-coach-toggle">
                        <button
                            type="button"
                            className="coach-inline-btn"
                            onClick={() => openCoach('chart')}
                        >
                            <FaQuestionCircle size={13} /> Ask Scloda
                        </button>
                    </div>
                </div>

                {/* Order ticket */}
                <motion.div
                    className="trading-container"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <motion.div className="trading-card" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                            <div className="trading-card-title" style={{ margin: 0 }}>
                                <FaExchangeAlt size={16} /> Order Ticket
                            </div>
                            <button
                                type="button"
                                className="coach-inline-btn"
                                style={{ margin: 0 }}
                                onClick={() => openCoach('trade')}
                            >
                                <FaQuestionCircle size={13} /> Ask Scloda
                            </button>
                        </div>
                        <form className="trade-form" onSubmit={handleSubmit}>

                            {/* Asset */}
                            <div className="trade-field">
                                <label>Asset</label>
                                <select value={asset} onChange={(e) => setAsset(e.target.value)}>
                                    {ASSETS.map(a => (
                                        <option key={a.key} value={a.key}>{a.label}</option>
                                    ))}
                                </select>
                            </div>

                            {/* Order type */}
                            <div className="trade-field">
                                <label>Order Type</label>
                                <div className="direction-btns">
                                    <button
                                        type="button"
                                        className={`direction-btn ${orderType === 'market' ? 'active-long' : ''}`}
                                        onClick={() => { playClick(); setOrderType('market'); }}
                                    >
                                        <FaBolt size={12} /> Market
                                    </button>
                                    <button
                                        type="button"
                                        className={`direction-btn ${orderType === 'conditional' ? 'active-short' : ''}`}
                                        onClick={() => { playClick(); setOrderType('conditional'); }}
                                    >
                                        🎯 Conditional (TP/SL)
                                    </button>
                                </div>
                            </div>

                            {/* Direction */}
                            <div className="trade-field">
                                <label>Direction</label>
                                <div className="direction-btns">
                                    <button
                                        type="button"
                                        className={`direction-btn ${direction === 'long' ? 'active-long' : ''}`}
                                        onClick={() => { playClick(); setDirection('long'); }}
                                    >
                                        📈 Buy Long
                                    </button>
                                    <button
                                        type="button"
                                        className={`direction-btn ${direction === 'short' ? 'active-short' : ''}`}
                                        onClick={() => { playClick(); setDirection('short'); }}
                                    >
                                        📉 Sell Short
                                    </button>
                                </div>
                            </div>

                            {/* Live Price */}
                            <div className="trade-field full-width">
                                <div className="trade-live-price">
                                    <div className="label">Live Price — {selectedAsset?.label}</div>
                                    <div className="price">
                                        {livePrice != null
                                            ? livePrice.toLocaleString('en-US', { maximumFractionDigits: 2 })
                                            : '—'}
                                    </div>
                                    <div className="unit">{selectedAsset?.unit}</div>
                                </div>
                            </div>

                            {/* Amount CLP */}
                            <div className="trade-field">
                                <label>Amount (CLP)</label>
                                <input
                                    type="number"
                                    placeholder="e.g. 500000"
                                    value={amount}
                                    onChange={(e) => setAmount(e.target.value)}
                                    min="1"
                                    max={walletBalance || 10000000}
                                />
                            </div>

                            {/* Estimated quantity */}
                            <div className="trade-field">
                                <label>Estimated Qty</label>
                                <input
                                    type="text"
                                    value={qty > 0 ? qty.toFixed(6) : '—'}
                                    disabled
                                    style={{ textAlign: 'center' }}
                                />
                            </div>

                            {/* Conditional TP/SL */}
                            {orderType === 'conditional' && (
                                <div className="trade-field full-width">
                                    <label>Risk Controls (optional)</label>
                                    <div className="risk-grid">
                                        <div>
                                            <small>Take Profit</small>
                                            <input
                                                type="number"
                                                placeholder="e.g. 4.60"
                                                value={takeProfit}
                                                onChange={(e) => setTakeProfit(e.target.value)}
                                                step="0.0001"
                                            />
                                        </div>
                                        <div>
                                            <small>Stop Loss</small>
                                            <input
                                                type="number"
                                                placeholder="e.g. 4.20"
                                                value={stopLoss}
                                                onChange={(e) => setStopLoss(e.target.value)}
                                                step="0.0001"
                                            />
                                        </div>
                                    </div>
                                    <small className="hint">
                                        The risk worker checks every 5 minutes and will close the position if these levels are crossed.
                                    </small>
                                </div>
                            )}

                            {/* Quick amounts */}
                            <div className="trade-field full-width">
                                <label>Quick Amount</label>
                                <div style={{ display: 'flex', gap: '0.5rem' }}>
                                    {[100000, 500000, 1000000, 2000000].map(v => (
                                        <button
                                            key={v}
                                            type="button"
                                            className="direction-btn"
                                            style={{ flex: 1, fontSize: '0.75rem', padding: '0.45rem' }}
                                            onClick={() => setAmount(String(v))}
                                        >
                                            {formatCLP(v)}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Submit */}
                            <motion.button
                                type="submit"
                                className={`trade-submit ${direction === 'long' ? 'buy-btn' : 'sell-btn'}`}
                                disabled={submitting || !amount || !livePrice || amountNum <= 0}
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                            >
                                {submitting ? 'Executing...' : direction === 'long'
                                    ? `📈 Buy ${selectedAsset?.label}`
                                    : `📉 Short ${selectedAsset?.label}`}
                            </motion.button>
                        </form>
                    </motion.div>
                </motion.div>
            </div>

            {/* Toast */}
            <AnimatePresence>
                {toast && (
                    <motion.div
                        className={`trading-toast ${toast.type}`}
                        initial={{ opacity: 0, y: 30 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 30 }}
                    >
                        {toast.type === 'success' ? <FaCheck size={14} /> : <FaExclamationTriangle size={14} />}
                        {toast.msg}
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Scloda Interactive Chat */}
            <SclodaChat
                isOpen={showSclodaChat}
                onClose={() => setShowSclodaChat(false)}
                onOpen={() => setShowSclodaChat(true)}
                contextAsset={selectedAsset}
            />

            {/* Scloda coach modal/popup overlay */}
            <AnimatePresence>
                {showCoach && (
                    <motion.div
                        className="coach-card"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 10 }}
                    >
                        <div className="coach-header">
                            <span>Scloda explains:</span>
                            <button onClick={() => { setShowCoach(false); }}>✕</button>
                        </div>
                        <div className="coach-body">
                            {currentTips[tipIndex]}
                        </div>
                        <div className="coach-actions" style={{ justifyContent: 'space-between' }}>
                            <div style={{ display: 'flex', gap: '8px' }}>
                                <button
                                    onClick={() => setTipIndex((tipIndex - 1 + currentTips.length) % currentTips.length)}
                                    className="direction-btn"
                                >
                                    ←
                                </button>
                                <button
                                    onClick={() => setTipIndex((tipIndex + 1) % currentTips.length)}
                                    className="direction-btn active-long"
                                >
                                    →
                                </button>
                            </div>
                            <button
                                onClick={openFullChat}
                                className="action-btn text-primary"
                                style={{ border: 'none', background: 'none', fontSize: '0.85rem', fontWeight: 600, padding: 0 }}
                            >
                                Chat with Scloda ✨
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default TradePage;
