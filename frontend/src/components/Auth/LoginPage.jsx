import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import {
    FaEnvelope, FaLock, FaUserTie, FaTimes,
    FaBitcoin, FaShieldAlt, FaLandmark, FaKey,
    FaChartLine, FaUserShield
} from 'react-icons/fa';
import { GiGoldBar, GiHouse, GiModernCity, GiFarmTractor } from 'react-icons/gi';
import AnimatedBackground from '../AnimatedBackground';
import useSounds from '../../hooks/useSounds';
import SignUpModal from './SignUpModal';
import './Auth.css';

// Floating icons for the auth background
const AUTH_FLOATING_ICONS = [
    { Icon: FaBitcoin, color: '#f7931a', size: 32 },
    { Icon: GiGoldBar, color: '#ffd700', size: 34 },
    { Icon: GiHouse, color: '#58a6ff', size: 36 },
    { Icon: GiModernCity, color: '#8b949e', size: 38 },
    { Icon: GiFarmTractor, color: '#238636', size: 30 },
    { Icon: FaShieldAlt, color: '#bf8700', size: 28 },
    { Icon: FaKey, color: '#f78166', size: 24 },
    { Icon: FaLandmark, color: '#627eea', size: 30 },
    { Icon: FaUserShield, color: '#da3633', size: 26 },
    { Icon: FaUserTie, color: '#ffc107', size: 26 },
    { Icon: FaChartLine, color: '#238636', size: 28 },
    { Icon: FaBitcoin, color: '#f7931a', size: 22 },
    { Icon: GiHouse, color: '#58a6ff', size: 28 },
    { Icon: FaShieldAlt, color: '#627eea', size: 32 },
];

const LoginPage = () => {
    const { login, user, loading } = useAuth();
    const navigate = useNavigate();

    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [showWelcome, setShowWelcome] = useState(true);
    const [showSignUp, setShowSignUp] = useState(false);
    const { playLogin, playError } = useSounds();

    const handleWelcomeCloseToLanding = () => {
        setShowWelcome(false);
        navigate('/landing', { replace: true });
    };

    // Redirect only if user was ALREADY authenticated when visiting /login
    React.useEffect(() => {
        if (!loading && user && !showSignUp) {
            navigate('/home', { replace: true });
        }
    }, [loading, user, showSignUp, navigate]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            await login(email, password);
            playLogin();
            navigate('/home', { replace: true });
        } catch (err) {
            const msg = err.response?.data?.error || 'Connection error. Please try again.';
            playError();
            setError(msg);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <AnimatedBackground />

            {/* Floating themed icons */}
            <div className="auth-floating-icons">
                {AUTH_FLOATING_ICONS.map(({ Icon, color, size }, i) => (
                    <motion.div
                        key={`auth-icon-${i}`}
                        className="auth-float-icon"
                        initial={{
                            x: ((i * 120) + Math.random() * 100) % (typeof window !== 'undefined' ? window.innerWidth : 1400),
                            y: (typeof window !== 'undefined' ? window.innerHeight : 900) + 60 + Math.random() * 200,
                            opacity: 0,
                            rotate: Math.random() * 40 - 20,
                        }}
                        animate={{
                            y: -150,
                            opacity: [0, 0.2, 0.2, 0],
                            rotate: [null, Math.random() * 20 - 10],
                        }}
                        transition={{
                            duration: 14 + Math.random() * 10,
                            repeat: Infinity,
                            delay: Math.random() * 12,
                            ease: 'linear',
                        }}
                    >
                        <Icon size={size} color={color} />
                    </motion.div>
                ))}
            </div>

            {/* Scloda Welcome Modal */}
            <AnimatePresence>
                {showWelcome && (
                    <motion.div
                        className="scloda-welcome-overlay"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        onClick={() => setShowWelcome(false)}
                    >
                        <motion.div
                            className="scloda-welcome-modal"
                            initial={{ opacity: 0, y: 30, scale: 0.9 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 20, scale: 0.95 }}
                            transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
                            onClick={(e) => e.stopPropagation()}
                        >
                            <button className="scloda-welcome-close" onClick={handleWelcomeCloseToLanding}>
                                <FaTimes size={14} />
                            </button>

                            <motion.div
                                className="scloda-welcome-avatar"
                                animate={{ y: [0, -6, 0] }}
                                transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
                            >
                                <FaUserTie size={32} />
                            </motion.div>

                            <h3 className="scloda-welcome-title">Hey there! I'm Scloda 👋</h3>

                            <p className="scloda-welcome-text">
                                Welcome to <strong>CostBench</strong>, the platform that helps you understand
                                the true cost of Chilean banking products through transparent,
                                data-driven benchmarking.
                            </p>
                            <p className="scloda-welcome-text">
                                📊 Compare banking costs in real-time<br />
                                🤖 ML models predict market trends<br />
                                💬 I'm your AI financial analyst — ask me anything
                            </p>

                            <motion.button
                                className="scloda-welcome-btn"
                                onClick={() => setShowWelcome(false)}
                                whileHover={{ scale: 1.03 }}
                                whileTap={{ scale: 0.97 }}
                            >
                                Got it, let's go!
                            </motion.button>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Login Card */}
            <motion.div
                className="auth-card"
                initial={{ opacity: 0, y: 40, scale: 0.92 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
            >
                <motion.div
                    className="auth-logo"
                    animate={{ y: [0, -6, 0] }}
                    transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
                >
                    <img src="/img/costbench_logo.svg" alt="CostBench" className="auth-logo-img" />
                </motion.div>

                <motion.p className="auth-subtitle" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}>
                    Sign in to your account
                </motion.p>

                {error && (
                    <motion.div className="auth-error" role="alert" initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}>
                        {error}
                    </motion.div>
                )}

                <form onSubmit={handleSubmit} className="auth-form">
                    <motion.div className="auth-field" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 }}>
                        <FaEnvelope className="auth-field-icon" />
                        <input id="login-email" type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" disabled={isLoading} />
                    </motion.div>

                    <motion.div className="auth-field" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.5 }}>
                        <FaLock className="auth-field-icon" />
                        <input id="login-password" type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" disabled={isLoading} />
                    </motion.div>

                    <motion.button id="login-submit" type="submit" className="auth-btn" disabled={isLoading} whileHover={{ scale: 1.03, boxShadow: '0 0 25px rgba(35, 134, 54, 0.4)' }} whileTap={{ scale: 0.97 }} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}>
                        {isLoading && <span className="spinner-border spinner-border-sm me-2" role="status" />}
                        {isLoading ? 'Signing in...' : 'Log In'}
                    </motion.button>
                </form>

                <motion.p className="auth-footer-text" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.7 }}>
                    Don't have an account?{' '}
                    <button className="auth-link-btn" onClick={() => setShowSignUp(true)}>
                        Register here
                    </button>
                </motion.p>

                <motion.p className="auth-footer-text" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.75 }}>
                    Want to explore without logging in first?{' '}
                    <Link to="/preview">Open product preview</Link>
                </motion.p>
            </motion.div>

            {/* Sign Up Modal */}
            <SignUpModal isOpen={showSignUp} onClose={() => setShowSignUp(false)} />
        </div>
    );
};

export default LoginPage;
