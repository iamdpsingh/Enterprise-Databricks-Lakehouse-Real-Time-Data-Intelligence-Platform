import React from 'react';

interface MetricCardProps {
  title: string;
  value: string | number;
  trend?: number;
  delayClass?: string;
}

export default function MetricCard({ title, value, trend, delayClass = '' }: MetricCardProps) {
  const isPositive = trend !== undefined && trend >= 0;
  
  return (
    <div className={`glass-panel metric-card animate-fade-in ${delayClass}`}>
      <h3 className="metric-title">{title}</h3>
      <p className="metric-value">{value}</p>
      
      {trend !== undefined && trend !== 0 && (
        <div className={`metric-trend ${isPositive ? 'trend-up' : 'trend-down'}`}>
          <span>{isPositive ? '↑' : '↓'}</span>
          <span>{Math.abs(trend)}% vs last week</span>
        </div>
      )}
    </div>
  );
}
