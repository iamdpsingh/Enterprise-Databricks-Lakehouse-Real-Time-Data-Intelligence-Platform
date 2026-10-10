'use client';

import React from 'react';
import MetricCard from '@/components/MetricCard';
import StatusIndicator from '@/components/StatusIndicator';
import { motion } from 'framer-motion';

import { getPlatformMetrics } from '@/actions/metrics';

export default function Dashboard() {
  const [metrics, setMetrics] = React.useState<any>({ 
    totalRecords: 'Loading...', 
    latestSync: 'Loading...',
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

  const getStatus = (rate: string, defaultHealthy: string = 'Healthy (GCP)') => {
    if (metrics.totalRecords === 'Loading...') return 'Connecting...';
    if (metrics.totalRecords === 'N/A') return 'Disconnected';
    if (rate === 'Calculating...') return 'Calculating...';
    if (rate === '0 msg/sec') return defaultHealthy;
    return 'Streaming (GCP)';
  };

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'Streaming (GCP)':
      case 'Healthy (GCP)':
        return { bg: 'rgba(16, 185, 129, 0.1)', text: '#10b981' };
      case 'Disconnected':
        return { bg: 'rgba(239, 68, 68, 0.1)', text: '#ef4444' };
      case 'Connecting...':
      case 'Calculating...':
        return { bg: 'rgba(251, 146, 60, 0.1)', text: '#fb923c' };
      default:
        return { bg: 'rgba(148, 163, 184, 0.1)', text: '#94a3b8' }; // Idling/Other
    }
  };

  const datasetStatuses = [
    { name: 'Ethereum Web3', rows: metrics.ethRows, rate: rates.ethRate, status: getStatus(rates.ethRate, 'Idling (GCP)') },
    { name: 'GitHub Archive', rows: metrics.ghRows, rate: rates.ghRate, status: getStatus(rates.ghRate, 'Idling (GCP)') },
    { name: 'Overture Maps', rows: metrics.ovRows, rate: rates.ovRate, status: getStatus(rates.ovRate, 'Healthy (GCP)') }
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
            title="Last Databricks Sync" 
            value={metrics.latestSync} 
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
                  <td>Databricks/GCP (us-central1)</td>
                  <td>
                    <span style={{ 
                      display: 'inline-block',
                      padding: '4px 12px', 
                      borderRadius: '999px',
                      background: getStatusColor(ds.status).bg,
                      color: getStatusColor(ds.status).text,
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

