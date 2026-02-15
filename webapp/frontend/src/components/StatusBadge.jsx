import React from 'react'

const statusColors = {
  interested: { bg: '#e3f2fd', color: '#1565c0' },
  applied: { bg: '#fff3e0', color: '#e65100' },
  interview: { bg: '#f3e5f5', color: '#7b1fa2' },
  offer: { bg: '#e8f5e9', color: '#2e7d32' },
  rejected: { bg: '#fce4ec', color: '#c62828' },
  not_interested: { bg: '#f5f5f5', color: '#999' },
}

export default function StatusBadge({ status }) {
  const colors = statusColors[status] || { bg: '#f5f5f5', color: '#666' }
  return (
    <span style={{
      display: 'inline-block',
      padding: '0.2rem 0.6rem',
      borderRadius: '12px',
      fontSize: '0.8rem',
      fontWeight: 600,
      background: colors.bg,
      color: colors.color,
      textTransform: 'capitalize',
    }}>
      {status}
    </span>
  )
}
