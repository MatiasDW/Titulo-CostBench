import React, { memo } from 'react';
import './AnimatedBackground.css';

const AnimatedBackground = () => {
    return (
        <div className="bg-container">
            {Array.from({ length: 15 }).map((_, i) => (
                <div
                    key={i}
                    className="particle"
                    style={{
                        left: `${Math.random() * 100}%`,
                        width: `${Math.random() * 8 + 4}px`,
                        height: `${Math.random() * 8 + 4}px`,
                        animationDelay: `${Math.random() * 10}s`,
                        animationDuration: `${Math.random() * 10 + 10}s`,
                    }}
                />
            ))}
        </div>
    );
};

export default memo(AnimatedBackground);
