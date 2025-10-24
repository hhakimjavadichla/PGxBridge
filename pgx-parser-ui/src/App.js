import React, { useState } from 'react';
import PgxProcessor from './components/PgxProcessor';
import PgxExtractor from './components/PgxExtractor';
import FolderBatchProcessor from './components/FolderBatchProcessor';

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
          <button 
            className={`tab ${activeTab === 'folder-batch' ? 'active' : ''}`}
            onClick={() => setActiveTab('folder-batch')}
          >
            Folder Batch Processor
          </button>
        </div>
        <div className="tab-content">
          {activeTab === 'processor' && <PgxProcessor />}
          {activeTab === 'extractor' && <PgxExtractor />}
          {activeTab === 'folder-batch' && <FolderBatchProcessor />}
        </div>
      </main>
    </div>
  );
}

export default App;