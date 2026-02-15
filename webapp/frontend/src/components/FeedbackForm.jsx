import React, { useState } from 'react'
import { addFeedback } from '../api'

const styles = {
  container: {
    background: '#fafafa',
    borderRadius: '10px',
    padding: '1.25rem',
    marginTop: '1rem',
    border: '1px solid #eee',
  },
  title: { fontSize: '0.95rem', fontWeight: 600, marginBottom: '0.75rem' },
  select: {
    width: '100%',
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '8px',
    marginBottom: '0.75rem',
    fontSize: '0.9rem',
  },
  textarea: {
    width: '100%',
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '8px',
    marginBottom: '0.75rem',
    fontSize: '0.9rem',
    minHeight: '80px',
    resize: 'vertical',
    fontFamily: 'inherit',
  },
  input: {
    width: '100%',
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '8px',
    marginBottom: '0.75rem',
    fontSize: '0.9rem',
  },
  button: {
    background: '#667eea',
    color: '#fff',
    border: 'none',
    padding: '0.5rem 1.25rem',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: 500,
  },
  label: { fontSize: '0.8rem', color: '#888', marginBottom: '0.25rem', display: 'block' },
}

export default function FeedbackForm({ applicationId, onSubmit }) {
  const [type, setType] = useState('why_applied')
  const [text, setText] = useState('')
  const [keywords, setKeywords] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async () => {
    if (!text.trim()) return
    setSubmitting(true)
    try {
      const kwList = keywords.split(',').map(k => k.trim()).filter(Boolean)
      await addFeedback(applicationId, {
        feedback_type: type,
        feedback_text: text,
        keywords_mentioned: kwList,
      })
      setText('')
      setKeywords('')
      if (onSubmit) onSubmit()
    } catch (err) {
      console.error('Failed to submit feedback:', err)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={styles.container}>
      <div style={styles.title}>Add Feedback</div>
      <label style={styles.label}>Type</label>
      <select style={styles.select} value={type} onChange={(e) => setType(e.target.value)}>
        <option value="why_applied">Why I applied</option>
        <option value="interview_notes">Interview notes</option>
        <option value="general">General</option>
      </select>
      <label style={styles.label}>Notes</label>
      <textarea
        style={styles.textarea}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="What attracted you to this role?"
      />
      <label style={styles.label}>Keywords that attracted you (comma-separated)</label>
      <input
        style={styles.input}
        value={keywords}
        onChange={(e) => setKeywords(e.target.value)}
        placeholder="e.g. AI, product analytics, Python"
      />
      <button style={styles.button} onClick={handleSubmit} disabled={submitting}>
        {submitting ? 'Saving...' : 'Submit Feedback'}
      </button>
    </div>
  )
}
