import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getJob, createApplication, updateApplication, saveLearnedKeywords } from '../api'
import StatusBadge from '../components/StatusBadge'
import FeedbackForm from '../components/FeedbackForm'

const styles = {
  back: {
    color: '#667eea',
    cursor: 'pointer',
    fontSize: '0.9rem',
    marginBottom: '1rem',
    display: 'inline-block',
    border: 'none',
    background: 'none',
    fontFamily: 'inherit',
  },
  card: {
    background: '#fff',
    borderRadius: '12px',
    padding: '2rem',
    boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
  },
  title: { fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' },
  meta: { fontSize: '0.95rem', color: '#666', marginBottom: '1rem' },
  score: {
    display: 'inline-block',
    padding: '0.3rem 0.8rem',
    borderRadius: '12px',
    fontWeight: 700,
    fontSize: '0.9rem',
    marginRight: '0.75rem',
  },
  tags: { display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '1.5rem' },
  tag: { fontSize: '0.8rem', padding: '0.2rem 0.6rem', borderRadius: '8px', background: '#f0f0f0' },
  desc: {
    fontSize: '0.95rem',
    lineHeight: 1.7,
    color: '#333',
    marginBottom: '1.5rem',
    whiteSpace: 'pre-wrap',
  },
  actions: { display: 'flex', gap: '0.75rem', marginBottom: '1.5rem', flexWrap: 'wrap', alignItems: 'center' },
  btn: {
    padding: '0.6rem 1.25rem',
    borderRadius: '8px',
    border: 'none',
    cursor: 'pointer',
    fontWeight: 500,
    fontSize: '0.9rem',
  },
  primaryBtn: { background: '#667eea', color: '#fff' },
  secondaryBtn: { background: '#f0f0f0', color: '#333' },
  select: {
    padding: '0.5rem 0.75rem',
    border: '1px solid #ddd',
    borderRadius: '8px',
    fontSize: '0.9rem',
  },
  textarea: {
    width: '100%',
    padding: '0.75rem',
    border: '1px solid #ddd',
    borderRadius: '8px',
    fontSize: '0.9rem',
    minHeight: '80px',
    resize: 'vertical',
    marginBottom: '0.75rem',
    fontFamily: 'inherit',
  },
  link: { color: '#667eea', textDecoration: 'none', fontWeight: 500 },
  section: { marginTop: '1.5rem' },
  sectionTitle: { fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem' },
  feedbackItem: {
    padding: '0.75rem',
    background: '#fafafa',
    borderRadius: '8px',
    marginBottom: '0.5rem',
    fontSize: '0.9rem',
  },
}

const STATUSES = ['interested', 'applied', 'interview', 'offer', 'rejected', 'not_interested']

function KeywordPicker({ suggestions, category, onDone }) {
  const [selected, setSelected] = useState(new Set(suggestions))
  const [customKw, setCustomKw] = useState('')
  const [allKeywords, setAllKeywords] = useState([...suggestions])
  const [saving, setSaving] = useState(false)

  const toggle = (kw) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(kw)) next.delete(kw)
      else next.add(kw)
      return next
    })
  }

  const addCustom = () => {
    const kw = customKw.trim().toLowerCase()
    if (kw && !allKeywords.includes(kw)) {
      setAllKeywords(prev => [...prev, kw])
      setSelected(prev => new Set([...prev, kw]))
    }
    setCustomKw('')
  }

  const handleSave = async () => {
    const toSave = [...selected]
    if (toSave.length === 0) {
      onDone([])
      return
    }
    setSaving(true)
    try {
      const res = await saveLearnedKeywords({ keywords: toSave, category })
      onDone(res.data.saved || [])
    } catch (err) {
      console.error('Failed to save keywords:', err)
      onDone([])
    } finally {
      setSaving(false)
    }
  }

  const chipBase = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.3rem',
    padding: '0.3rem 0.7rem',
    borderRadius: '16px',
    fontSize: '0.82rem',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.15s',
    border: '1px solid',
  }

  const isExclude = category === 'exclude'

  return (
    <div style={{
      padding: '1rem',
      background: isExclude ? '#fff8f8' : '#f8fff8',
      borderRadius: '10px',
      marginBottom: '1rem',
      border: `1px solid ${isExclude ? '#ffcdd2' : '#c8e6c9'}`,
    }}>
      <div style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '0.6rem' }}>
        Suggested {isExclude ? 'exclude' : 'boost'} keywords — select which to save:
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.75rem' }}>
        {allKeywords.map(kw => {
          const isSelected = selected.has(kw)
          return (
            <span
              key={kw}
              style={{
                ...chipBase,
                background: isSelected
                  ? (isExclude ? '#ffcdd2' : '#c8e6c9')
                  : '#f5f5f5',
                borderColor: isSelected
                  ? (isExclude ? '#e57373' : '#81c784')
                  : '#ddd',
                color: isSelected
                  ? (isExclude ? '#b71c1c' : '#1b5e20')
                  : '#999',
              }}
              onClick={() => toggle(kw)}
            >
              {isSelected ? '\u2713 ' : ''}{kw}
            </span>
          )
        })}
        {allKeywords.length === 0 && (
          <span style={{ color: '#999', fontSize: '0.85rem' }}>No suggestions found. Add your own below.</span>
        )}
      </div>
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <input
          style={{
            flex: 1,
            padding: '0.4rem 0.7rem',
            border: '1px solid #ddd',
            borderRadius: '8px',
            fontSize: '0.85rem',
          }}
          value={customKw}
          onChange={(e) => setCustomKw(e.target.value)}
          placeholder="Add custom keyword..."
          onKeyDown={(e) => e.key === 'Enter' && addCustom()}
        />
        <button
          style={{ ...styles.btn, ...styles.secondaryBtn, fontSize: '0.82rem', padding: '0.4rem 0.8rem' }}
          onClick={addCustom}
        >
          Add
        </button>
      </div>
      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
        <button
          style={{ ...styles.btn, ...styles.primaryBtn, fontSize: '0.85rem', padding: '0.4rem 1rem' }}
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? 'Saving...' : `Save ${selected.size} keyword${selected.size !== 1 ? 's' : ''}`}
        </button>
        <button
          style={{ ...styles.btn, ...styles.secondaryBtn, fontSize: '0.85rem', padding: '0.4rem 1rem' }}
          onClick={() => onDone([])}
        >
          Skip
        </button>
      </div>
    </div>
  )
}

