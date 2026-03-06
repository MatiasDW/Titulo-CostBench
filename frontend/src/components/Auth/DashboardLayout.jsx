import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import Sidebar from './Sidebar';
import ProtectedRoute from './ProtectedRoute';
import PageTransition from '../PageTransition';
import './DashboardLayout.css';

/**
 * DashboardLayout – wraps protected content with collapsible Sidebar
 * and animated page transitions on route changes.
 */
const DashboardLayout = ({ children }) => {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const location = useLocation();

    return (
        <ProtectedRoute>
            <div className={`dashboard-layout ${sidebarCollapsed ? 'sidebar-hidden' : ''}`}>
                <Sidebar
                    collapsed={sidebarCollapsed}
                    onToggle={() => setSidebarCollapsed(prev => !prev)}
                />
                <main className="dashboard-main">
                    <AnimatePresence mode="wait">
                        <PageTransition pageKey={location.pathname}>
                            {children}
                        </PageTransition>
                    </AnimatePresence>
                </main>
            </div>
        </ProtectedRoute>
    );
};

export default DashboardLayout;
