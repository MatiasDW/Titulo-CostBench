import React, { useState, useEffect, memo } from 'react';
import axios from 'axios';
import AssetIcon from './AssetIcon';
import './Ticker.css';

// Mapping from series_id to display config
const SERIES_CONFIG = {
    'CPIAUCSL': { label: 'US CPI', type: 'cpi' },
    'DGS10': { label: 'US 10Y', type: '10y' },
    'GOLDAMGBD228NLBM': { label: 'Gold', type: 'gold' },
    'PCOPPUSDM': { label: 'Copper', type: 'copper' },
    'DCOILWTICO': { label: 'Oil (WTI)', type: 'oil' },
    'SLVPRUSD': { label: 'Silver', type: 'silver' },
    'BTC-CLP': { label: 'Bitcoin', type: 'btc' },
    'ETH-CLP': { label: 'Ether', type: 'eth' },
    'USDCLP': { label: 'USD/CLP', type: 'usdclp' },
    'UF': { label: 'UF', type: 'uf' },
    'XRP-CLP': { label: 'XRP', type: 'xrp' },
    'SOL-CLP': { label: 'SOL', type: 'sol' },
};

const formatValue = (value, unit) => {
    if (value == null) return '—';
    // For CLP values (crypto), show with dots separator
    if (unit === 'CLP') return `$${Math.round(value).toLocaleString('es-CL')}`;
    // For percentages
    if (unit === '%') return `${value.toFixed(2)}%`;
    // For index values
    if (unit === 'Index') return value.toFixed(1);
    // For USD values, show 2 decimals
    if (unit?.startsWith('USD')) return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    // CLP/USD
    if (unit === 'CLP/USD') return `$${Math.round(value).toLocaleString('es-CL')}`;
    // Fallback
    return value.toLocaleString('es-CL', { maximumFractionDigits: 2 });
};

const Ticker = () => {
    const [items, setItems] = useState([]);

    useEffect(() => {
        const fetchMarketData = async () => {
            try {
                const res = await axios.get('/api/v1/market/latest');
                const latest = res.data.items || [];

                const tickerItems = latest
                    .filter(item => !item.is_mock) // Hide mock data from ticker
                    .map(item => {
                        const cfg = SERIES_CONFIG[item.series_id] || { label: item.label || item.series_id, type: 'trend' };
                        return {
                            label: cfg.label,
                            value: item.value,
                            changePct: item.change_pct,
                            unit: item.unit || '',
                            iconType: cfg.type,
                        };
                    });

                setItems(tickerItems);
            } catch (error) {
                console.error("Error fetching ticker data", error);
            }
        };

        fetchMarketData();
        const interval = setInterval(fetchMarketData, 60000);
        return () => clearInterval(interval);
    }, []);

    if (items.length === 0) return null;

    const displayItems = [...items, ...items];

    return (
        <div className="ticker-container bg-dark border-bottom border-secondary text-white py-1">
            <div className="ticker-wrap">
                <div className="ticker-move">
                    {displayItems.map((item, idx) => {
                        const isUp = item.changePct > 0;
                        const isDown = item.changePct < 0;
                        const arrow = isUp ? '▲' : isDown ? '▼' : '→';
                        const colorClass = isUp ? 'text-success' : isDown ? 'text-danger' : 'text-muted';

                        return (
                            <div key={idx} className="ticker-item me-4 d-inline-block">
                                <span className="me-1">
                                    <AssetIcon type={item.iconType} size={14} />
                                </span>
                                <span className="fw-bold me-1" style={{ fontSize: '0.78rem' }}>
                                    {item.label}
                                </span>
                                <span className={`${colorClass}`} style={{ fontSize: '0.72rem', fontFamily: 'monospace' }}>
                                    {arrow} {Math.abs(item.changePct).toFixed(1)}%
                                </span>
                                {item.unit && (
                                    <span className="ms-1" style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.65)' }}>
                                        {formatValue(item.value, item.unit)}
                                    </span>
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};

export default memo(Ticker);
