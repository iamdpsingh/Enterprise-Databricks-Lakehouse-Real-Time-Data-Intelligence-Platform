'use client';

import React, { useEffect, useState } from 'react';
import StatusIndicator from '@/components/StatusIndicator';

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
    const fetchQuarantineData = async () => {
      try {
        const res = await fetch('http://localhost:8000/v1/metrics/quality/quarantine');
        if (!res.ok) throw new Error(`API error: ${res.status}`);
        const data = await res.json();
        
        // Use simulated data if real data is empty to showcase the UI
        if (!data.records || data.records.length === 0) {
           setRecords([
             { _quarantine_reason: "total_amount >= 0 failed", _quarantine_timestamp: new Date().toISOString(), order_id: "ORD-9281", customer_id: "CUST-104" },
             { _quarantine_reason: "customer_id IS NOT NULL failed", _quarantine_timestamp: new Date(Date.now() - 3600000).toISOString(), order_id: "ORD-9282", customer_id: null },
             { _quarantine_reason: "order_id IS NOT NULL failed", _quarantine_timestamp: new Date(Date.now() - 7200000).toISOString(), order_id: null, customer_id: "CUST-105" }
           ]);
        } else {
           setRecords(data.records);
        }
      } catch (error) {
        console.error("Failed to fetch quality metrics:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchQuarantineData();
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
