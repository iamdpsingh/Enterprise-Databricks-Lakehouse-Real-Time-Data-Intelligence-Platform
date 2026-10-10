'use client';

import React, { useState, useEffect } from 'react';
import MetricCard from '@/components/MetricCard';
import StatusIndicator from '@/components/StatusIndicator';
import { motion } from 'framer-motion';

export default function OvertureDashboard() {
  const [data, setData] = useState({ pois: '0', quarantined: '0', categories: '0' });

  useEffect(() => {
    setTimeout(() => {
      setData({ pois: '502.1M', quarantined: '1.2M', categories: '1,420' });
    }, 1000);
  }, []);

  const containerVariants = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.1 } } };
  const itemVariants = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } };

  return (
    <main className="dashboard-container">
      <header className="dashboard-header animate-fade-in">
        <div>
          <h1 className="dashboard-title" style={{ color: '#f43f5e' }}>Overture Maps Pipeline</h1>
          <p className="dashboard-subtitle">Geospatial Parquet analytics and data quality</p>
        </div>
        <StatusIndicator />
      </header>

      <motion.div className="metrics-grid" variants={containerVariants} initial="hidden" animate="show">
        <motion.div variants={itemVariants}>
          <MetricCard title="Total POIs" value={data.pois} trend={0.5} delayClass="" />
        </motion.div>
        <motion.div variants={itemVariants}>
          <MetricCard title="Unique Categories" value={data.categories} trend={2.4} delayClass="" />
        </motion.div>
        <motion.div variants={itemVariants}>
          <MetricCard title="Quarantined (Invalid Bounds)" value={data.quarantined} trend={-15.2} delayClass="" />
        </motion.div>
      </motion.div>
      
      <motion.div variants={itemVariants} initial="hidden" animate="show" className="glass-panel" style={{ marginTop: '24px' }}>
        <h3 style={{ marginBottom: '16px', color: '#fff' }}>Geospatial Rules Engine</h3>
        <p style={{ color: '#94a3b8', lineHeight: '1.6' }}>
          Overture Parquet data undergoes strict boundary validation in the Silver layer. 
          Records with invalid latitude (-90 to 90) or longitude (-180 to 180) are instantly routed to the quarantine tables.
        </p>
      </motion.div>
    </main>
  );
}
