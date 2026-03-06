import React from 'react';
import { FaUserTie } from 'react-icons/fa';

const Header = ({ onOpenDashboard }) => {
    return (
        <div className="row align-items-center mb-5 border-bottom border-secondary pb-4">
            <div className="col-lg-5 text-start" style={{ paddingLeft: '55px' }}> {/* Clear sidebar toggle button */}
                {/* Logo stored in frontend/public/img, accessed via root relative path */}
                <img
                    src="/img/costbench_logo.svg"
                    alt="CostBench"
                    width="280"
                    className="mb-3 mb-lg-0 floating-logo" // Energy animation
                />
            </div>
            <div className="col-lg-7 text-lg-end">
                <div className="d-flex flex-column align-items-end justify-content-center h-100">
                    <h5 className="text-light mb-1 fw-light fst-italic" style={{ letterSpacing: '0.5px' }}>
                        "Empowering smarter financial decisions through ML-driven market intelligence and real-time macro analysis."
                    </h5>
                    <p className="text-secondary mb-0 fw-light">
                        Chile's commodities, currencies, and crypto — tracked, modeled, and explained by AI.
                    </p>

                    <button
                        className="btn btn-warning mt-3 px-4 py-2"
                        data-bs-toggle="modal"
                        data-bs-target="#chartsModal"
                        style={{
                            fontWeight: '600',
                            boxShadow: '0 0 20px rgba(255, 193, 7, 0.4)',
                            border: '2px solid rgba(255, 193, 7, 0.6)',
                        }}
                    >
                        <FaUserTie style={{ marginRight: '6px', marginBottom: '2px' }} /> Scloda's Analysis
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Header;
