'use client';

import React, { useEffect, useState } from 'react';
import MetricCard from '@/components/MetricCard';
import StatusIndicator from '@/components/StatusIndicator';

interface CustomerMetrics {
  total_lifetime_value: number;
  total_orders: number;
  active_users: number;
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState<CustomerMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate fetching from our FastAPI backend
    const fetchMetrics = async () => {
      try {
        // In production, this would be: await fetch('http://localhost:8000/v1/metrics/customer/all')
        // We'll simulate a slight network delay and return mock data for demonstration
        await new Promise(resolve => setTimeout(resolve, 800));
        
        setMetrics({
          total_lifetime_value: 1254300.50,
          total_orders: 8432,
          active_users: 1240,
        });
      } catch (error) {
        console.error("Failed to fetch metrics:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, []);

  return (
    <main className="dashboard-container">
      <header className="dashboard-header animate-fade-in">
        <div>
          <h1 className="dashboard-title">Intelligence Overview</h1>
          <p className="dashboard-subtitle">Real-time Databricks Lakehouse metrics</p>
        </div>
        <StatusIndicator />
      </header>

      {loading ? (
        <div className="glass-panel animate-fade-in" style={{ textAlign: 'center', padding: '40px' }}>
          Loading insights...
        </div>
      ) : (
        <div className="metrics-grid">
          <MetricCard 
            title="Total Lifetime Value (USD)" 
            value={`$${(metrics?.total_lifetime_value || 0).toLocaleString()}`} 
            trend={12.5}
            delayClass="delay-1"
          />
          <MetricCard 
            title="Total Orders Processed" 
            value={(metrics?.total_orders || 0).toLocaleString()} 
            trend={8.2}
            delayClass="delay-2"
          />
          <MetricCard 
            title="Active Users (30d)" 
            value={(metrics?.active_users || 0).toLocaleString()} 
            trend={-2.1}
            delayClass="delay-3"
          />
        </div>
      )}
      
      <div className="glass-panel animate-fade-in delay-3" style={{ minHeight: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: '#94a3b8' }}>Interactive Data Visualizations would render here.</p>
      </div>
    </main>
  );
}
