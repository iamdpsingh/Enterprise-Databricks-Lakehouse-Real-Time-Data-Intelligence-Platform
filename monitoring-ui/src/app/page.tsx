'use client';

import React from 'react';
import MetricCard from '@/components/MetricCard';
import StatusIndicator from '@/components/StatusIndicator';
import { motion } from 'framer-motion';

export default function Dashboard() {
  const datasetStatuses = [
    { name: 'Ethereum Web3', rows: '12B+', rate: '4k/sec', status: 'Streaming (GCP)' },
    { name: 'GitHub Archive', rows: '8B+', rate: '2.1k/sec', status: 'Streaming (GCP)' },
    { name: 'Overture Maps', rows: '500M+', rate: 'Batch/Daily', status: 'Healthy (GCP)' },
    { name: 'Reddit Pushshift', rows: '3B+', rate: '500/sec', status: 'Streaming (GCP)' }
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  };

  return (
    <main className="dashboard-container">
      <header className="dashboard-header animate-fade-in">
        <div>
          <h1 className="dashboard-title">Data Intelligence Command Center</h1>
          <p className="dashboard-subtitle">Monitoring 4 Global Datasets via Databricks & Google Cloud (GCP)</p>
        </div>
        <StatusIndicator />
      </header>

      <motion.div 
        className="metrics-grid"
        variants={containerVariants}
        initial="hidden"
        animate="show"
      >
        <motion.div variants={itemVariants}>
          <MetricCard 
            title="Total Records Governed" 
            value="23.5B+" 
            trend={5.2}
            delayClass=""
          />
        </motion.div>
        <motion.div variants={itemVariants}>
          <MetricCard 
            title="Real-Time Ingestion Rate" 
            value="6,600 msg/sec" 
            trend={12.4}
            delayClass=""
          />
        </motion.div>
        <motion.div variants={itemVariants}>
          <MetricCard 
            title="Compute Nodes (GCP)" 
            value="48 Workers" 
            trend={0}
            delayClass=""
          />
        </motion.div>
      </motion.div>
      
      <motion.div 
        variants={itemVariants}
        initial="hidden"
        animate="show"
        className="glass-panel" 
        style={{ marginTop: '24px' }}
      >
        <h3 style={{ marginBottom: '24px', fontSize: '1.2rem', color: '#fff' }}>Dataset Pipeline Status</h3>
        <div className="table-container">
          <table className="glass-table">
            <thead>
              <tr>
                <th>Dataset</th>
                <th>Volume</th>
                <th>Ingestion Rate</th>
                <th>Compute Platform</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {datasetStatuses.map((ds, idx) => (
                <tr key={idx}>
                  <td style={{ fontWeight: 500 }}>{ds.name}</td>
                  <td>{ds.rows}</td>
                  <td>{ds.rate}</td>
                  <td>GCP (us-central1)</td>
                  <td>
                    <span style={{ 
                      display: 'inline-block',
                      padding: '4px 12px', 
                      borderRadius: '999px',
                      background: 'rgba(16, 185, 129, 0.1)',
                      color: '#10b981',
                      fontSize: '0.8rem',
                      fontWeight: 600
                    }}>
                      {ds.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>
    </main>
  );
}

