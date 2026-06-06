import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = 'https://nl-sql-engine-jay1.onrender.com';

function App() {
  const [question, setQuestion] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const [activeTab, setActiveTab] = useState('query');

  // CSV state
  const [csvFile, setCsvFile] = useState(null);
  const [csvTable, setCsvTable] = useState(null);
  const [csvQuestion, setCsvQuestion] = useState('');
  const [csvResults, setCsvResults] = useState([]);
  const [csvLoading, setCsvLoading] = useState(false);
  const [csvUploading, setCsvUploading] = useState(false);
  const [csvError, setCsvError] = useState(null);

  useEffect(() => {
    if (activeTab === 'history') {
      fetchHistory();
    }
  }, [activeTab]);

  const fetchHistory = async () => {
    try {
      const [histRes, statsRes] = await Promise.all([
        axios.get(`${API_URL}/history`),
        axios.get(`${API_URL}/history/stats`)
      ]);
      setHistory(histRes.data.history);
      setStats(statsRes.data.stats);
    } catch (err) {
      console.error('Could not fetch history');
    }
  };

  const handleAsk = async () => {
    if (!question.trim()) return;
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API_URL}/query/ask`, {
        question: question
      });

      setResults(prev => [{
        question: question,
        sql: response.data.sql,
        columns: response.data.columns,
        rows: response.data.rows,
        row_count: response.data.row_count,
        status: response.data.status,
        message: response.data.message
      }, ...prev]);

    } catch (err) {
      setError('Could not connect to the backend. Make sure the server is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  };

  const handleCsvUpload = async () => {
    if (!csvFile) return;
    setCsvUploading(true);
    setCsvError(null);
    setCsvTable(null);
    setCsvResults([]);

    try {
      const formData = new FormData();
      formData.append('file', csvFile);

      const response = await axios.post(`${API_URL}/csv/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (response.data.status === 'success') {
        setCsvTable(response.data);
      } else {
        setCsvError(response.data.message);
      }
    } catch (err) {
      setCsvError('Upload failed. Please try again.');
    } finally {
      setCsvUploading(false);
    }
  };

  const handleCsvAsk = async () => {
    if (!csvQuestion.trim() || !csvTable) return;
    setCsvLoading(true);
    setCsvError(null);

    try {
      const response = await axios.post(`${API_URL}/csv/ask`, {
        question: csvQuestion,
        table_name: csvTable.table_name,
        schema_text: csvTable.schema_text
      });

      setCsvResults(prev => [{
        question: csvQuestion,
        sql: response.data.sql,
        columns: response.data.columns,
        rows: response.data.rows,
        row_count: response.data.row_count,
        status: response.data.status,
        message: response.data.message
      }, ...prev]);

    } catch (err) {
      setCsvError('Query failed. Please try again.');
    } finally {
      setCsvLoading(false);
    }
  };

  const handleCsvKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleCsvAsk();
    }
  };

  const renderTable = (columns, rows, row_count) => (
    <div className="result-table-section">
      <span className="label">
        Results — {row_count} row{row_count !== 1 ? 's' : ''}
      </span>
      {row_count === 0 ? (
        <p className="no-results">No results found.</p>
      ) : (
        <div className="table-wrapper">
          <table className="result-table">
            <thead>
              <tr>
                {columns.map((col, i) => <th key={i}>{col}</th>)}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr key={i}>
                  {columns.map((col, j) => (
                    <td key={j}>{row[col] === null ? '—' : String(row[col])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );

  return (
    <div className="app">
      <header className="header">
        <h1>NL-SQL Engine</h1>
        <p>Ask questions about your data in plain English</p>
      </header>

      <div className="tab-bar">
        <button className={`tab ${activeTab === 'query' ? 'active' : ''}`} onClick={() => setActiveTab('query')}>
          Northwind DB
        </button>
        <button className={`tab ${activeTab === 'csv' ? 'active' : ''}`} onClick={() => setActiveTab('csv')}>
          Upload CSV
        </button>
        <button className={`tab ${activeTab === 'history' ? 'active' : ''}`} onClick={() => setActiveTab('history')}>
          History
        </button>
      </div>

      <main className="main">

        {/* NORTHWIND QUERY TAB */}
        {activeTab === 'query' && (
          <>
            <div className="input-section">
              <textarea
                className="question-input"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask a question... e.g. Show me the top 5 products by unit price"
                rows={3}
              />
              <button className="ask-button" onClick={handleAsk} disabled={loading || !question.trim()}>
                {loading ? 'Thinking...' : 'Ask'}
              </button>
            </div>
            {error && <div className="error-box">{error}</div>}
            <div className="results-list">
              {results.map((result, index) => (
                <div key={index} className="result-card">
                  <div className="result-question">
                    <span className="label">Question</span>
                    <p>{result.question}</p>
                  </div>
                  <div className="result-sql">
                    <span className="label">Generated SQL</span>
                    <pre>{result.sql}</pre>
                  </div>
                  {result.status === 'error' ? (
                    <div className="error-box">{result.message}</div>
                  ) : renderTable(result.columns, result.rows, result.row_count)}
                </div>
              ))}
            </div>
          </>
        )}

        {/* CSV UPLOAD TAB */}
        {activeTab === 'csv' && (
          <div className="csv-section">
            <div className="upload-box">
              <span className="label">Upload your CSV file</span>
              <div className="upload-row">
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setCsvFile(e.target.files[0])}
                  className="file-input"
                />
                <button
                  className="ask-button"
                  onClick={handleCsvUpload}
                  disabled={csvUploading || !csvFile}
                >
                  {csvUploading ? 'Uploading...' : 'Upload'}
                </button>
              </div>
            </div>

            {csvError && <div className="error-box">{csvError}</div>}

            {csvTable && (
              <>
                <div className="csv-info">
                  <span className="label">Loaded table</span>
                  <p className="csv-table-name">{csvTable.table_name}</p>
                  <div className="csv-columns">
                    {csvTable.columns.map((col, i) => (
                      <span key={i} className="csv-col-badge">{col}</span>
                    ))}
                  </div>
                  <p className="csv-row-count">{csvTable.row_count} rows loaded</p>
                </div>

                <div className="input-section">
                  <textarea
                    className="question-input"
                    value={csvQuestion}
                    onChange={(e) => setCsvQuestion(e.target.value)}
                    onKeyDown={handleCsvKeyDown}
                    placeholder={`Ask a question about your CSV... e.g. What is the total sales by category?`}
                    rows={3}
                  />
                  <button
                    className="ask-button"
                    onClick={handleCsvAsk}
                    disabled={csvLoading || !csvQuestion.trim()}
                  >
                    {csvLoading ? 'Thinking...' : 'Ask'}
                  </button>
                </div>

                <div className="results-list">
                  {csvResults.map((result, index) => (
                    <div key={index} className="result-card">
                      <div className="result-question">
                        <span className="label">Question</span>
                        <p>{result.question}</p>
                      </div>
                      <div className="result-sql">
                        <span className="label">Generated SQL</span>
                        <pre>{result.sql}</pre>
                      </div>
                      {result.status === 'error' ? (
                        <div className="error-box">{result.message}</div>
                      ) : renderTable(result.columns, result.rows, result.row_count)}
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {/* HISTORY TAB */}
        {activeTab === 'history' && (
          <div className="history-section">
            {stats && (
              <div className="stats-grid">
                <div className="stat-card">
                  <span className="stat-number">{stats.total_queries}</span>
                  <span className="stat-label">Total Queries</span>
                </div>
                <div className="stat-card">
                  <span className="stat-number">{stats.successful_queries}</span>
                  <span className="stat-label">Successful</span>
                </div>
                <div className="stat-card">
                  <span className="stat-number">{stats.failed_queries}</span>
                  <span className="stat-label">Failed</span>
                </div>
                <div className="stat-card">
                  <span className="stat-number">{stats.success_rate}%</span>
                  <span className="stat-label">Success Rate</span>
                </div>
              </div>
            )}
            <div className="history-list">
              {history.map((item) => (
                <div key={item.id} className="history-card">
                  <div className="history-meta">
                    <span className={`status-badge ${item.status}`}>{item.status}</span>
                    <span className="history-time">{item.created_at}</span>
                  </div>
                  <p className="history-question">{item.question}</p>
                  <pre className="history-sql">{item.sql_generated}</pre>
                  {item.row_count !== null && (
                    <span className="history-rows">{item.row_count} rows returned</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

      </main>
    </div>
  );
}

export default App;