export default function JobDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [job, setJob] = useState(null)
  const [notes, setNotes] = useState('')
  const [noteSaved, setNoteSaved] = useState(false)
  const [showDismissNotes, setShowDismissNotes] = useState(false)
  const [dismissNotes, setDismissNotes] = useState('')
  const [savedMessage, setSavedMessage] = useState('')
  // Keyword suggestion state
  const [suggestedKeywords, setSuggestedKeywords] = useState([])
  const [keywordCategory, setKeywordCategory] = useState(null)

  const load = async () => {
    try {
      const res = await getJob(id)
      setJob(res.data)
      if (res.data.application?.notes) setNotes(res.data.application.notes)
    } catch (err) {
      console.error('Failed to load job:', err)
    }
  }

  useEffect(() => { load() }, [id])

  if (!job) return <div style={{ textAlign: 'center', padding: '3rem', color: '#888' }}>Loading...</div>

  const app = job.application
  const scoreColor = job.match_score >= 3
    ? { background: '#e8f5e9', color: '#2e7d32' }
    : job.match_score >= 1
    ? { background: '#fff3e0', color: '#e65100' }
    : { background: '#f5f5f5', color: '#999' }

  const showSuggestions = (suggestions, category) => {
    if (category) {
      setSuggestedKeywords(suggestions || [])
      setKeywordCategory(category)
    }
  }

  const handleTrack = async () => {
    try {
      await createApplication({ job_id: job.id, status: 'interested' })
      load()
    } catch (err) {
      if (err.response?.status === 409) load()
      else console.error(err)
    }
  }

  const handleStatusChange = async (newStatus) => {
    if (!app) return
    try {
      const res = await updateApplication(app.id, { status: newStatus })
      showSuggestions(res.data.suggested_keywords, res.data.keyword_category)
    } catch (err) {
      console.error(err)
    }
    load()
  }

  const handleNoteSave = async () => {
    if (!app) return
    try {
      const res = await updateApplication(app.id, { notes })
      showSuggestions(res.data.suggested_keywords, res.data.keyword_category)
    } catch (err) {
      console.error(err)
    }
    setNoteSaved(true)
    setTimeout(() => setNoteSaved(false), 2000)
    load()
  }

  const handleKeywordsDone = (saved) => {
    setSuggestedKeywords([])
    setKeywordCategory(null)
    if (saved.length > 0) {
      setSavedMessage(`Saved ${saved.length} keyword${saved.length !== 1 ? 's' : ''}: ${saved.join(', ')}`)
      setTimeout(() => setSavedMessage(''), 5000)
    }
  }

  return (
    <div>
      <button style={styles.back} onClick={() => navigate(-1)}>&larr; Back</button>
      <div style={styles.card}>
        <div style={styles.title}>{job.title}</div>
        <div style={styles.meta}>
          {job.company} &middot; {job.location}
          {job.salary && <> &middot; {job.salary}</>}
          {job.posted_date && <> &middot; Posted {job.posted_date}</>}
          {job.source && <> &middot; <span style={{ textTransform: 'capitalize' }}>{job.source}</span></>}
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <span style={{ ...styles.score, ...scoreColor }}>
            Score: {job.match_score}
          </span>
          {!job.experience_ok && (
            <span style={{ ...styles.score, background: '#fce4ec', color: '#c62828' }}>
              May be too senior
            </span>
          )}
          {app && <StatusBadge status={app.status} />}
        </div>

        {job.match_tags && job.match_tags.length > 0 && (
          <div style={styles.tags}>
            {job.match_tags.map((tag, i) => <span key={i} style={styles.tag}>{tag}</span>)}
          </div>
        )}

        {job.url && (
          <div style={{ marginBottom: '1.5rem' }}>
            <a href={job.url} target="_blank" rel="noopener noreferrer" style={styles.link}>
              View Original Listing &rarr;
            </a>
          </div>
        )}

        {job.description && (
          <div style={styles.desc}>{job.description}</div>
        )}

        {savedMessage && (
          <div style={{
            padding: '0.6rem 1rem',
            background: '#e8f5e9',
            borderRadius: '8px',
            fontSize: '0.85rem',
            color: '#2e7d32',
            marginBottom: '1rem',
            fontWeight: 500,
          }}>
            {savedMessage}
          </div>
        )}

        {keywordCategory && (
          <KeywordPicker
            suggestions={suggestedKeywords}
            category={keywordCategory}
            onDone={handleKeywordsDone}
          />
        )}

        <div style={styles.actions}>
          {!app ? (
            <>
              <button style={{ ...styles.btn, ...styles.primaryBtn }} onClick={handleTrack}>
                Track This Job
              </button>
              {!showDismissNotes ? (
                <button
                  style={{ ...styles.btn, background: '#f5f5f5', color: '#999' }}
                  onClick={() => setShowDismissNotes(true)}
                >
                  Not Interested
                </button>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1 }}>
                  <textarea
                    style={{ ...styles.textarea, minHeight: '60px', marginBottom: 0 }}
                    value={dismissNotes}
                    onChange={(e) => setDismissNotes(e.target.value)}
                    placeholder="Why not interested? (optional - helps learn your preferences)"
                    autoFocus
                  />
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                      style={{ ...styles.btn, background: '#c62828', color: '#fff', fontSize: '0.85rem', padding: '0.4rem 1rem' }}
                      onClick={async () => {
                        try {
                          const res = await createApplication({ job_id: job.id, status: 'not_interested', notes: dismissNotes })
                          setShowDismissNotes(false)
                          showSuggestions(res.data.suggested_keywords, res.data.keyword_category)
                          load()
                        } catch (err) {
                          if (err.response?.status === 409) load()
                        }
                      }}
                    >
                      Confirm Dismiss
                    </button>
                    <button
                      style={{ ...styles.btn, ...styles.secondaryBtn, fontSize: '0.85rem', padding: '0.4rem 1rem' }}
                      onClick={() => { setShowDismissNotes(false); setDismissNotes('') }}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <>
              <span style={{ fontSize: '0.85rem', color: '#888' }}>Status:</span>
              <select
                style={styles.select}
                value={app.status}
                onChange={(e) => handleStatusChange(e.target.value)}
              >
                {STATUSES.map(s => (
                  <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                ))}
              </select>
            </>
          )}
        </div>

        {app && (
          <div style={styles.section}>
            <div style={styles.sectionTitle}>Notes</div>
            <textarea
              style={styles.textarea}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add your notes about this application..."
            />
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <button
                style={{ ...styles.btn, ...styles.primaryBtn }}
                onClick={handleNoteSave}
              >
                Save Notes
              </button>
              {noteSaved && (
                <span style={{ color: '#2e7d32', fontSize: '0.85rem', fontWeight: 500 }}>
                  Saved!
                </span>
              )}
            </div>
          </div>
        )}

        {app && (
          <div style={styles.section}>
            <div style={styles.sectionTitle}>Feedback</div>
            {app.feedbacks && app.feedbacks.map(fb => (
              <div key={fb.id} style={styles.feedbackItem}>
                <strong>{fb.feedback_type}:</strong> {fb.feedback_text}
                {fb.keywords_mentioned && fb.keywords_mentioned.length > 0 && (
                  <div style={{ marginTop: '0.25rem', fontSize: '0.8rem', color: '#888' }}>
                    Keywords: {fb.keywords_mentioned.join(', ')}
                  </div>
                )}
              </div>
            ))}
            <FeedbackForm applicationId={app.id} onSubmit={load} />
          </div>
        )}
      </div>
    </div>
  )
}
