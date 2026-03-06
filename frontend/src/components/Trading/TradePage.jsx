import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
    FaArrowLeft, FaExchangeAlt, FaCheck,
    FaExclamationTriangle
} from 'react-icons/fa';
import axios from 'axios';
import AnimatedBackground from '../AnimatedBackground';
import useSounds from '../../hooks/useSounds';
import './Trading.css';

const tradingApi = axios.create({ baseURL: '/api/v1/trading', withCredentials: true });
const marketApi = axios.create({ baseURL: '/api/v1/market', withCredentials: true });

const ASSETS = [
    { key: 'gold', label: 'Gold (XAU)', unit: 'USD/oz' },
    { key: 'copper', label: 'Copper', unit: 'USD/lb' },
    { key: 'oil', label: 'Crude Oil (WTI)', unit: 'USD/bbl' },
    { key: 'btc', label: 'Bitcoin (BTC)', unit: 'USD' },
    { key: 'eth', label: 'Ethereum (ETH)', unit: 'USD' },
    { key: 'usdclp', label: 'USD/CLP', unit: 'CLP' },
    { key: 'uf', label: 'UF', unit: 'CLP' },
];

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
    const [submitting, setSubmitting] = useState(false);
    const [toast, setToast] = useState(null);
    const { playTrade, playError, playClick } = useSounds();

    const showToast = (msg, type = 'success') => {
        setToast({ msg, type });
        setTimeout(() => setToast(null), 3000);
    };

    const selectedAsset = ASSETS.find(a => a.key === asset);

    // Fetch live price
    const fetchPrice = useCallback(async () => {
        try {
            const res = await marketApi.get('/macro');
            const data = res.data;
            const priceMap = {
                gold: data.gold?.price,
                copper: data.copper?.price,
                oil: data.oil?.price,
                btc: data.btc?.price,
                eth: data.eth?.price,
                usdclp: data.usdclp?.price,
                uf: data.uf?.price,
            };
            setLivePrice(priceMap[asset] || null);
        } catch (err) {
            console.error('Price fetch error:', err);
            setLivePrice(null);
        }
    }, [asset]);

    // Fetch wallet balance
    const fetchWallet = useCallback(async () => {
        try {
            const res = await tradingApi.get('/wallet');
            setWalletBalance(res.data.available_cash);
        } catch (err) {
            console.error('Wallet fetch error:', err);
        }
    }, []);

    useEffect(() => { fetchPrice(); fetchWallet(); }, [fetchPrice, fetchWallet]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!amount || !livePrice) return;

        setSubmitting(true);
        try {
            const endpoint = direction === 'long' ? '/buy' : '/sell';
            const res = await tradingApi.post(endpoint, {
                asset,
                amount: parseFloat(amount),
                price: livePrice,
            });
            showToast(`${direction === 'long' ? 'Bought' : 'Sold'} ${selectedAsset.label}!`);
            playTrade();
            setAmount('');
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

    return (
        <div className="trading-page">
            <AnimatedBackground />

            <motion.div
                className="trading-container"
                style={{ maxWidth: '540px' }}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <button className="trading-back" onClick={() => navigate('/wallet')}>
                    <FaArrowLeft size={12} /> Back to Wallet
                </button>

                <div className="trading-header">
                    <h2><FaExchangeAlt /> New Trade</h2>
                    <p>
                        Available: <strong style={{ color: '#3fb950' }}>
                            {walletBalance != null ? formatCLP(walletBalance) : '...'}
                        </strong> CLP
                    </p>
                </div>

                <motion.div className="trading-card" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
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
        </div>
    );
};

export default TradePage;
