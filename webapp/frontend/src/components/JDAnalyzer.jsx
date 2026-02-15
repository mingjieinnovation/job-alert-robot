import React, { useState } from 'react'
import { analyzeJD, applyJDSuggestions } from '../api'

const styles = {
  container: {
    background: '#fff',
    borderRadius: '12px',
    padding: '1.5rem',
    boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
    marginBottom: '1.5rem',
  },
  title: { fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.5rem' },
  desc: { fontSize: '0.85rem', color: '#888', marginBottom: '1rem' },
  textarea: {
    width: '100%',
    minHeight: '120px',
    padding: '0.75rem',
    border: '1px solid #ddd',
    borderRadius: '8px',
    fontSize: '0.9rem',
    fontFamily: 'inherit',
    resize: 'vertical',
    boxSizing: 'border-box',
  },
  analyzeBtn: {
    background: '#667eea',
    color: '#fff',
    border: 'none',
    padding: '0.6rem 1.5rem',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: 600,
    fontSize: '0.9rem',
    marginTop: '0.75rem',
  },
  resultsBox: {
    marginTop: '1rem',
    padding: '1rem',
    background: '#fafafa',
    borderRadius: '8px',
    border: '1px solid #eee',
  },
  sectionTitle: { fontSize: '0.85rem', fontWeight: 600, color: '#888', marginBottom: '0.5rem', textTransform: 'uppercase' },
  chips: { display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.75rem' },
  chip: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.3rem',
    padding: '0.3rem 0.7rem',
    borderRadius: '16px',
    fontSize: '0.8rem',
    fontWeight: 500,
    cursor: 'pointer',
  },
  newChip: { background: '#e8f5e9', color: '#2e7d32', border: '1px solid #a5d6a7' },
  newChipSelected: { background: '#2e7d32', color: '#fff', border: '1px solid #2e7d32' },
  trackingChip: { background: '#f5f5f5', color: '#666', border: '1px solid #e0e0e0' },
  conflictChip: { background: '#fff3e0', color: '#e65100', border: '1px solid #ffcc80' },
  conflictChipSelected: { background: '#e65100', color: '#fff', border: '1px solid #e65100' },
  applyBtn: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: '#fff',
    border: 'none',
    padding: '0.6rem 1.5rem',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: 600,
    fontSize: '0.9rem',
    marginTop: '0.5rem',
  },
  section: { marginBottom: '0.5rem' },
  noResults: { fontSize: '0.85rem', color: '#999', fontStyle: 'italic' },
}

export default function JDAnalyzer({ onKeywordsUpdated }) {
  const [text, setText] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [selectedNew, setSelectedNew] = useState(new Set())
  const [selectedConflicts, setSelectedConflicts] = useState(new Set())
  const [applied, setApplied] = useState(false)

  const handleAnalyze = async () => {
    if (!text.trim()) return
    setLoading(true)
    setResults(null)
    setApplied(false)
    try {
      const res = await analyzeJD(text)
      setResults(res.data)
      setSelectedNew(new Set(res.data.new_suggestions))
      setSelectedConflicts(new Set())
    } catch (err) {
      console.error('Analysis failed:', err)
    } finally {
      setLoading(false)
    }
  }

  const toggleNew = (kw) => {
    setSelectedNew(prev => {
      const next = new Set(prev)
      next.has(kw) ? next.delete(kw) : next.add(kw)
      return next
    })
  }

  const toggleConflict = (kw) => {
    setSelectedConflicts(prev => {
      const next = new Set(prev)
      next.has(kw) ? next.delete(kw) : next.add(kw)
      return next
    })
  }

  const handleApply = async () => {
    const payload = {
      add_boost: Array.from(selectedNew),
      remove_exclude: Array.from(selectedConflicts),
    }
    if (payload.add_boost.length === 0 && payload.remove_exclude.length === 0) return
    try {
      await applyJDSuggestions(payload)
      setApplied(true)
      if (onKeywordsUpdated) onKeywordsUpdated()
    } catch (err) {
      console.error('Apply failed:', err)
    }
  }

  const hasResults = results && (results.new_suggestions.length > 0 || results.already_tracking.length > 0 || results.conflicts.length > 0)

  return (
    <div style={styles.container}>
      <div style={styles.title}>Job Description Analyzer</div>
      <div style={styles.desc}>Paste a job description you like to extract keywords and improve your search scoring.</div>

      <textarea
        style={styles.textarea}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste a job description here..."
      />
      <button style={styles.analyzeBtn} onClick={handleAnalyze} disabled={loading || !text.trim()}>
        {loading ? 'Analyzing...' : 'Analyze'}
      </button>

      {results && (
        <div style={styles.resultsBox}>
          {!hasResults && <div style={styles.noResults}>No known skills found in this job description.</div>}

          {results.new_suggestions.length > 0 && (
            <div style={styles.section}>
              <div style={styles.sectionTitle}>New Keywords to Add ({selectedNew.size} selected)</div>
              <div style={styles.chips}>
                {results.new_suggestions.map(kw => (
                  <span
                    key={kw}
                    style={{ ...styles.chip, ...(selectedNew.has(kw) ? styles.newChipSelected : styles.newChip) }}
                    onClick={() => toggleNew(kw)}
                  >
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          )}

          {results.already_tracking.length > 0 && (
            <div style={styles.section}>
              <div style={styles.sectionTitle}>Already Tracking</div>
              <div style={styles.chips}>
                {results.already_tracking.map(kw => (
                  <span key={kw} style={{ ...styles.chip, ...styles.trackingChip }}>{kw}</span>
                ))}
              </div>
            </div>
          )}

          {results.conflicts.length > 0 && (
            <div style={styles.section}>
              <div style={styles.sectionTitle}>Conflicts with Excludes (select to remove from excludes)</div>
              <div style={styles.chips}>
                {results.conflicts.map(kw => (
                  <span
                    key={kw}
                    style={{ ...styles.chip, ...(selectedConflicts.has(kw) ? styles.conflictChipSelected : styles.conflictChip) }}
                    onClick={() => toggleConflict(kw)}
                  >
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          )}

          {hasResults && (
            <button style={styles.applyBtn} onClick={handleApply} disabled={applied}>
              {applied ? 'Applied!' : 'Apply Selected'}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
