# IPO Intelligence Agent Backend

Autonomous multi-agent AI system for IPO investment intelligence.

## Requirements

- Python 3.12+
- PostgreSQL 15+
- Redis 7+
- Poetry 2.x

## Quick Start

```bash
# Install dependencies
poetry install -E dev -E test

# Set up environment
cp .env.example .env
# Edit .env with your API keys and database credentials

# Run database migrations
poetry run alembic upgrade head

# Start development server
poetry run uvicorn app.main:app --reload
```

## Project Structure

```
backend/
├── app/                    # Main application package
│   ├── agents/             # AI agents (LangGraph)
│   ├── application/        # Application layer (use cases)
│   ├── core/               # Core configuration & utilities
│   ├── domain/             # Domain models & entities
│   ├── infrastructure/     # External services (DB, APIs, cache)
│   ├── memory/             # Vector stores & memory systems
│   ├── presentation/       # API routes & WebSocket handlers
│   ├── reflection/         # Self-reflection & evaluation
│   ├── repositories/       # Data access layer
│   ├── schemas/            # Pydantic schemas
│   └── services/           # Business logic services
├── alembic/                # Database migrations
│   ├── env.py              # Alembic environment
│   └── versions/           # Migration scripts
├── tests/                  # Test suite
├── pyproject.toml          # Project configuration
├── alembic.ini             # Alembic configuration
├── .env                    # Environment variables (local)
└── .env.example            # Environment template
```

## Development

```bash
# Run tests
poetry run pytest

# Run linting
poetry run ruff check .
poetry run mypy app

# Format code
poetry run black .
poetry run isort .
```

## Environment Variables

See `.env.example` for all required variables:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - JWT secret (generate with `openssl rand -hex 32`)
- API keys for OpenAI, Anthropic, Google, etc.

## Docker

```bash
# Development
docker-compose -f docker-compose.yml up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

## License

Proprietary - All rights reserved.