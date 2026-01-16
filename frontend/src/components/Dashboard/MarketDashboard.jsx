import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
} from 'chart.js';
import { Bar, Line } from 'react-chartjs-2';
import AIInsight from './AIInsight';

// Register Chart.js components
ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

const MarketDashboard = ({ items, macro, analytics }) => {
    // Chart Global Options
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 1500, easing: 'easeOutQuart' },
        plugins: { legend: { display: false } },
        scales: {
            x: { grid: { color: '#30363d' }, ticks: { color: '#8b949e' } },
            y: { grid: { color: '#30363d' }, ticks: { color: '#8b949e' } }
        }
    };

    const horizontalOptions = {
        ...commonOptions,
        indexAxis: 'y',
        scales: {
            x: { grid: { color: '#30363d' }, ticks: { color: '#8b949e' } },
            y: { grid: { display: false }, ticks: { color: '#c9d1d9', font: { size: 11 } } }
        }
    };

    // Data Processing
    const { top5Cheap, top5Expensive, distribution } = useMemo(() => {
        if (!items || items.length === 0) return { top5Cheap: [], top5Expensive: [], distribution: {} };

        // Sort by cost
        const sorted = [...items].sort((a, b) => a.cost - b.cost);
        const top5Cheap = sorted.slice(0, 5);
        const top5Expensive = [...sorted].reverse().slice(0, 5); // Descending for Chart

        // Stats
        const costs = items.map(i => i.cost);
        const min = Math.min(...costs);
        const max = Math.max(...costs);
        const avg = costs.reduce((a, b) => a + b, 0) / costs.length;

        return { top5Cheap, top5Expensive, distribution: { min, avg, max, savings: max - min } };
    }, [items]);

    // Chart Data Configs
    const cheapData = {
        labels: top5Cheap.map(i => i.product),
        datasets: [{
            label: 'ATC',
            data: top5Cheap.map(i => i.cost),
            backgroundColor: '#238636',
            borderColor: '#2ea043',
            borderWidth: 1
        }]
    };

    const expensiveData = {
        labels: top5Expensive.map(i => i.institution),
        datasets: [{
            label: 'ATC',
            data: top5Expensive.map(i => i.cost),
            backgroundColor: '#a40e26',
            borderColor: '#da3633',
            borderWidth: 1
        }]
    };

    const distData = {
        labels: ['Lowest', 'Average', 'Highest'],
        datasets: [{
            label: 'Cost Spread',
            data: [distribution.min, distribution.avg, distribution.max],
            backgroundColor: ['#238636', '#d29922', '#a40e26'],
            borderColor: ['#2ea043', '#dbab09', '#da3633'],
            borderWidth: 1
        }]
    };

    // Macro Data Handling
    const cpiData = {
        labels: macro?.cpi?.map(d => new Date(d.date).toLocaleDateString()) || [],
        datasets: [{
            label: 'CPI',
            data: macro?.cpi?.map(d => d.value) || [],
            borderColor: '#f78166',
            backgroundColor: 'rgba(247, 129, 102, 0.1)',
            fill: true,
            tension: 0.4,
            pointRadius: 0
        }]
    };

    const yieldData = {
        labels: macro?.yields?.map(d => new Date(d.date).toLocaleDateString()) || [],
        datasets: [{
            label: '10Y Yield',
            data: macro?.yields?.map(d => d.value) || [],
            borderColor: '#58a6ff',
            backgroundColor: 'rgba(88, 166, 255, 0.1)',
            fill: true,
            tension: 0.4,
            pointRadius: 0
        }]
    };

    return (
        <div className="modal fade" id="chartsModal" tabIndex="-1" aria-hidden="true">
            <div className="modal-dialog modal-xl modal-dialog-scrollable">
                <div className="modal-content">
                    <div className="modal-header">
                        <h5 className="modal-title">Market Analytics Dashboard</h5>
                        <button type="button" className="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div className="modal-body bg-dark">
                        <div className="container-fluid">

                            {/* Row 1: Ranking Analysis */}
                            <div className="row g-3 mb-4">
                                <div className="col-md-4">
                                    <div className="card card-custom h-100 p-3 animate-in" style={{ animationDelay: '0.1s' }}>
                                        <h6 className="text-success">🇨🇱 Top 5 Cheapest (Annual)</h6>
                                        <div style={{ height: '200px' }}>
                                            <Bar data={cheapData} options={horizontalOptions} />
                                        </div>
                                        <AIInsight
                                            insight={analytics?.insight_cheap || macro?.insight_cheap || "Analyzing local efficiency..."}
                                            colorClass="text-success"
                                        />
                                    </div>
                                </div>
                                <div className="col-md-4">
                                    <div className="card card-custom h-100 p-3 animate-in" style={{ animationDelay: '0.2s' }}>
                                        <h6 className="text-danger">🇨🇱 Top 5 Most Expensive</h6>
                                        <div style={{ height: '200px' }}>
                                            <Bar data={expensiveData} options={horizontalOptions} />
                                        </div>
                                        <AIInsight
                                            insight={analytics?.insight_expensive || macro?.insight_expensive || "Analyzing cost premiums..."}
                                            colorClass="text-danger"
                                        />
                                    </div>
                                </div>
                                <div className="col-md-4">
                                    <div className="card card-custom h-100 p-3 animate-in" style={{ animationDelay: '0.3s' }}>
                                        <h6 className="text-info">🇨🇱 Cost Distribution</h6>
                                        <div style={{ height: '200px' }}>
                                            <Bar data={distData} options={commonOptions} />
                                        </div>
                                        <AIInsight
                                            insight={analytics?.insight_distribution || macro?.insight_distribution || "Analyzing market spread..."}
                                            colorClass="text-info"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Row 2: Macro Trends */}
                            <div className="row g-3">
                                <div className="col-md-6">
                                    <div className="card card-custom h-100 p-3 animate-in" style={{ animationDelay: '0.4s' }}>
                                        <h6>🇺🇸 US CPI Trend (Inflation)</h6>
                                        <div style={{ height: '250px' }}>
                                            <Line data={cpiData} options={commonOptions} />
                                        </div>
                                        <AIInsight
                                            insight={macro?.insight_cpi || "Tracking inflation impact..."}
                                            colorClass="text-danger"
                                        />
                                    </div>
                                </div>
                                <div className="col-md-6">
                                    <div className="card card-custom h-100 p-3 animate-in" style={{ animationDelay: '0.5s' }}>
                                        <h6>🇺🇸 US 10Y Treasury Yields</h6>
                                        <div style={{ height: '250px' }}>
                                            <Line data={yieldData} options={commonOptions} />
                                        </div>
                                        <AIInsight
                                            insight={macro?.insight_10y || "Monitoring risk-free rate..."}
                                            colorClass="text-primary"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Row 3: Commodities */}
                            <div className="row g-3 mt-3">
                                <div className="col-md-4">
                                    <div className="card card-custom h-100 p-3 animate-in" style={{ animationDelay: '0.6s' }}>
                                        <h6 className="text-warning">🥇 Gold Price</h6>
                                        <div style={{ height: '200px' }}>
                                            <Line data={{
                                                labels: macro?.gold?.map(d => new Date(d.date).toLocaleDateString()) || [],
                                                datasets: [{
                                                    label: 'Gold (USD)',
                                                    data: macro?.gold?.map(d => d.value) || [],
                                                    borderColor: '#bf8700',
                                                    backgroundColor: 'rgba(191, 135, 0, 0.1)',
                                                    fill: true,
                                                    tension: 0.4,
                                                    pointRadius: 0
                                                }]
                                            }} options={commonOptions} />
                                        </div>
                                        <AIInsight
                                            insight={macro?.insight_gold || "Evaluating safe-haven status..."}
                                            colorClass="text-warning"
                                        />
                                    </div>
                                </div>
                                <div className="col-md-4">
                                    <div className="card card-custom h-100 p-3 animate-in" style={{ animationDelay: '0.7s' }}>
                                        <h6 className="text-danger">⛏️ Copper</h6>
                                        <div style={{ height: '200px' }}>
                                            <Line data={{
                                                labels: macro?.copper?.map(d => new Date(d.date).toLocaleDateString()) || [],
                                                datasets: [{
                                                    label: 'Copper (USD)',
                                                    data: macro?.copper?.map(d => d.value) || [],
                                                    borderColor: '#da3633',
                                                    backgroundColor: 'rgba(218, 54, 51, 0.1)',
                                                    fill: true,
                                                    tension: 0.4,
                                                    pointRadius: 0
                                                }]
                                            }} options={commonOptions} />
                                        </div>
                                        <AIInsight
                                            insight={macro?.insight_copper || "Assessing export revenue..."}
                                            colorClass="text-danger"
                                        />
                                    </div>
                                </div>
                                <div className="col-md-4">
                                    <div className="card card-custom h-100 p-3 animate-in" style={{ animationDelay: '0.8s' }}>
                                        <h6 className="text-light">🛢️ WTI Oil</h6>
                                        <div style={{ height: '200px' }}>
                                            <Line data={{
                                                labels: macro?.oil?.map(d => new Date(d.date).toLocaleDateString()) || [],
                                                datasets: [{
                                                    label: 'Oil (USD)',
                                                    data: macro?.oil?.map(d => d.value) || [],
                                                    borderColor: '#c9d1d9',
                                                    backgroundColor: 'rgba(201, 209, 217, 0.1)',
                                                    fill: true,
                                                    tension: 0.4,
                                                    pointRadius: 0
                                                }]
                                            }} options={commonOptions} />
                                        </div>
                                        <AIInsight
                                            insight={macro?.insight_oil || "Checking energy costs..."}
                                            colorClass="text-light"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Row 4: Crypto (Separated) */}
                            <div className="row g-3 mt-3">
                                <div className="col-md-6">
                                    <div className="card card-custom h-100 p-3 animate-in" style={{ animationDelay: '0.9s' }}>
                                        <h6 className="text-warning">🪙 Bitcoin (CLP)</h6>
                                        <div style={{ height: '200px' }}>
                                            <Line data={{
                                                labels: macro?.btc?.map(d => new Date(d.date).toLocaleDateString()) || [],
                                                datasets: [{
                                                    label: 'BTC (CLP)',
                                                    data: macro?.btc?.map(d => d.value) || [],
                                                    borderColor: '#f2a900',
                                                    backgroundColor: 'rgba(242, 169, 0, 0.1)',
                                                    fill: true,
                                                    tension: 0.4,
                                                    pointRadius: 0
                                                }]
                                            }} options={commonOptions} />
                                        </div>
                                        <AIInsight
                                            insight={macro?.insight_crypto || "Scanning digital liquidity..."}
                                            colorClass="text-warning"
                                        />
                                    </div>
                                </div>
                                <div className="col-md-6">
                                    <div className="card card-custom h-100 p-3 animate-in" style={{ animationDelay: '1.0s' }}>
                                        <h6 className="text-primary">💠 Ethereum (CLP)</h6>
                                        <div style={{ height: '200px' }}>
                                            <Line data={{
                                                labels: macro?.eth?.map(d => new Date(d.date).toLocaleDateString()) || [],
                                                datasets: [{
                                                    label: 'ETH (CLP)',
                                                    data: macro?.eth?.map(d => d.value) || [],
                                                    borderColor: '#627eea',
                                                    backgroundColor: 'rgba(98, 126, 234, 0.1)',
                                                    fill: true,
                                                    tension: 0.4,
                                                    pointRadius: 0
                                                }]
                                            }} options={commonOptions} />
                                        </div>
                                        <AIInsight
                                            insight={macro?.insight_crypto || "Scanning digital liquidity..."}
                                            colorClass="text-primary"
                                        />
                                    </div>
                                </div>
                            </div>

                        </div>
                    </div>
                    <div className="modal-footer">
                        <small className="text-muted me-auto">*Data Sources: CMF Chile, BLS, US Treasury.</small>
                        <button type="button" className="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MarketDashboard;
