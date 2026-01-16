import React from 'react';

const Header = ({ onOpenDashboard }) => {
    return (
        <div className="row align-items-center mb-5 border-bottom border-secondary pb-4">
            <div className="col-lg-5 text-start ps-0"> {/* Strictly align left, remove padding */}
                {/* Logo stored in frontend/public/img, accessed via root relative path */}
                <img
                    src="/img/costbench_logo.svg"
                    alt="CostBench"
                    width="280"
                    className="mb-3 mb-lg-0 floating-logo" // Energy animation
                    style={{ marginLeft: '-15px' }} // Negative margin to align with container edge if needed
                />
            </div>
            <div className="col-lg-7 text-lg-end">
                <div className="d-flex flex-column align-items-end justify-content-center h-100">
                    <h5 className="text-light mb-1 fw-light fst-italic" style={{ letterSpacing: '0.5px' }}>
                        "To allow anyone to understand the true cost of banking products through transparent, data-driven benchmarking."
                    </h5>
                    <p className="text-secondary mb-0 fw-light">
                        A financial market where efficiency is transparent and aligned with global macro reality.
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
                        🧠 Scloda's Analysis
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Header;
