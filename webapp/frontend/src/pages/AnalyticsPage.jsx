import React, { useState, useEffect } from 'react'
import { getInsights, retrain } from '../api'

const styles = {
  h2: { fontSize: '1.4rem', fontWeight: 700, marginBottom: '1.5rem' },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '1rem',
    marginBottom: '2rem',
  },
  statCard: {
    background: '#fff',
    borderRadius: '12px',
    padding: '1.25rem',
    textAlign: 'center',
    boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
  },
  statValue: { fontSize: '2rem', fontWeight: 700, color: '#667eea' },
  statLabel: { fontSize: '0.85rem', color: '#888', marginTop: '0.25rem' },
  card: {
    background: '#fff',
    borderRadius: '12px',
    padding: '1.5rem',
    boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
    marginBottom: '1.5rem',
  },
  cardTitle: { fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' },
  table: { width: '100%', borderCollapse: 'collapse' },
  th: {
    textAlign: 'left',
    padding: '0.6rem 0.75rem',
    borderBottom: '2px solid #eee',
    fontSize: '0.85rem',
    fontWeight: 600,
    color: '#888',
  },
  td: {
    padding: '0.6rem 0.75rem',
    borderBottom: '1px solid #f5f5f5',
    fontSize: '0.9rem',
  },
  btn: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: '#fff',
    border: 'none',
    padding: '0.75rem 1.5rem',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: 600,
    fontSize: '1rem',
  },
  weightBar: {
    height: '6px',
    borderRadius: '3px',
    background: '#e0e0e0',
    overflow: 'hidden',
  },
  weightFill: {
    height: '100%',
    borderRadius: '3px',
    background: 'linear-gradient(90deg, #667eea, #764ba2)',
    transition: 'width 0.3s',
  },
  result: {
    marginTop: '1rem',
    padding: '1rem',
    background: '#f5f5f5',
    borderRadius: '8px',
    fontSize: '0.9rem',
  },
}

export default function AnalyticsPage() {
  const [insights, setInsights] = useState(null)
  const [retraining, setRetraining] = useState(false)
  const [trainResult, setTrainResult] = useState(null)

  const load = async () => {
    try {
      const res = await getInsights()
      setInsights(res.data)
    } catch (err) {
      console.error('Failed to load insights:', err)
    }
  }

  useEffect(() => { load() }, [])

  const handleRetrain = async () => {
    setRetraining(true)
    setTrainResult(null)
    try {
      const res = await retrain()
      setTrainResult(res.data)
      load()
    } catch (err) {
      console.error('Retrain failed:', err)
    } finally {
      setRetraining(false)
    }
  }

  if (!insights) {
    return <div style={{ textAlign: 'center', padding: '3rem', color: '#888' }}>Loading analytics...</div>
  }

  const maxWeight = Math.max(...(insights.keyword_stats?.map(k => k.weight) || [1]), 1)

  return (
    <div>
      <h2 style={styles.h2}>Analytics</h2>

      <div style={styles.statsGrid}>
        <div style={styles.statCard}>
          <div style={styles.statValue}>{insights.total_jobs}</div>
          <div style={styles.statLabel}>Total Jobs</div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statValue}>{insights.total_applications}</div>
          <div style={styles.statLabel}>Applications</div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statValue}>{insights.total_feedbacks}</div>
          <div style={styles.statLabel}>Feedbacks</div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statValue}>{insights.application_rate}%</div>
          <div style={styles.statLabel}>Application Rate</div>
        </div>
      </div>

      <div style={styles.card}>
        <div style={styles.cardTitle}>Keyword Performance</div>
        {insights.keyword_stats && insights.keyword_stats.length > 0 ? (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Keyword</th>
                <th style={styles.th}>Weight</th>
                <th style={styles.th}></th>
                <th style={styles.th}>Source</th>
                <th style={styles.th}>Applied Jobs</th>
              </tr>
            </thead>
            <tbody>
              {insights.keyword_stats.map((kw, i) => (
                <tr key={i}>
                  <td style={styles.td}>{kw.keyword}</td>
                  <td style={styles.td}>{kw.weight.toFixed(2)}</td>
                  <td style={{ ...styles.td, width: '120px' }}>
                    <div style={styles.weightBar}>
                      <div style={{ ...styles.weightFill, width: `${(kw.weight / maxWeight) * 100}%` }} />
                    </div>
                  </td>
                  <td style={styles.td}>
                    <span style={{
                      fontSize: '0.8rem',
                      padding: '0.15rem 0.5rem',
                      borderRadius: '8px',
                      background: kw.source === 'learned' ? '#e8f5e9' : kw.source === 'resume' ? '#e3f2fd' : '#f5f5f5',
                      color: kw.source === 'learned' ? '#2e7d32' : kw.source === 'resume' ? '#1565c0' : '#666',
                    }}>
                      {kw.source}
                    </span>
                  </td>
                  <td style={styles.td}>{kw.applied_job_hits}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div style={{ color: '#888', textAlign: 'center', padding: '2rem' }}>
            No keywords yet. Upload a resume or add keywords on the Home page.
          </div>
        )}
      </div>

      <div style={styles.card}>
        <div style={styles.cardTitle}>Improve Recommendations</div>
        <p style={{ color: '#666', marginBottom: '1rem', fontSize: '0.9rem' }}>
          Analyze your application history and feedback to automatically adjust keyword weights.
          Keywords found in jobs you applied for will get boosted, while keywords only found in
          ignored high-score jobs will get reduced.
        </p>
        <button style={styles.btn} onClick={handleRetrain} disabled={retraining}>
          {retraining ? 'Analyzing...' : 'Improve Recommendations'}
        </button>

        {trainResult && (
          <div style={styles.result}>
            <strong>Training Results:</strong>
            <ul style={{ marginTop: '0.5rem', paddingLeft: '1.25rem' }}>
              <li>Analyzed {trainResult.positive_jobs_count} applied jobs and {trainResult.ignored_jobs_count} ignored jobs</li>
              <li>{trainResult.weight_updates?.length || 0} keyword weights updated</li>
              <li>{trainResult.new_keywords?.length || 0} new keywords added from feedback</li>
              <li>{trainResult.total_feedbacks_analyzed} feedbacks analyzed</li>
            </ul>
            {trainResult.weight_updates && trainResult.weight_updates.length > 0 && (
              <div style={{ marginTop: '0.75rem' }}>
                <strong>Weight Changes:</strong>
                {trainResult.weight_updates.map((u, i) => (
                  <div key={i} style={{ fontSize: '0.85rem', color: '#555' }}>
                    {u.keyword}: {u.old_weight.toFixed(2)} &rarr; {u.new_weight.toFixed(2)}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
