import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (data: { name: string; email: string; password: string }) =>
    api.post('/api/auth/register', data),
  
  login: (data: { email: string; password: string }) =>
    api.post('/api/auth/login', data),
};

export const profileAPI = {
  getProfile: () => api.get('/api/profile'),
  
  createProfile: (data: any) => api.post('/api/profile', data),
  
  updateProfile: (data: any) => api.put('/api/profile', data),
  
  getPortfolioProjects: () => api.get('/api/profile/portfolio'),
  
  addPortfolioProject: (data: any) => api.post('/api/profile/portfolio', data),
};

export const jobsAPI = {
  getJobs: (params?: { skip?: number; limit?: number }) =>
    api.get('/api/jobs', { params }),

  getJob: (id: number) => api.get(`/api/jobs/${id}`),

  createJob: (data: any) => api.post('/api/jobs', data),

  analyzeJob: (id: number) => api.post(`/api/jobs/${id}/analyze`),

  getJobAnalysis: (id: number) => api.get(`/api/jobs/${id}/analysis`),

  /** Phase 3: approve a job (status → APPROVED) */
  approveJob: (id: number) => api.post(`/api/jobs/${id}/approve`),

  /** Phase 3: reject a job (status → REJECTED) */
  rejectJob: (id: number) => api.post(`/api/jobs/${id}/reject`),
};

export const healthAPI = {
  check: () => api.get('/api/health'),
};

export const gmailAPI = {
  /** Get the Google OAuth URL to redirect the user to */
  getAuthUrl: () => api.get<{ auth_url: string }>('/api/gmail/auth-url'),

  /** Get Gmail connection status */
  getStatus: () => api.get<import('../types').GmailStatus>('/api/gmail/status'),

  /** Manually trigger a Gmail sync */
  sync: () => api.post<import('../types').GmailSyncResult>('/api/gmail/sync'),

  /** Disconnect Gmail */
  disconnect: () => api.delete('/api/gmail/disconnect'),
};

export const notificationsAPI = {
  /** Lightweight unread count — polled every 30s */
  getCount: () => api.get<import('../types').NotificationCount>('/api/notifications/count'),

  /** Full notification list */
  getAll: (params?: { limit?: number; unread_only?: boolean }) =>
    api.get<import('../types').NotificationList>('/api/notifications', { params }),

  /** Mark a single notification as read */
  markRead: (id: number) => api.patch(`/api/notifications/${id}/read`),

  /** Mark all notifications as read */
  markAllRead: () => api.patch('/api/notifications/read-all'),

  /** Delete all notifications */
  clearAll: () => api.delete('/api/notifications/all'),
};

export const proposalsAPI = {
  /** Generate AI proposal and cover letter pitch */
  generate: (jobId: number, data?: import('../types').ProposalGenerateRequest) =>
    api.post<import('../types').Proposal>(`/api/jobs/${jobId}/proposals/generate`, data || {}),

  /** Get all proposals and version history for a job */
  getJobProposals: (jobId: number) =>
    api.get<import('../types').Proposal[]>(`/api/jobs/${jobId}/proposals`),

  /** Get a single proposal by ID */
  getProposal: (id: number) =>
    api.get<import('../types').Proposal>(`/api/proposals/${id}`),

  /** Update proposal content, cover letter, or metadata */
  updateProposal: (id: number, data: import('../types').ProposalUpdateRequest) =>
    api.put<import('../types').Proposal>(`/api/proposals/${id}`, data),

  /** Approve proposal (status -> APPROVED, job -> PROPOSAL_APPROVED) */
  approveProposal: (id: number) =>
    api.post<import('../types').Proposal>(`/api/proposals/${id}/approve`),

  /** Reject proposal (status -> REJECTED) */
  rejectProposal: (id: number) =>
    api.post<import('../types').Proposal>(`/api/proposals/${id}/reject`),
};

export const outreachAPI = {
  /** Create or save an outreach email draft */
  createDraft: (jobId: number, data: import('../types').OutreachDraftCreate) =>
    api.post<import('../types').OutreachMessage>(`/api/jobs/${jobId}/outreach/draft`, data),

  /** Get all outreach history and drafts for a job */
  getJobOutreach: (jobId: number) =>
    api.get<import('../types').OutreachMessage[]>(`/api/jobs/${jobId}/outreach`),

  /** Get single outreach message */
  getOutreach: (id: number) =>
    api.get<import('../types').OutreachMessage>(`/api/outreach/${id}`),

  /** Update an unsent outreach draft */
  updateOutreach: (id: number, data: import('../types').OutreachUpdate) =>
    api.put<import('../types').OutreachMessage>(`/api/outreach/${id}`, data),

  /** Send email outreach via connected Gmail API */
  send: (jobId: number, data: import('../types').OutreachSendRequest) =>
    api.post<import('../types').OutreachMessage>(`/api/jobs/${jobId}/outreach/send`, data),

  /** Delete an unsent draft */
  deleteDraft: (id: number) =>
    api.delete(`/api/outreach/${id}`),
};

export const linkedinAPI = {
  /** Generate LinkedIn Connection Note & InMail Pitch */
  generate: (jobId: number, data: import('../types').LinkedInGenerateRequest) =>
    api.post<import('../types').LinkedInMessage>(`/api/jobs/${jobId}/linkedin/generate`, data),

  /** Get all generated LinkedIn messages for a job */
  getJobMessages: (jobId: number) =>
    api.get<import('../types').LinkedInMessage[]>(`/api/jobs/${jobId}/linkedin`),

  /** Get single LinkedIn message */
  getMessage: (id: number) =>
    api.get<import('../types').LinkedInMessage>(`/api/linkedin/${id}`),

  /** Update connection note or InMail */
  updateMessage: (id: number, data: import('../types').LinkedInUpdateRequest) =>
    api.put<import('../types').LinkedInMessage>(`/api/linkedin/${id}`, data),

  /** Mark message as sent on LinkedIn (advances job status to CONTACTED) */
  markSent: (id: number) =>
    api.post<import('../types').LinkedInMessage>(`/api/linkedin/${id}/mark-sent`),

  /** Delete a LinkedIn message */
  deleteMessage: (id: number) =>
    api.delete(`/api/linkedin/${id}`),
};

export const webhooksAPI = {
  /** Get or generate inbound webhook token and url */
  getToken: () =>
    api.get<import('../types').WebhookTokenResponse>('/api/webhooks/token'),

  /** Regenerate inbound webhook token */
  regenerateToken: () =>
    api.post<import('../types').WebhookTokenResponse>('/api/webhooks/token/regenerate'),

  /** List all outbound webhook subscriptions */
  getSubscriptions: () =>
    api.get<import('../types').WebhookSubscription[]>('/api/webhooks/subscriptions'),

  /** Create new outbound webhook subscription */
  createSubscription: (data: import('../types').WebhookSubscriptionCreate) =>
    api.post<import('../types').WebhookSubscription>('/api/webhooks/subscriptions', data),

  /** Update outbound webhook subscription */
  updateSubscription: (id: number, data: import('../types').WebhookSubscriptionUpdate) =>
    api.put<import('../types').WebhookSubscription>(`/api/webhooks/subscriptions/${id}`, data),

  /** Delete outbound webhook subscription */
  deleteSubscription: (id: number) =>
    api.delete(`/api/webhooks/subscriptions/${id}`),

  /** Send test ping to subscription */
  testSubscription: (id: number) =>
    api.post<import('../types').WebhookTestResponse>(`/api/webhooks/subscriptions/${id}/test`),
};

export default api;


