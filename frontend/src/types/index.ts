export interface User {
  id: number;
  name: string;
  email: string;
  created_at: string;
}

export interface StartupProfile {
  id: number;
  user_id: number;
  startup_name: string;
  description?: string;
  website?: string;
  industry?: string;
  services?: string[];
  technical_skills?: string[];
  preferred_job_types?: string[];
  preferred_industries?: string[];
  minimum_budget?: number;
  preferred_budget?: number;
  preferred_locations?: string[];
  remote_allowed: boolean;
  team_size?: number;
  certifications?: string[];
  keywords?: string[];
  excluded_keywords?: string[];
  contact_email?: string;
  linkedin_url?: string;
  created_at: string;
  updated_at: string;
}

export interface PortfolioProject {
  id: number;
  startup_profile_id: number;
  project_name: string;
  description?: string;
  skills?: string[];
  portfolio_url?: string;
  case_study?: string;
  technologies?: string[];
  results?: string[];
  created_at: string;
  updated_at: string;
}

export type JobStatus = 'NEW' | 'ANALYZING' | 'REVIEW_REQUIRED' | 'REJECTED' | 'APPROVED' | 'PROPOSAL_PENDING' | 'PROPOSAL_READY' | 'PROPOSAL_APPROVED' | 'OUTREACH_PENDING' | 'CONTACTED' | 'CLOSED';

export interface Job {
  id: number;
  user_id: number;
  source: string;
  source_job_id?: string;
  url?: string;
  title: string;
  company?: string;
  description: string;
  location?: string;
  job_type?: string;
  salary_min?: number;
  salary_max?: number;
  currency: string;
  skills?: string[];
  posted_at?: string;
  discovered_at: string;
  raw_content?: string;
  status: JobStatus;
  created_at: string;
  updated_at: string;
}

export interface JobAnalysis {
  id: number;
  job_id: number;
  can_do: boolean;
  confidence?: number;
  match_score: number;
  technical_match: number;
  service_match: number;
  experience_match: number;
  budget_match: number;
  location_match: number;
  reasoning?: string[];
  missing_requirements?: string[];
  risks?: string[];
  recommended_action: string;
  relevant_portfolio_projects?: number[];
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

// Phase 2 — Gmail types
export interface GmailStatus {
  connected: boolean;
  gmail_email?: string | null;
  last_sync_at?: string | null;
}

export interface GmailSyncResult {
  new_jobs: number;
  duplicates_skipped: number;
  not_job_emails: number;
  errors: number;
  total_processed: number;
  message: string;
}

export interface GmailAuthUrl {
  auth_url: string;
}

// Phase 3 — Notification types
export type NotificationType =
  | 'NEW_JOB'
  | 'ANALYSIS_COMPLETE'
  | 'REVIEW_REQUIRED'
  | 'JOB_APPROVED'
  | 'JOB_REJECTED'
  | 'PROPOSAL_READY'
  | 'PROPOSAL_APPROVED'
  | 'OUTREACH_SENT';

export interface Notification {
  id: number;
  user_id: number;
  type: NotificationType;
  title: string;
  message: string;
  job_id?: number | null;
  read: boolean;
  created_at: string;
}

export interface NotificationList {
  notifications: Notification[];
  unread: number;
}

export interface NotificationCount {
  unread: number;
}

// Phase 4 — Proposal types
export type ProposalStatus = 'DRAFT' | 'APPROVED' | 'REJECTED';

export interface Proposal {
  id: number;
  job_id: number;
  user_id: number;
  version: number;
  title: string;
  tone: string;
  custom_instructions?: string | null;
  content: string;
  cover_letter?: string | null;
  estimated_duration?: string | null;
  estimated_budget?: string | null;
  relevant_projects?: number[];
  status: ProposalStatus;
  created_at: string;
  updated_at?: string | null;
}

export interface ProposalGenerateRequest {
  tone?: string;
  custom_instructions?: string;
  include_portfolio_ids?: number[];
}

export interface ProposalUpdateRequest {
  title?: string;
  content?: string;
  cover_letter?: string;
  estimated_duration?: string;
  estimated_budget?: string;
  tone?: string;
  status?: ProposalStatus;
}

// Phase 5 — Email Outreach types
export type OutreachStatus = 'DRAFT' | 'PENDING_APPROVAL' | 'SENT' | 'FAILED';

export interface OutreachMessage {
  id: number;
  job_id: number;
  user_id: number;
  proposal_id?: number | null;
  recipient_email: string;
  recipient_name?: string | null;
  subject: string;
  body: string;
  status: OutreachStatus;
  gmail_message_id?: string | null;
  gmail_thread_id?: string | null;
  sent_at?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface OutreachDraftCreate {
  recipient_email: string;
  recipient_name?: string;
  subject: string;
  body: string;
  proposal_id?: number;
}

export interface OutreachUpdate {
  recipient_email?: string;
  recipient_name?: string;
  subject?: string;
  body?: string;
}

export interface OutreachSendRequest {
  recipient_email: string;
  recipient_name?: string;
  subject: string;
  body: string;
  proposal_id?: number;
  confirm_send: boolean;
}

// Phase 6 — LinkedIn Outreach types
export interface LinkedInMessage {
  id: number;
  job_id: number;
  user_id: number;
  recipient_name?: string | null;
  recipient_role?: string | null;
  recipient_profile_url?: string | null;
  tone: string;
  connection_note: string;
  inmail_subject: string;
  inmail_body: string;
  status: 'GENERATED' | 'SENT';
  sent_at?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface LinkedInGenerateRequest {
  recipient_name?: string;
  recipient_role?: string;
  recipient_profile_url?: string;
  tone?: string;
  custom_instructions?: string;
}

export interface LinkedInUpdateRequest {
  recipient_name?: string;
  recipient_role?: string;
  recipient_profile_url?: string;
  connection_note?: string;
  inmail_subject?: string;
  inmail_body?: string;
}

// Phase 7 — Webhooks & Automations types
export interface WebhookTokenResponse {
  webhook_token: string;
  inbound_url: string;
}

export interface WebhookSubscription {
  id: number;
  user_id: number;
  target_url: string;
  description?: string | null;
  secret_token?: string | null;
  events: string[];
  is_active: boolean;
  created_at?: string | null;
  last_triggered_at?: string | null;
  last_status_code?: number | null;
}

export interface WebhookSubscriptionCreate {
  target_url: string;
  description?: string;
  secret_token?: string;
  events?: string[];
  is_active?: boolean;
}

export interface WebhookSubscriptionUpdate {
  target_url?: string;
  description?: string;
  secret_token?: string;
  events?: string[];
  is_active?: boolean;
}

export interface WebhookTestResponse {
  success: boolean;
  status_code?: number | null;
  response_body?: string | null;
  message: string;
}



