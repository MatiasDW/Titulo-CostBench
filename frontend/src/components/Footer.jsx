import React from 'react';
import './Footer.css';

const Footer = () => {
    return (
        <footer className="footer-custom mt-5 pt-4 pb-4">
            <div className="container">
                <div className="row align-items-center">
                    <div className="col-md-6 text-center text-md-start mb-3 mb-md-0">
                        <h6 className="text-white fw-bold mb-1">CostBench</h6>
                        <small className="text-secondary d-block">Open Financial Data Initiative</small>
                        <small className="text-muted">Santiago, Chile • contact@costbench.cl</small>
                    </div>
                </div>

                <hr className="border-secondary opacity-25 my-4" />

                <div className="row g-3">
                    <div className="col-md-6">
                        <div className="fred-disclaimer p-3 rounded border border-danger border-opacity-25 bg-danger bg-opacity-10 h-100">
                            <div className="d-flex align-items-start">
                                <span className="fs-4 me-3">⚖️</span>
                                <div>
                                    <h6 className="text-uppercase fw-bold text-light mb-1" style={{ fontSize: '0.75rem', letterSpacing: '1px' }}>FRED® Data Disclaimer</h6>
                                    <p className="mb-0 text-secondary" style={{ fontSize: '0.7rem' }}>
                                        This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis.
                                        All data provided is for informational purposes only.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="col-md-6">
                        <div className="bcch-disclaimer p-3 rounded border border-info border-opacity-25 bg-info bg-opacity-10 h-100">
                            <div className="d-flex align-items-start">
                                <span className="fs-4 me-3">🏛️</span>
                                <div>
                                    <h6 className="text-uppercase fw-bold text-light mb-1" style={{ fontSize: '0.75rem', letterSpacing: '1px' }}>Banco Central de Chile</h6>
                                    <p className="mb-0 text-secondary" style={{ fontSize: '0.7rem' }}>
                                        Datos UF/USDCLP provistos por la Base de Datos Estadísticos (BDE) del Banco Central de Chile.
                                        Este producto no está respaldado ni certificado por el BCCh.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="text-center mt-4">
                    <small className="text-muted" style={{ fontSize: '0.7rem' }}>© 2025 CostBench. All rights reserved.</small>
                </div>
            </div>
        </footer>
    );
};

export default Footer;
