# IPO Intelligence Agent

> **Autonomous multi-agent AI system for IPO investment intelligence**

IPO Intelligence Agent is a production-ready, autonomous multi-agent AI system that discovers, analyzes, and generates institutional-quality investment research reports for upcoming IPOs. It uses a sophisticated multi-agent architecture built on LangGraph, with continuous learning through a memory and reflection system.

---

## Features

### Multi-Agent Analysis Pipeline

| Agent | Role |
|-------|------|
| **Discovery Agent** | Scans global exchanges (NASDAQ, NYSE, LSE, HKEX, BSE, NSE) for upcoming IPOs via SEC filings, exchange listings, and financial data providers |
| **Collection Agent** | Gathers financials, news, social sentiment, and alternative data from multiple sources |
| **Fundamental Analysis Agent** | Deep financial health analysis with peer comparisons, DCF valuation, and ratio analysis |
| **Market Analysis Agent** | TAM/SAM/SOM sizing, competitive positioning, market timing, and industry analysis |
| **Risk Analysis Agent** | 50+ risk factors across financial, market, operational, and regulatory domains with severity scoring |
| **Sentiment Analysis Agent** | Multi-source sentiment analysis with divergence detection across news, social media, and expert opinions |
| **Decision Support Agent** | Synthesizes all agent outputs into a final BUY/HOLD/SELL recommendation with position sizing |
| **Report Generation Agent** | Generates professional PDF/HTML investment research reports with executive summaries, valuation models, and risk heatmaps |
| **Memory Management Agent** | 9 memory types: short-term, long-term, vector, failure, success, knowledge, experience, best-practice, reflection |
| **Reflection Agent** | Continuous learning engine that compares predictions against actual outcomes and extracts lessons |

### Continuous Learning System

- **Failure Memory** — Records errors with root cause analysis to prevent recurrence
- **Success Memory** — Stores winning strategies with context for reuse
- **Reflection Engine** — Compares predictions vs actual outcomes, extracts lessons
- **Knowledge Base** — Verified financial knowledge with version control
- **Best Practices** — Proven methodologies tracked with success rates
- **Lessons Learned** — Structured Do/Don't patterns with confidence scores

### Professional Output

- Executive Summary with one-page investment thesis
- Detailed financial, valuation, market, risk, and sentiment analysis
- Bull/Bear cases with structured arguments and evidence
- Valuation models: DCF, Comparable Companies, Precedent Transactions
- Risk heatmaps with 50+ factor assessment
- Risk-adjusted position sizing guidance
- Monitoring plans with key metrics, red flags, and catalysts

### Frontend Application

The Next.js frontend provides a full-featured dashboard with:

- **Dashboard** — Overview of market activity, recent analyses, and system status
- **Upcoming IPOs** — Browse, search, and filter upcoming IPOs by exchange, sector, status, and date
- **Analysis** — Trigger and view comprehensive IPO analysis with agent-level breakdowns
- **Reports** — View and download generated investment research reports
- **Memory** — Browse and search across all memory types (short-term, long-term, vector, etc.)
- **Reflection** — View prediction outcomes, accuracy metrics, and improvement areas
- **Failures** — Track system errors with root cause analysis and resolution status
- **Successes** — Review successful strategies and reuse proven approaches
- **Knowledge** — Browse verified financial knowledge with version history
- **Chat** — Interactive AI assistant for querying IPO data and analysis
- **Settings** — Configure API keys, agent parameters, and system preferences
- **Dark/Light mode**, global search, notifications, and responsive layout

---

## Tech Stack

### Backend

