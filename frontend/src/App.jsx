import React, { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
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
import ProtectedRoute from './components/Auth/ProtectedRoute';
import LoginPage from './components/Auth/LoginPage';
import RegisterPage from './components/Auth/RegisterPage';
import './index.css';

const App = () => {
  // State
  const [items, setItems] = useState([]);
  const [macro, setMacro] = useState({ cpi: [], yields: [], commodities: [] }); // Add commodities defaults
  const [loading, setLoading] = useState(true);
  const [currency, setCurrency] = useState('CLP');
  const [limit, setLimit] = useState(10);
  const [lastUpdate, setLastUpdate] = useState(null);

  // Fetch Data
  const fetchData = async () => {
    setLoading(true);
    try {
      // 1. Fetch Items
      const rankingRes = await axios.get(`/api/v1/atc/ranking?limit=${limit}&currency=${currency}`);
      // Verify structure: viewer.html used data.items. Let's start safely.
      const rankingData = rankingRes.data;
      setItems(rankingData.items || rankingData.data || []);
      setLastUpdate(rankingData.metadata ? rankingData.metadata.timestamp : new Date().toISOString());

      // 2. Fetch Macro (only once needed really, but fine to refresh)
      // We might need to fetch series individually if /market aggregate endpoint doesn't exist or returns differently
      // viewer.html fetches /market/history?series_id=...
      // Let's assume /api/v1/market returns aggregations, or we construct it here.
      // If /api/v1/market doesn't exist, we should use separate calls like Ticker does.

      // Let's try to fetch specific series for the Dashboard
      const cpiRes = await axios.get('/api/v1/market/history?series_id=CPIAUCSL');
      const yieldsRes = await axios.get('/api/v1/market/history?series_id=DGS10');
      const goldRes = await axios.get('/api/v1/market/history?series_id=GOLDAMGBD228NLBM');
      const copperRes = await axios.get('/api/v1/market/history?series_id=PCOPPUSDM');
      const oilRes = await axios.get('/api/v1/market/history?series_id=DCOILWTICO');
      const btcRes = await axios.get('/api/v1/market/history?series_id=BTC-CLP');
      const ethRes = await axios.get('/api/v1/market/history?series_id=ETH-CLP'); // Fetch ETH

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

  // derived metrics
  const cheapCost = items.length > 0 ? items[0].cost : 0;
  const expensiveCost = items.length > 0 ? items[items.length - 1].cost : 0;
  const arbitrage = expensiveCost - cheapCost;

  useEffect(() => {
    fetchData();
  }, [limit, currency]); // Trigger on limit/currency change!

  const handleUpdate = () => {
    fetchData();
  };

  // Dashboard content (extracted for readability inside Routes)
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
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/*" element={
        <ProtectedRoute>{dashboard}</ProtectedRoute>
      } />
    </Routes>
  );
};

export default App;
