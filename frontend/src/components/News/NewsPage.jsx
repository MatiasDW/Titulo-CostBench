import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FaNewspaper, FaRobot, FaExternalLinkAlt, FaGlobeAmericas } from 'react-icons/fa';
import SclodaChat from '../SclodaChat';
import './NewsPage.css';

const API_BASE = '/api/v1/news';

/* ── Tab definitions ─────────────────────────── */
const TABS = [
    { key: 'chile', label: '🇨🇱 Chile', endpoint: `${API_BASE}/chile` },
    { key: 'world', label: '🌎 World', endpoint: `${API_BASE}/world` },
];

/* ── Skeleton Card ───────────────────────────── */
const SkeletonCard = () => (
    <div className="news-skeleton">
        <div className="news-skeleton-img" />
        <div className="news-skeleton-body">
            <div className="news-skeleton-line short" />
            <div className="news-skeleton-line long" />
            <div className="news-skeleton-line medium" />
            <div className="news-skeleton-line short" />
        </div>
    </div>
);

/* ── News Card ───────────────────────────────── */
const NewsCard = ({ article, index, onAnalyze, analysisData }) => {
    const [analyzing, setAnalyzing] = useState(false);

    const handleAnalyze = async () => {
        setAnalyzing(true);
        await onAnalyze(article, index);
        setAnalyzing(false);
    };

    const formatDate = (iso) => {
        try {
            const d = new Date(iso);
            return d.toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
            });
        } catch {
            return iso?.slice(0, 16) || '';
        }
    };

    return (
        <motion.div
            className="news-card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.06, duration: 0.35 }}
        >
            {article.image ? (
                <img
                    className="news-card-image"
                    src={article.image}
                    alt={article.title}
                    loading="lazy"
                    onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.nextSibling && (e.target.nextSibling.style.display = 'flex');
                    }}
                />
            ) : null}
            {!article.image && (
                <div className="news-card-image-placeholder">
                    <FaNewspaper />
                </div>
            )}

            <div className="news-card-body">
                {/* Meta */}
                <div className="news-card-meta">
                    <span className="news-card-source">
                        {article.source?.name || 'Unknown'}
                    </span>
                    <span className="news-card-date">
                        {formatDate(article.publishedAt)}
                    </span>
                </div>

                {/* Title */}
                <h3 className="news-card-title">
                    <a href={article.url} target="_blank" rel="noopener noreferrer">
                        {article.title}
                    </a>
                </h3>

                {/* Description */}
                {article.description && (
                    <p className="news-card-desc">{article.description}</p>
                )}

                {/* Actions */}
                <div className="news-card-footer">
                    <button
                        className="news-btn-analyze"
                        onClick={handleAnalyze}
                        disabled={analyzing}
                        title="Ask Scloda: How does this affect your pocket or the UF?"
                    >
                        {analyzing ? (
                            <>
                                <span className="spinner" />
                                Analyzing…
                            </>
                        ) : (
                            <>
                                <FaRobot size={13} />
                                Analyze with Scloda
                            </>
                        )}
                    </button>

                    <a
                        href={article.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="news-btn-read"
                    >
                        Read <FaExternalLinkAlt size={10} />
                    </a>
                </div>

                {/* Analysis Result */}
                <AnimatePresence>
                    {analysisData && (
                        <motion.div
                            className="news-analysis"
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                        >
                            <div className="news-analysis-header">
                                <FaRobot size={12} />
                                Scloda Analysis
                            </div>
                            <p className="news-analysis-text">{analysisData}</p>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </motion.div>
    );
};

/* ── Main NewsPage ───────────────────────────── */
const NewsPage = () => {
    const [activeTab, setActiveTab] = useState('chile');
    const [articles, setArticles] = useState({ chile: [], world: [] });
    const [loading, setLoading] = useState({ chile: true, world: true });
    const [errors, setErrors] = useState({ chile: null, world: null });
    const [analyses, setAnalyses] = useState({}); // { "chile-0": "text", ... }

    /* ── Fetch news for a tab ──────────────── */
    const fetchNews = useCallback(async (tabKey) => {
        const tab = TABS.find((t) => t.key === tabKey);
        if (!tab) return;

        setLoading((prev) => ({ ...prev, [tabKey]: true }));
        setErrors((prev) => ({ ...prev, [tabKey]: null }));

        try {
            const res = await fetch(tab.endpoint, { credentials: 'include' });
            const data = await res.json();

            if (!res.ok || data.error) {
                setErrors((prev) => ({
                    ...prev,
                    [tabKey]: data.error || 'Failed to load news',
                }));
                setArticles((prev) => ({ ...prev, [tabKey]: [] }));
            } else {
                setArticles((prev) => ({
                    ...prev,
                    [tabKey]: data.articles || [],
                }));
            }
        } catch (err) {
            setErrors((prev) => ({
                ...prev,
                [tabKey]: 'Network error — check your connection',
            }));
        } finally {
            setLoading((prev) => ({ ...prev, [tabKey]: false }));
        }
    }, []);

    /* ── Load both tabs on mount ────────────── */
    useEffect(() => {
        fetchNews('chile');
        fetchNews('world');
    }, [fetchNews]);

    /* ── Analyze article with Scloda ────────── */
    const handleAnalyze = async (article, index) => {
        const key = `${activeTab}-${index}`;
        // Skip if already analyzed
        if (analyses[key]) return;

        try {
            const res = await fetch(`${API_BASE}/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ article }),
            });
            const data = await res.json();

            setAnalyses((prev) => ({
                ...prev,
                [key]: data.analysis || 'Analysis unavailable.',
            }));
        } catch {
            setAnalyses((prev) => ({
                ...prev,
                [key]: '⚠️ Could not reach the analysis service.',
            }));
        }
    };

    /* ── Render helpers ─────────────────────── */
    const currentArticles = articles[activeTab] || [];
    const isLoading = loading[activeTab];
    const error = errors[activeTab];

    return (
        <div className="news-page">
            {/* Header */}
            <div className="news-header">
                <h1>
                    <FaNewspaper style={{ marginRight: '0.5rem', color: '#58a6ff' }} />
                    Market News
                </h1>
                <p>
                    Financial headlines powered by GNews • Analyzed by Scloda AI
                </p>
            </div>

            {/* Tabs */}
            <div className="news-tabs">
                {TABS.map((tab) => (
                    <button
                        key={tab.key}
                        className={`news-tab ${activeTab === tab.key ? 'active' : ''}`}
                        onClick={() => setActiveTab(tab.key)}
                    >
                        {tab.label}
                        {!loading[tab.key] && articles[tab.key]?.length > 0 && (
                            <span style={{ marginLeft: '0.4rem', opacity: 0.6 }}>
                                ({articles[tab.key].length})
                            </span>
                        )}
                    </button>
                ))}
            </div>

            {/* Error */}
            {error && (
                <div className="news-error">
                    <p>⚠️ {error}</p>
                </div>
            )}

            {/* Loading skeletons */}
            {isLoading && (
                <div className="news-grid">
                    {Array.from({ length: activeTab === 'chile' ? 6 : 4 }).map((_, i) => (
                        <SkeletonCard key={i} />
                    ))}
                </div>
            )}

            {/* Articles */}
            {!isLoading && !error && currentArticles.length > 0 && (
                <div className="news-grid">
                    {currentArticles.map((article, i) => (
                        <NewsCard
                            key={`${activeTab}-${i}`}
                            article={article}
                            index={i}
                            onAnalyze={handleAnalyze}
                            analysisData={analyses[`${activeTab}-${i}`]}
                        />
                    ))}
                </div>
            )}

            {/* Empty state */}
            {!isLoading && !error && currentArticles.length === 0 && (
                <div className="news-empty">
                    <div className="news-empty-icon">
                        <FaGlobeAmericas />
                    </div>
                    <h3>No news available</h3>
                    <p>Check back later — news refreshes every 12 hours.</p>
                </div>
            )}

            <SclodaChat />
        </div>
    );
};

export default NewsPage;
