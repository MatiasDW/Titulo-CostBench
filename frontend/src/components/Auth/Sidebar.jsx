import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import {
    FaHome, FaTrophy, FaGlobeAmericas,
    FaSignOutAlt, FaUserTie, FaChartLine,
    FaBars, FaTimes, FaUserCog, FaChevronDown
} from 'react-icons/fa';
import './Sidebar.css';

const NAV_ITEMS = [
    { path: '/home', label: 'Home', icon: FaHome },
    { path: '/ranking', label: 'Ranking', icon: FaTrophy },
    { path: '/macro', label: 'Macro', icon: FaGlobeAmericas },
];

const RISK_BADGES = {
    conservative: { icon: '🛡️', label: 'Conservative' },
    moderate: { icon: '⚖️', label: 'Moderate' },
    aggressive: { icon: '🔥', label: 'Aggressive' },
};

const Sidebar = ({ collapsed, onToggle }) => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const [profileOpen, setProfileOpen] = useState(false);

    const handleLogout = async () => {
        await logout();
        navigate('/login', { replace: true });
    };

    return (
        <>
            {/* Hamburger toggle button */}
            <button
                className={`sidebar-toggle ${collapsed ? 'sidebar-toggle-collapsed' : ''}`}
                onClick={onToggle}
                aria-label={collapsed ? 'Open menu' : 'Close menu'}
            >
                {collapsed ? <FaBars size={18} /> : <FaTimes size={18} />}
            </button>

            {/* Sidebar panel */}
            <AnimatePresence>
                {!collapsed && (
                    <motion.aside
                        className="sidebar"
                        initial={{ x: -240 }}
                        animate={{ x: 0 }}
                        exit={{ x: -240 }}
                        transition={{ duration: 0.25, ease: 'easeInOut' }}
                    >
                        {/* Brand */}
                        <div className="sidebar-brand">
                            <img src="/img/costbench_logo.svg" alt="CostBench" className="sidebar-logo" />
                        </div>

                        {/* Clickable User Profile */}
                        <button
                            className="sidebar-user"
                            onClick={() => setProfileOpen(prev => !prev)}
                        >
                            <div className="sidebar-avatar">
                                {user?.is_admin ? <FaUserTie size={18} /> : <FaChartLine size={18} />}
                            </div>
                            <div className="sidebar-user-info">
                                <span className="sidebar-email">{user?.email}</span>
                                <span className="sidebar-role">
                                    {user?.is_admin && '⭐ Admin'}
                                    {user?.risk_profile && (
                                        <span className="sidebar-risk-badge">
                                            {RISK_BADGES[user.risk_profile]?.icon} {RISK_BADGES[user.risk_profile]?.label}
                                        </span>
                                    )}
                                    {!user?.is_admin && !user?.risk_profile && 'No profile set'}
                                </span>
                            </div>
                            <FaChevronDown
                                size={10}
                                className={`sidebar-chevron ${profileOpen ? 'open' : ''}`}
                            />
                        </button>

                        {/* Profile dropdown */}
                        <AnimatePresence>
                            {profileOpen && (
                                <motion.div
                                    className="sidebar-profile-menu"
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: 'auto', opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    transition={{ duration: 0.2 }}
                                >
                                    <button
                                        className="sidebar-profile-item"
                                        onClick={() => { setProfileOpen(false); navigate('/onboarding'); }}
                                    >
                                        <FaUserCog size={14} />
                                        <span>Edit Preferences</span>
                                    </button>
                                    {user?.is_admin && (
                                        <button
                                            className="sidebar-profile-item admin-item"
                                            onClick={() => { setProfileOpen(false); /* TODO: admin panel */ }}
                                        >
                                            <FaUserTie size={14} />
                                            <span>Admin Panel</span>
                                        </button>
                                    )}
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {/* Navigation */}
                        <nav className="sidebar-nav">
                            {NAV_ITEMS.map(({ path, label, icon: Icon }) => {
                                const isActive = location.pathname === path;
                                return (
                                    <motion.button
                                        key={path}
                                        className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
                                        onClick={() => navigate(path)}
                                        whileHover={{ x: 4 }}
                                        whileTap={{ scale: 0.97 }}
                                    >
                                        <Icon size={16} />
                                        <span>{label}</span>
                                    </motion.button>
                                );
                            })}
                        </nav>

                        <div className="sidebar-spacer" />

                        {/* Logout */}
                        <motion.button
                            className="sidebar-logout"
                            onClick={handleLogout}
                            whileHover={{ x: 4, backgroundColor: 'rgba(218, 54, 51, 0.15)' }}
                            whileTap={{ scale: 0.97 }}
                        >
                            <FaSignOutAlt size={16} />
                            <span>Log Out</span>
                        </motion.button>
                    </motion.aside>
                )}
            </AnimatePresence>
        </>
    );
};

export default Sidebar;
