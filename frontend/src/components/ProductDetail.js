import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams, Link } from 'react-router-dom';
import Plotly from 'plotly.js-basic-dist';
import createPlotlyComponent from 'react-plotly.js/factory';
import { getProductForecast } from '../services/api';
import './ProductDetail.css';

const Plot = createPlotlyComponent(Plotly);

function ProductDetail() {
  const { productId } = useParams();
  const [searchParams] = useSearchParams();
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const storeId = searchParams.get('store_id') || 'S001';

  useEffect(() => {
    fetchForecast();
  }, [productId, storeId]);

  const fetchForecast = async () => {
    try {
      setLoading(true);
      const res = await getProductForecast(productId, { store_id: storeId });
      setForecast(res.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!forecast) return <div>No forecast available</div>;

  const chartData = {
    data: [
      {
        x: forecast.historical_dates,
        y: forecast.historical_values,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Historical Units Sold',
      },
      {
        x: forecast.forecast_dates,
        y: forecast.forecast_values,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Forecast',
      },
      {
        x: forecast.forecast_dates.concat(forecast.forecast_dates.slice().reverse()),
        y: forecast.forecast_upper.concat(forecast.forecast_lower.slice().reverse()),
        fill: 'toself',
        fillcolor: 'rgba(245, 158, 11, 0.20)',
        line: { color: 'rgba(245, 158, 11, 0)' },
        name: 'Confidence Interval',
        type: 'scatter',
        hoverinfo: 'skip',
      },
    ],
    layout: {
      title: `Demand Forecast for SKU-${forecast.product_id.slice(1)}`,
      xaxis: { title: 'Date' },
      yaxis: { title: 'Units Sold' },
    },
  };

  return (
    <div className="product-detail">
      <Link to={`/?store_id=${storeId}`} className="back-button">Back to Dashboard</Link>
      <h2>Product Detail: SKU-{forecast.product_id.slice(1)}</h2>
      <p>Store: {forecast.store_id}</p>

      <div className="metrics">
        <div className="metric">Current Inventory: {forecast.current_inventory.toLocaleString()}</div>
        <div className="metric">Days Until Stockout: {forecast.days_until_stockout_display}</div>
        <div className="metric">Avg Daily Demand: {forecast.avg_daily_demand}</div>
      </div>

      <div className="chart">
        <Plot data={chartData.data} layout={chartData.layout} />
      </div>

      <div className="forecast-table">
        <h3>Forecast Table</h3>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Predicted</th>
              <th>Lower</th>
              <th>Upper</th>
            </tr>
          </thead>
          <tbody>
            {forecast.forecast_dates.map((date, i) => (
              <tr key={date}>
                <td>{date}</td>
                <td>{forecast.forecast_values[i]}</td>
                <td>{forecast.forecast_lower[i]}</td>
                <td>{forecast.forecast_upper[i]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default ProductDetail;