| Technology | Purpose |
|------------|---------|
| **Python 3.12** | Runtime |
| **FastAPI** | Async REST API + WebSocket |
| **LangGraph / LangChain** | Multi-agent orchestration |
| **SQLAlchemy 2.0** | ORM |
| **Alembic** | Database migrations |
| **PostgreSQL 16 + pgvector** | Relational DB + vector search |
| **Redis 7** | Caching, Celery broker, real-time updates |
| **Celery** | Background task queue |
| **Prefect** | Workflow orchestration |
| **JWT** | Authentication (python-jose + passlib) |
| **OpenTelemetry** | Distributed tracing |
| **Prometheus** | Metrics collection |
| **Pydantic** | Validation & settings |

### Frontend

| Technology | Purpose |
|------------|---------|
| **Next.js 15** | React framework (SSR/SSG) |
| **React 18** | UI library |
| **TypeScript** | Type safety |
| **Tailwind CSS** | Styling |
| **Radix UI Primitives** | Accessible headless UI components |
| **TanStack React Query** | Server state management |
| **Zustand** | Client state management |
| **Recharts / Lightweight Charts** | Financial charting |
| **Socket.IO Client** | Real-time updates |
| **Zod** | Schema validation |
| **NextAuth** | Authentication |
| **Jest + Testing Library** | Testing |

### Infrastructure

| Service | Role |
|---------|------|
| **Docker Compose** | Local development orchestration |
| **Jaeger** | Distributed tracing |
| **Prometheus** | Metrics collection |
| **Grafana** | Metrics visualization & dashboards |
| **pgvector** | Vector similarity search |

---

## Project Structure

```
ipo-intelligence-agent/
├── backend/                          # Python FastAPI backend
│   ├── app/
│   │   ├── agents/                   # LangGraph AI agents
│   │   ├── application/              # Use cases (business logic)
│   │   ├── core/                     # Config, logging, tracing, metrics
│   │   ├── domain/                   # Domain models, enums, value objects
│   │   ├── infrastructure/           # DB, external APIs, cache, messaging
│   │   ├── memory/                   # Vector stores & memory management
│   │   ├── presentation/api/         # API routes (ipos, analysis, memory)
│   │   ├── repositories/            # Data access layer
│   │   ├── schemas/                  # Pydantic schemas
│   │   ├── services/                 # Business logic services
│   │   └── main.py                   # FastAPI application entry point
│   ├── alembic/                      # Database migrations
│   ├── tests/                        # Test suite
│   ├── pyproject.toml                # Python dependencies (Poetry)
│   ├── requirements.txt              # pip fallback dependencies
│   ├── alembic.ini                   # Alembic configuration
│   ├── Dockerfile                    # Dev Docker image
│   ├── Dockerfile.prod               # Production Docker image
│   └── .env.example                  # Environment template
├── frontend/                         # Next.js frontend
│   ├── src/
│   │   ├── app/                      # Next.js App Router pages
│   │   │   ├── dashboard/
│   │   │   ├── ipos/
│   │   │   ├── analysis/
│   │   │   ├── reports/
│   │   │   ├── memory/
│   │   │   ├── reflection/
│   │   │   ├── failures/
│   │   │   ├── successes/
│   │   │   ├── knowledge/
│   │   │   ├── chat/
│   │   │   └── settings/
│   │   ├── components/               # Shared UI components
│   │   │   ├── layout/               # Sidebar, Header, Layout
│   │   │   └── ui/                   # Button, Card, Tabs, Table, etc.
│   │   └── lib/                      # Utility functions
│   ├── package.json                  # Node dependencies
│   ├── package-lock.json             # npm lock file
│   ├── next.config.js                # Next.js configuration
│   ├── tailwind.config.js            # Tailwind CSS configuration
│   ├── tsconfig.json                 # TypeScript configuration
│   ├── Dockerfile                    # Dev Docker image
│   └── Dockerfile.prod               # Production Docker image
├── .devcontainer/
│   └── devcontainer.json             # VS Code Dev Container config
├── .vscode/
│   ├── tasks.json                    # Build/test/run tasks
│   └── launch.json                   # Debug configurations
├── monitoring/                       # Observability configs
│   ├── prometheus.yml                # Prometheus scrape config
│   └── grafana/                      # Grafana dashboards & datasources
├── scripts/                          # Utility scripts
├── docker-compose.yml                # Development services
├── docker-compose.prod.yml           # Production services
├── Makefile                          # Convenience commands
└── .env                              # Docker Compose environment variables
```

