/**
 * useSclodaInsights – Consolidated insight fetching with single-flight dedup.
 *
 * Guarantees that even if ChartCarousel AND MarketDashboard both call this
 * hook at the same time, each asset key triggers AT MOST one HTTP request.
 *
 * Caching layers (in order):
 *   1. Module-level in-memory Map  → instant (same page session)
 *   2. localStorage (12 h TTL)     → survives refresh
 *   3. /api/v1/scloda/insight      → fresh LLM call (last resort)
 */
import { useState, useEffect, useCallback, useMemo } from 'react';

// ── Module-level singletons (shared across all hook instances) ──
const _cache = new Map();   // key → insight string
const _inflight = new Map();   // key → Promise<string|null>

const CACHE_TTL = 12 * 60 * 60 * 1000; // 12 h
const LS_PREFIX = 'scloda_insight_v3_';

// ── Asset chart configs (single source of truth) ──
export const ASSET_CHARTS = [
    { key: 'gold', title: '🥇 Oro', subtitle: 'USD/oz', color: '#bf8700', colorClass: 'text-warning', fallback: 'Activo refugio tradicional. Inversamente correlacional al riesgo.' },
    { key: 'copper', title: '⛏️ Cobre', subtitle: 'USD/lb', color: '#da3633', colorClass: 'text-danger', fallback: 'Sueldo de Chile. Indicador clave de demanda industrial global.' },
    { key: 'btc', title: '🪙 Bitcoin', subtitle: 'CLP', color: '#f2a900', colorClass: 'text-warning', fallback: 'Activo digital volátil. Proxy de riesgo.' },
    { key: 'eth', title: '💠 Ethereum', subtitle: 'CLP', color: '#627eea', colorClass: 'text-primary', fallback: 'Plataforma de contratos inteligentes. Alta exposición DeFi.' },
    { key: 'oil', title: '🛢️ Petróleo WTI', subtitle: 'USD/bbl', color: '#c9d1d9', colorClass: 'text-light', fallback: 'Referencia energética. Afecta inflación y transporte.' },
    { key: 'cpi', title: '📊 IPC EE.UU.', subtitle: 'Índice', color: '#f78166', colorClass: 'text-danger', fallback: 'Inflación USA. Clave para decisiones de la Fed.' },
    { key: 'yields', title: '📈 Treasury 10Y', subtitle: 'Tasa %', color: '#58a6ff', colorClass: 'text-primary', fallback: 'Tasa libre de riesgo. Presiona monedas emergentes al subir.' },
];

// ── Helpers ──

function getTrend(data) {
    if (!data || data.length < 2) return { percent: 0, trend: 'stable' };
    const last = data[data.length - 1]?.value || 0;
    const first = data[0]?.value || last;
    const pct = ((last - first) / first) * 100;
    const trend = pct > 0.5 ? 'up' : pct < -0.5 ? 'down' : 'stable';
    return { percent: parseFloat(pct.toFixed(2)), trend };
}

function readLS(key) {
    try {
        const raw = localStorage.getItem(LS_PREFIX + key);
        if (!raw) return null;
        const { insight, timestamp } = JSON.parse(raw);
        if (Date.now() - timestamp < CACHE_TTL) return insight;
    } catch { /* corrupted */ }
    return null;
}

function writeLS(key, insight) {
    try {
        localStorage.setItem(LS_PREFIX + key, JSON.stringify({ insight, timestamp: Date.now() }));
    } catch { /* quota */ }
}

/**
 * Fetch a single insight, deduplicating in-flight requests.
 * Returns the insight string or null.
 */
async function fetchOne(assetKey, data) {
    // 1. Memory cache
    if (_cache.has(assetKey)) return _cache.get(assetKey);

    // 2. localStorage
    const lsHit = readLS(assetKey);
    if (lsHit) {
        _cache.set(assetKey, lsHit);
        return lsHit;
    }

    // 3. Deduplicate: if a request is already in-flight, piggyback on it
    if (_inflight.has(assetKey)) return _inflight.get(assetKey);

    // 4. Fire the real HTTP call
    const { percent, trend } = getTrend(data);
    const currentValue = data[data.length - 1]?.value;

    const promise = fetch('/api/v1/scloda/insight', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            asset: assetKey,
            current_value: currentValue,
            change_percent: percent,
            trend,
        }),
    })
        .then(res => (res.ok ? res.json() : null))
        .then(json => {
            const text = json?.insight || null;
            if (text) {
                _cache.set(assetKey, text);
                writeLS(assetKey, text);
            }
            return text;
        })
        .catch(err => {
            console.error(`useSclodaInsights: ${assetKey}`, err);
            return null;
        })
        .finally(() => {
            _inflight.delete(assetKey);
        });

    _inflight.set(assetKey, promise);
    return promise;
}

// ── Hook ──

/**
 * @param {Object} macro – macro data object keyed by asset (e.g. { gold: [...], btc: [...] })
 * @returns {{ insights: Object, loading: boolean }}
 */
export default function useSclodaInsights(macro) {
    const [insights, setInsights] = useState({});
    const [loading, setLoading] = useState(true);

    const fetchAll = useCallback(async () => {
        if (!macro || Object.keys(macro).length === 0) {
            setLoading(false);
            return;
        }

        setLoading(true);

        const results = await Promise.all(
            ASSET_CHARTS.map(async (chart) => {
                const data = macro[chart.key]?.slice(-25) || [];
                if (data.length < 2) return null;
                const insight = await fetchOne(chart.key, data);
                return insight ? { key: chart.key, insight } : null;
            })
        );

        const merged = {};
        results.forEach(r => { if (r) merged[r.key] = r.insight; });
        setInsights(prev => ({ ...prev, ...merged }));
        setLoading(false);
    }, [macro]);

    useEffect(() => { fetchAll(); }, [fetchAll]);

    return useMemo(() => ({ insights, loading }), [insights, loading]);
}
