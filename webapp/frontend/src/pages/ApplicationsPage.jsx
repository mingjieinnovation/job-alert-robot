import React, { useState, useEffect } from 'react'
import { getApplications, updateApplication } from '../api'
import { useNavigate } from 'react-router-dom'

const COLUMNS = ['interested', 'applied', 'interview', 'offer', 'rejected']
const COLUMN_COLORS = {
  interested: '#e3f2fd',
  applied: '#fff3e0',
  interview: '#f3e5f5',
  offer: '#e8f5e9',
  rejected: '#fce4ec',
}

const styles = {
  h2: { fontSize: '1.4rem', fontWeight: 700, marginBottom: '1.5rem' },
  board: {
    display: 'grid',
    gridTemplateColumns: 'repeat(5, 1fr)',
    gap: '1rem',
    minHeight: '400px',
  },
  column: {
    borderRadius: '12px',
    padding: '1rem',
    minHeight: '300px',
  },
  colTitle: {
    fontSize: '0.9rem',
    fontWeight: 600,
    textTransform: 'capitalize',
    marginBottom: '0.75rem',
    textAlign: 'center',
  },
  card: {
    background: '#fff',
    borderRadius: '8px',
    padding: '0.75rem',
    marginBottom: '0.5rem',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    cursor: 'pointer',
    fontSize: '0.85rem',
  },
  cardTitle: { fontWeight: 600, marginBottom: '0.25rem' },
  cardMeta: { color: '#888', fontSize: '0.8rem' },
  empty: { color: '#aaa', fontSize: '0.8rem', textAlign: 'center', padding: '1rem' },
}

export default function ApplicationsPage() {
  const navigate = useNavigate()
  const [apps, setApps] = useState([])
  const [dragItem, setDragItem] = useState(null)

  const load = async () => {
    try {
      const res = await getApplications({ exclude_status: 'not_interested' })
      setApps(res.data)
    } catch (err) {
      console.error('Failed to load applications:', err)
    }
  }

  useEffect(() => { load() }, [])

  const handleDrop = async (newStatus) => {
    if (!dragItem || dragItem.status === newStatus) return
    try {
      await updateApplication(dragItem.id, { status: newStatus })
      load()
    } catch (err) {
      console.error('Failed to update:', err)
    }
    setDragItem(null)
  }

  return (
    <div>
      <h2 style={styles.h2}>Applications ({apps.length})</h2>
      <div style={styles.board}>
        {COLUMNS.map(status => {
          const colApps = apps.filter(a => a.status === status)
          return (
            <div
              key={status}
              style={{ ...styles.column, background: COLUMN_COLORS[status] }}
              onDragOver={(e) => e.preventDefault()}
              onDrop={() => handleDrop(status)}
            >
              <div style={styles.colTitle}>{status} ({colApps.length})</div>
              {colApps.length === 0 && <div style={styles.empty}>Drop here</div>}
              {colApps.map(app => (
                <div
                  key={app.id}
                  style={styles.card}
                  draggable
                  onDragStart={() => setDragItem(app)}
                  onClick={() => app.job && navigate(`/jobs/${app.job.id}`)}
                >
                  <div style={styles.cardTitle}>{app.job?.title || 'Unknown'}</div>
                  <div style={styles.cardMeta}>
                    {app.job?.company}
                    {app.job?.match_score != null && ` · Score: ${app.job.match_score}`}
                  </div>
                </div>
              ))}
            </div>
          )
        })}
      </div>
    </div>
  )
}
