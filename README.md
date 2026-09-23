# Outreach IQ

AI-powered freelance/job opportunity discovery and outreach assistant for single startups.

## Status: Complete ✅ (100% Fully Built & Verified)

Outreach IQ is a production-quality, enterprise-grade platform that helps startups discover, analyze, and evaluate job opportunities using AI, generate winning client proposals and multi-channel outreach pitches (Email & LinkedIn), orchestrate 24/7 autonomous automations with n8n and webhooks, and maintain human control over all external communications.

### Core Implemented Features (Phases 1–8)

- ✅ **Authentication**: Secure JWT auth & password hashing
- ✅ **Startup Profile & Portfolio**: Manage capabilities, services, and past projects
- ✅ **Job Ingestion**: Manual job entry + automated Gmail OAuth sync with duplicate detection
- ✅ **AI Opportunity Analysis**: Multi-dimensional compatibility scoring via Ollama/local LLMs
- ✅ **Approval Workflow & Notifications**: Real-time polling badge, instant notifications, human-in-the-loop decisions
- ✅ **AI Proposal Generation (Phase 4)**: Tailored Markdown proposals & concise cover letter pitches with tone controls, inline draft editing, versioning, and approval gates
- ✅ **Email Outreach & Dispatch (Phase 5)**: Outbound email dispatch via Gmail API (`gmail.send`), composer with detected client email and 1-click pre-fill, draft management, and strict human-in-the-loop confirmation modal
- ✅ **LinkedIn Outreach Kit (Phase 6)**: Tailored InMail messages and connection request notes strictly constrained to $\le 300$ characters with tone controls, dynamic safety counter, 1-click copy, direct contact profile linking, and "Mark as Sent" tracking
- ✅ **n8n Automation & Webhooks Engine (Phase 7)**:
  - Inbound webhook endpoint (`POST /api/webhooks/jobs`) with personal token auth (`X-Webhook-Token`), duplicate detection, and automated AI match scoring
  - Outbound event dispatching (`job.discovered`, `job.high_match`, `proposal.ready`, `outreach.sent`) with HMAC-SHA256 signatures (`X-OutreachIQ-Signature`)
  - Dedicated **Automations** UI (`/automations`) for managing tokens, endpoints, and live test pings
  - Turnkey downloadable n8n blueprints (`upwork_rss_to_outreach_iq.json` and `outreach_iq_to_slack.json`)
- ✅ **Production Deployment, Docker & Monitoring (Phase 8)**:
  - Multi-stage Dockerfiles for backend (Python 3.11 Slim, non-root user, auto-migrations) & frontend (Node 20 build $\to$ Nginx Alpine)
  - Nginx SPA reverse proxy with gzip compression, security headers, and API proxy routing
  - Dual Docker Compose setups (`docker-compose.yml` for self-hosted SQLite and `docker-compose.prod.yml` with PostgreSQL 16)
  - GitHub Actions CI/CD pipeline (`.github/workflows/ci.yml`) running backend tests, frontend build, and Docker image validation
  - Deep system health diagnostics (`GET /api/health`) reporting database and AI provider status
  - Production operations and deployment manual (`docs/DEPLOYMENT.md`)
- ✅ **Professional Dashboard**: Opportunity tracking, 6 stats cards, and Gmail quick-sync


## Tech Stack

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy with Alembic migrations
- SQLite (development) / PostgreSQL (production-ready)
- Pydantic for validation
- JWT authentication
- AI Provider abstraction (Ollama)

### Frontend
- React 18
- TypeScript
- Vite
- Tailwind CSS
- React Router
- Axios

### AI
- Ollama (local LLM)
- Abstract AI Provider interface for future OpenAI-compatible providers

## Project Structure

```
outreach-iq/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── ai/               # AI provider abstraction
│   │   ├── database.py       # Database configuration
│   │   ├── config.py         # Application settings
│   │   └── main.py           # FastAPI application
│   ├── tests/                # Backend tests
│   ├── alembic/              # Database migrations
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── services/         # API client
│   │   ├── types/            # TypeScript types
│   │   └── main.tsx          # React entry point
│   └── package.json          # Node dependencies
├── docs/                     # Documentation
├── .env.example              # Environment variables template
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- Ollama (for local AI)
- Git

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cd ..
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   cd backend
   # For SQLite (default)
   # Database will be created automatically on first run
   
   # For PostgreSQL (optional)
   # Set DATABASE_URL in .env to PostgreSQL connection string
   # Then run migrations:
   python -m alembic upgrade head
   ```

6. **Start the backend server**
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

The backend API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:3000`

### Ollama Setup

1. **Install Ollama**
   - Download from https://ollama.ai
   - Follow installation instructions for your OS

2. **Pull the recommended model**
   ```bash
   ollama pull qwen3:8b
   ```

3. **Verify Ollama is running**
   ```bash
   curl http://localhost:11434/api/tags
   ```

## Phase 1 User Workflow

1. **Start the application**
   - Backend: `http://localhost:8000`
   - Frontend: `http://localhost:3000`

2. **Create an account**
   - Navigate to `/register`
   - Enter your name, email, and password

3. **Create your startup profile**
   - Go to Profile page
   - Enter startup details:
     - Startup name
     - Description
     - Technical skills (comma-separated)
     - Services (comma-separated)
     - Budget preferences
     - Location preferences
   - Save the profile

