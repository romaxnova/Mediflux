// API Configuration
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_URL || 'https://mediflux-mf64.onrender.com',
  ENDPOINTS: {
    CHAT: '/chat',
    DOCUMENT_ANALYZE: '/document/analyze',
    PROFILE_SAVE: '/profile/save',
    PROFILE_GET: '/profile',
    REIMBURSEMENT: '/analysis/reimbursement',
    PATHWAY: '/analysis/pathway'
  }
}

export const getApiUrl = (endpoint: string) => {
  return `${API_CONFIG.BASE_URL}${endpoint}`
}