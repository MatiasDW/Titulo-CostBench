import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FaProjectDiagram, FaCaretUp, FaCaretDown, FaMinus } from 'react-icons/fa';
import AIInsight from './AIInsight';

// Dictionary to translate Yahoo Finance tickers to human-readable names
const tickerNameMap = {
    'HG=F': 'Copper',
    'CL=F': 'WTI Crude Oil',
    '^TNX': 'US 10Y Treasury',
    '^GSPC': 'S&P 500 Index',
    'GC=F': 'Gold',
    'USDCLP=X': 'USD/CLP',
    'BTC-USD': 'Bitcoin',
    'ETH-USD': 'Ethereum'
};

const getAssetName = (ticker) => {
    return tickerNameMap[ticker] || ticker;
};

const MarketIntelligenceCard = () => {
    const [insights, setInsights] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [lastRun, setLastRun] = useState(null);

    useEffect(() => {
        const fetchInsights = async () => {
            try {
                const response = await axios.get('/api/v1/market/markov-insights');
                setInsights(response.data.insights || []);
                setLastRun(response.data.run_date);
                setLoading(false);
            } catch (err) {
                console.error("Failed to fetch Markov insights:", err);
                setError("Failed to load Market Intelligence.");
                setLoading(false);
            }
        };

        fetchInsights();
    }, []);

    const renderProbability = (prob) => {
        const val = parseFloat(prob);
        if (isNaN(val)) return '—';
        // Highlight probabilities >= 50%
        const isHigh = val >= 50;
        return (
            <span className={isHigh ? 'text-primary fw-bold' : 'text-light'}>
                {val.toFixed(1)}%
            </span>
        );
    };

    if (loading) {
        return (
            <div className="card card-custom p-4 text-center">
                <div className="spinner-border text-primary" role="status">
                    <span className="visually-hidden">Loading...</span>
                </div>
            </div>
        );
    }

    if (error || insights.length === 0) {
        return (
            <div className="card card-custom p-4 mt-4 animate-in" style={{ borderLeft: '4px solid #58a6ff' }}>
                <div className="d-flex align-items-center mb-3">
                    <FaProjectDiagram className="text-primary me-2 fs-4" />
                    <h5 className="mb-0 text-white">Scloda Quant Intelligence</h5>
                </div>
                <div className="alert alert-warning mb-0" style={{ backgroundColor: '#2a2f38', borderColor: '#30363d', color: '#c9d1d9' }}>
                    {error || "Markov predictions have not been computed by the local model yet. Please run the weekly Machine Learning job."}
                </div>
            </div>
        );
    }

    // Ensure Copper -> USD/CLP is always shown first as it's the core macro metric for Chile
    let displayInsights = [];
    const copperUsd = insights.find(i => i.predictor === 'HG=F' && i.target === 'USDCLP=X');

    if (copperUsd) {
        displayInsights.push(copperUsd);
    }

    // Fill the rest with the most significant ones, avoiding duplicates
    for (const insight of insights) {
        if (displayInsights.length >= 3) break;
        if (!displayInsights.find(i => i.id === insight.id)) {
            displayInsights.push(insight);
        }
    }

    return (
        <div className="card card-custom p-3 mt-4 animate-in" style={{ borderLeft: '4px solid #58a6ff' }}>
            <div className="d-flex align-items-center mb-3">
                <FaProjectDiagram className="text-primary me-2 fs-4" />
                <h5 className="mb-0 text-white">Scloda Quant Intelligence</h5>
            </div>

            <p className="text-white-50 small mb-4">
                <strong>What is this?</strong> Our Quantitative Model scans thousands of global variables across 5 years of historical data to discover hidden mathematical causalities. It uses a Markov Chain algorithm to calculate the statistical probability of an asset going <strong>UP</strong> or <strong>DOWN</strong> tomorrow, based entirely on how its "predator" asset closed today. This gives you an edge by helping you anticipate market shocks before they happen.
            </p>

            <div className="row g-3">
                {displayInsights.map((insight, idx) => {
                    // Extract the matrix
                    const matrix = insight.transition_matrix || {};
                    const predictorName = getAssetName(insight.predictor);
                    const targetName = getAssetName(insight.target);

                    return (
                        <div key={idx} className="col-md-4">
                            <div className="card bg-dark border-secondary p-3 h-100">
                                <h6 className="text-light text-center mb-1">
                                    <span className="text-warning fw-bold">{predictorName}</span>
                                    {' '} ➡️ {' '}
                                    <span className="text-info fw-bold">{targetName}</span>
                                </h6>
                                <div className="text-center mb-3" style={{ fontSize: '0.70rem', color: '#8b949e' }}>
                                    (Statistical Impact P-Value: {insight.p_value.toFixed(4)})
                                </div>

                                <div className="table-responsive">
                                    <table className="table table-sm table-dark table-borderless text-center" style={{ fontSize: '0.8rem' }}>
                                        <thead>
                                            <tr style={{ borderBottom: '1px solid #30363d' }}>
                                                <th className="text-muted fw-normal text-start" style={{ width: '40%' }}>If today {predictorName}...</th>
                                                <th className="text-success fw-normal"><FaCaretUp /> Up</th>
                                                <th className="text-danger fw-normal"><FaCaretDown /> Down</th>
                                                <th className="text-secondary fw-normal"><FaMinus /> Neutral</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {/* Sube (Bull) */}
                                            {matrix['Bull'] && (
                                                <tr>
                                                    <td className="text-success text-start"><FaCaretUp /> Up</td>
                                                    <td>{renderProbability(matrix['Bull']['Bull'])}</td>
                                                    <td>{renderProbability(matrix['Bull']['Bear'])}</td>
                                                    <td>{renderProbability(matrix['Bull']['Sideways'])}</td>
                                                </tr>
                                            )}
                                            {/* Baja (Bear) */}
                                            {matrix['Bear'] && (
                                                <tr>
                                                    <td className="text-danger text-start"><FaCaretDown /> Down</td>
                                                    <td>{renderProbability(matrix['Bear']['Bull'])}</td>
                                                    <td>{renderProbability(matrix['Bear']['Bear'])}</td>
                                                    <td>{renderProbability(matrix['Bear']['Sideways'])}</td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default MarketIntelligenceCard;
