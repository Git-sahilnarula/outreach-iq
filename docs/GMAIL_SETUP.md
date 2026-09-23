# Gmail Integration Setup Guide

This guide walks you through getting `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` for the Outreach IQ Gmail integration. Estimated time: **5–10 minutes**.

---

## Step 1: Create or Select a Google Cloud Project

1. Go to [https://console.cloud.google.com](https://console.cloud.google.com)
2. In the top bar, click the project selector → **New Project**
3. Name it `outreach-iq` (or anything you like) → **Create**

---

## Step 2: Enable the Gmail API

1. In the left menu, go to **APIs & Services → Library**
2. Search for **Gmail API**
3. Click it → **Enable**

---

## Step 3: Configure the OAuth Consent Screen

1. Go to **APIs & Services → OAuth consent screen**
2. Choose **External** → **Create**
3. Fill in:
   - **App name**: `Outreach IQ`
   - **User support email**: your email
   - **Developer contact email**: your email
4. Click **Save and Continue** through all steps (no need to add scopes here)
5. On the last step, click **Back to Dashboard**

> **Note**: While in "Testing" mode, only accounts you add as test users can authenticate. Add your own Gmail address as a test user under **OAuth consent screen → Test users**.

---

## Step 4: Create OAuth 2.0 Credentials

1. Go to **APIs & Services → Credentials**
2. Click **+ Create Credentials → OAuth client ID**
3. Choose **Application type: Web application**
4. Set **Name**: `Outreach IQ Local`
5. Under **Authorized redirect URIs**, add:
   ```
   http://localhost:8000/api/gmail/callback
   ```
6. Click **Create**
7. A dialog will show your **Client ID** and **Client Secret** — copy both

---

## Step 5: Update Your `.env` File

Open `.env` in the project root and add:

```env
GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8000/api/gmail/callback
```

---

## Step 6: Restart the Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Step 7: Connect Gmail in the App

1. Open the frontend: [http://localhost:5173](http://localhost:5173)
2. Navigate to **Gmail** in the top nav
3. Click **Connect Gmail**
4. Sign in with your Google account
5. Grant the requested permissions

---

## Step 8: Label Emails in Gmail

For Outreach IQ to pick up job-alert emails:

1. Open Gmail: [https://mail.google.com](https://mail.google.com)
2. Create a new label called exactly: `Job Alerts`
   - Click the gear icon → **See all settings** → **Labels** tab → **Create new label**
3. Apply this label to job-alert emails from LinkedIn, Indeed, Glassdoor, etc.
4. Come back to Outreach IQ and click **Sync Now**

> **Tip**: You can auto-label emails using Gmail filters:
> Go to **Settings → Filters and Blocked Addresses → Create a new filter**
> Filter by sender (e.g. `jobalerts@linkedin.com`) → Apply label `Job Alerts`

---

## How Processed Emails Are Tracked

After a successful sync, Outreach IQ adds the label `OutreachIQ/Processed` to each ingested email in Gmail. This prevents the same email from being ingested twice on future syncs.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| "Gmail integration is not configured" | Check that `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set in `.env` and restart the backend |
| "Access denied" after clicking Connect | Make sure your Google account is added as a Test User in the OAuth consent screen |
| Redirect URI mismatch error | Ensure `http://localhost:8000/api/gmail/callback` is listed exactly in the Authorized redirect URIs |
| No emails found after sync | Make sure emails have the `Job Alerts` label in Gmail |
| AI extraction fails | Check that Ollama is running (`ollama serve`) and the model is available (`ollama list`) |

---

## Security Notes

- OAuth tokens are stored in the `gmail_tokens` table in your local SQLite database
- The integration only uses **read** and **label** permissions — it cannot send emails or delete them
- Tokens are refreshed automatically when they expire
- You can disconnect at any time from the Gmail settings page
