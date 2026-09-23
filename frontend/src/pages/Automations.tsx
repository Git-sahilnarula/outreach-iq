import { useState, useEffect, useCallback } from 'react';
import {
  Zap,
  Copy,
  Check,
  Eye,
  EyeOff,
  RefreshCw,
  Plus,
  Trash2,
  Send,
  Download,
  ExternalLink,
  Shield,
  Activity,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  AlertCircle
} from 'lucide-react';
import { webhooksAPI } from '../services/api';
import type {
  WebhookTokenResponse,
  WebhookSubscription,
  WebhookSubscriptionCreate,
  WebhookTestResponse
} from '../types';

const EVENT_OPTIONS = [
  { id: 'job.discovered', label: 'Job Discovered', desc: 'Fired when a new lead is ingested' },
  { id: 'job.high_match', label: 'High Match Alert', desc: 'Fired when AI match score >= 75' },
  { id: 'proposal.ready', label: 'Proposal Ready', desc: 'Fired when a proposal draft is generated' },
  { id: 'outreach.sent', label: 'Outreach Sent', desc: 'Fired when email or LinkedIn outreach is dispatched' },
];

const UPWORK_TEMPLATE = {
  name: "Upwork RSS to Outreach IQ Ingestion",
  nodes: [
    {
      parameters: { rule: { interval: [{ field: "minutes", minutesInterval: 15 }] } },
      id: "node-1",
      name: "Schedule Trigger (Every 15m)",
      type: "n8n-nodes-base.scheduleTrigger",
      typeVersion: 1.1,
      position: [240, 300]
    },
    {
      parameters: { url: "https://www.upwork.com/ab/feed/jobs/rss?q=fullstack+ai+python+react&sort=recency" },
      id: "node-2",
      name: "Fetch Upwork RSS Feed",
      type: "n8n-nodes-base.rssFeedRead",
      typeVersion: 1.1,
      position: [460, 300]
    },
    {
      parameters: {
        jsCode: "const items = $input.all();\nreturn items.map(item => {\n  const rawDesc = item.json.contentSnippet || item.json.description || '';\n  const budgetMatch = rawDesc.match(/Budget:\\s*\\$([0-9,]+)/i) || rawDesc.match(/Hourly Range:\\s*(\\$[0-9.-]+)/i);\n  return {\n    json: {\n      title: item.json.title ? item.json.title.replace(/ - Upwork$/i, '').trim() : 'Upwork Lead',\n      description: rawDesc,\n      source: 'upwork_rss',\n      source_job_id: item.json.guid || item.json.link || '',\n      budget: budgetMatch ? budgetMatch[0] : 'See description',\n      client_name: 'Upwork Client'\n    }\n  };\n});"
      },
      id: "node-3",
      name: "Clean & Format Lead",
      type: "n8n-nodes-base.code",
      typeVersion: 2,
      position: [680, 300]
    },
    {
      parameters: {
        method: "POST",
        url: "http://localhost:8000/api/webhooks/jobs",
        sendHeaders: true,
        headerParameters: {
          parameters: [
            { name: "X-Webhook-Token", value: "={{ $env.OUTREACH_IQ_WEBHOOK_TOKEN || 'YOUR_TOKEN_HERE' }}" },
            { name: "Content-Type", value: "application/json" }
          ]
        },
        sendBody: true,
        specifyBody: "json",
        jsonBody: "={\n  \"title\": {{ JSON.stringify($json.title) }},\n  \"description\": {{ JSON.stringify($json.description) }},\n  \"source\": {{ JSON.stringify($json.source) }},\n  \"source_job_id\": {{ JSON.stringify($json.source_job_id) }},\n  \"budget\": {{ JSON.stringify($json.budget) }},\n  \"client_name\": {{ JSON.stringify($json.client_name) }}\n}"
      },
      id: "node-4",
      name: "Post to Outreach IQ",
      type: "n8n-nodes-base.httpRequest",
      typeVersion: 4.1,
      position: [900, 300]
    }
  ]
};

