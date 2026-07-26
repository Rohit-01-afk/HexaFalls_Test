"use client";

import React, { useState, useEffect } from 'react';
import { LandingPage, BrandIconSvg } from '../components/LandingPage';
import { RedesignedDashboard } from '../components/RedesignedDashboard';

export default function AppMasterPage() {
  const [mounted, setMounted] = useState(false);
  const [currentView, setCurrentView] = useState('landing'); // 'landing' | 'dashboard'
  const [token, setToken] = useState('demo-jwt-token-blueprint-2026');
  const [username, setUsername] = useState('engineer_guest');

  useEffect(() => {
    // 1-second display timer for smooth loading screen experience
    const timer = setTimeout(() => {
      setMounted(true);
    }, 1000);
    return () => clearTimeout(timer);
  }, []);

  if (!mounted) {
    return (
      <div
        className="vh-100 vw-100 d-flex flex-column align-items-center justify-content-center text-light font-monospace"
        style={{ backgroundColor: 'var(--bg-deep, #060c06)' }}
      >
        <div className="d-flex flex-column align-items-center gap-3">
          <BrandIconSvg size={56} />
          <div className="d-flex align-items-center gap-2 mt-2">
            <div className="spinner-border spinner-border-sm text-emerald" role="status" style={{ width: '1rem', height: '1rem' }} />
            <span className="text-light fw-bold fs-6">Initializing <span className="text-emerald">BluePrint Ai</span> Engine...</span>
          </div>
        </div>
      </div>
    );
  }

  const handleLoginSuccess = (tok, user) => {
    setToken(tok);
    setUsername(user);
  };

  return (
    <>
      {currentView === 'landing' ? (
        <LandingPage
          onLaunchDashboard={() => setCurrentView('dashboard')}
          onLoginSuccess={handleLoginSuccess}
        />
      ) : (
        <RedesignedDashboard
          token={token}
          username={username}
          onSignOut={() => {
            setToken(null);
            setUsername(null);
            setCurrentView('landing');
          }}
          onReturnToLanding={() => setCurrentView('landing')}
        />
      )}
    </>
  );
}
