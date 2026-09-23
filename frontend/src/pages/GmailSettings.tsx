import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Mail, CheckCircle, XCircle, RefreshCw, Unlink, AlertCircle, Info, ExternalLink } from 'lucide-react';
import { gmailAPI } from '../services/api';
import type { GmailStatus, GmailSyncResult } from '../types';

const GmailSettings = () => {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState<GmailStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [syncResult, setSyncResult] = useState<GmailSyncResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await gmailAPI.getStatus();
      setStatus(res.data);
    } catch (e: any) {
      setError('Failed to load Gmail status.');
    } finally {
      setLoading(false);
    }
  }, []);

  // Handle OAuth callback params (?connected=true or ?error=...)
  useEffect(() => {
    const connected = searchParams.get('connected');
    const oauthError = searchParams.get('error');
    if (connected === 'true') {
      setSuccessMsg('Gmail connected successfully! You can now sync job-alert emails.');
    } else if (oauthError) {
      const messages: Record<string, string> = {
        access_denied: 'You denied Gmail access. No data was connected.',
        not_configured: 'Gmail integration is not configured on the server.',
        token_exchange_failed: 'Failed to complete the Gmail connection. Please try again.',
        invalid_state: 'Invalid OAuth state. Please try connecting again.',
      };
      setError(messages[oauthError] || `Connection failed: ${oauthError}`);
    }
    fetchStatus();
  }, [fetchStatus, searchParams]);

  const handleConnect = async () => {
    setConnecting(true);
    setError(null);
    try {
      const res = await gmailAPI.getAuthUrl();
      // Redirect to Google consent page
      window.location.href = res.data.auth_url;
    } catch (e: any) {
      const msg = e.response?.data?.detail || 'Failed to start Gmail connection.';
      setError(msg);
      setConnecting(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    setError(null);
    setSyncResult(null);
    try {
      const res = await gmailAPI.sync();
      setSyncResult(res.data);
      // Refresh status to update last_sync_at
      await fetchStatus();
    } catch (e: any) {
      const msg = e.response?.data?.detail || 'Sync failed. Please try again.';
      setError(msg);
    } finally {
      setSyncing(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm('Are you sure you want to disconnect Gmail? This will remove your stored tokens.')) return;
    setDisconnecting(true);
    setError(null);
    try {
      await gmailAPI.disconnect();
      setStatus({ connected: false });
      setSyncResult(null);
      setSuccessMsg('Gmail disconnected.');
    } catch (e: any) {
      setError('Failed to disconnect Gmail.');
    } finally {
      setDisconnecting(false);
    }
  };

  const formatDate = (iso?: string | null) => {
    if (!iso) return 'Never';
    return new Date(iso).toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <RefreshCw className="w-6 h-6 animate-spin text-indigo-500" />
        <span className="ml-2 text-gray-500">Loading Gmail status…</span>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Gmail Integration</h1>
        <p className="mt-1 text-sm text-gray-500">
          Connect your Gmail account to automatically ingest job opportunities from labelled emails.
        </p>
      </div>

      {/* Alert: success */}
      {successMsg && (
        <div className="flex items-start gap-3 bg-green-50 border border-green-200 rounded-lg p-4">
          <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-green-800">{successMsg}</p>
        </div>
      )}

      {/* Alert: error */}
      {error && (
        <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-lg p-4">
          <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Connection Card */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-6 py-5 flex items-center justify-between border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${status?.connected ? 'bg-green-50' : 'bg-gray-100'}`}>
              <Mail className={`w-5 h-5 ${status?.connected ? 'text-green-600' : 'text-gray-400'}`} />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-gray-900">Gmail Account</h2>
              {status?.connected ? (
                <p className="text-xs text-green-600 font-medium">Connected · {status.gmail_email}</p>
              ) : (
                <p className="text-xs text-gray-400">Not connected</p>
              )}
            </div>
          </div>
          {status?.connected ? (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
              <CheckCircle className="w-3 h-3" /> Connected
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
              <XCircle className="w-3 h-3" /> Disconnected
            </span>
          )}
        </div>

        <div className="px-6 py-5 space-y-4">
          {status?.connected ? (
            <>
              {/* Last sync info */}
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">Last synced</span>
                <span className="font-medium text-gray-800">{formatDate(status.last_sync_at)}</span>
              </div>
              <div className="flex gap-3 pt-1">
                <button
                  id="sync-gmail-btn"
                  onClick={handleSync}
                  disabled={syncing}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
                  {syncing ? 'Syncing…' : 'Sync Now'}
                </button>
                <button
                  id="disconnect-gmail-btn"
                  onClick={handleDisconnect}
                  disabled={disconnecting}
                  className="flex items-center gap-2 px-4 py-2.5 border border-red-200 text-red-600 text-sm font-medium rounded-lg hover:bg-red-50 disabled:opacity-50 transition-colors"
                >
                  <Unlink className="w-4 h-4" />
                  {disconnecting ? 'Disconnecting…' : 'Disconnect'}
                </button>
              </div>
            </>
          ) : (
            <button
              id="connect-gmail-btn"
              onClick={handleConnect}
              disabled={connecting}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Mail className="w-4 h-4" />
              {connecting ? 'Redirecting to Google…' : 'Connect Gmail'}
            </button>
          )}
        </div>
      </div>

      {/* Sync Result Card */}
      {syncResult && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-4">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-500" />
            <h3 className="font-semibold text-gray-900">Sync Complete</h3>
          </div>
          <p className="text-sm text-gray-600">{syncResult.message}</p>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              { label: 'New Jobs', value: syncResult.new_jobs, color: 'green' },
              { label: 'Duplicates', value: syncResult.duplicates_skipped, color: 'yellow' },
              { label: 'Non-Job', value: syncResult.not_job_emails, color: 'gray' },
              { label: 'Errors', value: syncResult.errors, color: 'red' },
            ].map(({ label, value, color }) => (
              <div key={label} className={`bg-${color}-50 rounded-lg p-3 text-center`}>
                <p className={`text-2xl font-bold text-${color}-700`}>{value}</p>
                <p className="text-xs text-gray-500 mt-0.5">{label}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* How it works */}
      <div className="bg-blue-50 rounded-xl border border-blue-100 p-5 space-y-3">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-blue-500 flex-shrink-0" />
          <h3 className="text-sm font-semibold text-blue-800">How it works</h3>
        </div>
        <ol className="text-sm text-blue-700 space-y-2 list-decimal list-inside">
          <li>Connect your Gmail account using the button above.</li>
          <li>
            In Gmail, create a label called{' '}
            <code className="bg-blue-100 px-1 rounded font-mono text-xs">Job Alerts</code>{' '}
            and apply it to job-alert emails from LinkedIn, Indeed, etc.
          </li>
          <li>
            Click <strong>Sync Now</strong> — Outreach IQ will read those emails, extract job details with AI, and add
            them to your dashboard automatically.
          </li>
          <li>
            Processed emails get tagged{' '}
            <code className="bg-blue-100 px-1 rounded font-mono text-xs">OutreachIQ/Processed</code>{' '}
            in Gmail so they are never ingested twice.
          </li>
        </ol>
        <a
          href="https://support.google.com/mail/answer/118708"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline"
        >
          How to create Gmail labels <ExternalLink className="w-3 h-3" />
        </a>
      </div>

      {/* Setup warning if not configured */}
      <div className="bg-amber-50 rounded-xl border border-amber-100 p-5">
        <div className="flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-amber-800 space-y-1">
            <p className="font-semibold">First-time setup required</p>
            <p>
              Gmail integration requires a Google Cloud OAuth 2.0 application. See{' '}
              <code className="bg-amber-100 px-1 rounded font-mono text-xs">docs/GMAIL_SETUP.md</code> for step-by-step
              instructions to get your <code className="bg-amber-100 px-1 rounded font-mono text-xs">GOOGLE_CLIENT_ID</code>{' '}
              and <code className="bg-amber-100 px-1 rounded font-mono text-xs">GOOGLE_CLIENT_SECRET</code>.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GmailSettings;
