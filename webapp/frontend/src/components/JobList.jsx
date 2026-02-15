import React from 'react'
import JobCard from './JobCard'

export default function JobList({ jobs, loading, onDismiss }) {
  if (loading) {
    return <div style={{ textAlign: 'center', padding: '3rem', color: '#888' }}>Searching for jobs...</div>
  }

  if (!jobs || jobs.length === 0) {
    return <div style={{ textAlign: 'center', padding: '3rem', color: '#888' }}>No jobs found. Try adjusting your keywords and searching again.</div>
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      {jobs.map(job => (
        <JobCard key={job.id} job={job} onDismiss={onDismiss} />
      ))}
    </div>
  )
}
