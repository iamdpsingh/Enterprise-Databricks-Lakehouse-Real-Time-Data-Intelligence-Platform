'use client';

import React from 'react';
import MetricCard from '@/components/MetricCard';
import StatusIndicator from '@/components/StatusIndicator';
import { motion } from 'framer-motion';

import { getPlatformMetrics } from '@/actions/metrics';

export default function Dashboard() {
  const [metrics, setMetrics] = React.useState<any>({ 
    totalRecords: 'Loading...', 
    computeNodes: 'Loading...',
    ethRows: 'Loading...',
    ghRows: 'Loading...',
    ovRows: 'Loading...'
  });

  const [rates, setRates] = React.useState({
    totalRate: 'Calculating...',
    ethRate: 'Calculating...',
    ghRate: 'Calculating...',
    ovRate: 'Calculating...'
  });

  const previousMetrics = React.useRef<any>(null);

  React.useEffect(() => {
    const fetchMetrics = () => {
      getPlatformMetrics().then(res => {
        if (res.totalRecords !== 'N/A') {
          if (previousMetrics.current && previousMetrics.current.totalRecords !== 'N/A') {
            const calcRate = (current: string, prev: string) => {
              const diff = parseInt(current) - parseInt(prev);
              return Math.max(0, Math.floor(diff / 5));
            };
            
            setRates({
              totalRate: `${calcRate(res.totalRecords, previousMetrics.current.totalRecords)} msg/sec`,
              ethRate: `${calcRate(res.ethRows, previousMetrics.current.ethRows)} msg/sec`,
              ghRate: `${calcRate(res.ghRows, previousMetrics.current.ghRows)} msg/sec`,
              ovRate: `${calcRate(res.ovRows, previousMetrics.current.ovRows)} msg/sec`
            });
          } else {
            setRates({
              totalRate: '0 msg/sec',
              ethRate: '0 msg/sec',
              ghRate: '0 msg/sec',
              ovRate: '0 msg/sec'
            });
          }
          previousMetrics.current = res;
        } else {
          setRates({
            totalRate: 'N/A',
            ethRate: 'N/A',
            ghRate: 'N/A',
            ovRate: 'N/A'
          });
        }
        setMetrics(res);
      }).catch(() => {});
    };
    
    fetchMetrics(); // Initial fetch
    const intervalId = setInterval(fetchMetrics, 5000); // Poll every 5 seconds
    
    return () => clearInterval(intervalId); // Cleanup on unmount
  }, []);

  const datasetStatuses = [
    { name: 'Ethereum Web3', rows: metrics.ethRows, rate: rates.ethRate, status: 'Streaming (GCP)' },
    { name: 'GitHub Archive', rows: metrics.ghRows, rate: rates.ghRate, status: 'Streaming (GCP)' },
    { name: 'Overture Maps', rows: metrics.ovRows, rate: rates.ovRate, status: 'Healthy (GCP)' }
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
          <p className="dashboard-subtitle">Monitoring 3 Global Datasets via Databricks & Google Cloud (GCP)</p>
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
            value={metrics.totalRecords} 
            trend={0}
            delayClass=""
          />
        </motion.div>
        <motion.div variants={itemVariants}>
          <MetricCard 
            title="Real-Time Ingestion Rate" 
            value={rates.totalRate} 
            trend={0}
            delayClass=""
          />
        </motion.div>
        <motion.div variants={itemVariants}>
          <MetricCard 
            title="Compute Nodes (GCP)" 
            value={metrics.computeNodes} 
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

