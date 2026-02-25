import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import {
    FaEnvelope, FaLock, FaShieldAlt, FaUserTie,
    FaBitcoin, FaLandmark, FaKey, FaChartLine, FaUserShield
} from 'react-icons/fa';
import { GiGoldBar, GiHouse, GiModernCity, GiFarmTractor } from 'react-icons/gi';
import AnimatedBackground from '../AnimatedBackground';
import './Auth.css';

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

const RegisterPage = () => {
    const { register } = useAuth();
    const navigate = useNavigate();

    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (password !== confirmPassword) {
            setError('Las contraseñas no coinciden.');
            return;
        }
        if (password.length < 8) {
            setError('La contraseña debe tener al menos 8 caracteres.');
            return;
        }

        setIsLoading(true);
        try {
            await register(email, password);
            navigate('/', { replace: true });
        } catch (err) {
            const msg = err.response?.data?.error || 'Error de conexión. Intenta de nuevo.';
            setError(msg);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <AnimatedBackground />

            {/* ── Auth-specific floating icons ── */}
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

            <motion.div
                className="auth-card"
                initial={{ opacity: 0, y: 40, scale: 0.92 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
            >
                <motion.div className="auth-logo" animate={{ y: [0, -6, 0] }} transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}>
                    <img src="/img/costbench_logo.svg" alt="CostBench" className="auth-logo-img" />
                </motion.div>

                <motion.p className="auth-subtitle" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}>
                    Crea tu cuenta gratuita
                </motion.p>

                {error && (
                    <motion.div className="auth-error" role="alert" initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}>
                        {error}
                    </motion.div>
                )}

                <form onSubmit={handleSubmit} className="auth-form">
                    <motion.div className="auth-field" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 }}>
                        <FaEnvelope className="auth-field-icon" />
                        <input id="register-email" type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" disabled={isLoading} />
                    </motion.div>

                    <motion.div className="auth-field" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.5 }}>
                        <FaLock className="auth-field-icon" />
                        <input id="register-password" type="password" placeholder="Contraseña (mín. 8 caracteres)" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="new-password" minLength={8} disabled={isLoading} />
                    </motion.div>

                    <motion.div className="auth-field" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.6 }}>
                        <FaShieldAlt className="auth-field-icon" />
                        <input id="register-confirm-password" type="password" placeholder="Confirmar contraseña" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required autoComplete="new-password" disabled={isLoading} />
                    </motion.div>

                    <motion.button id="register-submit" type="submit" className="auth-btn" disabled={isLoading} whileHover={{ scale: 1.03, boxShadow: '0 0 25px rgba(35, 134, 54, 0.4)' }} whileTap={{ scale: 0.97 }} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7 }}>
                        {isLoading && <span className="spinner-border spinner-border-sm me-2" role="status" />}
                        {isLoading ? 'Creando cuenta...' : 'Registrarse'}
                    </motion.button>
                </form>

                <motion.p className="auth-footer-text" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 }}>
                    ¿Ya tienes cuenta? <Link to="/login">Inicia sesión</Link>
                </motion.p>
            </motion.div>
        </div>
    );
};

export default RegisterPage;