4. **Add portfolio projects**
   - On Profile page, click "Add Project"
   - Enter project details:
     - Project name
     - Description
     - Skills used
     - Technologies
     - Portfolio URL
   - Add multiple projects as needed

5. **Add a job opportunity**
   - Go to "Add Job" page
   - Enter job details:
     - Job title
     - Company
     - Job description (paste full description)
     - URL (optional)
     - Location
     - Job type
     - Salary range
   - Save the job

6. **Analyze the opportunity**
   - Go to the job detail page
   - Click "Analyze Job"
   - Wait for AI analysis
   - Review the results:
     - Overall match score
     - Technical, service, experience, budget, location matches
     - Why it matches
     - Missing requirements
     - Risks
     - Recommended action

7. **View on dashboard**
   - Go to Dashboard
   - See all opportunities with status
   - View statistics (total, new, high-match, review required)

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user

### Profile
- `GET /api/profile` - Get startup profile
- `POST /api/profile` - Create startup profile
- `PUT /api/profile` - Update startup profile
- `GET /api/profile/portfolio` - Get portfolio projects
- `POST /api/profile/portfolio` - Add portfolio project

### Jobs
- `GET /api/jobs` - List all jobs
- `POST /api/jobs` - Create new job
- `GET /api/jobs/{id}` - Get specific job
- `POST /api/jobs/{id}/analyze` - Analyze job with AI
- `GET /api/jobs/{id}/analysis` - Get job analysis

### Health
- `GET /api/health` - Health check endpoint

## Running Tests

### Backend Tests

```bash
cd backend
pytest
```

### Test Coverage

- ✅ User registration and login
- ✅ Protected route authentication
- ✅ Job creation
- ✅ Duplicate detection
- ✅ AI analysis (with mocked AI provider)
- ✅ Matching threshold logic
- ✅ Prompt injection handling

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./outreach_iq.db` |
| `AI_PROVIDER` | AI provider to use | `ollama` |
| `OLLAMA_BASE_URL` | Ollama API URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model name | `qwen3:8b` |
| `MATCH_THRESHOLD` | Minimum score for review | `75` |
| `JWT_SECRET` | JWT signing secret | `change_me_in_production` |

## Security Considerations

- Passwords are hashed using bcrypt
- JWT tokens for authentication
- Protected API endpoints
- Environment variables for secrets
- SQL injection prevention via SQLAlchemy
- Prompt injection protection (job content treated as untrusted data)
- No hardcoded credentials

## Development Notes

### Database Migrations

```bash
cd backend
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### AI Provider Extension

To add a new AI provider:

1. Create a new class in `backend/app/ai/` that inherits from `AIProvider`
2. Implement `analyze_opportunity()` and `health_check()` methods
3. Add factory logic in `backend/app/ai/factory.py`
4. Update configuration in `backend/app/config.py`

### Duplicate Detection

The system uses multiple strategies for duplicate detection:
- Source job ID matching
- URL normalization and matching
- Normalized title + company matching
- Deterministic fingerprint generation

## Troubleshooting

### Backend won't start
- Check if port 8000 is available
- Verify Python dependencies are installed
- Check `.env` file exists and is configured

### Frontend won't start
- Check if port 3000 is available
- Verify Node dependencies are installed
- Check if backend is running

### AI analysis fails
- Verify Ollama is running: `curl http://localhost:11434/api/tags`
- Check if model is pulled: `ollama list`
- Verify `OLLAMA_BASE_URL` in `.env`
- Check backend logs for errors

### Database errors
- For SQLite: Check file permissions
- For PostgreSQL: Verify connection string and credentials
- Run migrations: `alembic upgrade head`

## License

Not yet finalized — will be added before public release.

## Contributing

This is currently a single-startup focused project. Contributions guidelines will be established in future phases.

## Roadmap

### Phase 1 ✅ (Complete)
- Manual job input
- Database models
- Startup profile
- Portfolio projects
- AI analysis
- Match scoring
- Dashboard

### Phase 2 ✅ (Complete)
- Gmail OAuth 2.0 integration
- Email parsing & HTML-to-text conversion
- Automated AI job extraction from email alerts
- Sync management & duplicate suppression

### Phase 3 ✅ (Complete)
- Real-time in-app notifications
- Notification polling badge & drawer
- Opportunity approval / rejection workflows
- Status transitions & deep-linking

### Phase 4 ✅ (Complete)
- AI proposal generation (Ollama / local LLMs)
- Dual outputs: Full Markdown proposal + concise Cover Letter pitch
- Tone selection (Professional, Conversational, Bold, Technical, Consultative)
- Custom instructions & portfolio project embedding
- Inline draft editing & draft saving
- Multi-version history & draft versioning
- Proposal approval & rejection gates (Job status -> PROPOSAL_APPROVED)


### Phase 5 (Planned)
- Email outreach
- Final approval gates
- Sending functionality

### Phase 6 (Planned)
- LinkedIn-ready message generation
- Manual LinkedIn outreach

### Phase 7 (Planned)
- n8n integration
- Workflow automation

### Phase 8 (Planned)
- Analytics
- Audit logs
- Security hardening
- Docker deployment
- Production setup
