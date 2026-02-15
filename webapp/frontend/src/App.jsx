import React from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import HomePage from './pages/HomePage'
import SearchPage from './pages/SearchPage'
import JobDetailPage from './pages/JobDetailPage'
import ApplicationsPage from './pages/ApplicationsPage'
import AnalyticsPage from './pages/AnalyticsPage'
import FiltersPage from './pages/FiltersPage'

const navStyle = {
  display: 'flex',
  gap: '1rem',
  padding: '1rem 2rem',
  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
  alignItems: 'center',
}

const linkStyle = {
  color: 'rgba(255,255,255,0.8)',
  textDecoration: 'none',
  padding: '0.5rem 1rem',
  borderRadius: '8px',
  fontSize: '0.95rem',
  fontWeight: 500,
  transition: 'all 0.2s',
}

const activeLinkStyle = {
  ...linkStyle,
  color: '#fff',
  background: 'rgba(255,255,255,0.2)',
}

export default function App() {
  return (
    <BrowserRouter>
      <nav style={navStyle}>
        <span style={{ color: '#fff', fontWeight: 700, fontSize: '1.2rem', marginRight: '1rem' }}>
          AI Job Alert
        </span>
        <NavLink to="/" style={({ isActive }) => isActive ? activeLinkStyle : linkStyle} end>
          Home
        </NavLink>
        <NavLink to="/search" style={({ isActive }) => isActive ? activeLinkStyle : linkStyle}>
          Search
        </NavLink>
        <NavLink to="/applications" style={({ isActive }) => isActive ? activeLinkStyle : linkStyle}>
          Applications
        </NavLink>
        <NavLink to="/filters" style={({ isActive }) => isActive ? activeLinkStyle : linkStyle}>
          Filters
        </NavLink>
        <NavLink to="/analytics" style={({ isActive }) => isActive ? activeLinkStyle : linkStyle}>
          Analytics
        </NavLink>
      </nav>
      <main style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem' }}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/jobs/:id" element={<JobDetailPage />} />
          <Route path="/applications" element={<ApplicationsPage />} />
          <Route path="/filters" element={<FiltersPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
