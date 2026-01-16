import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Header from './components/Header';
import Ticker from './components/Ticker'; // Import Ticker
import Footer from './components/Footer'; // Import Footer
import Filters from './components/Filters';
import RankingTable from './components/RankingTable';
import MarketDashboard from './components/Dashboard/MarketDashboard';
import AnimatedBackground from './components/AnimatedBackground'; // Animated BG
import ChartCarousel from './components/ChartCarousel'; // Rotating charts
import ModelComparison from './components/ModelComparison'; // ML Model Performance
import './index.css'; // Global styles

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

  return (
    <div className="container-fluid p-0"> {/* Full width wrapper */}
      <AnimatedBackground /> {/* Dynamic Finance Background */}
      <Ticker /> {/* Top Ticker */}

      {/* Header Full Width Wrapper */}
      <div className="container-fluid px-4 pt-4">
        <Header onOpenDashboard={() => { }} />
      </div>

      {/* Live Charts Grid - Main Page */}
      <div className="container-fluid px-4 mb-4">
        <ChartCarousel macro={macro} />
      </div>

      {/* ML Model Performance Section */}
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

        {/* Hidden Dashboard Modal */}
        <MarketDashboard items={items} macro={macro} />
      </div>
    </div>
  );
};

export default App;
