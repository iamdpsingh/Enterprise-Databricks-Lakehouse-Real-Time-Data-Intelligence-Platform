import React from 'react';
import Link from 'next/link';

export default function Sidebar() {
  return (
    <aside className="sidebar glass-panel">
      <div className="sidebar-header">
        <h2>Lakehouse UI</h2>
      </div>
      <nav className="sidebar-nav">
        <Link href="/" className="nav-link">
          <span className="icon">📊</span>
          Overview
        </Link>
        <Link href="/quality" className="nav-link">
          <span className="icon">🛡️</span>
          Data Quality
        </Link>
      </nav>
      <div className="sidebar-footer">
        <p>Enterprise Databricks</p>
      </div>
    </aside>
  );
}
