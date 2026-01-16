import React from 'react';
import Flag from 'react-world-flags';
import { FaChartLine, FaCoins, FaDollarSign, FaLandmark, FaOilCan } from 'react-icons/fa';
import { GiBrickPile, GiGoldBar } from 'react-icons/gi';
import { FiTrendingUp } from 'react-icons/fi';

// Inline SVG icons for cryptocurrencies (Vite-compatible alternative to react-crypto-icons)
const BtcIcon = ({ size = 18, color = '#f7931a' }) => (
    <svg viewBox="0 0 32 32" width={size} height={size} xmlns="http://www.w3.org/2000/svg">
        <circle cx="16" cy="16" r="16" fill={color} />
        <path fill="#fff" d="M22.5 14.4c.3-2-1.2-3.1-3.3-3.8l.7-2.7-1.6-.4-.6 2.6c-.4-.1-.9-.2-1.3-.3l.6-2.6-1.6-.4-.7 2.7c-.3-.1-.7-.2-1-.3v-.1l-2.3-.6-.4 1.7s1.2.3 1.2.3c.7.2.8.6.8 1l-.8 3.2c0 0 .1 0 .1 0l-.1 0-1.1 4.5c-.1.2-.3.5-.8.4 0 0-1.2-.3-1.2-.3l-.8 1.9 2.1.5c.4.1.8.2 1.2.3l-.7 2.7 1.6.4.7-2.7c.4.1.9.2 1.3.3l-.7 2.7 1.6.4.7-2.8c2.9.6 5.1.3 6-2.3.7-2.1 0-3.3-1.5-4.1 1.1-.3 1.9-1 2.1-2.5zm-3.8 5.3c-.5 2.1-4 1-5.1.7l.9-3.7c1.1.3 4.7.8 4.2 3zm.5-5.3c-.5 1.9-3.4.9-4.3.7l.8-3.3c1 .2 4 .7 3.5 2.6z" />
    </svg>
);

const EthIcon = ({ size = 18, color = '#627eea' }) => (
    <svg viewBox="0 0 32 32" width={size} height={size} xmlns="http://www.w3.org/2000/svg">
        <circle cx="16" cy="16" r="16" fill={color} />
        <g fill="#fff">
            <polygon fillOpacity=".6" points="16 5.5 16 13.1 22.5 16.1" />
            <polygon points="16 5.5 9.5 16.1 16 13.1" />
            <polygon fillOpacity=".6" points="16 21.9 16 26.5 22.5 17.4" />
            <polygon points="16 26.5 16 21.9 9.5 17.4" />
            <polygon fillOpacity=".2" points="16 20.6 22.5 16.1 16 13.1" />
            <polygon fillOpacity=".6" points="9.5 16.1 16 20.6 16 13.1" />
        </g>
    </svg>
);

const DEFAULT_COLORS = {
    gold: '#bf8700',
    copper: '#b87333',
    oil: '#c9d1d9',
    silver: '#c0c0c0',
    cpi: '#f78166',
    '10y': '#58a6ff',
    uf: '#8b5cf6',
    trend: '#8b949e'
};

const AssetIcon = ({ type, size = 18, color, className, style }) => {
    const classes = ['asset-icon', className].filter(Boolean).join(' ');
    const iconColor = color || DEFAULT_COLORS[type] || DEFAULT_COLORS.trend;
    const flagSize = Math.max(12, Math.round(size * 0.85));

    let content;
    switch (type) {
        case 'gold':
            content = <GiGoldBar size={size} color={iconColor} />;
            break;
        case 'copper':
            content = <GiBrickPile size={size} color={iconColor} />;
            break;
        case 'oil':
            content = <FaOilCan size={size} color={iconColor} />;
            break;
        case 'silver':
            content = <FaCoins size={size} color={iconColor} />;
            break;
        case 'btc':
            content = <BtcIcon size={size} />;
            break;
        case 'eth':
            content = <EthIcon size={size} />;
            break;
        case 'usd':
            content = <Flag code="US" height={flagSize} />;
            break;
        case 'clp':
            content = <Flag code="CL" height={flagSize} />;
            break;
        case 'usdclp':
            content = (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '2px' }}>
                    <Flag code="US" height={Math.max(10, Math.round(size * 0.7))} />
                    <Flag code="CL" height={Math.max(10, Math.round(size * 0.7))} />
                </span>
            );
            break;
        case 'uf':
            content = <FaDollarSign size={size} color={iconColor} />;
            break;
        case 'cpi':
            content = <FaChartLine size={size} color={iconColor} />;
            break;
        case '10y':
            content = <FaLandmark size={size} color={iconColor} />;
            break;
        default:
            content = <FiTrendingUp size={size} color={iconColor} />;
            break;
    }

    return (
        <span className={classes} style={style} aria-hidden="true">
            {content}
        </span>
    );
};

export default AssetIcon;
