'use client';

import React, { useEffect, useState } from 'react';
import { getPlatformMetrics } from '@/actions/metrics';

export default function StatusIndicator() {
  const [status, setStatus] = useState('Connecting...');

  useEffect(() => {
    const checkStatus = () => {
      getPlatformMetrics().then(res => {
        if (!res || res.totalRecords === 'N/A') {
          setStatus('Disconnected');
        } else {
          setStatus('Healthy');
        }
      }).catch(() => setStatus('Disconnected'));
    };

    checkStatus();
    const intervalId = setInterval(checkStatus, 5000);
    return () => clearInterval(intervalId);
  }, []);

  let color = '#fb923c'; // Connecting
  let bg = 'rgba(251, 146, 60, 0.1)';
  let border = 'rgba(251, 146, 60, 0.2)';

  if (status === 'Healthy') {
    color = '#10b981';
    bg = 'rgba(16, 185, 129, 0.1)';
    border = 'rgba(16, 185, 129, 0.2)';
  } else if (status === 'Disconnected') {
    color = '#ef4444';
    bg = 'rgba(239, 68, 68, 0.1)';
    border = 'rgba(239, 68, 68, 0.2)';
  }

  return (
    <div 
      className="status-indicator animate-fade-in" 
      style={{ color: color, background: bg, borderColor: border }}
    >
      <div 
        className="status-dot" 
        style={{ 
          background: color,
          boxShadow: `0 0 8px ${color}`
        }}
      ></div>
      Pipeline: {status}
    </div>
  );
}