const SLACK_TEMPLATE = {
  name: "Outreach IQ Events to Slack Notifications",
  nodes: [
    {
      parameters: { httpMethod: "POST", path: "outreach-iq" },
      id: "node-1",
      name: "Outreach IQ Webhook Receiver",
      type: "n8n-nodes-base.webhook",
      typeVersion: 1.1,
      position: [240, 300]
    },
    {
      parameters: {
        dataType: "string",
        value1: "={{$json.body.event}}",
        rules: {
          rules: [{ value2: "job.high_match" }, { value2: "proposal.ready" }, { value2: "outreach.sent" }]
        }
      },
      id: "node-2",
      name: "Route by Event",
      type: "n8n-nodes-base.switch",
      typeVersion: 1,
      position: [480, 300]
    },
    {
      parameters: {
        method: "POST",
        url: "https://hooks.slack.com/services/REPLACE/WITH/YOUR_SLACK_WEBHOOK",
        sendBody: true,
        specifyBody: "json",
        jsonBody: "={\n  \"text\": `🔥 *High Match Job Discovered:* ${$json.body.data.title}\\n🎯 *Score:* ${$json.body.data.match_score}/100`\n}"
      },
      id: "node-3",
      name: "Send Slack Alert",
      type: "n8n-nodes-base.httpRequest",
      typeVersion: 4.1,
      position: [750, 300]
    }
  ]
};

