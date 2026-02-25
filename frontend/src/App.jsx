import React, { useState, useEffect, useCallback } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';

// ── Lightweight imports (always loaded) ──
import LoginPage from './components/Auth/LoginPage';
import OnboardingPage from './components/Auth/OnboardingPage';
import DashboardLayout from './components/Auth/DashboardLayout';
import ProtectedRoute from './components/Auth/ProtectedRoute';
import './index.css';

// ── Lazy-loaded heavy components (code splitting) ──
const Header = React.lazy(() => import('./components/Header'));
const Ticker = React.lazy(() => import('./components/Ticker'));
const Footer = React.lazy(() => import('./components/Footer'));
const Filters = React.lazy(() => import('./components/Filters'));
const RankingTable = React.lazy(() => import('./components/RankingTable'));
const MarketDashboard = React.lazy(() => import('./components/Dashboard/MarketDashboard'));
const AnimatedBackground = React.lazy(() => import('./components/AnimatedBackground'));
const ChartCarousel = React.lazy(() => import('./components/ChartCarousel'));
const ModelComparison = React.lazy(() => import('./components/ModelComparison'));
const SclodaChat = React.lazy(() => import('./components/SclodaChat'));

const DashboardFallback = () => (
  <div className="d-flex justify-content-center align-items-center" style={{ height: '60vh' }}>
    <div className="spinner-border text-success" role="status">
      <span className="visually-hidden">Loading...</span>
    </div>
  </div>
);

const App = () => {
  const [items, setItems] = useState([]);
  const [macro, setMacro] = useState({ cpi: [], yields: [], commodities: [] });
  const [loading, setLoading] = useState(true);
  const [currency, setCurrency] = useState('CLP');
  const [limit, setLimit] = useState(10);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      // ── FIX #1: Promise.all — all 8 API calls in parallel (~7x faster) ──
      const [rankingRes, cpiRes, yieldsRes, goldRes, copperRes, oilRes, btcRes, ethRes] =
        await Promise.all([
          axios.get(`/api/v1/atc/ranking?limit=${limit}&currency=${currency}`),
          axios.get('/api/v1/market/history?series_id=CPIAUCSL'),
          axios.get('/api/v1/market/history?series_id=DGS10'),
          axios.get('/api/v1/market/history?series_id=GOLDAMGBD228NLBM'),
          axios.get('/api/v1/market/history?series_id=PCOPPUSDM'),
          axios.get('/api/v1/market/history?series_id=DCOILWTICO'),
          axios.get('/api/v1/market/history?series_id=BTC-CLP'),
          axios.get('/api/v1/market/history?series_id=ETH-CLP'),
        ]);

      const rankingData = rankingRes.data;
      setItems(rankingData.items || rankingData.data || []);
      setLastUpdate(rankingData.metadata ? rankingData.metadata.timestamp : new Date().toISOString());

      setMacro({
        cpi: cpiRes.data.observations || [],
        yields: yieldsRes.data.observations || [],
        gold: goldRes.data.observations || [],
        copper: copperRes.data.observations || [],
        oil: oilRes.data.observations || [],
        btc: btcRes.data.observations || [],
        eth: ethRes.data.observations || []
      });

    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  }, [limit, currency]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleUpdate = useCallback(() => {
    fetchData();
  }, [fetchData]);

  const dashboard = (
    <React.Suspense fallback={<DashboardFallback />}>
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
    </React.Suspense>
  );

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/onboarding" element={
        <ProtectedRoute>
          <OnboardingPage />
        </ProtectedRoute>
      } />
      <Route path="/home" element={
        <DashboardLayout>{dashboard}</DashboardLayout>
      } />
      {/* Redirect / to /home */}
      <Route path="/" element={<Navigate to="/home" replace />} />
      <Route path="*" element={<Navigate to="/home" replace />} />
    </Routes>
  );
};

export default App;
