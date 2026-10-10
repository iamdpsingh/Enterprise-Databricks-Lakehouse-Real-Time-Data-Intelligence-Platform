'use client';

import React, { useState, useEffect } from 'react';
import MetricCard from '@/components/MetricCard';
import StatusIndicator from '@/components/StatusIndicator';
import { motion } from 'framer-motion';

import { getGithubMetrics } from '@/actions/metrics';

export default function GithubDashboard() {
  const [data, setData] = useState({ events: 'Loading...', uniqueRepos: 'Loading...', pushEvents: 'Loading...' });

  useEffect(() => {
    getGithubMetrics().then(res => {
      setData(res);
    });
  }, []);

  const containerVariants = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.1 } } };
  const itemVariants = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } };

  return (
    <main className="dashboard-container">
      <header className="dashboard-header animate-fade-in">
        <div>
          <h1 className="dashboard-title" style={{ color: '#10b981' }}>GitHub Archive Pipeline</h1>
          <p className="dashboard-subtitle">Global developer activity and repository metrics</p>
        </div>
        <StatusIndicator />
      </header>

      <motion.div className="metrics-grid" variants={containerVariants} initial="hidden" animate="show">
        <motion.div variants={itemVariants}>
          <MetricCard title="Total Events Processed" value={data.events} trend={5.2} delayClass="" />
        </motion.div>
        <motion.div variants={itemVariants}>
          <MetricCard title="Active Repositories" value={data.uniqueRepos} trend={1.1} delayClass="" />
        </motion.div>
        <motion.div variants={itemVariants}>
          <MetricCard title="Push Events (All Time)" value={data.pushEvents} trend={8.9} delayClass="" />
        </motion.div>
      </motion.div>
      
      <motion.div variants={itemVariants} initial="hidden" animate="show" className="glass-panel" style={{ marginTop: '24px' }}>
        <h3 style={{ marginBottom: '16px', color: '#fff' }}>Processing Details</h3>
        <p style={{ color: '#94a3b8', lineHeight: '1.6' }}>
          GitHub Archive JSON is ingested via AutoLoader with `schemaEvolutionMode: "addNewColumns"`. 
          Nested structures are flattened and deduplicated in Silver before daily aggregation in the Gold layer.
        </p>
      </motion.div>
    </main>
  );
}
