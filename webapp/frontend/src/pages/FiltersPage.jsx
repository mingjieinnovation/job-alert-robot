import React, { useState, useEffect } from 'react'
import { getFilters, updateFilters, resetFilters } from '../api'

const styles = {
  h2: { fontSize: '1.4rem', fontWeight: 700, marginBottom: '1.5rem' },
  section: {
    background: '#fff',
    borderRadius: '12px',
    padding: '1.25rem 1.5rem',
    boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
    marginBottom: '1rem',
  },
  sectionTitle: { fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' },
  label: { fontSize: '0.85rem', color: '#666', marginBottom: '0.25rem', display: 'block' },
  numberInput: {
    padding: '0.5rem 0.75rem',
    border: '1px solid #ddd',
    borderRadius: '8px',
    fontSize: '0.95rem',
    width: '140px',
  },
  row: { display: 'flex', gap: '1.5rem', alignItems: 'center', marginBottom: '0.75rem', flexWrap: 'wrap' },
  chips: { display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.5rem' },
  chip: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.3rem',
    padding: '0.3rem 0.7rem',
    borderRadius: '16px',
    fontSize: '0.8rem',
    fontWeight: 500,
    background: '#f0f0f0',
    color: '#333',
  },
  chipDelete: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    fontSize: '0.85rem',
    color: '#999',
    padding: 0,
    lineHeight: 1,
  },
  addRow: { display: 'flex', gap: '0.4rem', marginTop: '0.5rem' },
  input: {
    flex: 1,
    padding: '0.4rem 0.6rem',
    border: '1px solid #ddd',
    borderRadius: '6px',
    fontSize: '0.85rem',
  },
  addBtn: {
    background: '#667eea',
    color: '#fff',
    border: 'none',
    padding: '0.4rem 0.8rem',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '0.8rem',
    fontWeight: 500,
  },
  saveBtn: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: '#fff',
    border: 'none',
    padding: '0.7rem 2rem',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: 600,
    fontSize: '1rem',
    marginRight: '0.75rem',
  },
  resetBtn: {
    background: '#f5f5f5',
    color: '#666',
    border: '1px solid #ddd',
    padding: '0.7rem 1.5rem',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: 500,
    fontSize: '0.9rem',
  },
  saved: { color: '#2e7d32', fontSize: '0.9rem', fontWeight: 500, marginLeft: '0.75rem' },
  desc: { fontSize: '0.8rem', color: '#999', marginBottom: '0.5rem' },
}

const FILTER_SECTIONS = [
  { key: 'title_must_contain', label: 'Title Must Contain (at least one)', desc: 'Job title must include one of these keywords', color: '#e8f5e9', textColor: '#2e7d32' },
  { key: 'title_exclude_roles', label: 'Exclude Roles', desc: 'Exclude these job roles from results', color: '#fce4ec', textColor: '#c62828' },
  { key: 'title_exclude_seniority', label: 'Exclude Seniority', desc: 'Too senior titles to exclude', color: '#fce4ec', textColor: '#c62828' },
  { key: 'title_exclude_junior', label: 'Exclude Junior/Entry', desc: 'Too junior titles to exclude', color: '#fce4ec', textColor: '#c62828' },
  { key: 'title_exclude_analyst_prefixes', label: 'Exclude Analyst Prefixes', desc: 'Associate/junior/intern analyst variants', color: '#fce4ec', textColor: '#c62828' },
  { key: 'title_exclude_other', label: 'Exclude Other', desc: 'Other title keywords to exclude (IT, summer, training...)', color: '#fce4ec', textColor: '#c62828' },
  { key: 'contract_keywords', label: 'Contract Keywords', desc: 'Keywords indicating contract/temp roles (checked in title + description)', color: '#fff3e0', textColor: '#e65100' },
  { key: 'language_exclude', label: 'Exclude Languages', desc: 'Filter out jobs requiring these languages (keeps Chinese + English)', color: '#e3f2fd', textColor: '#1565c0' },
]