---

## Prerequisites

| Tool | Version | Required For |
|------|---------|--------------|
| **Docker Desktop** | 24+ | PostgreSQL, Redis, and all containerized services |
| **VS Code** | Latest | Development environment |
| **Dev Containers extension** | Latest | Optional — project dev container |
| **Python** | >=3.12, <3.13 | Backend (local development) |
| **Poetry** | 2.x | Backend dependency management |
| **Node.js** | 20.x | Frontend development |
| **npm** | 10.x | Frontend dependency management |

Verify your tools:

```powershell
docker --version
python --version
poetry --version
node --version
npm --version
```

### API Keys (Required)

At least one LLM provider API key is needed for the AI agents to function:

- [OpenAI API Key](https://platform.openai.com/api-keys)
- [Anthropic API Key](https://console.anthropic.com/)
- [Google AI API Key](https://aistudio.google.com/apikey)

Optional but recommended for enhanced data:

- [Alpha Vantage API Key](https://www.alphavantage.co/support/#api-key)

---

## Quick Start (Docker Compose — All Services)

This runs everything (PostgreSQL, Redis, Backend, Frontend, Celery, monitoring) in Docker containers.

### 1. Configure Environment

```powershell
# Environment files already exist; verify or create from examples
if (-not (Test-Path backend\.env)) { Copy-Item backend\.env.example backend\.env }
if (-not (Test-Path frontend\.env.local)) { Copy-Item frontend\.env.example frontend\.env.local }
```

Edit `backend/.env` and set at least one LLM API key.

### 2. Start All Services

```powershell
docker-compose up -d
```

This starts: `postgres`, `redis`, `backend`, `frontend`, `celery-worker`, `celery-beat`, `prefect`, `jaeger`, `prometheus`, `grafana`.

### 3. Verify

| URL | Service |
|-----|---------|
| http://localhost:3000 | Frontend application |
| http://localhost:8000/docs | Backend Swagger API docs |
| http://localhost:8000/health | Backend health check |
| http://localhost:8000/ready | Backend readiness check |
| http://localhost:3001 | Grafana (admin/admin) |
| http://localhost:9090 | Prometheus |
| http://localhost:16686 | Jaeger tracing |
| http://localhost:4200 | Prefect server |

---

## Development Setup (Hybrid — Docker Services + Local Code)

This runs PostgreSQL + Redis in Docker while you develop the backend and frontend locally with hot-reload.

### Step 1 — Start Infrastructure

**Terminal 1 — Infrastructure**
Directory: `E:\PROJECT\MARQUEE\ipo-intelligence-agent`

```powershell
docker-compose up -d postgres redis
```

Expected: PostgreSQL on `localhost:5432`, Redis on `localhost:6379`.

Verify:
```powershell
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Step 2 — Configure Backend Environment

```powershell
if (-not (Test-Path backend\.env)) { Copy-Item backend\.env.example backend\.env }
```

Edit `backend/.env` to set your API keys. The defaults point to `localhost` for PostgreSQL and Redis, which matches the Docker containers.

### Step 3 — Install Backend Dependencies

**Terminal 2 — Backend**
Directory: `E:\PROJECT\MARQUEE\ipo-intelligence-agent\backend`

```powershell
poetry install --with dev,test
```

This installs all production, dev, and test dependencies from `pyproject.toml`.

> If Poetry is not installed: `pip install poetry`
>
> If Poetry installation fails, use pip as fallback:
> ```powershell
> pip install -r requirements.txt
> pip install -e .
> ```

### Step 4 — Run Database Migrations

**Terminal 2 — Backend**
Directory: `E:\PROJECT\MARQUEE\ipo-intelligence-agent\backend`

```powershell
poetry run alembic upgrade head
```

Expected: Migration logs or "No migrations to apply".

### Step 5 — Start Backend

**Terminal 2 — Backend** (leave running)
Directory: `E:\PROJECT\MARQUEE\ipo-intelligence-agent\backend`

```powershell
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Step 6 — Verify Backend Health

**Terminal 3 — Verification**
Directory: any

```powershell
curl.exe http://localhost:8000/health
```

Expected:
```json
{"status":"healthy","version":"1.0.0"}
```

Also open http://localhost:8000/docs in a browser — you should see the Swagger UI.

### Step 7 — Configure Frontend Environment

```powershell
if (-not (Test-Path frontend\.env.local)) { Copy-Item frontend\.env.example frontend\.env.local }
```

The defaults already point to `http://localhost:8000` for the backend API and `ws://localhost:8000` for WebSocket.

### Step 8 — Install Frontend Dependencies

**Terminal 4 — Frontend**
Directory: `E:\PROJECT\MARQUEE\ipo-intelligence-agent\frontend`

```powershell
npm install
```

### Step 9 — Start Frontend

**Terminal 4 — Frontend** (leave running)
Directory: `E:\PROJECT\MARQUEE\ipo-intelligence-agent\frontend`

```powershell
npm run dev
```

Expected:
```
▲ Next.js 15.x.x
- Local: http://localhost:3000
```

### Step 10 — Final Verification

Open http://localhost:3000 in your browser. The frontend proxies `/api/*` requests to `http://localhost:8000` (configured in `next.config.js`).

---

## Using the VS Code Dev Container

The project includes a `.devcontainer/devcontainer.json` that:

1. Uses the existing `docker-compose.yml`
2. Attaches VS Code to the `backend` container
3. Automatically starts `postgres`, `redis`, `frontend`, and `backend` services
4. Pre-installs recommended VS Code extensions (Python, Ruff, ESLint, Tailwind CSS, Docker)
5. The workspace is at `/app` inside the backend container

**To use it:**

1. Ensure Docker Desktop is running
2. In VS Code, open the command palette (`Ctrl+Shift+P`)
3. Run: **Dev Containers: Reopen in Container**
4. Wait for the build to complete (first time may take several minutes)
5. VS Code reopens inside the backend container with all services running

> **Important:** The project Dev Container replaces any generic Python container you may have created. It is configured specifically for this project and includes all required services.

---

## VS Code Tasks & Launch Configurations

The `.vscode/tasks.json` provides pre-configured tasks:

| Task | Description |
|------|-------------|
| `Backend: Install Dependencies` | `poetry install --with dev,test` |
| `Backend: Start FastAPI` | `poetry run uvicorn ... --reload` |
| `Backend: Run Migrations` | `poetry run alembic upgrade head` |
| `Backend: Run Tests` | `poetry run pytest` |
| `Backend: Lint` | `ruff check . && mypy app` |
| `Frontend: Install Dependencies` | `npm ci` |
| `Frontend: Start Dev Server` | `npm run dev` |
| `Frontend: Run Tests` | `npm run test -- --coverage` |
| `Docker: Start All (Dev)` | `docker-compose up -d` |

The `.vscode/launch.json` provides debug configurations:

- **Backend: FastAPI (uvicorn)** — Debug the backend with hot-reload
- **Backend: Celery Worker** — Debug the Celery worker
- **Backend: Alembic Upgrade** — Run migrations from the debugger
- **Frontend: Next.js Dev Server** — Debug the frontend
- **Full Stack: Backend + Frontend** — Debug both simultaneously

---

## API Reference

### Health

```bash
GET  /health          # Liveness check
GET  /ready           # Readiness check (includes database)
```

### IPOs

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/ipos/upcoming` | List upcoming IPOs (with filters) |
| GET | `/api/v1/ipos/recent` | Recently listed IPOs |
| GET | `/api/v1/ipos/search` | Search by symbol or company name |
| GET | `/api/v1/ipos/{symbol}` | Get IPO details by symbol |
| POST | `/api/v1/ipos` | Create a new IPO entry |
| PATCH | `/api/v1/ipos/{symbol}/status` | Update IPO status |
| POST | `/api/v1/ipos/discover` | Run discovery from external sources |
| GET | `/api/v1/ipos/companies/{symbol}` | Get company profile |
| POST | `/api/v1/ipos/companies` | Create company profile |
| GET | `/api/v1/ipos/companies/sector/{sector}` | List companies by sector |
| GET | `/api/v1/ipos/companies/industry/{industry}` | List companies by industry |

### Analysis

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/analysis/analyze` | Start full analysis pipeline |
| POST | `/api/v1/analysis/collect` | Collect IPO data only |
| POST | `/api/v1/analysis/report` | Generate investment report |
| POST | `/api/v1/analysis/reflection` | Run reflection cycle |
| POST | `/api/v1/analysis/verify-outcome` | Verify a prediction outcome |
| GET | `/api/v1/analysis/results/{symbol}` | Get latest analysis result |
| GET | `/api/v1/analysis/history/{symbol}` | Get analysis history |
| GET | `/api/v1/analysis/jobs` | List pending jobs |
| GET | `/api/v1/analysis/jobs/{job_id}` | Get job status |
| GET | `/api/v1/analysis/jobs/stats` | Get job statistics |

### Memory & Reflection

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/memory/store` | Store a memory entry |
| POST | `/api/v1/memory/search` | Semantic memory search |
| GET | `/api/v1/memory/recent` | Get recent memory entries |
| POST | `/api/v1/memory/cleanup` | Clean up old memory entries |
| POST | `/api/v1/memory/failures` | Record a failure |
| POST | `/api/v1/memory/failures/search` | Find similar failures |
| GET | `/api/v1/memory/failures/category/{category}` | Get failures by category |
| POST | `/api/v1/memory/failures/{id}/resolve` | Mark failure resolved |
| GET | `/api/v1/memory/failures/unresolved` | Get unresolved failures |
| POST | `/api/v1/memory/successes` | Record a successful strategy |
| POST | `/api/v1/memory/successes/search` | Find successful strategies |
| POST | `/api/v1/memory/successes/{id}/reuse` | Increment reuse count |
| POST | `/api/v1/memory/knowledge` | Store knowledge concept |
| GET | `/api/v1/memory/knowledge/concept/{concept}` | Get knowledge by concept |
| POST | `/api/v1/memory/knowledge/search` | Search knowledge concepts |
| GET | `/api/v1/memory/knowledge/domain/{domain}` | Get knowledge by domain |
| POST | `/api/v1/memory/best-practices` | Store a best practice |
| POST | `/api/v1/memory/best-practices/applicable` | Get applicable practices |
| POST | `/api/v1/memory/reflections` | Record a reflection |
| GET | `/api/v1/memory/reflections/prediction/{id}` | Get reflection by prediction |
| GET | `/api/v1/memory/reflections/ipo/{symbol}` | Get reflections by IPO |
| GET | `/api/v1/memory/reflections/unprocessed` | Get unprocessed reflections |
| POST | `/api/v1/memory/lessons` | Save a lesson |
| GET | `/api/v1/memory/lessons/{id}` | Get lesson by ID |
| GET | `/api/v1/memory/lessons/type/{type}` | Get lessons by type |
| POST | `/api/v1/memory/lessons/applicable` | Get applicable lessons |
| POST | `/api/v1/memory/lessons/search` | Search lessons |

---

## Environment Variables

### Backend (`backend/.env`)

See `backend/.env.example` for the complete list of all 177 variables. Key groups:

| Group | Key Variables |
|-------|---------------|
| **LLM API Keys** | `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY` (at least one required) |
| **Server** | `HOST=0.0.0.0`, `PORT=8000`, `WORKERS=4` |
| **Database** | `DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ipo_intelligence` |
| **Redis** | `REDIS_URL=redis://localhost:6379/0` |
| **Celery** | `CELERY_BROKER_URL=redis://localhost:6379/1`, `CELERY_RESULT_BACKEND=redis://localhost:6379/2` |
| **Security** | `SECRET_KEY` (generate with `openssl rand -hex 32`), `CORS_ORIGINS=["http://localhost:3000"]` |
| **External Data** | `ALPHA_VANTAGE_API_KEY`, `TWITTER_API_KEY`, `REDDIT_CLIENT_ID`, etc. |
| **Monitoring** | `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317` |

### Frontend (`frontend/.env.local`)

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API URL for client-side calls |
| `NEXT_PUBLIC_WS_URL` | `ws://localhost:8000` | WebSocket URL for real-time updates |

### Docker Compose Root (`.env`)

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Passed to backend container |
| `ANTHROPIC_API_KEY` | Passed to backend container |
| `GOOGLE_API_KEY` | Passed to backend container |
| `ALPHA_VANTAGE_API_KEY` | Passed to backend container |
| `SECRET_KEY` | Application secret key |

---

## Makefile Commands

```bash
make dev              # docker-compose up -d
make dev-backend      # Start backend services only
make dev-frontend     # Start frontend only
make prod             # docker-compose -f docker-compose.prod.yml up -d
make test             # Run all tests
make migrate          # Run database migrations
make logs             # Tail all logs
make shell            # Open backend shell
make clean            # docker-compose down -v
make monitor          # Show service URLs
```

---

## Testing

```bash
# Backend tests
cd backend && poetry run pytest -v --cov=app --cov-report=html

# Frontend tests
cd frontend && npm run test -- --coverage
```

Coverage targets: Backend >80%, Frontend >70%.

---

## Troubleshooting

| Problem | Likely Cause | Solution |
|---------|--------------|----------|
| Docker: "Cannot connect to the Docker daemon" | Docker Desktop not running | Start Docker Desktop from Start menu |
| Dev Container build fails | Insufficient Docker resources | Allocate 8+ GB RAM in Docker Desktop Settings → Resources |
| `alembic upgrade head` fails — database connection | PostgreSQL not ready | Wait 10s, retry. Check `docker ps` for `ipo-postgres` healthy status |
| `poetry install` fails — dependency resolution | Python version mismatch | Ensure `python --version` is 3.12.x |
| `poetry install` fails — no matching distribution | Missing system build tools | Install Microsoft C++ Build Tools from visualstudio.microsoft.com |
| `npm install` fails | Node.js version mismatch | Ensure `node --version` is 18+ (20 recommended) |
| Backend startup fails — "address already in use" | Port 8000 occupied | `netstat -ano \| Select-String :8000` then `taskkill /PID <PID> /F` |
| Frontend shows blank page or API errors | Backend not running | Verify `curl.exe http://localhost:8000/health` returns 200 |
| CORS errors in frontend | Backend CORS config | Check `CORS_ORIGINS` in `backend/.env` includes `http://localhost:3000` |
| AI agents return no results | Missing API keys | Verify `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is set in `backend/.env` |
| Frontend build fails with type errors | TypeScript strict mode | The project has `ignoreBuildErrors: true` in `next.config.js` — run `npm run dev` instead of `build` |

---

## Security Notes

- The `backend/.env` and `.env` files contain API keys and secrets. **Never commit these to version control.**
- The `.gitignore` already excludes `.env` and `.env.local` files.
- JWT tokens are used for API authentication. Change `SECRET_KEY` in production.
- Rate limiting: 100 requests/minute by default.
- CORS is configured to allow only the frontend origin.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
