'use client';
import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  ShieldCheck, 
  Network, 
  GitBranch, 
  Map, 
  MessageSquare,
  Server
} from 'lucide-react';

export default function Sidebar() {
  const pathname = usePathname();

  const navItems = [
    { href: '/', label: 'Platform Overview', icon: LayoutDashboard },
    { href: '/ethereum', label: 'Ethereum Web3', icon: Network },
    { href: '/github', label: 'GitHub Archive', icon: GitBranch },
    { href: '/overture', label: 'Overture Maps', icon: Map },
    { href: '/reddit', label: 'Reddit Pushshift', icon: MessageSquare },
    { href: '/quality', label: 'Data Quality', icon: ShieldCheck },
  ];

  return (
    <aside className="sidebar glass-panel">
      <div className="sidebar-header">
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Server size={24} color="#6366f1" />
          Data Intel
        </h2>
      </div>
      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link 
              key={item.href} 
              href={item.href} 
              className={`nav-link ${isActive ? 'active' : ''}`}
              style={{
                background: isActive ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                color: isActive ? '#fff' : '#94a3b8',
                borderLeft: isActive ? '3px solid #6366f1' : '3px solid transparent'
              }}
            >
              <Icon size={18} className="icon" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="sidebar-footer" style={{ marginTop: 'auto' }}>
        <p>Compute: <strong>GCP (Google Cloud)</strong></p>
        <p style={{ marginTop: '8px', fontSize: '0.75rem' }}>Engine: Databricks</p>
      </div>
    </aside>
  );
}
