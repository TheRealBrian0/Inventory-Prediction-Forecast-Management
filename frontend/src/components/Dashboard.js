import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import Plotly from 'plotly.js-basic-dist';
import createPlotlyComponent from 'react-plotly.js/factory';
import { getMetrics, getForecasts } from '../services/api';
import './Dashboard.css';

const Plot = createPlotlyComponent(Plotly);

function Dashboard() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [metrics, setMetrics] = useState(null);
  const [forecasts, setForecasts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const storeId = searchParams.get('store_id') || 'S001';

  useEffect(() => {
    fetchData();
  }, [storeId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [metricsRes, forecastsRes] = await Promise.all([
        getMetrics({ store_id: storeId }),
        getForecasts({ store_id: storeId })
      ]);
      setMetrics(metricsRes.data);
      setForecasts(forecastsRes.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleStoreChange = (newStoreId) => {
    setSearchParams({ store_id: newStoreId });
  };

  const getStatusClass = (recommendation) => {
    if (recommendation.includes('SUFFICIENT')) return 'sufficient';
    if (recommendation.includes('REORDER NOW') || recommendation.includes('PREPARE TO ORDER')) return 'reorder';
    if (recommendation.includes('URGENT')) return 'critical';
    return '';
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="dashboard">
      <div className="header">
        <h2>Inventory Status Dashboard</h2>
        <select value={storeId} onChange={(e) => handleStoreChange(e.target.value)}>
          <option value="S001">S001</option>
          <option value="S002">S002</option>
          <option value="S003">S003</option>
          <option value="S004">S004</option>
          <option value="S005">S005</option>
        </select>
      </div>

      {metrics && (
        <div className="metrics">
          <div className="metric">Total Products: {metrics.total_products}</div>
          <div className="metric">At Risk: {metrics.products_at_risk}</div>
          <div className="metric">Low Stock: {metrics.products_low_stock}</div>
          <div className="metric">Healthy: {metrics.products_healthy}</div>
        </div>
      )}

      <div className="forecasts-grid">
        {forecasts.map((forecast) => (
          <Link key={forecast.product_id} to={`/product/${forecast.product_id}?store_id=${storeId}`} className="forecast-card">
            <h3>SKU-{forecast.product_id.slice(1)}</h3>
            <p>Store: {forecast.store_id}</p>
            <p>Inventory: {forecast.current_inventory.toLocaleString()}</p>
            <p>Days Until Stockout: {forecast.days_until_stockout_display}</p>
            <p className={`status ${getStatusClass(forecast.recommendation)}`}>
              {forecast.recommendation}
            </p>
            {forecast.days_until_stockout < 14 && forecast.available_stores_categorized && (
              <div className="tooltip">
                <div className="tooltip-section">
                  <strong>Same Region:</strong> {forecast.available_stores_categorized.same_region.join(', ') || 'None'}
                </div>
                <div className="tooltip-section">
                  <strong>Stocked:</strong> {forecast.available_stores_categorized.other.join(', ') || 'None'}
                </div>
                <div className="tooltip-section">
                  <strong>No Stock:</strong> {forecast.available_stores_categorized.no_stock.join(', ') || 'None'}
                </div>
              </div>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}

export default Dashboard;