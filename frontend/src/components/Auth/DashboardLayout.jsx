import React, { useState } from 'react';
import Sidebar from './Sidebar';
import ProtectedRoute from './ProtectedRoute';
import './DashboardLayout.css';

/**
 * DashboardLayout – wraps protected content with collapsible Sidebar.
 */
const DashboardLayout = ({ children }) => {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

    return (
        <ProtectedRoute>
            <div className={`dashboard-layout ${sidebarCollapsed ? 'sidebar-hidden' : ''}`}>
                <Sidebar
                    collapsed={sidebarCollapsed}
                    onToggle={() => setSidebarCollapsed(prev => !prev)}
                />
                <main className="dashboard-main">
                    {children}
                </main>
            </div>
        </ProtectedRoute>
    );
};

export default DashboardLayout;
