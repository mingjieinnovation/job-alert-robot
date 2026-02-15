import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import ResumeUploader from '../components/ResumeUploader'
import KeywordManager from '../components/KeywordManager'
import JDAnalyzer from '../components/JDAnalyzer'

const styles = {
  hero: {
    textAlign: 'center',
    marginBottom: '2rem',
  },
  h1: { fontSize: '1.8rem', fontWeight: 700, marginBottom: '0.5rem' },
  sub: { color: '#666', fontSize: '1rem' },
  searchBtn: {
    display: 'block',
    width: '100%',
    padding: '1rem',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: '#fff',
    border: 'none',
    borderRadius: '12px',
    fontSize: '1.1rem',
    fontWeight: 600,
    cursor: 'pointer',
    boxShadow: '0 4px 15px rgba(102,126,234,0.3)',
    transition: 'transform 0.2s, box-shadow 0.2s',
  },
}

export default function HomePage() {
  const navigate = useNavigate()
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  return (
    <div>
      <div style={styles.hero}>
        <h1 style={styles.h1}>AI Job Alert</h1>
        <p style={styles.sub}>Upload your resume, manage keywords, and find your next role</p>
      </div>

      <ResumeUploader onKeywordsExtracted={() => setRefreshTrigger(r => r + 1)} />
      <KeywordManager refreshTrigger={refreshTrigger} />
      <JDAnalyzer onKeywordsUpdated={() => setRefreshTrigger(r => r + 1)} />

      <button
        style={styles.searchBtn}
        onClick={() => navigate('/search')}
        onMouseOver={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 6px 20px rgba(102,126,234,0.4)' }}
        onMouseOut={(e) => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = '0 4px 15px rgba(102,126,234,0.3)' }}
      >
        Search for Jobs
      </button>
    </div>
  )
}
