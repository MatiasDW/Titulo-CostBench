import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import {
    FaUserEdit, FaArrowLeft, FaSave, FaCheck,
    FaShieldAlt, FaUserTie, FaChartLine, FaStar,
    FaRobot, FaBitcoin, FaBuilding, FaIdCard
} from 'react-icons/fa';
import { GiGoldBar } from 'react-icons/gi';
import AnimatedBackground from '../AnimatedBackground';
import useSounds from '../../hooks/useSounds';
import './ProfilePage.css';

// ── Same cards as OnboardingPage (single source of truth) ──
const INTEREST_CARDS = [
    {
        id: 'banking_costs',
        icon: <FaChartLine size={22} />,
        title: 'Banking Cost Analysis',
        description: 'Compare and benchmark the true cost of Chilean banking products.',
        color: '#58a6ff',
    },
    {
        id: 'market_forecasting',
        icon: <FaRobot size={22} />,
        title: 'Market Forecasting',
        description: 'ML-powered predictions using ARIMA models for financial time series.',
        color: '#238636',
    },
    {
        id: 'crypto_commodities',
        icon: <FaBitcoin size={22} />,
        title: 'Crypto & Commodities',
        description: 'Track Bitcoin, Ethereum, Gold, Copper, and Oil with live data.',
        color: '#f7931a',
    },
    {
        id: 'real_estate',
        icon: <FaBuilding size={22} />,
        title: 'Real Estate & Mortgages',
        description: 'Housing market analytics, mortgage rates, and UF tracking.',
        color: '#bf8700',
    },
    {
        id: 'macro_indicators',
        icon: <GiGoldBar size={22} />,
        title: 'Macro Indicators',
        description: 'CPI, Treasury yields, and global macro data.',
        color: '#627eea',
    },
];

const RISK_OPTIONS = [
    { value: 'conservative', label: 'Conservative', emoji: '🛡️' },
    { value: 'moderate', label: 'Moderate', emoji: '⚖️' },
    { value: 'aggressive', label: 'Aggressive', emoji: '🔥' },
];

const EXPERIENCE_OPTIONS = [
    { value: 'beginner', label: 'Beginner', emoji: '🌱' },
    { value: 'intermediate', label: 'Intermediate', emoji: '📊' },
    { value: 'advanced', label: 'Advanced', emoji: '🚀' },
];

const INCOME_OPTIONS = [
    { value: '0-1M', label: '$0 – $1M CLP' },
    { value: '1M-3M', label: '$1M – $3M CLP' },
    { value: '3M-5M', label: '$3M – $5M CLP' },
    { value: '5M-10M', label: '$5M – $10M CLP' },
    { value: '10M+', label: '$10M+ CLP' },
];

