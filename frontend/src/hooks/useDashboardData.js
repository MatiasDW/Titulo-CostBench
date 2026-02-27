/**
 * useDashboardData – Consolidated data fetching hook.
 *
 * Fetches ranking + all macro series once and provides them to the entire
 * dashboard tree.  Prevents duplicate HTTP requests when child components
 * mount/unmount (tabs, modals, etc.).
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

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

    const fetchData = useCallback(async () => {
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
            setItems(rankingData.items || rankingData.data || []);
            setLastUpdate(
                rankingData.metadata?.timestamp || new Date().toISOString()
            );

            // Macro – build object keyed by series name
            const macroObj = {};
            MACRO_SERIES.forEach((s, idx) => {
                macroObj[s.key] = macroResults[idx].data.observations || [];
            });
            setMacro(macroObj);
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
