import React, { useState, useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';
import { FaArrowUp, FaArrowDown, FaPlay, FaSpinner, FaUserTie, FaInfoCircle, FaBuilding } from 'react-icons/fa';

const RealEstatePage = () => {
    // ---- STATE ----
    const [metrics, setMetrics] = useState([]);
    const [currentUf, setCurrentUf] = useState(null);
    const [loadingMetrics, setLoadingMetrics] = useState(true);
    const [error, setError] = useState(null);

    const [hoveredCard, setHoveredCard] = useState(null);

    // Simulation State
    const [selectedComuna, setSelectedComuna] = useState(null);
    const [pieUf, setPieUf] = useState(2000);
    const [plazoAnios, setPlazoAnios] = useState(20);
    const [simulating, setSimulating] = useState(false);

    // Simulation Results
    const [chartData, setChartData] = useState([]);
    const [sclodaAdvice, setSclodaAdvice] = useState('');
    const [simSummary, setSimSummary] = useState(null);

    const chartContainerRef = useRef(null);
    const chartInstanceRef = useRef(null);

    // ---- EFFECT: Fetch Initial Metrics ----
    useEffect(() => {
        const fetchMetrics = async () => {
            try {
                const response = await fetch('/api/v1/real-estate/metrics');
                const data = await response.json();
                if (data.status === 'success') {
                    // Sort descending by UF/m2 just for display
                    const sorted = data.metrics.sort((a, b) => b.uf_m2 - a.uf_m2);
                    setMetrics(sorted);
                    setCurrentUf(data.current_uf);
                    if (sorted.length > 0) setSelectedComuna(sorted[0].comuna);
                } else {
                    setError(data.message || 'Failed to fetch metrics');
                }
            } catch (err) {
                setError('Network error fetching metrics');
            } finally {
                setLoadingMetrics(false);
            }
        };

        fetchMetrics();
    }, []);

    // ---- EFFECT: Handle Lightweight Charts Render ----
    useEffect(() => {
        if (!chartContainerRef.current || chartData.length === 0) return;

        // Cleanup previous instance
        if (chartInstanceRef.current) {
            chartInstanceRef.current.remove();
        }

        const chart = createChart(chartContainerRef.current, {
            width: chartContainerRef.current.clientWidth,
            height: 300,
            layout: {
                background: { type: 'solid', color: '#161b22' },
                textColor: '#c9d1d9',
            },
            grid: {
                vertLines: { color: '#2a2f38' },
                horzLines: { color: '#2a2f38' },
            },
            timeScale: {
                timeVisible: false,
                borderVisible: false,
            },
            rightPriceScale: {
                borderVisible: false,
            },
        });

        // Add Cost (Dividendo) Line
        const costSeries = chart.addLineSeries({
            color: '#f85149',
            lineWidth: 2,
            title: 'Mortgage (CLP)',
        });

        // Add Yield (Renta Neta) Line
        const yieldSeries = chart.addLineSeries({
            color: '#2ea043',
            lineWidth: 2,
            title: 'Net Rent (CLP)',
        });

        const baseDate = new Date('2026-01-01');
        const sequentialCost = chartData.map((d, i) => {
            const date = new Date(baseDate);
            date.setMonth(baseDate.getMonth() + i);
            return { time: date.toISOString().split('T')[0], value: d.dividendo_clp };
        });
        const sequentialYield = chartData.map((d, i) => {
            const date = new Date(baseDate);
            date.setMonth(baseDate.getMonth() + i);
            return { time: date.toISOString().split('T')[0], value: d.renta_neta_clp };
        });

        costSeries.setData(sequentialCost);
        yieldSeries.setData(sequentialYield);

        chart.timeScale().fitContent();
        chartInstanceRef.current = chart;

        // Handle Resize
        const handleResize = () => {
            if (chartContainerRef.current && chartInstanceRef.current) {
                chartInstanceRef.current.applyOptions({
                    width: chartContainerRef.current.clientWidth,
                });
            }
        };
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            if (chartInstanceRef.current) {
                chartInstanceRef.current.remove();
                chartInstanceRef.current = null;
            }
        };
    }, [chartData]);


    // ---- HANDLERS ----
    const handleSimulate = async () => {
        if (!selectedComuna) return;

        setSimulating(true);
        setError(null);

        try {
            const response = await fetch('/api/v1/real-estate/simulate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    comuna: selectedComuna,
                    pie_uf: pieUf,
                    plazo_anios: plazoAnios
                })
            });

            const data = await response.json();

            if (data.status === 'success') {
                setChartData(data.chart_data);
                setSclodaAdvice(data.scloda_advice);
                setSimSummary({
                    total_uf: data.total_uf,
                    loan_uf: data.loan_uf,
                    monthly_dividend_uf: data.monthly_dividend_uf,
                    monthly_rent_uf: data.monthly_rent_uf
                });
            } else {
                setError(data.message || 'Simulation failed');
            }
        } catch (err) {
            setError('Network error during simulation');
        } finally {
            setSimulating(false);
        }
    };

    // ---- RENDERERS ----
    if (loadingMetrics) {
        return (
            <div className="d-flex justify-content-center align-items-center vh-100">
                <FaSpinner className="fa-spin text-primary fs-1" />
            </div>
        );
    }

    return (
        <div className="container-fluid p-4" style={{ backgroundColor: '#0d1117', minHeight: '100vh', color: '#c9d1d9' }}>
            <div className="d-flex align-items-center mb-4 pb-2" style={{ borderBottom: '1px solid #30363d' }}>
                <div className="d-flex align-items-center justify-content-center me-3 flex-shrink-0" style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(56, 139, 253, 0.1)', color: '#388bfd', marginLeft: '20px' }}>
                    <FaBuilding size={18} />
                </div>
                <h2 className="mb-0 text-white fw-bold">Real Estate Quant Dashboard</h2>
                {currentUf && (
                    <span className="ms-auto badge bg-dark border border-secondary text-info fs-6">
                        Current UF: ${currentUf.toLocaleString('en-US')}
                    </span>
                )}
            </div>

            {error && (
                <div className="alert alert-danger" style={{ backgroundColor: '#3d1619', borderColor: '#e5534b', color: '#ff7b72' }}>
                    {error}
                </div>
            )}

            {/* TOP BAR: MARKET SNAPSHOT CARDS */}
            <div className="row g-3 mb-4">
                {metrics.map((m, idx) => (
                    <div key={idx} className="col position-relative">
                        <div
                            className={`card h-100 p-3 shadow-sm border ${selectedComuna === m.comuna ? 'border-primary' : 'border-secondary'}`}
                            style={{ backgroundColor: selectedComuna === m.comuna ? '#1f2937' : '#161b22', cursor: 'pointer', transition: '0.2s' }}
                            onClick={() => setSelectedComuna(m.comuna)}
                            onMouseEnter={() => setHoveredCard(idx)}
                            onMouseLeave={() => setHoveredCard(null)}
                        >
                            <div className="d-flex justify-content-between align-items-center mb-1">
                                <h6 className="text-light fw-bold mb-0 text-uppercase" style={{ fontSize: '0.80rem', letterSpacing: '0.5px' }}>{m.comuna}</h6>
                                <span className="text-secondary cursor-help" style={{ fontSize: '0.7rem' }}>ℹ️</span>
                            </div>
                            <div className="d-flex align-items-center justify-content-between mt-2">
                                <h4 className="text-white mb-0 fw-bold">{Math.round(m.uf_m2)} <span style={{ fontSize: '0.8rem', color: '#8b949e', fontWeight: 'normal' }}>UF/m²</span></h4>
                                {m.net_cap_rate > 0.025 ?
                                    <FaArrowUp className="text-success" /> :
                                    <FaArrowDown className="text-danger" />
                                }
                            </div>
                        </div>

                        {/* Custom Animated Tooltip */}
                        {hoveredCard === idx && (
                            <div
                                className="position-absolute z-3 p-3 rounded border border-primary text-light"
                                style={{
                                    backgroundColor: '#0d1117',
                                    top: '100%',
                                    left: '50%',
                                    transform: 'translateX(-50%)',
                                    marginTop: '8px',
                                    width: '280px',
                                    boxShadow: '0 8px 16px rgba(0,0,0,0.8)',
                                    fontSize: '0.8rem',
                                    zIndex: 1000
                                }}
                            >
                                <div className="d-flex align-items-center mb-2">
                                    <div className="d-flex align-items-center justify-content-center me-2 flex-shrink-0" style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'linear-gradient(135deg, #38a169, #2d7d54)', color: 'white' }}>
                                        <FaUserTie size={14} />
                                    </div>
                                    <strong className="text-primary">Scloda Insight</strong>
                                </div>
                                <p className="mb-2 text-light" style={{ lineHeight: '1.4' }}>
                                    With a <strong>Net Yield</strong> of <span className="text-success fw-bold">{(m.net_cap_rate * 100).toFixed(1)}%</span> and taking <strong className="text-warning">{m.days_on_market} days</strong> to rent, this commune is <strong>{m.net_cap_rate > 0.045 ? "highly profitable for rapid cash flow" : m.vacancy_rate < 0.05 ? "a safe haven for capital preservation" : "speculative, requiring careful tenant screening"}</strong>.
                                </p>
                                <p className="mb-0 text-light border-top border-secondary pt-2" style={{ fontSize: '0.75rem', opacity: 0.85 }}>
                                    <em>Tip: Compare this yield vs. the mortgage rate in the Simulator.</em>
                                </p>
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* GENERAL SCLODA CONTEXT */}
            <div className="alert border-secondary rounded mb-4 d-flex align-items-start" style={{ backgroundColor: '#1c2128', color: '#c9d1d9' }}>
                <div className="d-flex align-items-center justify-content-center mt-1 me-3 flex-shrink-0" style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'linear-gradient(135deg, #38a169, #2d7d54)', color: 'white' }}>
                    <FaUserTie size={16} />
                </div>
                <div>
                    <h6 className="text-white fw-bold mb-1" style={{ fontSize: '0.9rem' }}>Scloda's Take: How to read this Dashboard?</h6>
                    <p className="mb-0" style={{ fontSize: '0.85rem' }}>
                        The top cards show the average <strong>UF per square meter</strong> in the most sought-after communes.
                        Hover over the ℹ️ icon on any card to reveal my real-time analysis on <strong>Vacancy Risk</strong> and <strong>Net Yield</strong>.
                    </p>
                    <hr style={{ borderColor: '#30363d', margin: '8px 0' }} />
                    <p className="mb-0 text-light" style={{ fontSize: '0.8rem', opacity: 0.9 }}>
                        Below on the left is the <strong>Quant Matrix</strong>. Click on any commune you want to evaluate to load the <strong className="text-white">ARIMAX Simulator</strong> on the right. This engine uses Autoregressive Integrated Moving Average (ARIMA) models enriched with Exogenous variables (X) like Inflation and the Central Bank Interest Rate. It mathematically projects if your monthly rental income will be able to sustain your mortgage payments over the next 24 months, predicting cash flow bottlenecks before you buy.
                    </p>
                </div>
            </div>

            {/* MAIN GRID: MATRIX vs SIMULATOR */}
            <div className="row g-4">
                {/* LEFT COL: THE QUANT MATRIX */}
                <div className="col-lg-7 d-flex flex-column">
                    <div className="card w-100 border-secondary d-flex flex-column" style={{ backgroundColor: '#161b22' }}>
                        <div className="card-header border-secondary" style={{ backgroundColor: '#21262d' }}>
                            <h5 className="mb-0 text-light fw-bold">The Quant Matrix</h5>
                        </div>
                        <div className="card-body p-0 table-responsive flex-grow-1">
                            <table className="table table-dark table-hover mb-0 h-100" style={{ fontSize: '0.9rem' }}>
                                <thead style={{ borderBottom: '2px solid #30363d' }}>
                                    <tr>
                                        <th className="py-3 px-3">Commune</th>
                                        <th className="py-3">Segment</th>
                                        <th className="py-3 text-end">UF/m²</th>
                                        <th className="py-3 text-end">Net Cap Rate</th>
                                        <th className="py-3 text-end">Vacancy</th>
                                        <th className="py-3 text-end px-3">Days on Market</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {metrics.map((m, idx) => (
                                        <tr
                                            key={idx}
                                            onClick={() => setSelectedComuna(m.comuna)}
                                            style={{ cursor: 'pointer', backgroundColor: selectedComuna === m.comuna ? '#2a2f38' : 'transparent' }}
                                        >
                                            <td className="py-3 px-3 fw-bold text-light">{m.comuna}</td>
                                            <td className="py-3"><span className="badge bg-dark border border-secondary">{m.segment_type}</span></td>
                                            <td className="py-3 text-end text-info">{m.uf_m2}</td>
                                            <td className="py-3 text-end text-success">{(m.net_cap_rate * 100).toFixed(1)}%</td>
                                            <td className="py-3 text-end text-warning">{(m.vacancy_rate * 100).toFixed(1)}%</td>
                                            <td className="py-3 text-end px-3">{m.days_on_market}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* SCLODA MATRIX EXPLANATION */}
                    <div className="alert border-secondary rounded mt-3 d-flex align-items-start" style={{ backgroundColor: '#1c2128', color: '#8b949e', padding: '12px' }}>
                        <div className="d-flex align-items-center justify-content-center mt-1 me-3 flex-shrink-0" style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'linear-gradient(135deg, #38a169, #2d7d54)', color: 'white', opacity: 0.8 }}>
                            <FaUserTie size={14} />
                        </div>
                        <div style={{ fontSize: '0.8rem' }}>
                            <strong className="text-light mb-2 d-block">Matrix Definitions:</strong>
                            <ul className="mb-0 ps-3">
                                <li className="mb-1"><strong className="text-white">Net Cap Rate:</strong> Your guaranteed annual return. It's the expected yearly rental income minus operating expenses, divided by the property's total price.</li>
                                <li className="mb-1"><strong className="text-white">Vacancy:</strong> The estimated percentage of the year the property will sit empty, directly impacting your cash flow.</li>
                                <li><strong className="text-white">Days on Market:</strong> The average time it takes to sign a lease based on current macroeconomic liquidity.</li>
                            </ul>
                        </div>
                    </div>
                </div>

                {/* RIGHT COL: ARIMAX SIMULATOR & RAG */}
                <div className="col-lg-5 d-flex align-items-stretch">
                    <div className="card w-100 border-secondary d-flex flex-column" style={{ backgroundColor: '#161b22' }}>
                        <div className="card-header border-secondary d-flex justify-content-between align-items-center" style={{ backgroundColor: '#21262d' }}>
                            <h5 className="mb-0 text-light fw-bold">ARIMAX Simulator</h5>
                            <span className="badge bg-primary px-3 py-2">{selectedComuna || 'Select Commune'}</span>
                        </div>

                        <div className="card-body">
                            {/* Simulator Instructions */}
                            <div className="mb-4 p-3 rounded" style={{ backgroundColor: '#1c2128', borderLeft: '4px solid #388bfd' }}>
                                <p className="text-light mb-1" style={{ fontSize: '0.85rem' }}>
                                    Adjust the <strong>Down Payment</strong> and <strong>Term</strong> below. I will simulate your expected 24-month cash flow by comparing the underlying mortgage cost with the mathematical net yield of the selected property.
                                </p>
                            </div>

                            {/* Controls */}
                            <div className="row g-3 mb-4">
                                <div className="col-6">
                                    <label className="form-label text-light small fw-bold mb-1 d-flex align-items-center">
                                        Down Payment (UF) <FaInfoCircle className="ms-2 text-secondary" title="Amount of equity paid upfront to lower the loan" />
                                    </label>
                                    <input
                                        type="number"
                                        className="form-control bg-dark text-light border-secondary focus-ring focus-ring-primary"
                                        value={pieUf}
                                        onChange={(e) => setPieUf(Number(e.target.value))}
                                        min="0"
                                    />
                                </div>
                                <div className="col-6">
                                    <label className="form-label text-light small fw-bold mb-1 d-flex align-items-center">
                                        Term (Years) <FaInfoCircle className="ms-2 text-secondary" title="Length of the mortgage loan" />
                                    </label>
                                    <select
                                        className="form-select bg-dark text-light border-secondary focus-ring focus-ring-primary"
                                        value={plazoAnios}
                                        onChange={(e) => setPlazoAnios(Number(e.target.value))}
                                    >
                                        <option value={15}>15 Years</option>
                                        <option value={20}>20 Years</option>
                                        <option value={25}>25 Years</option>
                                        <option value={30}>30 Years</option>
                                    </select>
                                </div>
                                <div className="col-12 mt-3">
                                    <button
                                        className="btn btn-primary w-100 fw-bold d-flex align-items-center justify-content-center p-2"
                                        onClick={handleSimulate}
                                        disabled={simulating || !selectedComuna}
                                    >
                                        {simulating ? (
                                            <><FaSpinner className="fa-spin me-2" /> Running Model...</>
                                        ) : (
                                            <><FaPlay className="me-2" /> Run Quant Simulation</>
                                        )}
                                    </button>
                                </div>
                            </div>

                            {/* Predictive Chart */}
                            {chartData.length > 0 ? (
                                <div className="mb-4">
                                    <div className="d-flex justify-content-between mb-2">
                                        <h6 className="text-muted mb-0" style={{ fontSize: '0.8rem' }}>24-Month Projection (CLP)</h6>
                                        <div className="d-flex gap-3" style={{ fontSize: '0.75rem' }}>
                                            <span className="text-danger fw-bold">● Mortgage (- Cost)</span>
                                            <span className="text-success fw-bold">● Net Rent (+ Flow)</span>
                                        </div>
                                    </div>
                                    <div
                                        ref={chartContainerRef}
                                        className="rounded border border-secondary"
                                        style={{ height: '300px', overflow: 'hidden' }}
                                    />

                                    {/* Simulation Summary Mini-Stats */}
                                    {simSummary && (
                                        <div className="row text-center mt-3 g-2">
                                            <div className="col-4">
                                                <div className="p-2 rounded bg-dark border border-secondary">
                                                    <div className="text-muted" style={{ fontSize: '0.7rem' }}>Property Price</div>
                                                    <div className="text-info fw-bold">{simSummary.total_uf} UF</div>
                                                </div>
                                            </div>
                                            <div className="col-4">
                                                <div className="p-2 rounded bg-dark border border-secondary">
                                                    <div className="text-muted" style={{ fontSize: '0.7rem' }}>Monthly Mortgage</div>
                                                    <div className="text-danger fw-bold">{simSummary.monthly_dividend_uf} UF</div>
                                                </div>
                                            </div>
                                            <div className="col-4">
                                                <div className="p-2 rounded bg-dark border border-secondary">
                                                    <div className="text-muted" style={{ fontSize: '0.7rem' }}>Expected Rent</div>
                                                    <div className="text-success fw-bold">{simSummary.monthly_rent_uf} UF</div>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="d-flex flex-column justify-content-center align-items-center text-center p-4 rounded border border-secondary mb-4" style={{ height: '300px', backgroundColor: '#0d1117' }}>
                                    <FaUserTie className="text-secondary mb-3" size={40} opacity={0.5} />
                                    <h6 className="text-light fw-bold">No Simulation Running</h6>
                                    <p className="text-muted small w-75 mb-0">
                                        Select a commune from the Matrix, adjust your mortgage terms, and click "Run Quant Simulation" to see the expected 24-month return vs cost.
                                    </p>
                                </div>
                            )}

                            {/* Scloda Advice Panel */}
                            {sclodaAdvice && (
                                <div className="card border-primary mt-4" style={{ backgroundColor: 'rgba(56, 139, 253, 0.05)' }}>
                                    <div className="card-body p-3">
                                        <div className="d-flex align-items-center mb-2">
                                            <div className="d-flex align-items-center justify-content-center me-2 flex-shrink-0" style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'linear-gradient(135deg, #38a169, #2d7d54)', color: 'white' }}>
                                                <FaUserTie size={14} />
                                            </div>
                                            <h6 className="mb-0 text-primary fw-bold">Scloda Intelligence</h6>
                                            <span className="ms-auto badge bg-primary" style={{ fontSize: '0.6rem' }}>RAG Insights</span>
                                        </div>
                                        <div className="text-light" style={{ fontSize: '0.85rem', lineHeight: '1.5' }}>
                                            {sclodaAdvice.split('\n').map((paragraph, index) => (
                                                <p key={index} className="mb-2">{paragraph}</p>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div >
    );
};

export default RealEstatePage;