const ProfilePage = () => {
    const { user, updateProfile } = useAuth();
    const navigate = useNavigate();

    const [form, setForm] = useState({
        first_name: '',
        last_name: '',
        phone: '',
        bio: '',
        risk_profile: '',
        rut: '',
        date_of_birth: '',
        nationality: '',
        address: '',
        city: '',
        occupation: '',
        income_range: '',
        investment_experience: '',
    });
    const [selectedInterests, setSelectedInterests] = useState([]);
    const [saving, setSaving] = useState(false);
    const [showToast, setShowToast] = useState(false);
    const { playSelect, playDeselect, playSave } = useSounds();

    // Initialize form with current user data
    useEffect(() => {
        if (user) {
            setForm({
                first_name: user.first_name || '',
                last_name: user.last_name || '',
                phone: user.phone || '',
                bio: user.bio || '',
                risk_profile: user.risk_profile || '',
                rut: user.rut || '',
                date_of_birth: user.date_of_birth || '',
                nationality: user.nationality || '',
                address: user.address || '',
                city: user.city || '',
                occupation: user.occupation || '',
                income_range: user.income_range || '',
                investment_experience: user.investment_experience || '',
            });
            setSelectedInterests(user.interests || []);
        }
    }, [user]);

    const handleChange = (field, value) => {
        setForm(prev => ({ ...prev, [field]: value }));
    };

    const toggleInterest = (id) => {
        const isSelected = selectedInterests.includes(id);
        isSelected ? playDeselect() : playSelect();
        setSelectedInterests(prev =>
            isSelected ? prev.filter(i => i !== id) : [...prev, id]
        );
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            await updateProfile({
                ...form,
                interests: selectedInterests,
            });
            playSave();
            setShowToast(true);
            setTimeout(() => setShowToast(false), 3000);
        } catch (err) {
            console.error('Profile save error:', err);
        } finally {
            setSaving(false);
        }
    };

    const memberSince = user?.created_at
        ? new Date(user.created_at).toLocaleDateString('en-US', {
            year: 'numeric', month: 'long', day: 'numeric'
        })
        : null;

    return (
        <div className="profile-page">
            <AnimatedBackground />

            <motion.div
                className="profile-container"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
            >
                {/* Header */}
                <div className="profile-header">
                    <div className="profile-avatar">
                        {user?.is_admin ? <FaUserTie size={28} /> : <FaChartLine size={28} />}
                    </div>
                    <h2>Edit Profile</h2>
                    <p>{user?.email}</p>
                </div>

                {/* ─── CARD 1: Personal Information ─── */}
                <motion.div
                    className="profile-card"
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                >
                    <div className="profile-card-title">
                        <FaUserEdit size={16} />
                        Personal Information
                    </div>

                    <div className="profile-row">
                        <div className="profile-field">
                            <label htmlFor="first_name">First Name</label>
                            <input
                                id="first_name"
                                type="text"
                                placeholder="John"
                                value={form.first_name}
                                onChange={(e) => handleChange('first_name', e.target.value)}
                                maxLength={100}
                            />
                        </div>
                        <div className="profile-field">
                            <label htmlFor="last_name">Last Name</label>
                            <input
                                id="last_name"
                                type="text"
                                placeholder="Doe"
                                value={form.last_name}
                                onChange={(e) => handleChange('last_name', e.target.value)}
                                maxLength={100}
                            />
                        </div>
                    </div>

                    <div className="profile-field">
                        <label htmlFor="phone">Phone</label>
                        <input
                            id="phone"
                            type="tel"
                            placeholder="+56 9 1234 5678"
                            value={form.phone}
                            onChange={(e) => handleChange('phone', e.target.value)}
                            maxLength={30}
                        />
                    </div>

                    <div className="profile-field">
                        <label htmlFor="bio">About / Notes</label>
                        <textarea
                            id="bio"
                            placeholder="Write something about yourself or any personal notes..."
                            value={form.bio}
                            onChange={(e) => handleChange('bio', e.target.value)}
                            maxLength={500}
                            rows={3}
                        />
                    </div>
                </motion.div>

                {/* ─── CARD 2: Interests (from Onboarding) ─── */}
                <motion.div
                    className="profile-card"
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.15 }}
                >
                    <div className="profile-card-title">
                        <FaStar size={16} />
                        Your Interests
                    </div>

                    <div className="profile-interests-grid">
                        {INTEREST_CARDS.map((card) => {
                            const isSelected = selectedInterests.includes(card.id);
                            return (
                                <motion.button
                                    key={card.id}
                                    className={`profile-interest-card ${isSelected ? 'selected' : ''}`}
                                    onClick={() => toggleInterest(card.id)}
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                    style={{ '--card-accent': card.color }}
                                    type="button"
                                >
                                    <div className="profile-interest-icon" style={{ color: card.color }}>
                                        {card.icon}
                                    </div>
                                    <div className="profile-interest-check">
                                        {isSelected && <FaCheck size={10} />}
                                    </div>
                                    <h4 className="profile-interest-title">{card.title}</h4>
                                    <p className="profile-interest-desc">{card.description}</p>
                                </motion.button>
                            );
                        })}
                    </div>
                </motion.div>

                {/* ─── CARD 3: Risk Profile ─── */}
                <motion.div
                    className="profile-card"
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                >
                    <div className="profile-card-title">
                        <FaShieldAlt size={16} />
                        Investor Profile
                    </div>

                    <div className="profile-risk-options">
                        {RISK_OPTIONS.map((opt) => (
                            <button
                                key={opt.value}
                                className={`profile-risk-btn ${form.risk_profile === opt.value ? 'active' : ''}`}
                                onClick={() => handleChange('risk_profile', opt.value)}
                                type="button"
                            >
                                <span className="profile-risk-emoji">{opt.emoji}</span>
                                <span className="profile-risk-label">{opt.label}</span>
                            </button>
                        ))}
                    </div>
                </motion.div>

                {/* ─── CARD 4: Account Verification (KYC) ─── */}
                <motion.div
                    className="profile-card"
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.25 }}
                >
                    <div className="profile-card-title">
                        <FaIdCard size={16} />
                        Account Verification
                    </div>

                    <div className="profile-row">
                        <div className="profile-field">
                            <label htmlFor="rut">RUT</label>
                            <input
                                id="rut"
                                type="text"
                                placeholder="12.345.678-9"
                                value={form.rut}
                                onChange={(e) => handleChange('rut', e.target.value)}
                                maxLength={12}
                            />
                        </div>
                        <div className="profile-field">
                            <label htmlFor="date_of_birth">Date of Birth</label>
                            <input
                                id="date_of_birth"
                                type="date"
                                value={form.date_of_birth}
                                onChange={(e) => handleChange('date_of_birth', e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="profile-row">
                        <div className="profile-field">
                            <label htmlFor="nationality">Nationality</label>
                            <input
                                id="nationality"
                                type="text"
                                placeholder="Chilean"
                                value={form.nationality}
                                onChange={(e) => handleChange('nationality', e.target.value)}
                                maxLength={60}
                            />
                        </div>
                        <div className="profile-field">
                            <label htmlFor="city">City</label>
                            <input
                                id="city"
                                type="text"
                                placeholder="Santiago"
                                value={form.city}
                                onChange={(e) => handleChange('city', e.target.value)}
                                maxLength={80}
                            />
                        </div>
                    </div>

                    <div className="profile-field">
                        <label htmlFor="address">Address</label>
                        <input
                            id="address"
                            type="text"
                            placeholder="Av. Providencia 1234, Depto 56"
                            value={form.address}
                            onChange={(e) => handleChange('address', e.target.value)}
                            maxLength={255}
                        />
                    </div>

                    <div className="profile-row">
                        <div className="profile-field">
                            <label htmlFor="occupation">Occupation</label>
                            <input
                                id="occupation"
                                type="text"
                                placeholder="Software Engineer"
                                value={form.occupation}
                                onChange={(e) => handleChange('occupation', e.target.value)}
                                maxLength={100}
                            />
                        </div>
                        <div className="profile-field">
                            <label htmlFor="income_range">Income Range</label>
                            <select
                                id="income_range"
                                value={form.income_range}
                                onChange={(e) => handleChange('income_range', e.target.value)}
                                className="profile-field-select"
                            >
                                <option value="">Select...</option>
                                {INCOME_OPTIONS.map(o => (
                                    <option key={o.value} value={o.value}>{o.label}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <div className="profile-field">
                        <label>Investment Experience</label>
                        <div className="profile-risk-options">
                            {EXPERIENCE_OPTIONS.map(opt => (
                                <button
                                    key={opt.value}
                                    className={`profile-risk-btn ${form.investment_experience === opt.value ? 'active' : ''}`}
                                    onClick={() => handleChange('investment_experience', opt.value)}
                                    type="button"
                                >
                                    <span className="profile-risk-emoji">{opt.emoji}</span>
                                    <span className="profile-risk-label">{opt.label}</span>
                                </button>
                            ))}
                        </div>
                    </div>
                </motion.div>

                {/* Actions */}
                <div className="profile-actions">
                    <button className="profile-btn-back" onClick={() => navigate(-1)}>
                        <FaArrowLeft size={12} /> Back
                    </button>
                    <motion.button
                        className="profile-btn-save"
                        onClick={handleSave}
                        disabled={saving}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                    >
                        <FaSave size={14} />
                        {saving ? 'Saving...' : 'Save Changes'}
                    </motion.button>
                </div>

                {memberSince && (
                    <p className="profile-member-since">
                        Member since {memberSince}
                    </p>
                )}
            </motion.div>

            {/* Success toast */}
            <AnimatePresence>
                {showToast && (
                    <motion.div
                        className="profile-toast"
                        initial={{ opacity: 0, y: 30 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 30 }}
                    >
                        <FaCheck size={14} /> Profile updated successfully
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default ProfilePage;
