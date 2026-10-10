'use client';

import React, { useState, useEffect } from 'react';
import MetricCard from '@/components/MetricCard';
import StatusIndicator from '@/components/StatusIndicator';
import { motion } from 'framer-motion';

import { getRedditMetrics } from '@/actions/metrics';

export default function RedditDashboard() {
  const [data, setData] = useState({ posts: 'Loading...', avgScore: 'Loading...', maskedUsers: 'Loading...' });

  useEffect(() => {
    getRedditMetrics().then(res => {
      setData(res);
    });
  }, []);

  const containerVariants = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.1 } } };
  const itemVariants = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } };

  return (
    <main className="dashboard-container">
      <header className="dashboard-header animate-fade-in">
        <div>
          <h1 className="dashboard-title" style={{ color: '#fb923c' }}>Reddit Pushshift Pipeline</h1>
          <p className="dashboard-subtitle">NLP cleaning, PII Masking, and SCD Type 2 CDC</p>
        </div>
        <StatusIndicator />
      </header>

      <motion.div className="metrics-grid" variants={containerVariants} initial="hidden" animate="show">
        <motion.div variants={itemVariants}>
          <MetricCard title="Total Posts Processed" value={data.posts} trend={4.2} delayClass="" />
        </motion.div>
        <motion.div variants={itemVariants}>
          <MetricCard title="Global Avg Score" value={data.avgScore} trend={1.1} delayClass="" />
        </motion.div>
        <motion.div variants={itemVariants}>
          <MetricCard title="Users PII Masked" value={data.maskedUsers} trend={0} delayClass="" />
        </motion.div>
      </motion.div>
      
      <motion.div variants={itemVariants} initial="hidden" animate="show" className="glass-panel" style={{ marginTop: '24px' }}>
        <h3 style={{ marginBottom: '16px', color: '#fff' }}>CDC & PII Transformation</h3>
        <p style={{ color: '#94a3b8', lineHeight: '1.6' }}>
          Data is ingested via custom RestApiReader. In Silver, HTML is stripped, emails are pseudonymized, 
          and records are merged via SCD Type 2. Gold layer calculates daily community sentiment and activity.
        </p>
      </motion.div>
    </main>
  );
}
