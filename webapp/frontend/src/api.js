import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

// Resume
export const getResumeStatus = () => api.get('/resume/status')
export const uploadResume = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/resume/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

// Keywords
export const getKeywords = () => api.get('/keywords')
export const addKeyword = (data) => api.post('/keywords', data)
export const updateKeyword = (id, data) => api.put(`/keywords/${id}`, data)
export const deleteKeyword = (id) => api.delete(`/keywords/${id}`)

// Jobs
export const searchJobs = () => api.post('/jobs/search')
export const getJobs = (params) => api.get('/jobs', { params })
export const getJob = (id) => api.get(`/jobs/${id}`)
export const rescoreJobs = () => api.post('/jobs/rescore')

// Applications
export const getApplications = (params) => api.get('/applications', { params })
export const createApplication = (data) => api.post('/applications', data)
export const updateApplication = (id, data) => api.put(`/applications/${id}`, data)
export const deleteApplication = (id) => api.delete(`/applications/${id}`)
export const addFeedback = (appId, data) => api.post(`/applications/${appId}/feedback`, data)
export const saveLearnedKeywords = (data) => api.post('/applications/save-keywords', data)

// Analytics
export const retrain = () => api.post('/analytics/retrain')
export const getInsights = () => api.get('/analytics/insights')

// Filters
export const getFilters = () => api.get('/filters')
export const updateFilters = (data) => api.put('/filters', data)
export const resetFilters = () => api.post('/filters/reset')

// JD Analysis
export const analyzeJD = (text) => api.post('/jd/analyze', { text })
export const applyJDSuggestions = (data) => api.post('/jd/apply', data)

export default api
