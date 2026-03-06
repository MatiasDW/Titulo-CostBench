import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
    FaWallet, FaArrowLeft, FaChartLine, FaSync,
    FaCheck, FaExclamationTriangle
} from 'react-icons/fa';
import axios from 'axios';
import AnimatedBackground from '../AnimatedBackground';
import useSounds from '../../hooks/useSounds';
import './Trading.css';

const api = axios.create({ baseURL: '/api/v1/trading', withCredentials: true });

const formatCLP = (v) => {
    if (v == null) return '$0';
    return '$' + Math.round(v).toLocaleString('es-CL');
};

const WalletPage = () => {
    const navigate = useNavigate();
    const [wallet, setWallet] = useState(null);
    const [positions, setPositions] = useState([]);
    const [trades, setTrades] = useState([]);
    const [loading, setLoading] = useState(true);
    const [toast, setToast] = useState(null);
    const { playSuccess, playError, playClick, playTrade } = useSounds();

    const showToast = (msg, type = 'success') => {
        setToast({ msg, type });
        setTimeout(() => setToast(null), 3000);
    };

    const fetchData = useCallback(async () => {
        try {
            const [wRes, pRes] = await Promise.all([
                api.get('/wallet'),
                api.get('/positions'),
            ]);
            setWallet(wRes.data);
            setPositions(pRes.data.positions || []);
            setTrades(wRes.data.recent_trades || []);
        } catch (err) {
            console.error('Fetch error:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { fetchData(); }, [fetchData]);

    const handleClose = async (posId) => {
        // For now, use the entry price as exit price (demo)
        // In production, fetch live price
        const pos = positions.find(p => p.id === posId);
        if (!pos) return;

        try {
            const res = await api.post('/close', {
                position_id: posId,
                price: pos.entry_price, // TODO: live price
            });
            showToast(`Position closed. P&L: ${formatCLP(res.data.trade.pnl)}`);
            playSuccess();
            fetchData();
        } catch (err) {
            playError();
            showToast(err.response?.data?.error || 'Error closing position', 'error');
        }
    };

    const handleReset = async () => {
        if (!window.confirm('Reset wallet to $10,000,000 CLP? All open positions will be deleted.')) return;
        try {
            await api.post('/reset');
            playTrade();
            showToast('Wallet reset to $10,000,000 CLP');
            fetchData();
        } catch (err) {
            showToast('Error resetting wallet', 'error');
        }
    };

    if (loading) {
        return (
            <div className="trading-page">
                <AnimatedBackground />
                <div className="d-flex justify-content-center align-items-center" style={{ height: '60vh', position: 'relative', zIndex: 1 }}>
                    <div className="spinner-border text-success" />
                </div>
            </div>
        );
    }

    const totalPnL = wallet ? (wallet.total_equity - wallet.wallet.initial_balance) : 0;
    const pnlPercent = wallet?.wallet?.initial_balance ? ((totalPnL / wallet.wallet.initial_balance) * 100).toFixed(2) : '0';

    return (
        <div className="trading-page">
            <AnimatedBackground />

            <motion.div
                className="trading-container"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <button className="trading-back" onClick={() => navigate(-1)}>
                    <FaArrowLeft size={12} /> Back
                </button>

                <div className="trading-header">
                    <h2><FaWallet /> Paper Wallet</h2>
                    <p>Practice trading with virtual CLP — no risk, real market data</p>
                </div>

                {/* Balance Cards */}
                <div className="wallet-stats">
                    <div className="wallet-stat-card">
                        <div className="wallet-stat-label">Available Cash</div>
                        <div className="wallet-stat-value">{formatCLP(wallet?.available_cash)}</div>
                    </div>
                    <div className="wallet-stat-card">
                        <div className="wallet-stat-label">Invested</div>
                        <div className="wallet-stat-value">{formatCLP(wallet?.total_invested)}</div>
                    </div>
                    <div className="wallet-stat-card">
                        <div className="wallet-stat-label">Total P&L</div>
                        <div className={`wallet-stat-value ${totalPnL >= 0 ? 'positive' : 'negative'}`}>
                            {totalPnL >= 0 ? '+' : ''}{formatCLP(totalPnL)} ({pnlPercent}%)
                        </div>
                    </div>
                </div>

                {/* Open Positions */}
                <motion.div className="trading-card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}>
                    <div className="trading-card-title">
                        <FaChartLine size={16} /> Open Positions ({positions.length})
                    </div>

                    {positions.length === 0 ? (
                        <div className="trading-empty">
                            No open positions. <button onClick={() => navigate('/trade')} style={{ color: '#58a6ff', background: 'none', border: 'none', cursor: 'pointer' }}>Start trading →</button>
                        </div>
                    ) : (
                        <div style={{ overflowX: 'auto' }}>
                            <table className="positions-table">
                                <thead>
                                    <tr>
                                        <th>Asset</th>
                                        <th>Direction</th>
                                        <th>Qty</th>
                                        <th>Entry Price</th>
                                        <th>Invested</th>
                                        <th>Opened</th>
                                        <th></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {positions.map(pos => (
                                        <tr key={pos.id}>
                                            <td style={{ fontWeight: 600 }}>{pos.asset.toUpperCase()}</td>
                                            <td>
                                                <span style={{ color: pos.direction === 'long' ? '#3fb950' : '#f85149' }}>
                                                    {pos.direction === 'long' ? '📈 Long' : '📉 Short'}
                                                </span>
                                            </td>
                                            <td>{parseFloat(pos.quantity).toFixed(4)}</td>
                                            <td>{formatCLP(pos.entry_price)}</td>
                                            <td>{formatCLP(pos.invested_amount)}</td>
                                            <td style={{ color: '#8b949e', fontSize: '0.75rem' }}>
                                                {new Date(pos.opened_at).toLocaleDateString()}
                                            </td>
                                            <td>
                                                <button className="btn-close-pos" onClick={() => handleClose(pos.id)}>
                                                    Close
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </motion.div>

                {/* Trade History */}
                <motion.div className="trading-card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.15 }}>
                    <div className="trading-card-title">
                        <FaSync size={14} /> Recent Trades
                    </div>

                    {trades.length === 0 ? (
                        <div className="trading-empty">No closed trades yet.</div>
                    ) : (
                        <div style={{ overflowX: 'auto' }}>
                            <table className="positions-table">
                                <thead>
                                    <tr>
                                        <th>Asset</th>
                                        <th>Direction</th>
                                        <th>Entry</th>
                                        <th>Exit</th>
                                        <th>P&L</th>
                                        <th>%</th>
                                        <th>Closed</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {trades.map(t => (
                                        <tr key={t.id}>
                                            <td style={{ fontWeight: 600 }}>{t.asset.toUpperCase()}</td>
                                            <td style={{ color: t.direction === 'long' ? '#3fb950' : '#f85149' }}>
                                                {t.direction === 'long' ? 'Long' : 'Short'}
                                            </td>
                                            <td>{formatCLP(t.entry_price)}</td>
                                            <td>{formatCLP(t.exit_price)}</td>
                                            <td className={t.pnl >= 0 ? 'pnl-positive' : 'pnl-negative'}>
                                                {t.pnl >= 0 ? '+' : ''}{formatCLP(t.pnl)}
                                            </td>
                                            <td className={t.pnl_percent >= 0 ? 'pnl-positive' : 'pnl-negative'}>
                                                {t.pnl_percent >= 0 ? '+' : ''}{t.pnl_percent}%
                                            </td>
                                            <td style={{ color: '#8b949e', fontSize: '0.75rem' }}>
                                                {new Date(t.closed_at).toLocaleDateString()}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </motion.div>

                {/* Actions */}
                <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
                    <motion.button
                        className="trade-submit buy-btn"
                        style={{ width: 'auto', padding: '0.6rem 2rem' }}
                        onClick={() => { playClick(); navigate('/trade'); }}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                    >
                        New Trade →
                    </motion.button>
                    <button className="wallet-reset-btn" onClick={handleReset}>
                        <FaSync size={11} /> Reset Wallet
                    </button>
                </div>
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

export default WalletPage;
