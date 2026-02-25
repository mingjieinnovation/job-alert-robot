import React, { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { searchJobs, getJobs } from '../api'
import JobList from '../components/JobList'

const styles = {
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' },
  h2: { fontSize: '1.4rem', fontWeight: 700 },
  controls: { display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' },
  select: {
    padding: '0.5rem 0.75rem',
    border: '1px solid #ddd',
    borderRadius: '8px',
    fontSize: '0.85rem',
    background: '#fff',
  },
  btn: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: '#fff',
    border: 'none',
    padding: '0.5rem 1.25rem',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: 500,
    fontSize: '0.9rem',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
  btnDisabled: {
    opacity: 0.7,
    cursor: 'not-allowed',
  },
  stats: { fontSize: '0.85rem', color: '#888', marginBottom: '1rem' },
  tabs: {
    display: 'flex',
    gap: '0',
    marginBottom: '1.5rem',
    borderBottom: '2px solid #eee',
  },
  tab: {
    padding: '0.6rem 1.25rem',
    cursor: 'pointer',
    fontSize: '0.9rem',
    fontWeight: 500,
    color: '#888',
    border: 'none',
    background: 'none',
    borderBottom: '2px solid transparent',
    marginBottom: '-2px',
    transition: 'all 0.2s',
  },
  tabActive: {
    color: '#667eea',
    borderBottomColor: '#667eea',
  },
  tabCount: {
    display: 'inline-block',
    background: '#f0f0f0',
    padding: '0.1rem 0.5rem',
    borderRadius: '10px',
    fontSize: '0.75rem',
    marginLeft: '0.4rem',
  },
  // Search animation
  searchingOverlay: {
    textAlign: 'center',
    padding: '3rem 1rem',
  },
  spinner: {
    width: '40px',
    height: '40px',
    border: '4px solid #e0e0e0',
    borderTop: '4px solid #667eea',
    borderRadius: '50%',
    margin: '0 auto 1rem',
    animation: 'spin 1s linear infinite',
  },
  searchingText: {
    color: '#667eea',
    fontSize: '1rem',
    fontWeight: 500,
  },
  searchingSub: {
    color: '#999',
    fontSize: '0.85rem',
    marginTop: '0.5rem',
  },
}

export default function SearchPage() {
  const location = useLocation()
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(false)
  const [searching, setSearching] = useState(false)
  const [total, setTotal] = useState(0)
  const [minScore, setMinScore] = useState('')
  const [source, setSource] = useState('')
  const [sort, setSort] = useState('score')
  const [activeTab, setActiveTab] = useState('new')
  const [searchProgress, setSearchProgress] = useState('')
  const [dismissedIds, setDismissedIds] = useState(new Set())

  const loadJobs = async () => {
    setLoading(true)
    try {
      const params = { sort, per_page: 500 }
      if (minScore !== '') params.min_score = parseFloat(minScore)
      if (source) params.source = source
      const res = await getJobs(params)
      setJobs(res.data.jobs)
      setTotal(res.data.total)
    } catch (err) {
      console.error('Failed to load jobs:', err)
    } finally {
      setLoading(false)
    }
  }

  // Reload when navigating back to this page (location changes) or filters change
  useEffect(() => { loadJobs() }, [location, minScore, source, sort])

  const handleSearch = async () => {
    setSearching(true)
    setSearchProgress('Connecting to job sources...')
    try {
      const progressMessages = [
        'Searching Adzuna...',
        'Searching LinkedIn...',
        'Searching Google Jobs...',
        'Searching X/Twitter...',
        'Scoring and filtering results...',
      ]
      let i = 0
      const interval = setInterval(() => {
        if (i < progressMessages.length) {
          setSearchProgress(progressMessages[i])
          i++
        }
      }, 3000)

      const res = await searchJobs()
      clearInterval(interval)
      setSearchProgress('')
      alert(`Found ${res.data.new_count} new jobs (${res.data.total_fetched} total fetched)`)
      loadJobs()
    } catch (err) {
      setSearchProgress('')
      alert(`Search failed: ${err.response?.data?.error || err.message}`)
    } finally {
      setSearching(false)
    }
  }

  // Split jobs into tabs
  const newJobs = jobs.filter(j => !j.application && !dismissedIds.has(j.id))
  const processedJobs = jobs.filter(j => j.application && j.application.status !== 'not_interested')
  const notInterestedJobs = jobs.filter(j => j.application && j.application.status === 'not_interested')
  const displayedJobs = activeTab === 'processed' ? processedJobs
    : activeTab === 'not_interested' ? notInterestedJobs
    : newJobs

  return (
    <div>
      {/* Inject spinner keyframe animation */}
      <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>

      <div style={styles.header}>
        <h2 style={styles.h2}>Job Results</h2>
        <div style={styles.controls}>
          <select style={styles.select} value={minScore} onChange={(e) => setMinScore(e.target.value)}>
            <option value="">All Scores</option>
            <option value="1">Score 1+</option>
            <option value="3">Score 3+</option>
            <option value="5">Score 5+</option>
          </select>
          <select style={styles.select} value={source} onChange={(e) => setSource(e.target.value)}>
            <option value="">All Sources</option>
            <option value="adzuna">Adzuna</option>
            <option value="reed">Reed</option>
            <option value="linkedin">LinkedIn</option>
            <option value="google_jobs">Google Jobs</option>
            <option value="x_twitter">X/Twitter</option>
            <option value="jungle">Jungle</option>
          </select>
          <select style={styles.select} value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="score">Sort by Score</option>
            <option value="date">Sort by Date</option>
          </select>
          <button
            style={{ ...styles.btn, ...(searching ? styles.btnDisabled : {}) }}
            onClick={handleSearch}
            disabled={searching}
          >
            {searching && (
              <span style={{
                display: 'inline-block',
                width: '14px',
                height: '14px',
                border: '2px solid rgba(255,255,255,0.3)',
                borderTop: '2px solid #fff',
                borderRadius: '50%',
                animation: 'spin 0.8s linear infinite',
              }} />
            )}
            {searching ? 'Searching...' : 'New Search'}
          </button>
        </div>
      </div>

      {/* Search animation overlay */}
      {searching && (
        <div style={styles.searchingOverlay}>
          <div style={styles.spinner} />
          <div style={styles.searchingText}>Searching for jobs...</div>
          <div style={styles.searchingSub}>{searchProgress}</div>
        </div>
      )}

      {!searching && (
        <>
          <div style={styles.tabs}>
            <button
              style={{ ...styles.tab, ...(activeTab === 'new' ? styles.tabActive : {}) }}
              onClick={() => setActiveTab('new')}
            >
              New
              <span style={styles.tabCount}>{newJobs.length}</span>
            </button>
            <button
              style={{ ...styles.tab, ...(activeTab === 'processed' ? styles.tabActive : {}) }}
              onClick={() => setActiveTab('processed')}
            >
              Processed
              <span style={styles.tabCount}>{processedJobs.length}</span>
            </button>
            <button
              style={{ ...styles.tab, ...(activeTab === 'not_interested' ? styles.tabActive : {}) }}
              onClick={() => setActiveTab('not_interested')}
            >
              Not Interested
              <span style={styles.tabCount}>{notInterestedJobs.length}</span>
            </button>
          </div>
          <div style={styles.stats}>
            Showing {displayedJobs.length} of {total} jobs
          </div>
          <JobList jobs={displayedJobs} loading={loading} onDismiss={(jobId) => {
            setDismissedIds(prev => new Set([...prev, jobId]))
            loadJobs()
          }} />
        </>
      )}
    </div>
  )
}
