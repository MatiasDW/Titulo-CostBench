import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

// Axios instance with credentials (sends HttpOnly cookies automatically)
const api = axios.create({
    baseURL: '/api/v1/auth',
    withCredentials: true,
    headers: { 'Content-Type': 'application/json' },
});

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true); // true until initial /me check completes

    // Restore session from cookie on mount
    useEffect(() => {
        api.get('/me')
            .then(res => setUser(res.data.user))
            .catch(() => setUser(null))
            .finally(() => setLoading(false));
    }, []);

    const login = useCallback(async (email, password) => {
        const res = await api.post('/login', { email, password });
        setUser(res.data.user);
        return res.data;
    }, []);

    const register = useCallback(async (email, password) => {
        const res = await api.post('/register', { email, password });
        setUser(res.data.user);
        return res.data;
    }, []);

    const logout = useCallback(async () => {
        await api.post('/logout');
        setUser(null);
    }, []);

    const updateProfile = useCallback(async (riskProfile) => {
        const res = await api.put('/profile', { risk_profile: riskProfile });
        setUser(res.data.user);
        return res.data;
    }, []);

    const value = { user, loading, login, register, logout, updateProfile };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used within <AuthProvider>');
    return ctx;
}

export default AuthContext;
