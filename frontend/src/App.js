import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = 'http://127.0.0.1:8000';

function App() {
  const [question, setQuestion] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const [activeTab, setActiveTab] = useState('query');

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

  return (
    <div className="app">
      <header className="header">
        <h1>NL-SQL Engine</h1>
        <p>Ask questions about your data in plain English</p>
      </header>

      <div className="tab-bar">
        <button
          className={`tab ${activeTab === 'query' ? 'active' : ''}`}
          onClick={() => setActiveTab('query')}
        >
          Query
        </button>
        <button
          className={`tab ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          History
        </button>
      </div>

      <main className="main">
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
              <button
                className="ask-button"
                onClick={handleAsk}
                disabled={loading || !question.trim()}
              >
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
                  ) : (
                    <div className="result-table-section">
                      <span className="label">
                        Results — {result.row_count} row{result.row_count !== 1 ? 's' : ''}
                      </span>
                      {result.row_count === 0 ? (
                        <p className="no-results">No results found.</p>
                      ) : (
                        <div className="table-wrapper">
                          <table className="result-table">
                            <thead>
                              <tr>
                                {result.columns.map((col, i) => (
                                  <th key={i}>{col}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {result.rows.map((row, i) => (
                                <tr key={i}>
                                  {result.columns.map((col, j) => (
                                    <td key={j}>
                                      {row[col] === null ? '—' : String(row[col])}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
        )}

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
                    <span className={`status-badge ${item.status}`}>
                      {item.status}
                    </span>
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