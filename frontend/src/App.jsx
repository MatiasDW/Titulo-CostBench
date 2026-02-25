import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
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
import LoginPage from './components/Auth/LoginPage';
import OnboardingPage from './components/Auth/OnboardingPage';
import DashboardLayout from './components/Auth/DashboardLayout';
import ProtectedRoute from './components/Auth/ProtectedRoute';
import './index.css';

const App = () => {
  const [items, setItems] = useState([]);
  const [macro, setMacro] = useState({ cpi: [], yields: [], commodities: [] });
  const [loading, setLoading] = useState(true);
  const [currency, setCurrency] = useState('CLP');
  const [limit, setLimit] = useState(10);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const rankingRes = await axios.get(`/api/v1/atc/ranking?limit=${limit}&currency=${currency}`);
      const rankingData = rankingRes.data;
      setItems(rankingData.items || rankingData.data || []);
      setLastUpdate(rankingData.metadata ? rankingData.metadata.timestamp : new Date().toISOString());

      const cpiRes = await axios.get('/api/v1/market/history?series_id=CPIAUCSL');
      const yieldsRes = await axios.get('/api/v1/market/history?series_id=DGS10');
      const goldRes = await axios.get('/api/v1/market/history?series_id=GOLDAMGBD228NLBM');
      const copperRes = await axios.get('/api/v1/market/history?series_id=PCOPPUSDM');
      const oilRes = await axios.get('/api/v1/market/history?series_id=DCOILWTICO');
      const btcRes = await axios.get('/api/v1/market/history?series_id=BTC-CLP');
      const ethRes = await axios.get('/api/v1/market/history?series_id=ETH-CLP');

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
  };

  useEffect(() => {
    fetchData();
  }, [limit, currency]);

  const handleUpdate = () => {
    fetchData();
  };

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
