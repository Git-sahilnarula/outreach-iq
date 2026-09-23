# Outreach IQ — n8n Automation Workflows

This directory contains turnkey workflow blueprints for connecting **Outreach IQ** to **n8n**, Zapier, Make, and external platforms (Upwork RSS, Slack, Discord).

---

## 📦 Included Workflow Templates

| Template | File | Description |
|---|---|---|
| **Upwork RSS Ingestion** | [`templates/upwork_rss_to_outreach_iq.json`](./templates/upwork_rss_to_outreach_iq.json) | Polls Upwork RSS searches every 15 min, formats the lead, and posts it to Outreach IQ's inbound webhook with duplicate detection & AI auto-matching. |
| **Outreach IQ to Slack** | [`templates/outreach_iq_to_slack.json`](./templates/outreach_iq_to_slack.json) | Receives real-time outbound webhooks (`job.high_match`, `proposal.ready`, `outreach.sent`) and routes formatted rich alerts into Slack/Discord channels. |

---

## 🚀 Quick Setup Guide

### 1. Inbound Ingestion (Upwork / RSS / Scraping -> Outreach IQ)

1. Open your Outreach IQ dashboard and navigate to **Automations** (`/automations`).
2. Copy your personal **Inbound Webhook URL** and **Webhook Token** (`whk_...`).
3. In n8n:
   - Click **Add Workflow** -> **Import from File**.
   - Select [`templates/upwork_rss_to_outreach_iq.json`](./templates/upwork_rss_to_outreach_iq.json).
   - In the **Post Lead to Outreach IQ** HTTP Request node, set the `X-Webhook-Token` header to your personal token.
   - Adjust the Upwork RSS search query in the **Fetch Upwork RSS Feed** node (e.g., your preferred keywords).
   - Click **Save** and **Activate**.

#### Inbound Ingestion API Spec:
- **Method**: `POST`
- **Path**: `/api/webhooks/jobs`
- **Headers**:
  - `Content-Type: application/json`
  - `X-Webhook-Token: <your_token>` *(or query parameter `?token=<your_token>`)*
- **Body**:
```json
{
  "title": "Senior React & Python Engineer",
  "description": "Full job description text...",
  "client_name": "Acme Corp",
  "client_email": "client@example.com",
  "client_linkedin": "https://linkedin.com/in/client",
  "budget": "$5,000 fixed",
  "source": "upwork",
  "source_job_id": "job_12345"
}
```

---

### 2. Outbound Event Subscriptions (Outreach IQ -> Slack / n8n)

1. In n8n:
   - Import [`templates/outreach_iq_to_slack.json`](./templates/outreach_iq_to_slack.json).
   - Copy the test or production **Webhook URL** from the **Outreach IQ Webhook Receiver** node (e.g. `https://your-n8n.com/webhook/outreach-iq`).
   - In the **Send Slack Notification** node, paste your Slack incoming webhook URL.
   - Activate the workflow.
2. In Outreach IQ:
   - Navigate to **Automations** (`/automations`).
   - Click **Add Endpoint**.
   - Paste the n8n webhook URL.
   - Select subscribed events (`job.high_match`, `proposal.ready`, `outreach.sent`, or `*`).
   - Click **Save**.
   - Click **Send Test Ping** to verify delivery immediately.

#### Outbound Events Dispatched:
- `job.discovered`: Fired whenever a new opportunity is ingested.
- `job.high_match`: Fired when AI match score $\ge 75$, signalling immediate attention.
- `proposal.ready`: Fired when a proposal version draft is generated.
- `outreach.sent`: Fired when an email or LinkedIn message is dispatched.

#### Security & Signature Verification:
Outreach IQ signs every webhook request using HMAC-SHA256 if a secret token is configured:
```
X-OutreachIQ-Event: job.high_match
X-OutreachIQ-Signature: sha256=4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945
```
