import React, { useState, useCallback } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// ── Lightweight imports (always loaded) ──
import LoginPage from './components/Auth/LoginPage';
import OnboardingPage from './components/Auth/OnboardingPage';
import ProfilePage from './components/Auth/ProfilePage';
import WalletPage from './components/Trading/WalletPage';
import TradePage from './components/Trading/TradePage';
import RealEstatePage from './components/RealEstate/RealEstatePage';
import NewsPage from './components/News/NewsPage';
import DashboardLayout from './components/Auth/DashboardLayout';
import ProtectedRoute from './components/Auth/ProtectedRoute';
import useDashboardData from './hooks/useDashboardData';
import './index.css';

import Header from './components/Header';
import Ticker from './components/Ticker';
import Footer from './components/Footer';
import Filters from './components/Filters';
import RankingTable from './components/RankingTable';
import MarketDashboard from './components/Dashboard/MarketDashboard';
import AnimatedBackground from './components/AnimatedBackground';
import ChartCarousel from './components/ChartCarousel';
import ModelComparison from './components/ModelComparison';
import SclodaChat from './components/SclodaChat';
import MarketIntelligenceCard from './components/Dashboard/MarketIntelligenceCard';



const App = () => {
  const [currency, setCurrency] = useState('CLP');
  const [limit, setLimit] = useState(10);

  // ── FIX #6: Single source of truth for all dashboard data ──
  const { items, macro, loading, lastUpdate, refetch } = useDashboardData({ limit, currency });

  const handleUpdate = useCallback(() => {
    refetch();
  }, [refetch]);

  const dashboard = (
    <div className="container-fluid p-0">
      <AnimatedBackground />
      <Ticker />

      <div className="container-fluid px-4 pt-4">
        <Header onOpenDashboard={() => { }} />
      </div>

      <div className="container-fluid px-4 mb-4">
        <ChartCarousel macro={macro} />
      </div>

      <div className="container-fluid px-4 mb-4">
        <ModelComparison />
      </div>

      <div className="container py-3">
        <div className="mb-4">
          <MarketIntelligenceCard />
        </div>

        <Filters
          limit={limit}
          onLimitChange={setLimit}
          currency={currency}
          onCurrencyChange={setCurrency}
          onUpdate={handleUpdate}
        />

        <div className="card-header-custom text-white d-flex justify-content-between align-items-center mb-0">
          <span>Banking Cost Ranking (Annual)</span>
          {lastUpdate && <span className="badge bg-dark border border-secondary text-secondary fw-normal">Updated: {new Date(lastUpdate).toLocaleString()}</span>}
        </div>

        <div className="card-custom p-0 mb-5" style={{ borderTopLeftRadius: 0, borderTopRightRadius: 0 }}>
          {loading ? (
            <div className="p-5 text-center text-secondary">Loading financial data...</div>
          ) : (
            <RankingTable items={items} currency={currency} />
          )}
        </div>

        <Footer />
        <MarketDashboard items={items} macro={macro} />
      </div>

      <SclodaChat />
    </div>
  );

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/onboarding" element={
        <ProtectedRoute>
          <OnboardingPage />
        </ProtectedRoute>
      } />
      <Route path="/profile" element={
        <ProtectedRoute>
          <ProfilePage />
        </ProtectedRoute>
      } />
      <Route path="/wallet" element={
        <ProtectedRoute>
          <DashboardLayout><WalletPage /></DashboardLayout>
        </ProtectedRoute>
      } />
      <Route path="/trade" element={
        <ProtectedRoute>
          <DashboardLayout><TradePage /></DashboardLayout>
        </ProtectedRoute>
      } />
      <Route path="/real-estate" element={
        <ProtectedRoute>
          <DashboardLayout><RealEstatePage /></DashboardLayout>
        </ProtectedRoute>
      } />
      <Route path="/news" element={
        <ProtectedRoute>
          <DashboardLayout><NewsPage /></DashboardLayout>
        </ProtectedRoute>
      } />
      <Route path="/home" element={
        <ProtectedRoute>
          <DashboardLayout>{dashboard}</DashboardLayout>
        </ProtectedRoute>
      } />
      <Route path="/" element={<Navigate to="/home" replace />} />
      <Route path="*" element={<Navigate to="/home" replace />} />
    </Routes>
  );
};

export default App;
