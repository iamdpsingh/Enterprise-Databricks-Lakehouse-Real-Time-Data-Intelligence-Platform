'use client';

import React, { useEffect, useState } from 'react';
import StatusIndicator from '@/components/StatusIndicator';

import { getQuarantineMetrics } from '@/actions/metrics';

interface QuarantineRecord {
  _quarantine_reason: string;
  _quarantine_timestamp: string;
  order_id: string | null;
  customer_id: string | null;
}

export default function QualityDashboard() {
  const [records, setRecords] = useState<QuarantineRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getQuarantineMetrics().then(res => {
      setRecords(res);
      setLoading(false);
    }).catch(err => {
      console.error("Failed to fetch quality metrics:", err);
      setLoading(false);
    });
  }, []);

  return (
    <main className="dashboard-container">
      <header className="dashboard-header animate-fade-in">
        <div>
          <h1 className="dashboard-title">Data Quality Monitor</h1>
          <p className="dashboard-subtitle">Real-time Quarantine (Dead-Letter) Queue</p>
        </div>
        <StatusIndicator />
      </header>

      <div className="glass-panel animate-fade-in delay-1">
        <h3 className="metric-title" style={{ marginBottom: '24px' }}>Recent Quarantined Records</h3>
        
        {loading ? (
          <p style={{ textAlign: 'center', color: '#94a3b8', padding: '20px' }}>Loading quarantine queue...</p>
        ) : (
          <div className="table-container">
            <table className="glass-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Order ID</th>
                  <th>Customer ID</th>
                  <th>Failure Reason</th>
                </tr>
              </thead>
              <tbody>
                {records.map((record, index) => (
                  <tr key={index}>
                    <td>{new Date(record._quarantine_timestamp).toLocaleString()}</td>
                    <td>{record.order_id || <span className="null-value">NULL</span>}</td>
                    <td>{record.customer_id || <span className="null-value">NULL</span>}</td>
                    <td className="error-text">{record._quarantine_reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  );
}
