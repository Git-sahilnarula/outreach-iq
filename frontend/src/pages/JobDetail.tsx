import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { jobsAPI, proposalsAPI, outreachAPI, gmailAPI, linkedinAPI } from '../services/api';
import { Job, JobAnalysis, Proposal, OutreachMessage, GmailStatus, LinkedInMessage } from '../types';
import {
  ArrowLeft, Brain, AlertTriangle, CheckCircle,
  ThumbsUp, ThumbsDown, FileText, Sparkles, Copy, Check, Edit3, Save, X, RefreshCw,
  Mail, Send, ExternalLink, ChevronDown, ChevronUp, History,
  Linkedin, UserPlus, MessageSquare
} from 'lucide-react';


const TONES = [
  { value: 'professional', label: 'Professional', desc: 'Authoritative, polished & executive' },
  { value: 'conversational', label: 'Conversational', desc: 'Warm, personable & collaborative' },
  { value: 'bold', label: 'Bold', desc: 'High-impact, confident & outcome-driven' },
  { value: 'technical', label: 'Technical', desc: 'Deep engineering & architecture focus' },
  { value: 'consultative', label: 'Consultative', desc: 'Strategic advisory & high ROI' },
];

const LINKEDIN_TONES = [
  { value: 'value_first', label: 'Value-First', desc: 'Focus on immediate ROI & solution preview' },
  { value: 'direct', label: 'Direct', desc: 'Concise, punchy & straight to business' },
  { value: 'networking', label: 'Networking', desc: 'Warm, collaborative & peer-to-peer' },
  { value: 'thought_leadership', label: 'Thought Leadership', desc: 'Strategic insights & domain authority' },
];

const JobDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [job, setJob] = useState<Job | null>(null);
  const [analysis, setAnalysis] = useState<JobAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [approving, setApproving] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  // Phase 4: Proposals state
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [activeProposal, setActiveProposal] = useState<Proposal | null>(null);
  const [generatingProposal, setGeneratingProposal] = useState(false);
  const [proposalTone, setProposalTone] = useState('professional');
  const [customInstructions, setCustomInstructions] = useState('');
  const [activeTab, setActiveTab] = useState<'proposal' | 'cover_letter'>('proposal');
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [editCoverLetter, setEditCoverLetter] = useState('');
  const [editDuration, setEditDuration] = useState('');
  const [editBudget, setEditBudget] = useState('');
  const [savingEdit, setSavingEdit] = useState(false);
  const [copiedProposal, setCopiedProposal] = useState(false);
  const [copiedCoverLetter, setCopiedCoverLetter] = useState(false);
  const [proposalActionMsg, setProposalActionMsg] = useState<string | null>(null);
  const [showConfig, setShowConfig] = useState(false);

  // Phase 5: Outreach state
  const [outreachList, setOutreachList] = useState<OutreachMessage[]>([]);
  const [gmailStatus, setGmailStatus] = useState<GmailStatus | null>(null);
  const [recipientEmail, setRecipientEmail] = useState('');
  const [recipientName, setRecipientName] = useState('');
  const [outreachSubject, setOutreachSubject] = useState('');
  const [outreachBody, setOutreachBody] = useState('');
  const [savingDraft, setSavingDraft] = useState(false);
  const [sendingOutreach, setSendingOutreach] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [outreachAlert, setOutreachAlert] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [expandedOutreachId, setExpandedOutreachId] = useState<number | null>(null);

  // Phase 6: LinkedIn state
  const [linkedinMessages, setLinkedinMessages] = useState<LinkedInMessage[]>([]);
  const [activeLinkedInMsg, setActiveLinkedInMsg] = useState<LinkedInMessage | null>(null);
  const [liRecipientName, setLiRecipientName] = useState('');
  const [liRecipientRole, setLiRecipientRole] = useState('');
  const [liProfileUrl, setLiProfileUrl] = useState('');
  const [liTone, setLiTone] = useState('value_first');
  const [liCustomInstructions, setLiCustomInstructions] = useState('');
  const [generatingLinkedIn, setGeneratingLinkedIn] = useState(false);
  const [isEditingLinkedIn, setIsEditingLinkedIn] = useState(false);
  const [editLiNote, setEditLiNote] = useState('');
  const [editLiSubject, setEditLiSubject] = useState('');
  const [editLiBody, setEditLiBody] = useState('');
  const [savingLiEdit, setSavingLiEdit] = useState(false);
  const [markingLiSent, setMarkingLiSent] = useState(false);
  const [copiedLiNote, setCopiedLiNote] = useState(false);
  const [copiedLiInmail, setCopiedLiInmail] = useState(false);
  const [liAlert, setLiAlert] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [showLiConfig, setShowLiConfig] = useState(false);

  useEffect(() => {
    if (id) {
      loadJob(parseInt(id));
    }
  }, [id]);

  const loadJob = async (jobId: number) => {
    try {
      const [jobRes, analysisRes, proposalsRes, outreachRes, gmailRes, linkedinRes] = await Promise.all([
        jobsAPI.getJob(jobId),
        jobsAPI.getJobAnalysis(jobId).catch(() => null),
        proposalsAPI.getJobProposals(jobId).catch(() => null),
        outreachAPI.getJobOutreach(jobId).catch(() => null),
        gmailAPI.getStatus().catch(() => null),
        linkedinAPI.getJobMessages(jobId).catch(() => null),
      ]);
      const currentJob = jobRes.data;
      setJob(currentJob);
      setAnalysis(analysisRes?.data || null);

      const loadedProposals = proposalsRes?.data || [];
      setProposals(loadedProposals);
      if (loadedProposals.length > 0) {
        setActiveProposal(loadedProposals[0]);
      } else {
        setShowConfig(true); // Open config by default if no proposals exist yet
      }

      const messages: OutreachMessage[] = outreachRes?.data || [];
      setOutreachList(messages);
      setGmailStatus(gmailRes?.data || null);

      const liMsgs: LinkedInMessage[] = linkedinRes?.data || [];
      setLinkedinMessages(liMsgs);
      if (liMsgs.length > 0) {
        setActiveLinkedInMsg(liMsgs[0]);
      } else {
        setShowLiConfig(true);
      }

      // Pre-fill composer if a draft exists
      const draft = messages.find((m) => m.status === 'DRAFT');
      if (draft) {
        setRecipientEmail(draft.recipient_email);
        setRecipientName(draft.recipient_name || '');
        setOutreachSubject(draft.subject);
        setOutreachBody(draft.body);
      } else {
        const match = currentJob.description?.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
        if (match) {
          setRecipientEmail(match[0]);
        }
      }
    } catch (error) {
      console.error('Failed to load job details:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!job) return;
    setAnalyzing(true);
    try {
      const response = await jobsAPI.analyzeJob(job.id);
      setAnalysis(response.data);
      const jobRes = await jobsAPI.getJob(job.id);
      setJob(jobRes.data);
    } catch (error: any) {
      console.error('Analysis failed:', error);
      alert(error.response?.data?.detail || 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleApprove = async () => {
    if (!job) return;
    setApproving(true);
    setActionMsg(null);
    try {
      const res = await jobsAPI.approveJob(job.id);
      setJob(res.data);
      setActionMsg('Job approved! Proceed below to generate your client proposal.');
      setShowConfig(true);
    } catch (e: any) {
      setActionMsg(e.response?.data?.detail || 'Failed to approve job.');
    } finally {
      setApproving(false);
    }
  };

  const handleReject = async () => {
    if (!job) return;
    setRejecting(true);
    setActionMsg(null);
    try {
      const res = await jobsAPI.rejectJob(job.id);
      setJob(res.data);
      setActionMsg('Job marked as rejected.');
    } catch (e: any) {
      setActionMsg(e.response?.data?.detail || 'Failed to reject job.');
    } finally {
      setRejecting(false);
    }
  };

  // Phase 4: Proposal handlers
  const handleGenerateProposal = async () => {
    if (!job) return;
    setGeneratingProposal(true);
    setProposalActionMsg(null);
    try {
      const res = await proposalsAPI.generate(job.id, {
        tone: proposalTone,
        custom_instructions: customInstructions.trim() || undefined,
      });
      const newProposal = res.data;
      setProposals([newProposal, ...proposals]);
      setActiveProposal(newProposal);
      setIsEditing(false);
      setShowConfig(false);

      // Reload job to get PROPOSAL_READY status
      const jobRes = await jobsAPI.getJob(job.id);
      setJob(jobRes.data);
      setProposalActionMsg(`Draft proposal (v${newProposal.version}) created successfully!`);
    } catch (error: any) {
      console.error('Proposal generation failed:', error);
      alert(error.response?.data?.detail || 'Proposal generation failed.');
    } finally {
      setGeneratingProposal(false);
    }
  };

  const handleStartEdit = () => {
    if (!activeProposal) return;
    setEditTitle(activeProposal.title);
    setEditContent(activeProposal.content);
    setEditCoverLetter(activeProposal.cover_letter || '');
    setEditDuration(activeProposal.estimated_duration || '');
    setEditBudget(activeProposal.estimated_budget || '');
    setIsEditing(true);
  };

  const handleSaveEdit = async () => {
    if (!activeProposal) return;
    setSavingEdit(true);
    try {
      const res = await proposalsAPI.updateProposal(activeProposal.id, {
        title: editTitle,
        content: editContent,
        cover_letter: editCoverLetter,
        estimated_duration: editDuration || undefined,
        estimated_budget: editBudget || undefined,
      });
      const updated = res.data;
      setActiveProposal(updated);
      setProposals(proposals.map((p) => (p.id === updated.id ? updated : p)));
      setIsEditing(false);
      setProposalActionMsg('Proposal changes saved successfully.');
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Failed to save changes.');
    } finally {
      setSavingEdit(false);
    }
  };

  const handleApproveProposal = async () => {
    if (!activeProposal || !job) return;
    try {
      const res = await proposalsAPI.approveProposal(activeProposal.id);
      const updated = res.data;
      setActiveProposal(updated);
      setProposals(proposals.map((p) => (p.id === updated.id ? updated : p)));

      const jobRes = await jobsAPI.getJob(job.id);
      setJob(jobRes.data);
      setProposalActionMsg(`Proposal (v${updated.version}) approved! Ready for client outreach.`);
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Failed to approve proposal.');
    }
  };

  const handleRejectProposal = async () => {
    if (!activeProposal) return;
    try {
      const res = await proposalsAPI.rejectProposal(activeProposal.id);
      const updated = res.data;
      setActiveProposal(updated);
      setProposals(proposals.map((p) => (p.id === updated.id ? updated : p)));
      setProposalActionMsg(`Proposal (v${updated.version}) marked as rejected.`);
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Failed to reject proposal.');
    }
  };

  // Phase 5: Outreach handlers
  const handlePrefillFromProposal = () => {
    if (!activeProposal && proposals.length === 0) {
      setOutreachAlert({ text: 'No proposal available yet. Generate a proposal draft first.', type: 'error' });
      return;
    }
    const prop = activeProposal || proposals[0];
    const detected = job?.description?.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
    if (!recipientEmail && detected) {
      setRecipientEmail(detected[0]);
    }
    setOutreachSubject(`Proposal: ${job?.title || 'Project'} — Freelance / Contract`);
    setOutreachBody(prop.cover_letter || prop.content || '');
    setOutreachAlert({ text: `Pre-filled email pitch from proposal v${prop.version}!`, type: 'success' });
  };

  const handleSaveDraft = async () => {
    if (!job) return;
    if (!recipientEmail.trim() || !outreachSubject.trim() || !outreachBody.trim()) {
      setOutreachAlert({ text: 'Please fill in recipient email, subject, and body before saving a draft.', type: 'error' });
      return;
    }
    setSavingDraft(true);
    setOutreachAlert(null);
    try {
      await outreachAPI.createDraft(job.id, {
        recipient_email: recipientEmail.trim(),
        recipient_name: recipientName.trim() || undefined,
        subject: outreachSubject.trim(),
        body: outreachBody.trim(),
        proposal_id: activeProposal?.id,
      });
      const updated = await outreachAPI.getJobOutreach(job.id);
      setOutreachList(updated.data);
      setOutreachAlert({ text: 'Draft saved successfully.', type: 'success' });
    } catch (e: any) {
      setOutreachAlert({ text: e.response?.data?.detail || 'Failed to save draft.', type: 'error' });
    } finally {
      setSavingDraft(false);
    }
  };

  const handleOpenSendConfirm = () => {
    setOutreachAlert(null);
    if (!recipientEmail.trim()) {
      setOutreachAlert({ text: 'Please enter a recipient email address.', type: 'error' });
      return;
    }
    if (!recipientEmail.includes('@') || !recipientEmail.includes('.')) {
      setOutreachAlert({ text: 'Please enter a valid recipient email address.', type: 'error' });
      return;
    }
    if (!outreachSubject.trim()) {
      setOutreachAlert({ text: 'Please enter an email subject line.', type: 'error' });
      return;
    }
    if (!outreachBody.trim()) {
      setOutreachAlert({ text: 'Email body cannot be empty.', type: 'error' });
      return;
    }
    if (!gmailStatus?.connected) {
      setOutreachAlert({
        text: 'Your Gmail account is not connected. Please connect Gmail in Settings before dispatching emails.',
        type: 'error',
      });
      return;
    }
    setShowConfirmModal(true);
  };

  const handleConfirmSend = async () => {
    if (!job) return;
    setSendingOutreach(true);
    setOutreachAlert(null);
    try {
      await outreachAPI.send(job.id, {
        recipient_email: recipientEmail.trim(),
        recipient_name: recipientName.trim() || undefined,
        subject: outreachSubject.trim(),
        body: outreachBody.trim(),
        proposal_id: activeProposal?.id,
        confirm_send: true,
      });
      setShowConfirmModal(false);
      setOutreachAlert({
        text: `Email successfully dispatched via Gmail to ${recipientEmail}! Opportunity status updated to CONTACTED.`,
        type: 'success',
      });
      const [jobRes, outreachRes] = await Promise.all([
        jobsAPI.getJob(job.id),
        outreachAPI.getJobOutreach(job.id),
      ]);
      setJob(jobRes.data);
      setOutreachList(outreachRes.data);
    } catch (e: any) {
      setOutreachAlert({
        text: e.response?.data?.detail || 'Failed to send outreach email.',
        type: 'error',
      });
    } finally {
      setSendingOutreach(false);
    }
  };

  const toggleExpandOutreach = (msgId: number) => {
    setExpandedOutreachId(expandedOutreachId === msgId ? null : msgId);
  };

  // Phase 6: LinkedIn handlers
  const handleGenerateLinkedIn = async () => {
    if (!job) return;
    setGeneratingLinkedIn(true);
    setLiAlert(null);
    try {
      const res = await linkedinAPI.generate(job.id, {
        recipient_name: liRecipientName.trim() || undefined,
        recipient_role: liRecipientRole.trim() || undefined,
        recipient_profile_url: liProfileUrl.trim() || undefined,
        tone: liTone,
        custom_instructions: liCustomInstructions.trim() || undefined,
      });
      const newMsg = res.data;
      setLinkedinMessages([newMsg, ...linkedinMessages]);
      setActiveLinkedInMsg(newMsg);
      setIsEditingLinkedIn(false);
      setShowLiConfig(false);
      setLiAlert({ text: 'LinkedIn outreach kit generated successfully!', type: 'success' });
    } catch (e: any) {
      setLiAlert({ text: e.response?.data?.detail || 'Failed to generate LinkedIn outreach.', type: 'error' });
    } finally {
      setGeneratingLinkedIn(false);
    }
  };

  const handleStartEditLinkedIn = () => {
    if (!activeLinkedInMsg) return;
    setEditLiNote(activeLinkedInMsg.connection_note);
    setEditLiSubject(activeLinkedInMsg.inmail_subject);
    setEditLiBody(activeLinkedInMsg.inmail_body);
    setIsEditingLinkedIn(true);
  };

  const handleSaveEditLinkedIn = async () => {
    if (!activeLinkedInMsg) return;
    if (editLiNote.length > 300) {
      setLiAlert({ text: `Connection note must be 300 characters or fewer (currently ${editLiNote.length}).`, type: 'error' });
      return;
    }
    setSavingLiEdit(true);
    setLiAlert(null);
    try {
      const res = await linkedinAPI.updateMessage(activeLinkedInMsg.id, {
        connection_note: editLiNote.trim(),
        inmail_subject: editLiSubject.trim(),
        inmail_body: editLiBody.trim(),
      });
      const updated = res.data;
      setActiveLinkedInMsg(updated);
      setLinkedinMessages(linkedinMessages.map((m) => (m.id === updated.id ? updated : m)));
      setIsEditingLinkedIn(false);
      setLiAlert({ text: 'LinkedIn message saved successfully.', type: 'success' });
    } catch (e: any) {
      setLiAlert({ text: e.response?.data?.detail || 'Failed to save changes.', type: 'error' });
    } finally {
      setSavingLiEdit(false);
    }
  };

  const handleMarkLinkedInSent = async () => {
    if (!activeLinkedInMsg || !job) return;
    setMarkingLiSent(true);
    setLiAlert(null);
    try {
      const res = await linkedinAPI.markSent(activeLinkedInMsg.id);
      const updated = res.data;
      setActiveLinkedInMsg(updated);
      setLinkedinMessages(linkedinMessages.map((m) => (m.id === updated.id ? updated : m)));

      const jobRes = await jobsAPI.getJob(job.id);
      setJob(jobRes.data);
      setLiAlert({ text: 'Marked as sent on LinkedIn! Opportunity updated to CONTACTED.', type: 'success' });
    } catch (e: any) {
      setLiAlert({ text: e.response?.data?.detail || 'Failed to update outreach status.', type: 'error' });
    } finally {
      setMarkingLiSent(false);
    }
  };

  const handleCopyLiNote = () => {
    if (!activeLinkedInMsg) return;
    navigator.clipboard.writeText(isEditingLinkedIn ? editLiNote : activeLinkedInMsg.connection_note);
    setCopiedLiNote(true);
    setTimeout(() => setCopiedLiNote(false), 2000);
  };

  const handleCopyLiInmail = () => {
    if (!activeLinkedInMsg) return;
    const textToCopy = isEditingLinkedIn
      ? `Subject: ${editLiSubject}\n\n${editLiBody}`
      : `Subject: ${activeLinkedInMsg.inmail_subject}\n\n${activeLinkedInMsg.inmail_body}`;
    navigator.clipboard.writeText(textToCopy);
    setCopiedLiInmail(true);
    setTimeout(() => setCopiedLiInmail(false), 2000);
  };

  const handleCopy = (text: string, type: 'proposal' | 'cover_letter') => {
    navigator.clipboard.writeText(text);
    if (type === 'proposal') {
      setCopiedProposal(true);
      setTimeout(() => setCopiedProposal(false), 2000);
    } else {
      setCopiedCoverLetter(true);
      setTimeout(() => setCopiedCoverLetter(false), 2000);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  const detectedEmail = job?.description?.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/)?.[0];

  if (loading) {
    return <div className="text-center py-12 text-gray-500 font-medium">Loading opportunity details...</div>;
  }

  if (!job) {
    return <div className="text-center py-12 text-gray-500 font-medium">Job opportunity not found</div>;
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <button
            onClick={() => navigate('/dashboard')}
            className="mr-4 p-2 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{job.title}</h2>
            <p className="mt-0.5 text-sm text-gray-500">{job.company || 'Unknown Company'}</p>
          </div>
        </div>

        {/* Status Pill */}
        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold tracking-wide uppercase ${
          job.status === 'NEW' ? 'bg-gray-100 text-gray-800' :
          job.status === 'ANALYZING' ? 'bg-blue-100 text-blue-800' :
          job.status === 'REVIEW_REQUIRED' ? 'bg-yellow-100 text-yellow-800' :
          job.status === 'REJECTED' ? 'bg-red-100 text-red-800' :
          job.status === 'APPROVED' ? 'bg-green-100 text-green-800' :
          job.status === 'PROPOSAL_READY' ? 'bg-purple-100 text-purple-800' :
          job.status === 'PROPOSAL_APPROVED' ? 'bg-emerald-100 text-emerald-800' :
          job.status === 'CONTACTED' ? 'bg-cyan-100 text-cyan-800 border border-cyan-200' :
          'bg-gray-100 text-gray-800'
        }`}>
          {job.status.replace(/_/g, ' ')}
        </span>
      </div>

      {/* Job Details Card */}
      <div className="bg-white shadow-sm border border-gray-200 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Job Details</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium text-gray-500">Source:</span>
            <span className="ml-2 text-gray-900 capitalize">{job.source}</span>
          </div>
          <div>
            <span className="font-medium text-gray-500">Location:</span>
            <span className="ml-2 text-gray-900">{job.location || 'Flexible / Remote'}</span>
          </div>
          <div>
            <span className="font-medium text-gray-500">Job Type:</span>
            <span className="ml-2 text-gray-900 capitalize">{job.job_type || 'Contract'}</span>
          </div>
          <div>
            <span className="font-medium text-gray-500">Compensation:</span>
            <span className="ml-2 text-gray-900 font-medium">
              {job.salary_min && job.salary_max
                ? `${job.currency} ${job.salary_min.toLocaleString()} - ${job.salary_max.toLocaleString()}`
                : job.salary_min
                ? `${job.currency} ${job.salary_min.toLocaleString()}+`
                : 'Not specified'}
            </span>
          </div>
          {job.url && (
            <div className="md:col-span-2">
              <span className="font-medium text-gray-500">Original Link:</span>
              <a
                href={job.url}
                target="_blank"
                rel="noopener noreferrer"
                className="ml-2 text-indigo-600 hover:text-indigo-700 underline break-all"
              >
                {job.url}
              </a>
            </div>
          )}
        </div>

        <div className="mt-4">
          <h4 className="font-medium text-gray-900 mb-1">Description</h4>
          <div className="text-sm text-gray-700 whitespace-pre-wrap bg-gray-50 p-4 rounded-lg border border-gray-100 max-h-60 overflow-y-auto">
            {job.description}
          </div>
        </div>

        {/* Opportunity Decision Actions */}
        <div className="mt-5 pt-4 border-t border-gray-100 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <button
              id="approve-job-btn"
              onClick={handleApprove}
              disabled={approving || rejecting || job.status === 'APPROVED' || job.status === 'PROPOSAL_READY' || job.status === 'PROPOSAL_APPROVED' || job.status === 'CONTACTED'}
              className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition-colors"
            >
              <ThumbsUp className="w-4 h-4" />
              {approving ? 'Approving…' : job.status === 'APPROVED' || job.status === 'PROPOSAL_READY' || job.status === 'PROPOSAL_APPROVED' || job.status === 'CONTACTED' ? 'Approved' : 'Approve Job'}
            </button>
            <button
              id="reject-job-btn"
              onClick={handleReject}
              disabled={approving || rejecting || job.status === 'REJECTED' || job.status === 'CONTACTED'}
              className="inline-flex items-center gap-2 px-4 py-2 bg-red-50 text-red-700 text-sm font-medium rounded-lg hover:bg-red-100 border border-red-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ThumbsDown className="w-4 h-4" />
              {rejecting ? 'Rejecting…' : job.status === 'REJECTED' ? 'Rejected' : 'Reject'}
            </button>
          </div>
          {actionMsg && (
            <p className="text-sm text-gray-600 italic">{actionMsg}</p>
          )}
        </div>
      </div>

      {/* AI Analysis Section */}
      <div className="bg-white shadow-sm border border-gray-200 rounded-xl p-6">
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-indigo-600" />
            <h3 className="text-lg font-semibold text-gray-900">AI Compatibility Analysis</h3>
          </div>
          {!analysis && job.status === 'NEW' && (
            <button
              onClick={handleAnalyze}
              disabled={analyzing}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 shadow-sm"
            >
              <Sparkles className="w-4 h-4" />
              {analyzing ? 'Analyzing with AI...' : 'Analyze Opportunity'}
            </button>
          )}
        </div>

        {analyzing && (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600 mx-auto"></div>
            <p className="mt-3 text-sm text-gray-500">Evaluating against startup profile & portfolio...</p>
          </div>
        )}

        {!analysis && !analyzing && (
          <div className="text-center py-6 text-gray-400 text-sm">
            No analysis yet. Click "Analyze Opportunity" to get AI insights and score breakdowns.
          </div>
        )}

        {analysis && (
          <div className="space-y-6">
            <div className="flex items-center justify-center">
              <div className={`text-center px-8 py-4 rounded-xl ${getScoreBgColor(analysis.match_score)}`}>
                <div className={`text-4xl font-extrabold ${getScoreColor(analysis.match_score)}`}>
                  {analysis.match_score}
                </div>
                <div className="text-xs font-semibold tracking-wider text-gray-600 uppercase mt-1">Match Score</div>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              <div className="border border-gray-100 bg-gray-50/50 rounded-lg p-3 text-center">
                <div className="text-xs text-gray-500">Technical Match</div>
                <div className={`text-xl font-bold ${getScoreColor(analysis.technical_match)}`}>{analysis.technical_match}</div>
              </div>
              <div className="border border-gray-100 bg-gray-50/50 rounded-lg p-3 text-center">
                <div className="text-xs text-gray-500">Service Match</div>
                <div className={`text-xl font-bold ${getScoreColor(analysis.service_match)}`}>{analysis.service_match}</div>
              </div>
              <div className="border border-gray-100 bg-gray-50/50 rounded-lg p-3 text-center">
                <div className="text-xs text-gray-500">Experience Match</div>
                <div className={`text-xl font-bold ${getScoreColor(analysis.experience_match)}`}>{analysis.experience_match}</div>
              </div>
              <div className="border border-gray-100 bg-gray-50/50 rounded-lg p-3 text-center">
                <div className="text-xs text-gray-500">Budget Match</div>
                <div className={`text-xl font-bold ${getScoreColor(analysis.budget_match)}`}>{analysis.budget_match}</div>
              </div>
              <div className="border border-gray-100 bg-gray-50/50 rounded-lg p-3 text-center">
                <div className="text-xs text-gray-500">Location Match</div>
                <div className={`text-xl font-bold ${getScoreColor(analysis.location_match)}`}>{analysis.location_match}</div>
              </div>
              <div className="border border-gray-100 bg-gray-50/50 rounded-lg p-3 text-center">
                <div className="text-xs text-gray-500">Confidence</div>
                <div className="text-xl font-bold text-gray-800">
                  {analysis.confidence ? `${(analysis.confidence * 100).toFixed(0)}%` : 'N/A'}
                </div>
              </div>
            </div>

            {analysis.reasoning && analysis.reasoning.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 mb-2 flex items-center gap-1.5 text-sm">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  Key Match Strengths
                </h4>
                <ul className="list-disc list-inside space-y-1 text-sm text-gray-700 pl-2">
                  {analysis.reasoning.map((reason, idx) => (
                    <li key={idx}>{reason}</li>
                  ))}
                </ul>
              </div>
            )}

            {analysis.risks && analysis.risks.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 mb-2 flex items-center gap-1.5 text-sm">
                  <AlertTriangle className="w-4 h-4 text-amber-500" />
                  Potential Risks or Gaps
                </h4>
                <ul className="list-disc list-inside space-y-1 text-sm text-gray-700 pl-2">
                  {analysis.risks.map((risk, idx) => (
                    <li key={idx}>{risk}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      {/* PHASE 4: AI PROPOSALS & OUTREACH PITCH SECTION */}
      <div className="bg-white shadow-sm border border-gray-200 rounded-xl p-6">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-6 pb-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-indigo-600" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">AI Proposals & Pitch Drafts</h3>
              <p className="text-xs text-gray-500">Customized proposals and pitch messages crafted by AI</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {proposals.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500 font-medium">Version:</span>
                <select
                  value={activeProposal?.id || ''}
                  onChange={(e) => {
                    const sel = proposals.find((p) => p.id === parseInt(e.target.value));
                    if (sel) {
                      setActiveProposal(sel);
                      setIsEditing(false);
                    }
                  }}
                  className="text-xs font-medium border border-gray-200 rounded-lg px-2.5 py-1.5 bg-white text-gray-700 hover:border-gray-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  {proposals.map((p) => (
                    <option key={p.id} value={p.id}>
                      v{p.version} · {p.tone} ({p.status})
                    </option>
                  ))}
                </select>
              </div>
            )}

            <button
              onClick={() => setShowConfig(!showConfig)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-colors border border-indigo-100"
            >
              <Sparkles className="w-3.5 h-3.5" />
              {showConfig ? 'Hide Generator' : proposals.length > 0 ? '+ New Draft / Regenerate' : 'Generate Proposal'}
            </button>
          </div>
        </div>

        {/* Generator Controls Card (Shown when toggled or when no proposals exist) */}
        {showConfig && (
          <div className="bg-indigo-50/40 border border-indigo-100 rounded-xl p-5 mb-6 space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold text-indigo-900 flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-indigo-600" />
                Configure Proposal Generator
              </h4>
              {proposals.length > 0 && (
                <button
                  onClick={() => setShowConfig(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Tone Selector */}
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">
                Pitch Tone & Style
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                {TONES.map((t) => (
                  <button
                    key={t.value}
                    type="button"
                    onClick={() => setProposalTone(t.value)}
                    className={`p-2.5 text-left rounded-lg border text-xs transition-all ${
                      proposalTone === t.value
                        ? 'border-indigo-600 bg-white text-indigo-900 shadow-sm ring-1 ring-indigo-600'
                        : 'border-gray-200 bg-white/70 text-gray-600 hover:bg-white hover:border-gray-300'
                    }`}
                  >
                    <div className="font-semibold">{t.label}</div>
                    <div className="text-[11px] text-gray-400 mt-0.5 leading-tight">{t.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Custom Instructions */}
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1.5">
                Special Instructions or Focus Areas (Optional)
              </label>
              <textarea
                value={customInstructions}
                onChange={(e) => setCustomInstructions(e.target.value)}
                placeholder="e.g., Emphasize our experience with real-time websocket backends and highlight our 48-hour delivery guarantee..."
                rows={2}
                className="w-full text-xs text-gray-800 bg-white border border-gray-200 rounded-lg p-2.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={handleGenerateProposal}
                disabled={generatingProposal}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white text-xs font-semibold rounded-lg hover:bg-indigo-700 disabled:opacity-50 shadow-sm transition-all"
              >
                {generatingProposal ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    Generating with AI...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    Generate Proposal (v{proposals.length + 1})
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Feedback message */}
        {proposalActionMsg && (
          <div className="mb-4 p-3 bg-indigo-50 border border-indigo-200 text-indigo-800 rounded-lg text-xs font-medium flex items-center justify-between">
            <span>{proposalActionMsg}</span>
            <button onClick={() => setProposalActionMsg(null)} className="text-indigo-400 hover:text-indigo-600">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Active Proposal View / Edit */}
        {activeProposal ? (
          <div className="space-y-4">
            {/* Proposal Subheader & Metadata */}
            <div className="flex flex-wrap items-center justify-between gap-3 bg-gray-50 border border-gray-200 rounded-xl p-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h4 className="font-bold text-gray-900 text-base">{activeProposal.title}</h4>
                  <span className="text-xs bg-indigo-100 text-indigo-800 font-semibold px-2 py-0.5 rounded">
                    v{activeProposal.version}
                  </span>
                  <span className="text-xs bg-gray-100 text-gray-700 font-medium px-2 py-0.5 rounded capitalize">
                    {activeProposal.tone}
                  </span>
                  <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${
                    activeProposal.status === 'APPROVED' ? 'bg-green-100 text-green-800' :
                    activeProposal.status === 'REJECTED' ? 'bg-red-100 text-red-800' :
                    'bg-amber-100 text-amber-800'
                  }`}>
                    {activeProposal.status}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-xs text-gray-500">
                  {activeProposal.estimated_duration && (
                    <span><strong>Timeline:</strong> {activeProposal.estimated_duration}</span>
                  )}
                  {activeProposal.estimated_budget && (
                    <span><strong>Budget:</strong> {activeProposal.estimated_budget}</span>
                  )}
                  {activeProposal.created_at && (
                    <span>Created: {new Date(activeProposal.created_at).toLocaleDateString()}</span>
                  )}
                </div>
              </div>

              {/* Proposal Actions */}
              <div className="flex items-center gap-2">
                {!isEditing ? (
                  <>
                    <button
                      onClick={handleStartEdit}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <Edit3 className="w-3.5 h-3.5 text-gray-500" />
                      Edit Draft
                    </button>
                    {activeProposal.status !== 'APPROVED' && (
                      <button
                        onClick={handleApproveProposal}
                        className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 shadow-sm transition-colors"
                      >
                        <Check className="w-3.5 h-3.5" />
                        Approve Proposal
                      </button>
                    )}
                    {activeProposal.status !== 'REJECTED' && (
                      <button
                        onClick={handleRejectProposal}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-red-600 bg-red-50 hover:bg-red-100 border border-red-200 rounded-lg transition-colors"
                      >
                        <X className="w-3.5 h-3.5" />
                        Reject Draft
                      </button>
                    )}
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => setIsEditing(false)}
                      disabled={savingEdit}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSaveEdit}
                      disabled={savingEdit}
                      className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 shadow-sm"
                    >
                      <Save className="w-3.5 h-3.5" />
                      {savingEdit ? 'Saving...' : 'Save Draft'}
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* View Mode: Tab selector */}
            {!isEditing && (
              <div className="border-b border-gray-200 flex items-center justify-between">
                <div className="flex gap-4">
                  <button
                    onClick={() => setActiveTab('proposal')}
                    className={`pb-2.5 text-sm font-semibold border-b-2 transition-colors ${
                      activeTab === 'proposal'
                        ? 'border-indigo-600 text-indigo-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Full Markdown Proposal
                  </button>
                  <button
                    onClick={() => setActiveTab('cover_letter')}
                    className={`pb-2.5 text-sm font-semibold border-b-2 transition-colors ${
                      activeTab === 'cover_letter'
                        ? 'border-indigo-600 text-indigo-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Cover Letter Pitch
                  </button>
                </div>

                <button
                  onClick={() =>
                    handleCopy(
                      activeTab === 'proposal' ? activeProposal.content : activeProposal.cover_letter || '',
                      activeTab
                    )
                  }
                  className="inline-flex items-center gap-1.5 text-xs text-gray-600 hover:text-indigo-600 mb-2 p-1.5 rounded hover:bg-gray-100 transition-colors"
                >
                  {(activeTab === 'proposal' ? copiedProposal : copiedCoverLetter) ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-green-600" />
                      <span className="text-green-600 font-semibold">Copied to Clipboard!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy {activeTab === 'proposal' ? 'Proposal' : 'Pitch'}</span>
                    </>
                  )}
                </button>
              </div>
            )}

            {/* Display Body or Edit Form */}
            {isEditing ? (
              <div className="space-y-4 pt-2">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Proposal Title</label>
                  <input
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Estimated Timeline</label>
                    <input
                      type="text"
                      value={editDuration}
                      onChange={(e) => setEditDuration(e.target.value)}
                      placeholder="e.g. 4-6 weeks"
                      className="w-full text-sm border border-gray-300 rounded-lg p-2.5"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Estimated Budget</label>
                    <input
                      type="text"
                      value={editBudget}
                      onChange={(e) => setEditBudget(e.target.value)}
                      placeholder="e.g. $8,000 - $12,000"
                      className="w-full text-sm border border-gray-300 rounded-lg p-2.5"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Full Proposal (Markdown)</label>
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    rows={12}
                    className="w-full font-mono text-xs border border-gray-300 rounded-lg p-3 leading-relaxed focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Cover Letter / Pitch</label>
                  <textarea
                    value={editCoverLetter}
                    onChange={(e) => setEditCoverLetter(e.target.value)}
                    rows={6}
                    className="w-full text-xs border border-gray-300 rounded-lg p-3 leading-relaxed focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </div>
            ) : (
              <div className="pt-2">
                {activeTab === 'proposal' ? (
                  <div className="bg-gray-50/70 border border-gray-200 rounded-xl p-6 text-sm text-gray-800 whitespace-pre-wrap font-sans leading-relaxed">
                    {activeProposal.content}
                  </div>
                ) : (
                  <div className="bg-gray-50/70 border border-gray-200 rounded-xl p-6 text-sm text-gray-800 whitespace-pre-wrap font-sans leading-relaxed">
                    {activeProposal.cover_letter || 'No cover letter pitch draft generated for this version.'}
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          !showConfig && (
            <div className="text-center py-8 text-gray-400 text-sm">
              No proposal generated yet. Click "Generate Proposal" above to tailor a proposal and outreach pitch for this client.
            </div>
          )
        )}
      </div>

      {/* Phase 5: Email Outreach & Gmail Dispatch Card */}
      <div className="bg-white shadow-sm border border-gray-200 rounded-xl p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-gray-100 gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
              <Mail className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-semibold text-gray-900">Email Outreach & Dispatch</h3>
                <span className="text-[11px] font-semibold bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded border border-indigo-100">
                  Phase 5 · Gmail API
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-0.5">
                Dispatch personalized proposals directly through your connected Gmail account with a human approval gate.
              </p>
            </div>
          </div>

          {/* Gmail Connection Status Pill */}
          <div>
            {gmailStatus?.connected ? (
              <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-green-50 text-green-700 border border-green-200">
                <CheckCircle className="w-3.5 h-3.5 text-green-600" />
                <span>Connected: <strong className="font-semibold">{gmailStatus.gmail_email}</strong></span>
              </div>
            ) : (
              <Link
                to="/gmail"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200 hover:bg-amber-100 transition-colors shadow-sm"
              >
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                <span>Connect Gmail to Dispatch</span>
                <ExternalLink className="w-3 h-3 text-amber-600" />
              </Link>
            )}
          </div>
        </div>

        {/* Opportunity Contacted Banner */}
        {job.status === 'CONTACTED' && (
          <div className="mt-4 p-3.5 bg-cyan-50 border border-cyan-200 rounded-lg flex items-center justify-between">
            <div className="flex items-center gap-2 text-cyan-800 text-xs font-medium">
              <CheckCircle className="w-4 h-4 text-cyan-600 shrink-0" />
              <span>
                <strong>Opportunity Contacted:</strong> You have reached out to this client! View dispatched history below or send a follow-up.
              </span>
            </div>
          </div>
        )}

        {/* Alert Feedback Message */}
        {outreachAlert && (
          <div className={`mt-4 p-3 rounded-lg text-xs font-medium border flex items-center justify-between ${
            outreachAlert.type === 'success'
              ? 'bg-green-50 border-green-200 text-green-800'
              : 'bg-red-50 border-red-200 text-red-800'
          }`}>
            <span>{outreachAlert.text}</span>
            <button
              onClick={() => setOutreachAlert(null)}
              className="text-gray-400 hover:text-gray-600 p-0.5 ml-2"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Outreach History Section (if any messages exist) */}
        {outreachList.length > 0 && (
          <div className="mt-5 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-gray-700 uppercase tracking-wider">
              <History className="w-3.5 h-3.5 text-gray-400" />
              <span>Outreach History ({outreachList.length})</span>
            </div>

            <div className="space-y-2">
              {outreachList.map((msg) => (
                <div
                  key={msg.id}
                  className="border border-gray-200 rounded-lg p-3 bg-gray-50/50 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                        msg.status === 'SENT' ? 'bg-green-100 text-green-800' :
                        msg.status === 'FAILED' ? 'bg-red-100 text-red-800' :
                        'bg-amber-100 text-amber-800'
                      }`}>
                        {msg.status}
                      </span>
                      <span className="text-xs font-semibold text-gray-900">
                        To: {msg.recipient_email}
                      </span>
                      {msg.recipient_name && (
                        <span className="text-xs text-gray-500">
                          ({msg.recipient_name})
                        </span>
                      )}
                      <span className="text-xs text-gray-400">·</span>
                      <span className="text-xs text-gray-500 truncate max-w-xs font-medium">
                        "{msg.subject}"
                      </span>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className="text-xs text-gray-400">
                        {msg.sent_at
                          ? new Date(msg.sent_at).toLocaleString()
                          : new Date(msg.created_at).toLocaleString()}
                      </span>
                      <button
                        onClick={() => toggleExpandOutreach(msg.id)}
                        className="text-xs text-indigo-600 hover:text-indigo-800 font-medium inline-flex items-center gap-0.5"
                      >
                        {expandedOutreachId === msg.id ? (
                          <>Hide <ChevronUp className="w-3.5 h-3.5" /></>
                        ) : (
                          <>View <ChevronDown className="w-3.5 h-3.5" /></>
                        )}
                      </button>
                    </div>
                  </div>

                  {expandedOutreachId === msg.id && (
                    <div className="mt-3 pt-3 border-t border-gray-200 space-y-2">
                      <div className="flex items-center gap-3 text-xs text-gray-500">
                        {msg.gmail_message_id && (
                          <span>
                            <strong>Gmail Message ID:</strong>{' '}
                            <code className="bg-gray-200 px-1 py-0.5 rounded font-mono text-[11px]">
                              {msg.gmail_message_id}
                            </code>
                          </span>
                        )}
                        {msg.gmail_thread_id && (
                          <span>
                            <strong>Thread:</strong>{' '}
                            <code className="bg-gray-200 px-1 py-0.5 rounded font-mono text-[11px]">
                              {msg.gmail_thread_id}
                            </code>
                          </span>
                        )}
                      </div>
                      <div className="bg-white border border-gray-200 rounded p-3 text-xs font-sans whitespace-pre-wrap text-gray-800 leading-relaxed">
                        {msg.body}
                      </div>
                      {msg.error_message && (
                        <p className="text-xs text-red-600 font-medium">
                          Error: {msg.error_message}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Email Composer Form */}
        <div className="mt-6 pt-5 border-t border-gray-100 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <h4 className="text-sm font-bold text-gray-900 flex items-center gap-1.5">
              <span>Compose Outreach Email</span>
            </h4>

            {/* Pre-fill CTA */}
            {(activeProposal || proposals.length > 0) && (
              <button
                type="button"
                onClick={handlePrefillFromProposal}
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 bg-indigo-50 hover:bg-indigo-100 px-3 py-1.5 rounded-lg border border-indigo-100 transition-colors shadow-xs"
              >
                <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                Pre-fill from Active Proposal Pitch
              </button>
            )}
          </div>

          {/* Form Fields */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-semibold text-gray-700">
                  Recipient Email <span className="text-red-500">*</span>
                </label>
                {detectedEmail && recipientEmail !== detectedEmail && (
                  <button
                    type="button"
                    onClick={() => setRecipientEmail(detectedEmail)}
                    className="text-[11px] text-indigo-600 hover:text-indigo-800 font-medium underline"
                  >
                    Use detected: {detectedEmail}
                  </button>
                )}
              </div>
              <input
                id="outreach-to-email"
                type="email"
                value={recipientEmail}
                onChange={(e) => setRecipientEmail(e.target.value)}
                placeholder="client@company.com"
                className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Recipient Name <span className="text-gray-400 font-normal">(optional)</span>
              </label>
              <input
                id="outreach-to-name"
                type="text"
                value={recipientName}
                onChange={(e) => setRecipientName(e.target.value)}
                placeholder="e.g. Sarah Connor / Hiring Lead"
                className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Subject Line <span className="text-red-500">*</span>
            </label>
            <input
              id="outreach-subject"
              type="text"
              value={outreachSubject}
              onChange={(e) => setOutreachSubject(e.target.value)}
              placeholder="e.g. Full-Stack Developer Proposal for your Project"
              className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Email Pitch & Message Body <span className="text-red-500">*</span>
            </label>
            <textarea
              id="outreach-body"
              value={outreachBody}
              onChange={(e) => setOutreachBody(e.target.value)}
              rows={8}
              placeholder="Hi [Name], I came across your job post and would love to propose my services..."
              className="w-full text-xs font-sans border border-gray-300 rounded-lg p-3 leading-relaxed focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
            />
          </div>

          {/* Composer Actions */}
          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              id="save-draft-btn"
              onClick={handleSaveDraft}
              disabled={savingDraft || sendingOutreach}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Save className="w-3.5 h-3.5 text-gray-500" />
              {savingDraft ? 'Saving Draft…' : 'Save Draft'}
            </button>

            <button
              type="button"
              id="send-outreach-btn"
              onClick={handleOpenSendConfirm}
              disabled={sendingOutreach || savingDraft}
              className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-md"
            >
              <Send className="w-4 h-4" />
              <span>Review & Send via Gmail</span>
            </button>
          </div>
        </div>
      </div>

      {/* Phase 5: Human-in-the-Loop Confirmation Modal */}
      {showConfirmModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs flex items-center justify-center z-50 p-4 animate-in fade-in">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-gray-100 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-gray-100">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                  <Send className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-gray-900">Confirm Email Dispatch</h3>
              </div>
              <button
                onClick={() => setShowConfirmModal(false)}
                disabled={sendingOutreach}
                className="text-gray-400 hover:text-gray-600 p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-gray-600 leading-relaxed">
              You are about to dispatch an actual email through your connected Google Workspace account. Please review the recipient and preview below:
            </p>

            {/* Dispatch details card */}
            <div className="bg-gray-50 rounded-xl p-4 space-y-2.5 text-xs border border-gray-200">
              <div>
                <span className="font-semibold text-gray-500">From:</span>
                <span className="ml-2 font-medium text-gray-900">{gmailStatus?.gmail_email || 'Connected Gmail'}</span>
              </div>
              <div>
                <span className="font-semibold text-gray-500">To:</span>
                <span className="ml-2 font-medium text-gray-900">
                  {recipientEmail} {recipientName ? `(${recipientName})` : ''}
                </span>
              </div>
              <div>
                <span className="font-semibold text-gray-500">Subject:</span>
                <span className="ml-2 font-semibold text-indigo-700">{outreachSubject}</span>
              </div>
              <div>
                <span className="font-semibold text-gray-500 block mb-1">Message Preview:</span>
                <div className="bg-white border border-gray-200 rounded p-2.5 max-h-36 overflow-y-auto whitespace-pre-wrap text-[11px] text-gray-700 leading-relaxed font-sans">
                  {outreachBody}
                </div>
              </div>
            </div>

            {/* Human Gate Warning */}
            <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg text-[11px] text-amber-800 leading-normal">
              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <span>
                <strong>Human Gate:</strong> Once sent, this message cannot be recalled. Job status will automatically transition to <strong>CONTACTED</strong>.
              </span>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowConfirmModal(false)}
                disabled={sendingOutreach}
                className="px-4 py-2 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                id="confirm-send-email-btn"
                onClick={handleConfirmSend}
                disabled={sendingOutreach}
                className="inline-flex items-center gap-1.5 px-5 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition-all disabled:opacity-50 hover:shadow-md"
              >
                {sendingOutreach ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Dispatching…</span>
                  </>
                ) : (
                  <>
                    <Send className="w-3.5 h-3.5" />
                    <span>Confirm & Send via Gmail</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Phase 6: LinkedIn Outreach Kit Card */}
      <div className="bg-white shadow-sm border border-gray-200 rounded-xl p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-gray-100 gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[#0077b5]/10 text-[#0077b5] rounded-lg">
              <Linkedin className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-semibold text-gray-900">LinkedIn Outreach Kit</h3>
                <span className="text-[11px] font-semibold bg-sky-50 text-sky-700 px-2 py-0.5 rounded border border-sky-100">
                  Phase 6 · InMail & Connection Note
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-0.5">
                Generate tailored InMail pitches and connection request notes strictly constrained to LinkedIn's 300-character limit.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {linkedinMessages.length > 0 && (
              <button
                type="button"
                onClick={() => setShowLiConfig(!showLiConfig)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors shadow-xs"
              >
                <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                <span>{showLiConfig ? 'Hide Generator' : 'New LinkedIn Pitch'}</span>
              </button>
            )}
          </div>
        </div>

        {/* Feedback Alert */}
        {liAlert && (
          <div className={`mt-4 p-3 rounded-lg text-xs font-medium border flex items-center justify-between ${
            liAlert.type === 'success'
              ? 'bg-green-50 border-green-200 text-green-800'
              : 'bg-red-50 border-red-200 text-red-800'
          }`}>
            <span>{liAlert.text}</span>
            <button
              onClick={() => setLiAlert(null)}
              className="text-gray-400 hover:text-gray-600 p-0.5 ml-2"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* LinkedIn Generation Form */}
        {showLiConfig && (
          <div className="mt-5 p-5 bg-sky-50/40 border border-sky-100 rounded-xl space-y-4">
            <h4 className="text-xs font-bold text-gray-900 uppercase tracking-wider flex items-center gap-1.5">
              <UserPlus className="w-3.5 h-3.5 text-[#0077b5]" />
              <span>Target Decision Maker & Tone Settings</span>
            </h4>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Target Contact Name</label>
                <input
                  type="text"
                  value={liRecipientName}
                  onChange={(e) => setLiRecipientName(e.target.value)}
                  placeholder="e.g. Sarah Connor"
                  className="w-full text-xs border border-gray-300 rounded-lg p-2.5 focus:ring-1 focus:ring-sky-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Target Role / Title</label>
                <input
                  type="text"
                  value={liRecipientRole}
                  onChange={(e) => setLiRecipientRole(e.target.value)}
                  placeholder="e.g. Head of Engineering / Founder"
                  className="w-full text-xs border border-gray-300 rounded-lg p-2.5 focus:ring-1 focus:ring-sky-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">LinkedIn Profile URL</label>
                <input
                  type="url"
                  value={liProfileUrl}
                  onChange={(e) => setLiProfileUrl(e.target.value)}
                  placeholder="https://linkedin.com/in/username"
                  className="w-full text-xs border border-gray-300 rounded-lg p-2.5 focus:ring-1 focus:ring-sky-500"
                />
              </div>
            </div>

            {/* Tone Selector */}
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1.5">Outreach Tone</label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {LINKEDIN_TONES.map((t) => (
                  <button
                    key={t.value}
                    type="button"
                    onClick={() => setLiTone(t.value)}
                    className={`p-2.5 rounded-lg border text-left transition-all ${
                      liTone === t.value
                        ? 'bg-white border-[#0077b5] ring-2 ring-[#0077b5]/20 shadow-xs'
                        : 'bg-white/70 border-gray-200 hover:bg-white'
                    }`}
                  >
                    <div className="text-xs font-bold text-gray-900">{t.label}</div>
                    <div className="text-[11px] text-gray-500 mt-0.5 leading-tight">{t.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Custom Instructions (optional)</label>
              <input
                type="text"
                value={liCustomInstructions}
                onChange={(e) => setLiCustomInstructions(e.target.value)}
                placeholder="e.g. Emphasize our experience scaling React pipelines; keep it under 250 chars"
                className="w-full text-xs border border-gray-300 rounded-lg p-2.5 focus:ring-1 focus:ring-sky-500"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-1">
              {linkedinMessages.length > 0 && (
                <button
                  type="button"
                  onClick={() => setShowLiConfig(false)}
                  className="px-3 py-1.5 text-xs text-gray-600 hover:text-gray-900"
                >
                  Cancel
                </button>
              )}
              <button
                type="button"
                id="generate-linkedin-btn"
                onClick={handleGenerateLinkedIn}
                disabled={generatingLinkedIn}
                className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-[#0077b5] hover:bg-[#006097] rounded-lg shadow-sm transition-all disabled:opacity-50"
              >
                {generatingLinkedIn ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Generating Outreach Kit…</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Generate LinkedIn Kit</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Active LinkedIn Message Display */}
        {activeLinkedInMsg ? (
          <div className="mt-6 space-y-5">
            {/* Version / Draft Switcher */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-gray-100 gap-3">
              <div className="flex items-center gap-3 flex-wrap">
                {linkedinMessages.length > 1 && (
                  <select
                    value={activeLinkedInMsg.id}
                    onChange={(e) => {
                      const found = linkedinMessages.find((m) => m.id === parseInt(e.target.value));
                      if (found) {
                        setActiveLinkedInMsg(found);
                        setIsEditingLinkedIn(false);
                      }
                    }}
                    className="text-xs font-semibold border border-gray-300 rounded-lg py-1.5 px-2.5 bg-white shadow-xs focus:ring-1 focus:ring-sky-500"
                  >
                    {linkedinMessages.map((m, idx) => (
                      <option key={m.id} value={m.id}>
                        Kit #{linkedinMessages.length - idx} · {m.recipient_name || 'Contact'} ({m.tone})
                      </option>
                    ))}
                  </select>
                )}

                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-gray-900">
                    Target: {activeLinkedInMsg.recipient_name || 'Hiring Lead'}
                  </span>
                  {activeLinkedInMsg.recipient_role && (
                    <span className="text-xs text-gray-500">· {activeLinkedInMsg.recipient_role}</span>
                  )}
                  <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                    activeLinkedInMsg.status === 'SENT' ? 'bg-green-100 text-green-800' : 'bg-sky-100 text-sky-800'
                  }`}>
                    {activeLinkedInMsg.status}
                  </span>
                </div>

                {activeLinkedInMsg.recipient_profile_url && (
                  <a
                    href={activeLinkedInMsg.recipient_profile_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-[#0077b5] hover:underline font-medium"
                  >
                    <span>Open LinkedIn Profile</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2">
                {!isEditingLinkedIn ? (
                  <>
                    <button
                      type="button"
                      onClick={handleStartEditLinkedIn}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <Edit3 className="w-3.5 h-3.5 text-gray-500" />
                      <span>Edit Kit</span>
                    </button>
                    {activeLinkedInMsg.status !== 'SENT' && (
                      <button
                        type="button"
                        id="mark-li-sent-btn"
                        onClick={handleMarkLinkedInSent}
                        disabled={markingLiSent}
                        className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-green-600 hover:bg-green-700 rounded-lg shadow-sm transition-colors"
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>{markingLiSent ? 'Updating…' : 'Mark as Sent on LinkedIn'}</span>
                      </button>
                    )}
                  </>
                ) : (
                  <>
                    <button
                      type="button"
                      onClick={() => setIsEditingLinkedIn(false)}
                      disabled={savingLiEdit}
                      className="px-3 py-1.5 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={handleSaveEditLinkedIn}
                      disabled={savingLiEdit}
                      className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-[#0077b5] hover:bg-[#006097] rounded-lg shadow-sm"
                    >
                      <Save className="w-3.5 h-3.5" />
                      <span>{savingLiEdit ? 'Saving…' : 'Save Changes'}</span>
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Part 1: Connection Request Note */}
            <div className="bg-gradient-to-r from-sky-50/50 to-blue-50/30 border border-sky-100 rounded-xl p-4 space-y-2.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <UserPlus className="w-4 h-4 text-[#0077b5]" />
                  <span className="text-xs font-bold text-gray-900">1. LinkedIn Connection Request Note</span>
                  {/* Character Counter Badge */}
                  {(() => {
                    const len = isEditingLinkedIn ? editLiNote.length : activeLinkedInMsg.connection_note.length;
                    const badgeClass =
                      len <= 280
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        : len <= 300
                        ? 'bg-amber-50 text-amber-700 border-amber-200'
                        : 'bg-red-50 text-red-700 border-red-200';
                    return (
                      <span className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded border ${badgeClass}`}>
                        {len} / 300 chars
                      </span>
                    );
                  })()}
                </div>

                {!isEditingLinkedIn && (
                  <button
                    type="button"
                    onClick={handleCopyLiNote}
                    className="inline-flex items-center gap-1.5 text-xs text-[#0077b5] hover:text-[#006097] font-semibold bg-white border border-sky-200 px-2.5 py-1 rounded-lg shadow-xs hover:bg-sky-50 transition-colors"
                  >
                    {copiedLiNote ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-green-600" />
                        <span className="text-green-600">Copied!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        <span>Copy Note</span>
                      </>
                    )}
                  </button>
                )}
              </div>

              {isEditingLinkedIn ? (
                <div>
                  <textarea
                    value={editLiNote}
                    onChange={(e) => setEditLiNote(e.target.value)}
                    rows={3}
                    className="w-full text-xs border border-gray-300 rounded-lg p-2.5 leading-relaxed focus:ring-1 focus:ring-sky-500 font-sans"
                  />
                  <div className="text-[11px] text-gray-500 mt-1">
                    Free LinkedIn connection notes are hard-capped at 300 characters.
                  </div>
                </div>
              ) : (
                <div className="bg-white border border-gray-200 rounded-lg p-3 text-xs text-gray-800 leading-relaxed font-sans shadow-xs whitespace-pre-wrap">
                  {activeLinkedInMsg.connection_note}
                </div>
              )}
            </div>

            {/* Part 2: InMail / DM Pitch */}
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 space-y-2.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-indigo-600" />
                  <span className="text-xs font-bold text-gray-900">2. InMail / Direct Message Pitch</span>
                </div>

                {!isEditingLinkedIn && (
                  <button
                    type="button"
                    onClick={handleCopyLiInmail}
                    className="inline-flex items-center gap-1.5 text-xs text-indigo-600 hover:text-indigo-800 font-semibold bg-white border border-indigo-200 px-2.5 py-1 rounded-lg shadow-xs hover:bg-indigo-50 transition-colors"
                  >
                    {copiedLiInmail ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-green-600" />
                        <span className="text-green-600">Copied InMail!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        <span>Copy Full Pitch</span>
                      </>
                    )}
                  </button>
                )}
              </div>

              {isEditingLinkedIn ? (
                <div className="space-y-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-gray-600 mb-1">Subject Line</label>
                    <input
                      type="text"
                      value={editLiSubject}
                      onChange={(e) => setEditLiSubject(e.target.value)}
                      className="w-full text-xs border border-gray-300 rounded-lg p-2 focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-semibold text-gray-600 mb-1">Message Body</label>
                    <textarea
                      value={editLiBody}
                      onChange={(e) => setEditLiBody(e.target.value)}
                      rows={6}
                      className="w-full text-xs border border-gray-300 rounded-lg p-2.5 leading-relaxed focus:ring-1 focus:ring-indigo-500 font-sans"
                    />
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-indigo-900 bg-indigo-50/70 border border-indigo-100 px-3 py-1.5 rounded-lg">
                    Subject: {activeLinkedInMsg.inmail_subject}
                  </div>
                  <div className="bg-white border border-gray-200 rounded-lg p-3.5 text-xs text-gray-800 leading-relaxed font-sans shadow-xs whitespace-pre-wrap">
                    {activeLinkedInMsg.inmail_body}
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          !showLiConfig && (
            <div className="text-center py-8 text-gray-400 text-sm">
              No LinkedIn outreach kit generated yet. Click "New LinkedIn Pitch" above to tailor a connection note and InMail.
            </div>
          )
        )}
      </div>
    </div>
  );
};

export default JobDetail;