function ChipList({ items, color, textColor, onRemove, onAdd }) {
  const [newItem, setNewItem] = useState('')

  const handleAdd = () => {
    if (newItem.trim() && !items.includes(newItem.trim())) {
      onAdd(newItem.trim())
      setNewItem('')
    }
  }

  return (
    <>
      <div style={styles.chips}>
        {items.map((item, i) => (
          <span key={i} style={{ ...styles.chip, background: color, color: textColor }}>
            {item}
            <button style={styles.chipDelete} onClick={() => onRemove(item)}>&times;</button>
          </span>
        ))}
        {items.length === 0 && <span style={{ color: '#999', fontSize: '0.8rem' }}>None</span>}
      </div>
      <div style={styles.addRow}>
        <input
          style={styles.input}
          value={newItem}
          onChange={(e) => setNewItem(e.target.value)}
          placeholder="Add keyword..."
          onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
        />
        <button style={styles.addBtn} onClick={handleAdd}>Add</button>
      </div>
    </>
  )
}

export default function FiltersPage() {
  const [filters, setFilters] = useState(null)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    getFilters().then(res => setFilters(res.data)).catch(console.error)
  }, [])

  if (!filters) return <div style={{ textAlign: 'center', padding: '3rem', color: '#888' }}>Loading filters...</div>

  const updateLocal = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }))
    setSaved(false)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const res = await updateFilters(filters)
      setFilters(res.data.filters)
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err) {
      alert('Failed to save: ' + (err.response?.data?.error || err.message))
    } finally {
      setSaving(false)
    }
  }

  const handleReset = async () => {
    if (!window.confirm('Reset all filters to defaults?')) return
    try {
      const res = await resetFilters()
      setFilters(res.data.filters)
      setSaved(false)
    } catch (err) {
      alert('Failed to reset: ' + err.message)
    }
  }

  return (
    <div>
      <h2 style={styles.h2}>Search Filters</h2>

      {/* Numeric filters */}
      <div style={styles.section}>
        <div style={styles.sectionTitle}>Salary & Experience</div>
        <div style={styles.row}>
          <div>
            <label style={styles.label}>Minimum Salary (per year)</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <span style={{ fontSize: '1rem' }}>£</span>
              <input
                type="number"
                style={styles.numberInput}
                value={filters.min_salary}
                onChange={(e) => updateLocal('min_salary', parseInt(e.target.value) || 0)}
                step={5000}
              />
            </div>
          </div>
          <div>
            <label style={styles.label}>Max Experience (years)</label>
            <input
              type="number"
              style={styles.numberInput}
              value={filters.max_experience_years}
              onChange={(e) => updateLocal('max_experience_years', parseInt(e.target.value) || 0)}
              min={0}
              max={20}
            />
          </div>
        </div>
      </div>

      {/* List filters */}
      {FILTER_SECTIONS.map(({ key, label, desc, color, textColor }) => (
        <div key={key} style={styles.section}>
          <div style={styles.sectionTitle}>{label}</div>
          <div style={styles.desc}>{desc}</div>
          <ChipList
            items={filters[key] || []}
            color={color}
            textColor={textColor}
            onRemove={(item) => updateLocal(key, filters[key].filter(i => i !== item))}
            onAdd={(item) => updateLocal(key, [...(filters[key] || []), item])}
          />
        </div>
      ))}

      {/* Actions */}
      <div style={{ marginTop: '1.5rem', display: 'flex', alignItems: 'center' }}>
        <button style={styles.saveBtn} onClick={handleSave} disabled={saving}>
          {saving ? 'Saving...' : 'Save Filters'}
        </button>
        <button style={styles.resetBtn} onClick={handleReset}>
          Reset to Defaults
        </button>
        {saved && <span style={styles.saved}>Filters saved!</span>}
      </div>
    </div>
  )
}
