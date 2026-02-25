import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

/**
 * Wraps a route so only authenticated users can access it.
 * Shows a loading spinner while the initial session check runs,
 * then redirects to /login if no user is found.
 */
const ProtectedRoute = ({ children }) => {
    const { user, loading } = useAuth();

    if (loading) {
        return (
            <div className="d-flex justify-content-center align-items-center" style={{ height: '100vh' }}>
                <div className="spinner-border text-light" role="status">
                    <span className="visually-hidden">Loading...</span>
                </div>
            </div>
        );
    }

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    return children;
};

export default ProtectedRoute;
