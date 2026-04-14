import React from 'react';
import { FaUserTie } from 'react-icons/fa';

const AIInsight = ({ text, insight, colorClass = "text-muted" }) => {
    const display = insight || text || "Analizando datos recientes...";
    return (
        <div
            className="mt-3 p-2"
            style={{
                borderRadius: '12px',
                background: 'linear-gradient(135deg, rgba(56,161,105,0.18), rgba(56,189,248,0.08))',
                border: '1px solid rgba(88,166,255,0.25)',
                boxShadow: '0 8px 18px rgba(0,0,0,0.25)',
            }}
        >
            <div className="d-flex align-items-start">
                <div
                    style={{
                        width: 28, height: 28,
                        borderRadius: '50%',
                        background: 'rgba(88,166,255,0.15)',
                        display: 'grid',
                        placeItems: 'center',
                        marginRight: 10
                    }}
                >
                    <FaUserTie size={14} color="#58a6ff" />
                </div>
                <div>
                    <div
                        style={{
                            fontSize: '0.7rem',
                            letterSpacing: '0.3px',
                            textTransform: 'uppercase',
                            color: '#58a6ff',
                            marginBottom: 2,
                            fontWeight: 700
                        }}
                    >
                        Scloda Insight
                    </div>
                    <div
                        className={`fw-semibold ${colorClass}`}
                        style={{ fontSize: '0.85rem', lineHeight: 1.35, color: '#e6edf3' }}
                    >
                        {display}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AIInsight;
