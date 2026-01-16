import React from 'react';
import { FaUserTie } from 'react-icons/fa';

const AIInsight = ({ title, text, insight, colorClass = "text-muted" }) => {
    return (
        <div className="mt-2 pt-2 border-top border-secondary">
            <small className="text-light d-block fst-italic" style={{ fontSize: '0.75rem', opacity: 0.9 }}>
                <span className={colorClass}><FaUserTie style={{ marginRight: '4px', marginBottom: '2px' }} /> Scloda:</span> {insight || text}
            </small>
        </div>
    );
};

export default AIInsight;
