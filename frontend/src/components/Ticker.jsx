import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Ticker.css'; // Make sure to create this CSS file

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

                        let label = item.series_id;
                        let icon = '📈';

                        if (item.series_id === 'CPIAUCSL') { label = 'US CPI'; icon = '🇺🇸'; }
                        if (item.series_id === 'DGS10') { label = 'US 10Y'; icon = '🏦'; }
                        if (item.series_id === 'GOLDAMGBD228NLBM') { label = 'Gold'; icon = '🥇'; }
                        if (item.series_id === 'PCOPPUSDM') { label = 'Copper'; icon = '⛏️'; }
                        if (item.series_id === 'DCOILWTICO') { label = 'Oil (WTI)'; icon = '🛢️'; }
                        if (item.series_id === 'SLVPRUSD') { label = 'Silver'; icon = '🥈'; }
                        if (item.series_id === 'BTC-CLP') { label = 'Bitcoin'; icon = '🪙'; } // If implemented
                        if (item.series_id === 'ETH-CLP') { label = 'Ether'; icon = '💠'; }

                        return { label, value: latest.value, icon };
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
                            <span className="me-2">{item.icon}</span>
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
