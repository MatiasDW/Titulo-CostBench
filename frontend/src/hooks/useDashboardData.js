/**
 * useDashboardData – Consolidated data fetching hook.
 *
 * Fetches ranking + all macro series once and provides them to the entire
 * dashboard tree.  Prevents duplicate HTTP requests when child components
 * mount/unmount (tabs, modals, etc.).
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

// --- Shared Memory Cache ---
// Global cache outside the hook to persist across unmounts/remounts.
const DATA_CACHE = new Map();
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

const MACRO_SERIES = [
    { key: 'cpi', seriesId: 'CPIAUCSL' },
    { key: 'yields', seriesId: 'DGS10' },
    { key: 'gold', seriesId: 'GOLDAMGBD228NLBM' },
    { key: 'copper', seriesId: 'PCOPPUSDM' },
    { key: 'oil', seriesId: 'DCOILWTICO' },
    { key: 'btc', seriesId: 'BTC-CLP' },
    { key: 'eth', seriesId: 'ETH-CLP' },
];

export default function useDashboardData({ limit = 10, currency = 'CLP' } = {}) {
    const [items, setItems] = useState([]);
    const [macro, setMacro] = useState({
        cpi: [], yields: [], gold: [], copper: [], oil: [], btc: [], eth: [],
    });
    const [loading, setLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState(null);

    const fetchData = useCallback(async (force = false) => {
        const cacheKey = `${limit}-${currency}`;

        // Return cached data if valid and not forcing a refresh
        if (!force && DATA_CACHE.has(cacheKey)) {
            const cached = DATA_CACHE.get(cacheKey);
            if (Date.now() - cached.timestamp < CACHE_TTL_MS) {
                setItems(cached.items);
                setMacro(cached.macro);
                setLastUpdate(cached.lastUpdate);
                setLoading(false);
                return;
            } else {
                DATA_CACHE.delete(cacheKey); // Expired
            }
        }

        setLoading(true);
        try {
            // All requests in parallel – ranking + 7 macro series
            const [rankingRes, ...macroResults] = await Promise.all([
                axios.get(`/api/v1/atc/ranking?limit=${limit}&currency=${currency}`),
                ...MACRO_SERIES.map(s =>
                    axios.get(`/api/v1/market/history?series_id=${s.seriesId}`)
                ),
            ]);

            // Ranking
            const rankingData = rankingRes.data;
            const rankingItems = rankingData.items || rankingData.data || [];
            const metaTimestamp = rankingData.metadata?.timestamp || new Date().toISOString();
            setItems(rankingItems);
            setLastUpdate(metaTimestamp);

            // Macro – build object keyed by series name
            const macroObj = {};
            MACRO_SERIES.forEach((s, idx) => {
                macroObj[s.key] = macroResults[idx].data.observations || [];
            });
            setMacro(macroObj);

            // Save to memory cache
            DATA_CACHE.set(cacheKey, {
                items: rankingItems,
                macro: macroObj,
                lastUpdate: metaTimestamp,
                timestamp: Date.now()
            });
        } catch (error) {
            console.error('useDashboardData fetch error:', error);
        } finally {
            setLoading(false);
        }
    }, [limit, currency]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return useMemo(() => ({
        items,
        macro,
        loading,
        lastUpdate,
        refetch: fetchData,
    }), [items, macro, loading, lastUpdate, fetchData]);
}
