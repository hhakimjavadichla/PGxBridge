import React, { useState } from 'react';
import PgxProcessor from './components/PgxProcessor';
import PgxExtractor from './components/PgxExtractor';

function App() {
  const [activeTab, setActiveTab] = useState('processor');

  return (
    <div className="app">
      <header className="app-header">
        <h1>PGX Parser</h1>
        <p>Filter PDF pages by keyword and analyze with Azure Document Intelligence</p>
      </header>
      <main className="app-main">
        <div className="tabs">
          <button 
            className={`tab ${activeTab === 'processor' ? 'active' : ''}`}
            onClick={() => setActiveTab('processor')}
          >
            Document Processor
          </button>
          <button 
            className={`tab ${activeTab === 'extractor' ? 'active' : ''}`}
            onClick={() => setActiveTab('extractor')}
          >
            PGX Gene Extractor
          </button>
        </div>
        <div className="tab-content">
          {activeTab === 'processor' ? <PgxProcessor /> : <PgxExtractor />}
        </div>
      </main>
    </div>
  );
}

export default App;