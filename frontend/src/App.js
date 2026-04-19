import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import ProductDetail from './components/ProductDetail';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>SYSCO Inventory Forecasting</h1>
        <button className="login-btn">Log In</button>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/product/:productId" element={<ProductDetail />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;