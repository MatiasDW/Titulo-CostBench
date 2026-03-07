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
let _version = 'v1';          // bumps whenever data changes to bust caches
const _cache = new Map();     // key → insight string
const _inflight = new Map();  // key → Promise<string|null>

const CACHE_TTL = 12 * 60 * 60 * 1000; // 12 h
const LS_PREFIX = 'scloda_insight_v5_';

// ── Asset chart configs (single source of truth) ──
export const ASSET_CHARTS = [
    { key: 'gold', title: '🥇 Gold', subtitle: 'USD/oz', color: '#bf8700', colorClass: 'text-warning', fallback: 'Traditional safe-haven asset. Inversely correlated with risk appetite.' },
    { key: 'copper', title: '⛏️ Copper', subtitle: 'USD/lb', color: '#da3633', colorClass: 'text-danger', fallback: 'Chile\'s lifeblood. Key indicator of global industrial demand.' },
    { key: 'btc', title: '🪙 Bitcoin', subtitle: 'CLP', color: '#f2a900', colorClass: 'text-warning', fallback: 'Volatile digital asset. Risk sentiment proxy.' },
    { key: 'eth', title: '💠 Ethereum', subtitle: 'CLP', color: '#627eea', colorClass: 'text-primary', fallback: 'Smart contract platform. High DeFi exposure.' },
    { key: 'oil', title: '🛢️ Oil WTI', subtitle: 'USD/bbl', color: '#c9d1d9', colorClass: 'text-light', fallback: 'Energy benchmark. Impacts inflation and transportation costs.' },
    { key: 'cpi', title: '📊 US CPI', subtitle: 'Index', color: '#f78166', colorClass: 'text-danger', fallback: 'US inflation gauge. Key driver of Fed policy decisions.' },
    { key: 'yields', title: '📈 Treasury 10Y', subtitle: 'Yield %', color: '#58a6ff', colorClass: 'text-primary', fallback: 'Risk-free rate. Higher yields pressure emerging market currencies.' },
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

// Derive a version string from latest dates to invalidate caches when data updates
function deriveVersion(macro) {
    if (!macro || Object.keys(macro).length === 0) return _version;
    const maxDate = Object.values(macro)
        .flat()
        .map(d => d.date || d.observation_date)
        .filter(Boolean)
        .map(d => new Date(d).getTime())
        .reduce((a, b) => Math.max(a, b), 0);
    return maxDate ? `v${maxDate}` : _version;
}

/**
 * Fetch a single insight, deduplicating in-flight requests.
 * Returns the insight string or null.
 */
async function fetchOne(assetKey, data) {
    const cacheKey = `${_version}:${assetKey}`;

    // 1. Memory cache
    if (_cache.has(cacheKey)) return _cache.get(cacheKey);

    // 2. localStorage
    const lsHit = readLS(cacheKey);
    if (lsHit) {
        _cache.set(cacheKey, lsHit);
        return lsHit;
    }

    // 3. Deduplicate: if a request is already in-flight, piggyback on it
    if (_inflight.has(cacheKey)) return _inflight.get(cacheKey);

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
                _cache.set(cacheKey, text);
                writeLS(cacheKey, text);
            }
            return text;
        })
        .catch(err => {
            console.error(`useSclodaInsights: ${assetKey}`, err);
            return null;
        })
        .finally(() => {
            _inflight.delete(cacheKey);
        });

    _inflight.set(cacheKey, promise);
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
        const nextVersion = deriveVersion(macro);
        if (nextVersion !== _version) {
            // Data changed → clear caches to force fresh insights
            _version = nextVersion;
            _cache.clear();
            _inflight.clear();
            // Purge localStorage entries from previous versions
            try {
                Object.keys(localStorage)
                    .filter(k => k.startsWith(LS_PREFIX))
                    .forEach(k => localStorage.removeItem(k));
            } catch { /* ignore */ }
        }

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
