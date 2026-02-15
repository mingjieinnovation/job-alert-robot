import React, { useState, useEffect } from 'react'
import { uploadResume, getResumeStatus } from '../api'

const styles = {
  container: {
    background: '#fff',
    borderRadius: '12px',
    padding: '1.5rem',
    boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
    marginBottom: '1.5rem',
  },
  title: { fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' },
  input: { marginBottom: '1rem' },
  button: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: '#fff',
    border: 'none',
    padding: '0.6rem 1.5rem',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: 500,
  },
  status: { marginTop: '0.75rem', fontSize: '0.9rem', color: '#666' },
  existingResume: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    padding: '0.75rem 1rem',
    background: '#e8f5e9',
    borderRadius: '8px',
    marginBottom: '1rem',
    fontSize: '0.9rem',
    color: '#2e7d32',
  },
  replaceBtn: {
    background: 'none',
    border: '1px solid #667eea',
    color: '#667eea',
    padding: '0.4rem 0.8rem',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '0.8rem',
  },
}

export default function ResumeUploader({ onKeywordsExtracted }) {
  const [uploading, setUploading] = useState(false)
  const [status, setStatus] = useState('')
  const [resumeInfo, setResumeInfo] = useState(null)
  const [showUpload, setShowUpload] = useState(false)

  useEffect(() => {
    getResumeStatus().then(res => {
      if (res.data.has_resume) {
        setResumeInfo(res.data)
      } else {
        setShowUpload(true)
      }
    }).catch(() => setShowUpload(true))
  }, [])

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setUploading(true)
    setStatus('Uploading and parsing...')

    try {
      const res = await uploadResume(file)
      setStatus(`Extracted ${res.data.keywords.length} keywords from resume`)
      setResumeInfo({ filename: file.name, keywords_count: res.data.keywords.length })
      setShowUpload(false)
      if (onKeywordsExtracted) onKeywordsExtracted(res.data.keywords)
    } catch (err) {
      setStatus(`Error: ${err.response?.data?.error || err.message}`)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div style={styles.container}>
      <div style={styles.title}>Resume</div>

      {resumeInfo && !showUpload && (
        <div style={styles.existingResume}>
          <span>Resume uploaded: <strong>{resumeInfo.filename}</strong> ({resumeInfo.keywords_count} keywords extracted)</span>
          <button style={styles.replaceBtn} onClick={() => setShowUpload(true)}>
            Replace
          </button>
        </div>
      )}

      {showUpload && (
        <>
          <input
            type="file"
            accept=".pdf"
            onChange={handleUpload}
            disabled={uploading}
            style={styles.input}
          />
          {resumeInfo && (
            <button
              style={{ ...styles.replaceBtn, marginLeft: '0.5rem' }}
              onClick={() => setShowUpload(false)}
            >
              Cancel
            </button>
          )}
        </>
      )}

      {status && <div style={styles.status}>{status}</div>}
    </div>
  )
}