export default function Automations() {
  const [tokenData, setTokenData] = useState<WebhookTokenResponse | null>(null);
  const [subscriptions, setSubscriptions] = useState<WebhookSubscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [showToken, setShowToken] = useState(false);
  const [tokenCopied, setTokenCopied] = useState(false);
  const [urlCopied, setUrlCopied] = useState(false);
  const [curlCopied, setCurlCopied] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  // New Subscription Modal / Form state
  const [showModal, setShowModal] = useState(false);
  const [newUrl, setNewUrl] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newSecret, setNewSecret] = useState('');
  const [selectedEvents, setSelectedEvents] = useState<string[]>(['*']);
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Test ping feedback
  const [testingId, setTestingId] = useState<number | null>(null);
  const [testResults, setTestResults] = useState<Record<number, WebhookTestResponse>>({});

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [tokenRes, subsRes] = await Promise.all([
        webhooksAPI.getToken(),
        webhooksAPI.getSubscriptions()
      ]);
      setTokenData(tokenRes.data);
      setSubscriptions(subsRes.data);
    } catch (err) {
      console.error('Failed to load webhook automation data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCopy = (text: string, type: 'token' | 'url' | 'curl') => {
    navigator.clipboard.writeText(text);
    if (type === 'token') {
      setTokenCopied(true);
      setTimeout(() => setTokenCopied(false), 2000);
    } else if (type === 'url') {
      setUrlCopied(true);
      setTimeout(() => setUrlCopied(false), 2000);
    } else {
      setCurlCopied(true);
      setTimeout(() => setCurlCopied(false), 2000);
    }
  };

  const handleRegenerateToken = async () => {
    if (!window.confirm('Regenerating will invalidate your current webhook token. Any active automations using it will fail until updated. Continue?')) {
      return;
    }
    try {
      setRegenerating(true);
      const res = await webhooksAPI.regenerateToken();
      setTokenData(res.data);
    } catch (err) {
      alert('Failed to regenerate token. Please try again.');
    } finally {
      setRegenerating(false);
    }
  };

  const handleToggleEvent = (eventId: string) => {
    if (eventId === '*') {
      setSelectedEvents(['*']);
      return;
    }
    let updated = selectedEvents.filter(e => e !== '*');
    if (updated.includes(eventId)) {
      updated = updated.filter(e => e !== eventId);
    } else {
      updated.push(eventId);
    }
    if (updated.length === 0) {
      updated = ['*'];
    }
    setSelectedEvents(updated);
  };

  const handleCreateSubscription = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUrl.trim()) {
      setFormError('Please enter a target webhook URL');
      return;
    }
    try {
      setCreating(true);
      setFormError(null);
      const payload: WebhookSubscriptionCreate = {
        target_url: newUrl.trim(),
        description: newDesc.trim() || undefined,
        secret_token: newSecret.trim() || undefined,
        events: selectedEvents,
        is_active: true
      };
      await webhooksAPI.createSubscription(payload);
      setShowModal(false);
      setNewUrl('');
      setNewDesc('');
      setNewSecret('');
      setSelectedEvents(['*']);
      await loadData();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to register webhook subscription');
    } finally {
      setCreating(false);
    }
  };

  const handleToggleActive = async (sub: WebhookSubscription) => {
    try {
      await webhooksAPI.updateSubscription(sub.id, { is_active: !sub.is_active });
      setSubscriptions(subs =>
        subs.map(s => (s.id === sub.id ? { ...s, is_active: !s.is_active } : s))
      );
    } catch (err) {
      alert('Failed to update subscription status');
    }
  };

  const handleDeleteSubscription = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this webhook endpoint?')) return;
    try {
      await webhooksAPI.deleteSubscription(id);
      setSubscriptions(subs => subs.filter(s => s.id !== id));
    } catch (err) {
      alert('Failed to delete webhook subscription');
    }
  };

  const handleTestPing = async (id: number) => {
    try {
      setTestingId(id);
      const res = await webhooksAPI.testSubscription(id);
      setTestResults(prev => ({ ...prev, [id]: res.data }));
      // Refresh list to show updated last_triggered_at
      const subsRes = await webhooksAPI.getSubscriptions();
      setSubscriptions(subsRes.data);
    } catch (err: any) {
      setTestResults(prev => ({
        ...prev,
        [id]: {
          success: false,
          status_code: 0,
          response_body: err.message,
          message: 'Failed to send test ping'
        }
      }));
    } finally {
      setTestingId(null);
    }
  };

  const downloadBlueprint = (template: any, filename: string) => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(template, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', filename);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const fullInboundUrl = `${window.location.origin}${tokenData?.inbound_url || '/api/webhooks/jobs'}`;

  const curlExample = `curl -X POST "${fullInboundUrl}" \\
  -H "Content-Type: application/json" \\
  -H "X-Webhook-Token: ${tokenData?.webhook_token || 'whk_your_token'}" \\
  -d '{
    "title": "Senior AI & Fullstack Engineer",
    "description": "Looking for expert in FastAPI and React.",
    "client_name": "Upwork Client",
    "budget": "$5,000 fixed",
    "source": "n8n_automation"
  }'`;

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin mb-3" />
        <p className="text-gray-500 font-medium">Loading automation settings...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-gray-200 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 bg-indigo-50 rounded-lg text-indigo-600">
              <Zap className="w-6 h-6" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Automations & Webhooks</h1>
          </div>
          <p className="text-gray-500 mt-1">
            Connect Outreach IQ to n8n, Zapier, and Slack for 24/7 autonomous opportunity ingestion and alert routing.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            Webhook Engine Active
          </span>
        </div>
      </div>

      {/* Grid: Inbound & Outbound */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Inbound Webhook (8 cols) */}
        <div className="lg:col-span-12 space-y-6">
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <Shield className="w-5 h-5 text-indigo-600" />
                  Inbound Webhook: Autonomous Job Ingestion
                </h2>
                <p className="text-sm text-gray-500 mt-1">
                  Send incoming job postings from n8n, Upwork RSS bots, or web scrapers directly into Outreach IQ.
                </p>
              </div>
              <span className="text-xs px-2.5 py-1 font-medium bg-indigo-50 text-indigo-700 rounded-md">
                POST /api/webhooks/jobs
              </span>
            </div>

            <div className="mt-6 space-y-4">
              {/* Endpoint URL */}
              <div>
                <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1.5">
                  Webhook Target URL
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    readOnly
                    value={fullInboundUrl}
                    className="flex-1 bg-gray-50 border border-gray-300 rounded-lg px-3.5 py-2 text-sm text-gray-800 font-mono focus:outline-none"
                  />
                  <button
                    onClick={() => handleCopy(fullInboundUrl, 'url')}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 text-sm font-medium bg-white border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition"
                  >
                    {urlCopied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                    {urlCopied ? 'Copied' : 'Copy'}
                  </button>
                </div>
              </div>

              {/* Personal Webhook Token */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Personal Webhook Token (Secret)
                  </label>
                  <button
                    onClick={handleRegenerateToken}
                    disabled={regenerating}
                    className="text-xs text-rose-600 hover:text-rose-700 font-medium inline-flex items-center gap-1 transition disabled:opacity-50"
                  >
                    <RefreshCw className={`w-3 h-3 ${regenerating ? 'animate-spin' : ''}`} />
                    Regenerate Token
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <div className="relative flex-1">
                    <input
                      type={showToken ? 'text' : 'password'}
                      readOnly
                      value={tokenData?.webhook_token || ''}
                      className="w-full bg-gray-50 border border-gray-300 rounded-lg px-3.5 py-2 pr-10 text-sm text-gray-800 font-mono focus:outline-none"
                    />
                    <button
                      type="button"
                      onClick={() => setShowToken(!showToken)}
                      className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600"
                    >
                      {showToken ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  <button
                    onClick={() => handleCopy(tokenData?.webhook_token || '', 'token')}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 text-sm font-medium bg-white border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition"
                  >
                    {tokenCopied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                    {tokenCopied ? 'Copied' : 'Copy'}
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-1.5">
                  Pass this token in the <code className="bg-gray-100 px-1 py-0.5 rounded text-gray-700">X-Webhook-Token</code> header or as query parameter <code className="bg-gray-100 px-1 py-0.5 rounded text-gray-700">?token=</code>.
                </p>
              </div>

              {/* cURL Snippet */}
              <div className="pt-2">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Quick cURL Test Snippet
                  </span>
                  <button
                    onClick={() => handleCopy(curlExample, 'curl')}
                    className="text-xs text-indigo-600 hover:text-indigo-700 font-medium inline-flex items-center gap-1"
                  >
                    {curlCopied ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                    {curlCopied ? 'Copied to clipboard' : 'Copy cURL command'}
                  </button>
                </div>
                <pre className="bg-slate-900 text-slate-100 text-xs rounded-lg p-3.5 overflow-x-auto font-mono">
                  {curlExample}
                </pre>
              </div>

              {/* Ingestion Highlights */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                  <div className="flex items-center gap-2 text-indigo-600 font-semibold text-xs mb-1">
                    <Sparkles className="w-3.5 h-3.5" />
                    AI Auto-Analysis
                  </div>
                  <p className="text-xs text-gray-600">
                    Incoming leads are automatically scored against your profile and portfolio projects.
                  </p>
                </div>
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                  <div className="flex items-center gap-2 text-indigo-600 font-semibold text-xs mb-1">
                    <Shield className="w-3.5 h-3.5" />
                    Duplicate Suppression
                  </div>
                  <p className="text-xs text-gray-600">
                    Duplicate titles, descriptions, and source IDs are detected and silently de-duplicated.
                  </p>
                </div>
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                  <div className="flex items-center gap-2 text-indigo-600 font-semibold text-xs mb-1">
                    <Activity className="w-3.5 h-3.5" />
                    Instant Dispatch
                  </div>
                  <p className="text-xs text-gray-600">
                    High matches (score &ge; 75) trigger immediate in-app & outbound webhook notifications.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Outbound Webhooks (Subscriptions) */}
        <div className="lg:col-span-12 space-y-6">
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-indigo-600" />
                  Outbound Webhooks: Event Dispatcher
                </h2>
                <p className="text-sm text-gray-500 mt-1">
                  Deliver real-time notifications to your n8n workflows, Slack bots, or internal services when events happen.
                </p>
              </div>
              <button
                onClick={() => setShowModal(true)}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition shadow-sm"
              >
                <Plus className="w-4 h-4" />
                Add Webhook Endpoint
              </button>
            </div>

            {/* Subscriptions List */}
            <div className="mt-6 space-y-4">
              {subscriptions.length === 0 ? (
                <div className="text-center py-10 bg-gray-50 border border-dashed border-gray-300 rounded-xl">
                  <Activity className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm font-medium text-gray-700">No outbound endpoints configured</p>
                  <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
                    Add a webhook URL to receive instant alerts when high-match opportunities are found or proposals are generated.
                  </p>
                  <button
                    onClick={() => setShowModal(true)}
                    className="mt-4 inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-gray-300 text-gray-700 rounded-md text-xs font-medium hover:bg-gray-50"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    Register Your First Endpoint
                  </button>
                </div>
              ) : (
                subscriptions.map(sub => {
                  const testResult = testResults[sub.id];
                  return (
                    <div
                      key={sub.id}
                      className={`border rounded-xl p-4 transition ${
                        sub.is_active ? 'bg-white border-gray-200' : 'bg-gray-50 border-gray-200 opacity-75'
                      }`}
                    >
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div className="space-y-1.5">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-gray-900 text-sm">
                              {sub.description || 'Outbound Webhook'}
                            </span>
                            <span
                              className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                                sub.is_active
                                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                  : 'bg-gray-100 text-gray-600'
                              }`}
                            >
                              {sub.is_active ? 'Active' : 'Disabled'}
                            </span>
                            {sub.last_status_code !== null && sub.last_status_code !== undefined && (
                              <span
                                className={`px-2 py-0.5 rounded-md text-xs font-mono font-medium ${
                                  sub.last_status_code >= 200 && sub.last_status_code < 400
                                    ? 'bg-emerald-100 text-emerald-800'
                                    : 'bg-rose-100 text-rose-800'
                                }`}
                              >
                                {sub.last_status_code === 0 ? 'Failed' : `HTTP ${sub.last_status_code}`}
                              </span>
                            )}
                          </div>
                          <p className="text-xs font-mono text-gray-600 break-all">{sub.target_url}</p>
                          <div className="flex flex-wrap items-center gap-1.5 pt-1">
                            <span className="text-xs text-gray-400">Events:</span>
                            {sub.events.map(ev => (
                              <span
                                key={ev}
                                className="px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded text-xs font-mono font-medium"
                              >
                                {ev}
                              </span>
                            ))}
                          </div>
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-2 self-start md:self-center">
                          <button
                            onClick={() => handleTestPing(sub.id)}
                            disabled={testingId === sub.id}
                            className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium bg-white border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition disabled:opacity-50"
                          >
                            <Send className={`w-3.5 h-3.5 ${testingId === sub.id ? 'animate-bounce' : ''}`} />
                            {testingId === sub.id ? 'Testing...' : 'Test Ping'}
                          </button>
                          <button
                            onClick={() => handleToggleActive(sub)}
                            className="px-3 py-1.5 text-xs font-medium bg-white border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition"
                          >
                            {sub.is_active ? 'Pause' : 'Activate'}
                          </button>
                          <button
                            onClick={() => handleDeleteSubscription(sub.id)}
                            className="p-1.5 text-gray-400 hover:text-rose-600 transition"
                            title="Delete subscription"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>

                      {/* Test Result Toast/Banner */}
                      {testResult && (
                        <div
                          className={`mt-3 p-3 rounded-lg text-xs flex items-start gap-2 border ${
                            testResult.success
                              ? 'bg-emerald-50 text-emerald-900 border-emerald-200'
                              : 'bg-rose-50 text-rose-900 border-rose-200'
                          }`}
                        >
                          {testResult.success ? (
                            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                          ) : (
                            <XCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                          )}
                          <div className="flex-1">
                            <span className="font-semibold">{testResult.message}</span>
                            {testResult.response_body && (
                              <p className="font-mono text-gray-600 mt-1 max-h-20 overflow-y-auto">
                                {testResult.response_body}
                              </p>
                            )}
                          </div>
                        </div>
                      )}

                      {sub.last_triggered_at && (
                        <div className="mt-2 text-xs text-gray-400 flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          Last dispatched: {new Date(sub.last_triggered_at).toLocaleString()}
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Turnkey n8n Blueprints */}
        <div className="lg:col-span-12">
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Download className="w-5 h-5 text-indigo-600" />
                Turnkey n8n Workflow Blueprints
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                Download pre-configured n8n templates to automate lead scraping and Slack alerts in 60 seconds.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
              {/* Template 1: Upwork RSS */}
              <div className="border border-gray-200 rounded-xl p-5 hover:border-indigo-300 transition bg-gradient-to-br from-white to-gray-50/50 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="px-2.5 py-0.5 text-xs font-semibold bg-blue-50 text-blue-700 rounded-md">
                      Inbound Automation
                    </span>
                    <span className="text-xs text-gray-400">n8n Workflow</span>
                  </div>
                  <h3 className="font-bold text-gray-900 text-base">Upwork RSS &rarr; Outreach IQ</h3>
                  <p className="text-xs text-gray-500 mt-1.5 leading-relaxed">
                    Polls Upwork search RSS feeds every 15 minutes, strips HTML noise, parses budgets, and posts directly into Outreach IQ with automated AI match evaluation.
                  </p>
                  <div className="flex items-center gap-1.5 mt-3 text-xs text-gray-600 font-medium">
                    <span className="bg-gray-100 px-2 py-0.5 rounded">Schedule (15m)</span>
                    <span>&rarr;</span>
                    <span className="bg-gray-100 px-2 py-0.5 rounded">RSS Read</span>
                    <span>&rarr;</span>
                    <span className="bg-gray-100 px-2 py-0.5 rounded">HTTP POST</span>
                  </div>
                </div>

                <div className="mt-5 pt-4 border-t border-gray-100 flex items-center justify-between">
                  <span className="text-xs text-gray-400">upwork_rss_to_outreach_iq.json</span>
                  <button
                    onClick={() => downloadBlueprint(UPWORK_TEMPLATE, 'upwork_rss_to_outreach_iq.json')}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg text-xs font-semibold transition"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Download Blueprint
                  </button>
                </div>
              </div>

              {/* Template 2: Slack Alert */}
              <div className="border border-gray-200 rounded-xl p-5 hover:border-indigo-300 transition bg-gradient-to-br from-white to-gray-50/50 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="px-2.5 py-0.5 text-xs font-semibold bg-emerald-50 text-emerald-700 rounded-md">
                      Outbound Alerts
                    </span>
                    <span className="text-xs text-gray-400">n8n Workflow</span>
                  </div>
                  <h3 className="font-bold text-gray-900 text-base">Outreach IQ &rarr; Slack & Discord</h3>
                  <p className="text-xs text-gray-500 mt-1.5 leading-relaxed">
                    Listens for high-match opportunities (&ge; 75 score), generated proposals, and sent messages, formatting rich Markdown cards with 1-click links into Slack channels.
                  </p>
                  <div className="flex items-center gap-1.5 mt-3 text-xs text-gray-600 font-medium">
                    <span className="bg-gray-100 px-2 py-0.5 rounded">Webhook</span>
                    <span>&rarr;</span>
                    <span className="bg-gray-100 px-2 py-0.5 rounded">Event Switch</span>
                    <span>&rarr;</span>
                    <span className="bg-gray-100 px-2 py-0.5 rounded">Slack Webhook</span>
                  </div>
                </div>

                <div className="mt-5 pt-4 border-t border-gray-100 flex items-center justify-between">
                  <span className="text-xs text-gray-400">outreach_iq_to_slack.json</span>
                  <button
                    onClick={() => downloadBlueprint(SLACK_TEMPLATE, 'outreach_iq_to_slack.json')}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 rounded-lg text-xs font-semibold transition"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Download Blueprint
                  </button>
                </div>
              </div>
            </div>

            <div className="mt-6 p-4 bg-gray-50 border border-gray-200 rounded-xl">
              <h4 className="text-xs font-bold text-gray-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <ExternalLink className="w-3.5 h-3.5 text-indigo-600" />
                How to Import into n8n:
              </h4>
              <ol className="text-xs text-gray-600 space-y-1 list-decimal list-inside">
                <li>Download either JSON blueprint above to your computer.</li>
                <li>In your n8n workspace, click <strong>Workflows &rarr; Add Workflow</strong>.</li>
                <li>Open the top-right menu (three dots) and select <strong>Import from File</strong>.</li>
                <li>Select the downloaded JSON file. Enter your personal Webhook Token or Slack URL in the node properties.</li>
                <li>Click <strong>Activate</strong> to begin 24/7 automation!</li>
              </ol>
            </div>
          </div>
        </div>
      </div>

      {/* Register Subscription Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-gray-100 animate-in fade-in duration-200">
            <h3 className="text-lg font-bold text-gray-900 mb-1">Add Outbound Webhook Endpoint</h3>
            <p className="text-xs text-gray-500 mb-4">
              Specify the target URL that will receive Outreach IQ event notifications via HTTP POST.
            </p>

            {formError && (
              <div className="mb-4 p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-lg flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {formError}
              </div>
            )}

            <form onSubmit={handleCreateSubscription} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Target Webhook URL <span className="text-rose-500">*</span>
                </label>
                <input
                  type="url"
                  required
                  placeholder="https://n8n.yourcompany.com/webhook/outreach"
                  value={newUrl}
                  onChange={e => setNewUrl(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Description / Label
                </label>
                <input
                  type="text"
                  placeholder="e.g. n8n High Match Alert Workflow"
                  value={newDesc}
                  onChange={e => setNewDesc(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Signing Secret (Optional HMAC-SHA256)
                </label>
                <input
                  type="text"
                  placeholder="Leave empty or enter secret to sign X-OutreachIQ-Signature"
                  value={newSecret}
                  onChange={e => setNewSecret(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-2">
                  Subscribed Events
                </label>
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-xs font-medium text-gray-700 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedEvents.includes('*')}
                      onChange={() => handleToggleEvent('*')}
                      className="rounded text-indigo-600 focus:ring-indigo-500"
                    />
                    <span>All Events (*)</span>
                  </label>
                  {EVENT_OPTIONS.map(opt => (
                    <label key={opt.id} className="flex items-start gap-2 text-xs text-gray-600 cursor-pointer ml-4">
                      <input
                        type="checkbox"
                        checked={selectedEvents.includes(opt.id) && !selectedEvents.includes('*')}
                        onChange={() => handleToggleEvent(opt.id)}
                        className="rounded text-indigo-600 focus:ring-indigo-500 mt-0.5"
                      />
                      <div>
                        <span className="font-semibold text-gray-800">{opt.label}</span> ({opt.id})
                        <p className="text-[11px] text-gray-400">{opt.desc}</p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              <div className="pt-4 flex items-center justify-end gap-3 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-xs font-semibold hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-semibold hover:bg-indigo-700 transition disabled:opacity-50"
                >
                  {creating ? 'Saving...' : 'Register Endpoint'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
