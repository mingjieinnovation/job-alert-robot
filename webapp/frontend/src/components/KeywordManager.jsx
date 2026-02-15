import React, { useState, useEffect } from 'react'
import { getKeywords, addKeyword, updateKeyword, deleteKeyword } from '../api'

const styles = {
  container: {
    background: '#fff',
    borderRadius: '12px',
    padding: '1.5rem',
    boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
    marginBottom: '1.5rem',
  },
  title: { fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' },
  section: { marginBottom: '1rem' },
  sectionTitle: { fontSize: '0.85rem', fontWeight: 600, color: '#888', marginBottom: '0.5rem', textTransform: 'uppercase' },
  chips: { display: 'flex', flexWrap: 'wrap', gap: '0.5rem' },
  chip: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.4rem',
    padding: '0.35rem 0.75rem',
    borderRadius: '20px',
    fontSize: '0.85rem',
    fontWeight: 500,
    cursor: 'pointer',
  },
  boostChip: { background: '#e8f5e9', color: '#2e7d32', border: '1px solid #a5d6a7' },
  excludeChip: { background: '#fce4ec', color: '#c62828', border: '1px solid #ef9a9a' },
  deleteBtn: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    fontSize: '0.8rem',
    color: 'inherit',
    opacity: 0.6,
    padding: 0,
  },
  addRow: { display: 'flex', gap: '0.5rem', marginTop: '1rem' },
  input: {
    flex: 1,
    padding: '0.5rem 0.75rem',
    border: '1px solid #ddd',
    borderRadius: '8px',
    fontSize: '0.9rem',
  },
  select: {
    padding: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '8px',
    fontSize: '0.9rem',
  },
  addBtn: {
    background: '#667eea',
    color: '#fff',
    border: 'none',
    padding: '0.5rem 1rem',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: 500,
  },
  weight: { fontSize: '0.7rem', opacity: 0.7 },
}

export default function KeywordManager({ refreshTrigger }) {
  const [keywords, setKeywords] = useState([])
  const [newKw, setNewKw] = useState('')
  const [newCat, setNewCat] = useState('boost')

  const load = async () => {
    try {
      const res = await getKeywords()
      setKeywords(res.data)
    } catch (err) {
      console.error('Failed to load keywords:', err)
    }
  }

  useEffect(() => { load() }, [refreshTrigger])

  const handleAdd = async () => {
    if (!newKw.trim()) return
    await addKeyword({ keyword: newKw.trim(), category: newCat })
    setNewKw('')
    load()
  }

  const handleToggle = async (kw) => {
    const newCategory = kw.category === 'boost' ? 'exclude' : 'boost'
    await updateKeyword(kw.id, { category: newCategory })
    load()
  }

  const handleDelete = async (kw) => {
    await deleteKeyword(kw.id)
    load()
  }

  const boostKws = keywords.filter(k => k.category === 'boost')
  const excludeKws = keywords.filter(k => k.category === 'exclude')

  return (
    <div style={styles.container}>
      <div style={styles.title}>Keywords ({keywords.length})</div>

      <div style={styles.section}>
        <div style={styles.sectionTitle}>Boost Keywords</div>
        <div style={styles.chips}>
          {boostKws.map(kw => (
            <span key={kw.id} style={{ ...styles.chip, ...styles.boostChip }} onClick={() => handleToggle(kw)}>
              {kw.keyword}
              {kw.weight !== 1 && <span style={styles.weight}>({kw.weight}x)</span>}
              {kw.source === 'learned' && <span style={styles.weight}>learned</span>}
              <button style={styles.deleteBtn} onClick={(e) => { e.stopPropagation(); handleDelete(kw) }}>x</button>
            </span>
          ))}
          {boostKws.length === 0 && <span style={{ color: '#999', fontSize: '0.85rem' }}>No boost keywords yet</span>}
        </div>
      </div>

      <div style={styles.section}>
        <div style={styles.sectionTitle}>Exclude Keywords</div>
        <div style={styles.chips}>
          {excludeKws.map(kw => (
            <span key={kw.id} style={{ ...styles.chip, ...styles.excludeChip }} onClick={() => handleToggle(kw)}>
              {kw.keyword}
              {kw.source === 'learned' && <span style={styles.weight}>learned</span>}
              <button style={styles.deleteBtn} onClick={(e) => { e.stopPropagation(); handleDelete(kw) }}>x</button>
            </span>
          ))}
          {excludeKws.length === 0 && <span style={{ color: '#999', fontSize: '0.85rem' }}>No exclude keywords yet</span>}
        </div>
      </div>

      <div style={styles.addRow}>
        <input
          style={styles.input}
          value={newKw}
          onChange={(e) => setNewKw(e.target.value)}
          placeholder="Add keyword..."
          onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
        />
        <select style={styles.select} value={newCat} onChange={(e) => setNewCat(e.target.value)}>
          <option value="boost">Boost</option>
          <option value="exclude">Exclude</option>
        </select>
        <button style={styles.addBtn} onClick={handleAdd}>Add</button>
      </div>
    </div>
  )
}
