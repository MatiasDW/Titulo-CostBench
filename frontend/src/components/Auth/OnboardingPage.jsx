import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import {
    FaChartLine, FaRobot, FaBitcoin, FaBuilding,
    FaUserTie, FaArrowLeft, FaCheck
} from 'react-icons/fa';
import { GiGoldBar } from 'react-icons/gi';
import AnimatedBackground from '../AnimatedBackground';
import useSounds from '../../hooks/useSounds';
import './Onboarding.css';

const INTEREST_CARDS = [
    {
        id: 'banking_costs',
        icon: <FaChartLine size={28} />,
        title: 'Banking Cost Analysis',
        description: 'Compare and benchmark the true cost of Chilean banking products in real time.',
        color: '#58a6ff',
    },
    {
        id: 'market_forecasting',
        icon: <FaRobot size={28} />,
        title: 'Market Forecasting',
        description: 'ML-powered predictions using ARIMA models for financial time series.',
        color: '#238636',
    },
    {
        id: 'crypto_commodities',
        icon: <FaBitcoin size={28} />,
        title: 'Crypto & Commodities',
        description: 'Track Bitcoin, Ethereum, Gold, Copper, and Oil with live data feeds.',
        color: '#f7931a',
    },
    {
        id: 'real_estate',
        icon: <FaBuilding size={28} />,
        title: 'Real Estate & Mortgages',
        description: 'Housing market analytics, mortgage rate comparisons, and UF tracking.',
        color: '#bf8700',
    },
    {
        id: 'macro_indicators',
        icon: <GiGoldBar size={28} />,
        title: 'Macro Indicators',
        description: 'CPI, Treasury yields, and global macro data to understand the big picture.',
        color: '#627eea',
    },
];

const RISK_OPTIONS = [
    { value: 'conservative', label: 'Conservative', emoji: '🛡️', description: 'Low risk, stable returns. Prefer bonds and savings.' },
    { value: 'moderate', label: 'Moderate', emoji: '⚖️', description: 'Balanced risk-reward. Mix of growth and stability.' },
    { value: 'aggressive', label: 'Aggressive', emoji: '🔥', description: 'High risk, high reward. Growth-focused investments.' },
];

const OnboardingPage = () => {
    const { completeOnboarding } = useAuth();
    const navigate = useNavigate();

    const [step, setStep] = useState(1);
    const [selectedInterests, setSelectedInterests] = useState([]);
    const [selectedRisk, setSelectedRisk] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { playSelect, playDeselect, playClick, playNav, playSuccess } = useSounds();

    const toggleInterest = (id) => {
        const isSelected = selectedInterests.includes(id);
        isSelected ? playDeselect() : playSelect();
        setSelectedInterests(prev =>
            isSelected ? prev.filter(i => i !== id) : [...prev, id]
        );
    };

    const goHome = () => navigate('/home', { replace: true });

    const handleFinish = async () => {
        setIsLoading(true);
        try {
            await completeOnboarding(selectedInterests, selectedRisk || undefined);
            playSuccess();
        } catch (err) {
            console.error('Onboarding save error:', err);
        }
        // Always go home, even if save failed
        goHome();
    };

    return (
        <div className="onboarding-page">
            <AnimatedBackground />

            <motion.div
                className="onboarding-container"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
            >
                <motion.div
                    className="onboarding-mascot"
                    animate={{ y: [0, -8, 0] }}
                    transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
                >
                    <FaUserTie size={40} />
                </motion.div>

                {step === 1 ? (
                    <>
                        <h2 className="onboarding-title">What brings you to CostBench?</h2>
                        <p className="onboarding-subtitle">
                            Select all that interest you — we'll personalize your experience
                        </p>

                        <div className="onboarding-grid">
                            {INTEREST_CARDS.map((card) => {
                                const isSelected = selectedInterests.includes(card.id);
                                return (
                                    <motion.button
                                        key={card.id}
                                        className={`onboarding-card ${isSelected ? 'selected' : ''}`}
                                        onClick={() => toggleInterest(card.id)}
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                        style={{ '--card-accent': card.color }}
                                    >
                                        <div className="onboarding-card-icon" style={{ color: card.color }}>
                                            {card.icon}
                                        </div>
                                        <div className="onboarding-card-check">
                                            {isSelected && <FaCheck size={12} />}
                                        </div>
                                        <h4 className="onboarding-card-title">{card.title}</h4>
                                        <p className="onboarding-card-desc">{card.description}</p>
                                    </motion.button>
                                );
                            })}
                        </div>

                        <div className="onboarding-actions">
                            <button className="onboarding-skip" onClick={goHome}>
                                Skip for now →
                            </button>
                            <motion.button
                                className="onboarding-next"
                                onClick={() => setStep(2)}
                                disabled={selectedInterests.length === 0}
                                whileHover={{ scale: 1.03 }}
                                whileTap={{ scale: 0.97 }}
                            >
                                Next →
                            </motion.button>
                        </div>
                    </>
                ) : (
                    <>
                        <h2 className="onboarding-title">What's your risk tolerance?</h2>
                        <p className="onboarding-subtitle">
                            This helps Scloda tailor analysis and recommendations to you
                        </p>

                        <div className="onboarding-risk-grid">
                            {RISK_OPTIONS.map((opt) => {
                                const isSelected = selectedRisk === opt.value;
                                return (
                                    <motion.button
                                        key={opt.value}
                                        className={`onboarding-risk-card ${isSelected ? 'selected' : ''}`}
                                        onClick={() => setSelectedRisk(opt.value)}
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                    >
                                        <span className="onboarding-risk-emoji">{opt.emoji}</span>
                                        <h4>{opt.label}</h4>
                                        <p>{opt.description}</p>
                                    </motion.button>
                                );
                            })}
                        </div>

                        <div className="onboarding-actions">
                            <button className="onboarding-back" onClick={() => setStep(1)}>
                                <FaArrowLeft size={12} /> Back
                            </button>
                            <motion.button
                                className="onboarding-finish"
                                onClick={handleFinish}
                                disabled={isLoading}
                                whileHover={{ scale: 1.03 }}
                                whileTap={{ scale: 0.97 }}
                            >
                                {isLoading ? 'Saving...' : 'Get Started'} <FaCheck size={14} />
                            </motion.button>
                        </div>

                        <button className="onboarding-skip" onClick={goHome}>
                            Skip for now →
                        </button>
                    </>
                )}
            </motion.div>
        </div>
    );
};

export default OnboardingPage;
