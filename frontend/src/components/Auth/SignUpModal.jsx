import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import { FaEnvelope, FaLock, FaShieldAlt, FaTimes } from 'react-icons/fa';
import './Auth.css';

const SignUpModal = ({ isOpen, onClose }) => {
    const { register } = useAuth();
    const navigate = useNavigate();

    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const resetForm = () => {
        setEmail('');
        setPassword('');
        setConfirmPassword('');
        setError('');
    };

    const handleClose = () => {
        resetForm();
        onClose();
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (password !== confirmPassword) {
            setError('Passwords do not match.');
            return;
        }

        if (password.length < 8) {
            setError('Password must be at least 8 characters.');
            return;
        }

        setIsLoading(true);
        try {
            await register(email, password);
            resetForm();
            onClose();
            // Navigate to onboarding for new users, or home
            navigate('/onboarding', { replace: true });
        } catch (err) {
            const msg = err.response?.data?.error || 'Connection error. Please try again.';
            setError(msg);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    className="signup-overlay"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.25 }}
                    onClick={handleClose}
                >
                    <motion.div
                        className="signup-modal"
                        initial={{ opacity: 0, y: 40, scale: 0.92 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 30, scale: 0.95 }}
                        transition={{ duration: 0.35, ease: [0.25, 0.46, 0.45, 0.94] }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <button className="signup-close" onClick={handleClose}>
                            <FaTimes size={16} />
                        </button>

                        <h2 className="signup-title">Create Account</h2>
                        <p className="signup-subtitle">Join CostBench and start analyzing</p>

                        {error && (
                            <motion.div className="auth-error" role="alert" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                                {error}
                            </motion.div>
                        )}

                        <form onSubmit={handleSubmit} className="auth-form">
                            <div className="auth-field">
                                <FaEnvelope className="auth-field-icon" />
                                <input id="signup-email" type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" disabled={isLoading} />
                            </div>

                            <div className="auth-field">
                                <FaLock className="auth-field-icon" />
                                <input id="signup-password" type="password" placeholder="Password (min. 8 characters)" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="new-password" minLength={8} disabled={isLoading} />
                            </div>

                            <div className="auth-field">
                                <FaShieldAlt className="auth-field-icon" />
                                <input id="signup-confirm-password" type="password" placeholder="Confirm password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required autoComplete="new-password" disabled={isLoading} />
                            </div>

                            <motion.button id="signup-submit" type="submit" className="auth-btn" disabled={isLoading} whileHover={{ scale: 1.03, boxShadow: '0 0 25px rgba(35, 134, 54, 0.4)' }} whileTap={{ scale: 0.97 }}>
                                {isLoading && <span className="spinner-border spinner-border-sm me-2" role="status" />}
                                {isLoading ? 'Creating account...' : 'Register'}
                            </motion.button>
                        </form>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};

export default SignUpModal;
