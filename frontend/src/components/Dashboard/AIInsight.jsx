import React from 'react';

const AIInsight = ({ title, text, insight, colorClass = "text-muted" }) => {
    return (
        <div className="mt-2 pt-2 border-top border-secondary">
            <small className="text-light d-block fst-italic" style={{ fontSize: '0.75rem', opacity: 0.9 }}>
                <span className={colorClass}>🧠 Scloda:</span> {insight || text}
            </small>
        </div>
    );
};

export default AIInsight;
