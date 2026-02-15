import React from 'react'
import { useNavigate } from 'react-router-dom'
import { createApplication } from '../api'
import StatusBadge from './StatusBadge'

const styles = {
  card: {
    background: '#fff',
    borderRadius: '10px',
    padding: '1.25rem',
    boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
    cursor: 'pointer',
    transition: 'box-shadow 0.2s, transform 0.2s',
    borderLeft: '4px solid transparent',
  },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' },
  title: { fontSize: '1rem', fontWeight: 600, color: '#1a1a2e' },
  score: {
    fontSize: '0.85rem',
    fontWeight: 700,
    padding: '0.2rem 0.6rem',
    borderRadius: '12px',
    whiteSpace: 'nowrap',
  },
  meta: { fontSize: '0.85rem', color: '#666', marginBottom: '0.5rem' },
  tags: { display: 'flex', flexWrap: 'wrap', gap: '0.3rem', marginTop: '0.5rem' },
  tag: {
    fontSize: '0.75rem',
    padding: '0.15rem 0.5rem',
    borderRadius: '8px',
    background: '#f0f0f0',
  },
  desc: { fontSize: '0.85rem', color: '#555', marginTop: '0.5rem', lineHeight: 1.5 },
  dismissBtn: {
    background: 'none',
    border: '1px solid #ddd',
    borderRadius: '6px',
    padding: '0.25rem 0.6rem',
    fontSize: '0.75rem',
    color: '#999',
    cursor: 'pointer',
    marginTop: '0.5rem',
    transition: 'all 0.2s',
  },
  footer: { display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' },
}

function getScoreStyle(score) {
  if (score >= 3) return { background: '#e8f5e9', color: '#2e7d32' }
  if (score >= 1) return { background: '#fff3e0', color: '#e65100' }
  return { background: '#f5f5f5', color: '#999' }
}

export default function JobCard({ job, onDismiss }) {
  const navigate = useNavigate()
  const scoreColor = getScoreStyle(job.match_score)

  const handleDismiss = async (e) => {
    e.stopPropagation()
    try {
      await createApplication({ job_id: job.id, status: 'not_interested' })
      if (onDismiss) onDismiss(job.id)
    } catch (err) {
      if (err.response?.status === 409 && onDismiss) onDismiss(job.id)
    }
  }

  return (
    <div
      style={{
        ...styles.card,
        borderLeftColor: scoreColor.color,
      }}
      onClick={() => navigate(`/jobs/${job.id}`)}
      onMouseOver={(e) => { e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.12)'; e.currentTarget.style.transform = 'translateY(-1px)' }}
      onMouseOut={(e) => { e.currentTarget.style.boxShadow = '0 1px 4px rgba(0,0,0,0.08)'; e.currentTarget.style.transform = 'none' }}
    >
      <div style={styles.header}>
        <div style={styles.title}>{job.title}</div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          {job.application && <StatusBadge status={job.application.status} />}
          <span style={{ ...styles.score, ...scoreColor }}>
            {job.match_score >= 0 ? '+' : ''}{job.match_score}
          </span>
        </div>
      </div>
      <div style={styles.meta}>
        {job.company} &middot; {job.location}
        {job.salary && <> &middot; {job.salary}</>}
        {job.source && <> &middot; <span style={{ textTransform: 'capitalize' }}>{job.source}</span></>}
      </div>
      {job.description && (
        <div style={styles.desc}>
          {job.description.length > 200 ? job.description.slice(0, 200) + '...' : job.description}
        </div>
      )}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.5rem' }}>
        <div style={styles.tags}>
          {job.match_tags && job.match_tags.map((tag, i) => (
            <span key={i} style={styles.tag}>{tag}</span>
          ))}
        </div>
        {!job.application && (
          <button
            style={styles.dismissBtn}
            onClick={handleDismiss}
            onMouseOver={(e) => { e.currentTarget.style.borderColor = '#c62828'; e.currentTarget.style.color = '#c62828' }}
            onMouseOut={(e) => { e.currentTarget.style.borderColor = '#ddd'; e.currentTarget.style.color = '#999' }}
          >
            Not Interested
          </button>
        )}
      </div>
    </div>
  )
}
