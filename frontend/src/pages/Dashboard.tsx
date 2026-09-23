import { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { jobsAPI, gmailAPI } from '../services/api';
import { Job, GmailStatus } from '../types';
import { Briefcase, TrendingUp, AlertCircle, Clock, Mail, RefreshCw, FileText, Send } from 'lucide-react';


const Dashboard = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [gmailStatus, setGmailStatus] = useState<GmailStatus | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState<string | null>(null);
  const navigate = useNavigate();

  const loadJobs = useCallback(async () => {
    try {
      const response = await jobsAPI.getJobs();
      setJobs(response.data);
    } catch (error) {
      console.error('Failed to load jobs:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadJobs();
    // Quietly check Gmail connection status for the quick-sync button
    gmailAPI.getStatus().then(res => setGmailStatus(res.data)).catch(() => null);
  }, [loadJobs]);

  const handleQuickSync = async () => {
    setSyncing(true);
    setSyncMsg(null);
    try {
      const res = await gmailAPI.sync();
      setSyncMsg(res.data.message);
      if (res.data.new_jobs > 0) await loadJobs();
    } catch (e: any) {
      setSyncMsg(e.response?.data?.detail || 'Sync failed.');
    } finally {
      setSyncing(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'NEW':               return 'bg-gray-100 text-gray-800';
      case 'ANALYZING':         return 'bg-blue-100 text-blue-800';
      case 'REVIEW_REQUIRED':   return 'bg-yellow-100 text-yellow-800';
      case 'REJECTED':          return 'bg-red-100 text-red-800';
      case 'APPROVED':          return 'bg-green-100 text-green-800';
      case 'PROPOSAL_READY':    return 'bg-purple-100 text-purple-800';
      case 'PROPOSAL_APPROVED': return 'bg-emerald-100 text-emerald-800';
      case 'OUTREACH_PENDING':  return 'bg-amber-100 text-amber-800';
      case 'CONTACTED':         return 'bg-teal-100 text-teal-800 border border-teal-200';
      case 'CLOSED':            return 'bg-gray-200 text-gray-700';
      default:                  return 'bg-gray-100 text-gray-800';
    }
  };

  const getSourceBadge = (source: string) => {
    if (source === 'gmail') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-50 text-red-700 border border-red-100">
          <Mail className="w-3 h-3" /> Gmail
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
        Manual
      </span>
    );
  };

  const stats = {
    total: jobs.length,
    new: jobs.filter(j => j.status === 'NEW').length,
    highMatch: jobs.filter(j => j.status === 'REVIEW_REQUIRED' || j.status === 'APPROVED' || j.status === 'PROPOSAL_READY' || j.status === 'PROPOSAL_APPROVED' || j.status === 'CONTACTED').length,
    reviewRequired: jobs.filter(j => j.status === 'REVIEW_REQUIRED').length,
    proposalsReady: jobs.filter(j => j.status === 'PROPOSAL_READY' || j.status === 'PROPOSAL_APPROVED').length,
    contacted: jobs.filter(j => j.status === 'CONTACTED').length,
  };



  if (loading) {
    return <div className="text-center py-12">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
          <p className="mt-1 text-sm text-gray-500">Overview of your job opportunities</p>
        </div>
        {/* Quick Gmail sync button — only shown when Gmail is connected */}
        {gmailStatus?.connected && (
          <div className="flex flex-col items-end gap-1">
            <button
              id="dashboard-sync-btn"
              onClick={handleQuickSync}
              disabled={syncing}
              className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg border border-indigo-100 disabled:opacity-50 transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
              {syncing ? 'Syncing Gmail…' : 'Sync Gmail'}
            </button>
            {syncMsg && (
              <p className="text-xs text-gray-500 max-w-xs text-right">{syncMsg}</p>
            )}
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-6">
        <div className="bg-white overflow-hidden shadow-sm border border-gray-100 rounded-lg">
          <div className="p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Briefcase className="h-5 w-5 text-gray-400" />
              </div>
              <div className="ml-4 w-0 flex-1">
                <dl>
                  <dt className="text-xs font-medium text-gray-500 truncate">Total</dt>
                  <dd className="text-lg font-bold text-gray-900">{stats.total}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow-sm border border-gray-100 rounded-lg">
          <div className="p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Clock className="h-5 w-5 text-gray-400" />
              </div>
              <div className="ml-4 w-0 flex-1">
                <dl>
                  <dt className="text-xs font-medium text-gray-500 truncate">New</dt>
                  <dd className="text-lg font-bold text-gray-900">{stats.new}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow-sm border border-gray-100 rounded-lg">
          <div className="p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <TrendingUp className="h-5 w-5 text-gray-400" />
              </div>
              <div className="ml-4 w-0 flex-1">
                <dl>
                  <dt className="text-xs font-medium text-gray-500 truncate">High Match</dt>
                  <dd className="text-lg font-bold text-gray-900">{stats.highMatch}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow-sm border border-gray-100 rounded-lg">
          <div className="p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <AlertCircle className="h-5 w-5 text-yellow-500" />
              </div>
              <div className="ml-4 w-0 flex-1">
                <dl>
                  <dt className="text-xs font-medium text-gray-500 truncate">Review Needed</dt>
                  <dd className="text-lg font-bold text-gray-900">{stats.reviewRequired}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow-sm border border-gray-100 rounded-lg">
          <div className="p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <FileText className="h-5 w-5 text-indigo-500" />
              </div>
              <div className="ml-4 w-0 flex-1">
                <dl>
                  <dt className="text-xs font-medium text-gray-500 truncate">Proposals</dt>
                  <dd className="text-lg font-bold text-indigo-600">{stats.proposalsReady}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow-sm border border-gray-100 rounded-lg">
          <div className="p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Send className="h-5 w-5 text-teal-500" />
              </div>
              <div className="ml-4 w-0 flex-1">
                <dl>
                  <dt className="text-xs font-medium text-gray-500 truncate">Contacted</dt>
                  <dd className="text-lg font-bold text-teal-600">{stats.contacted}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>


      {/* Recent Jobs */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Recent Opportunities</h3>

          {jobs.length === 0 ? (
            <div className="text-center py-8 text-gray-500 space-y-2">
              <p>No opportunities yet.</p>
              <div className="flex justify-center gap-3 text-sm">
                <Link to="/jobs/new" className="text-indigo-600 hover:text-indigo-500">Add manually</Link>
                <span className="text-gray-300">|</span>
                <Link to="/gmail" className="text-indigo-600 hover:text-indigo-500">Connect Gmail</Link>
              </div>
            </div>
          ) : (
            <div className="overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Company</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Source</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Location</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {jobs.map((job) => (
                    <tr
                      key={job.id}
                      className="hover:bg-gray-50 cursor-pointer"
                      onClick={() => navigate(`/jobs/${job.id}`)}
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{job.title}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500">{job.company || 'N/A'}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getSourceBadge(job.source)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500">{job.location || 'Remote'}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(job.status)}`}>
                          {job.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(job.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
