import React, { useState, useEffect } from 'react';
import axios from 'axios';
import AssetIcon from './AssetIcon';
import './Ticker.css'; // Make sure to create this CSS file

// Mapping from series_id to AssetIcon type and display label
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
    'UF': { label: 'UF', type: 'uf' }
};

const Ticker = () => {
    const [items, setItems] = useState([]);

    useEffect(() => {
        const fetchMarketData = async () => {
            try {
                // Fetch market indices + commodities
                const res = await axios.get('/api/v1/market');
                // Adjust if API returns different structure. 
                // Assuming it returns { data: { cpi:..., yields:..., commodities: [...] } }
                // Or we might need to fetch /market/indices

                // For now, let's try to hit the same endpoint or just mock if API isn't ready for unified feed
                const indicesRes = await axios.get('/api/v1/market/indices');
                const indices = indicesRes.data.items || [];

                const fetchedItems = await Promise.all(indices.map(async (item) => {
                    try {
                        const hRes = await axios.get(`/api/v1/market/history?series_id=${item.series_id}`);
                        const obs = hRes.data.observations;
                        const latest = obs.length > 0 ? obs[obs.length - 1] : { value: 'N/A' };

                        const config = SERIES_CONFIG[item.series_id] || { label: item.series_id, type: 'trend' };

                        return {
                            label: config.label,
                            value: latest.value,
                            iconType: config.type
                        };
                    } catch (e) {
                        return null;
                    }
                }));

                setItems(fetchedItems.filter(i => i !== null));

            } catch (error) {
                console.error("Error fetching ticker data", error);
            }
        };

        fetchMarketData();
        const interval = setInterval(fetchMarketData, 60000); // Update every minute
        return () => clearInterval(interval);
    }, []);

    if (items.length === 0) return null;

    return (
        <div className="ticker-container bg-dark border-bottom border-secondary text-white py-1">
            <div className="ticker-wrap">
                <div className="ticker-move">
                    {items.map((item, idx) => (
                        <div key={idx} className="ticker-item me-5 d-inline-block">
                            <span className="me-2">
                                <AssetIcon type={item.iconType} size={16} />
                            </span>
                            <span className="fw-bold me-2">{item.label}:</span>
                            <span className="font-monospace text-warning">{item.value}</span>
                        </div>
                    ))}
                    {/* Duplicate for infinite loop illusion if needed, but CSS animation handles it usually */}
                </div>
            </div>
        </div>
    );
};

export default Ticker;
