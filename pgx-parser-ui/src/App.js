import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import LoginPage from './components/LoginPage';
import PgxExtractor from './components/PgxExtractor';
import FolderBatchProcessor from './components/FolderBatchProcessor';
import UserManagement from './components/UserManagement';
import './styles/app.css';

function AppContent() {
  const [activeTab, setActiveTab] = useState('extractor');
  const { user, logout, isAdmin, loading, isAuthenticated } = useAuth();

  // Show loading state
  if (loading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="header-title">
            <h1>PGX Parser</h1>
            <p>Pharmacogenomics Report Processing</p>
          </div>
          <div className="header-user">
            <span className="user-info">
              {user?.username}
              {isAdmin() && <span className="admin-tag">Admin</span>}
            </span>
            <button className="logout-btn" onClick={logout}>
              Logout
            </button>
          </div>
        </div>
      </header>
      <main className="app-main">
        <div className="tabs">
          <button 
            className={`tab ${activeTab === 'extractor' ? 'active' : ''}`}
            onClick={() => setActiveTab('extractor')}
          >
            PGX Gene Extractor
          </button>
          <button 
            className={`tab ${activeTab === 'folder-batch' ? 'active' : ''}`}
            onClick={() => setActiveTab('folder-batch')}
          >
            Folder Batch Processor
          </button>
          {isAdmin() && (
            <button 
              className={`tab ${activeTab === 'users' ? 'active' : ''}`}
              onClick={() => setActiveTab('users')}
            >
              User Management
            </button>
          )}
        </div>
        <div className="tab-content">
          {activeTab === 'extractor' && <PgxExtractor />}
          {activeTab === 'folder-batch' && <FolderBatchProcessor />}
          {activeTab === 'users' && isAdmin() && <UserManagement />}
        </div>
      </main>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;