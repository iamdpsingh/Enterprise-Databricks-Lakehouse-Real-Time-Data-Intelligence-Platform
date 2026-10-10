'use client';

import React, { useState, useEffect } from 'react';
import MetricCard from '@/components/MetricCard';
import StatusIndicator from '@/components/StatusIndicator';
import { motion } from 'framer-motion';

import { getEthereumMetrics } from '@/actions/metrics';

export default function EthereumDashboard() {
  const [data, setData] = useState({ totalTransfers: 'Loading...', avgGas: 'Loading...', txCount: 'Loading...' });

  useEffect(() => {
    const fetchMetrics = () => {
      getEthereumMetrics().then(res => {
        setData(res);
      });
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  const containerVariants = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.1 } } };
  const itemVariants = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } };

  return (
    <main className="dashboard-container">
      <header className="dashboard-header animate-fade-in">
        <div>
          <h1 className="dashboard-title" style={{ color: '#6366f1' }}>Ethereum Web3 Pipeline</h1>
          <p className="dashboard-subtitle">Real-time blockchain event processing (Silver & Gold Layers)</p>
        </div>
        <StatusIndicator />
      </header>

      <motion.div className="metrics-grid" variants={containerVariants} initial="hidden" animate="show">
        <motion.div variants={itemVariants}>
          <MetricCard title="Total ETH Transferred (24h)" value={data.totalTransfers} trend={0} delayClass="" />
        </motion.div>
        <motion.div variants={itemVariants}>
          <MetricCard title="Average Gas Used" value={data.avgGas} trend={0} delayClass="" />
        </motion.div>
        <motion.div variants={itemVariants}>
          <MetricCard title="Transaction Count" value={data.txCount} trend={0} delayClass="" />
        </motion.div>
      </motion.div>

      <motion.div variants={itemVariants} initial="hidden" animate="show" className="glass-panel" style={{ marginTop: '24px' }}>
        <h3 style={{ marginBottom: '16px', color: '#fff' }}>Pipeline Health</h3>
        <p style={{ color: '#94a3b8', lineHeight: '1.6' }}>
          The Ethereum Bronze layer is currently utilizing AutoLoader with `schemaEvolutionMode: "rescue"`. 
          Hex-to-long casting is actively functioning in the Silver layer, feeding the Gold aggregations running on GCP.
        </p>
      </motion.div>
    </main>
  );
}
