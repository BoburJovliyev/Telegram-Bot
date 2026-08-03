# 🚀 Telegram Invite Tracker Bot

> An enterprise-grade Telegram bot for tracking group invitations, built with Aiogram 3.x, PostgreSQL, Redis, and clean architecture principles.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Database Schema](#-database-schema)
- [Project Structure](#-project-structure)
- [Commands](#-commands)
- [Development](#-development)
- [Deployment](#-deployment)
- [Contributing](#-contributing)

---

## ✨ Features

| Feature | Description |
|---|---|
| **Invite Attribution** | Tracks exactly who invited whom using invite links, admin additions, and join requests |
| **Leaderboard** | Ranked list of top inviters per group with active vs. total counts |
| **Daily Reports** | Pre-aggregated statistics with join method breakdowns and retention rates |
| **Export** | Downloadable CSV and Excel reports for admins |
| **RBAC** | Role-based access control synced with Telegram's admin system |
| **Idempotency** | Race-condition-safe processing of concurrent Telegram events |
| **Rate Limiting** | Redis-backed token bucket throttling to prevent spam |
| **Structured Logging** | JSON-formatted logs with Telegram context (user_id, chat_id) |
| **Background Jobs** | APScheduler for periodic stats aggregation |
| **Docker Ready** | Multi-stage Dockerfile + docker-compose for one-command deployment |
| **CI/CD** | GitHub Actions pipeline with lint, test, build, and SSH deploy |

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────┐
│                  Telegram API                     │
└──────────────────────┬───────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────┐
│              Aiogram Dispatcher                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │ Logging  │→│Throttling│→│   Database MW    │  │
│  │Middleware│ │Middleware│ │(Session + UoW +  │  │
│  │          │ │ (Redis)  │ │   Services)      │  │
│  └──────────┘ └──────────┘ └──────────────────┘  │
└──────────────────────┬───────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────┐
│                   Handlers                        │
│  ┌─────────────┐ ┌──────────┐ ┌───────────────┐  │
│  │chat_member  │ │my_chat   │ │  commands     │  │
│  │(join/leave) │ │member    │ │  (/start etc) │  │
│  └──────┬──────┘ └────┬─────┘ └───────────────┘  │
└─────────┼─────────────┼─────────────────────────┘
          │             │
          ▼             ▼
┌──────────────────────────────────────────────────┐
│                   Services                        │
│  ┌──────────────┐ ┌──────────┐ ┌──────────────┐  │
│  │InviteTracking│ │  Group   │ │    Admin     │  │
│  │   Service    │ │ Service  │ │   Service    │  │
│  └──────┬───────┘ └────┬─────┘ └──────────────┘  │
└─────────┼──────────────┼────────────────────────┘
          │              │
          ▼              ▼
┌──────────────────────────────────────────────────┐
│              Unit of Work                         │
│  ┌────────────────────────────────────────────┐   │
│  │           Repositories                     │   │
│  │  BotUser │ Group │ Member │ InviteRecord  │   │
│  │  InviteLink │ Admin │ Event │ DailyStats  │   │
│  └──────────────────────┬─────────────────────┘   │
└─────────────────────────┼────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────┐
│          PostgreSQL (asyncpg) + Redis             │
└──────────────────────────────────────────────────┘
```

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Framework | Aiogram 3.x |
| Language | Python 3.13+ |
| Database | PostgreSQL 16 + SQLAlchemy 2.x Async |
| Cache | Redis 7 |
| Migrations | Alembic |
| Scheduler | APScheduler 4.x |
| Logging | structlog (JSON) |
| Metrics | Prometheus Client |
| Exports | openpyxl (Excel), csv, reportlab (PDF) |
| Config | Pydantic Settings v2 |
| Testing | pytest + pytest-asyncio |
| CI/CD | GitHub Actions |
| Container | Docker + Docker Compose |

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

### 1. Clone the repository

```bash
git clone https://github.com/your-repo/telegram-invite-tracker.git
cd telegram-invite-tracker
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your BOT_TOKEN and BOT_OWNER_ID
```

### 3. Start all services

```bash
make up
# or
docker compose up -d --build
```

The bot will automatically:
1. Wait for PostgreSQL and Redis to be healthy
2. Run Alembic migrations
3. Start processing Telegram updates

### 4. Add the bot to your group

1. Add the bot to a Telegram group
2. Promote it to administrator with **"Invite Users"** permission
3. The bot will start tracking invites automatically

---

## ⚙ Configuration

All configuration is managed via environment variables. See [`.env.example`](.env.example) for the full list.

| Variable | Required | Default | Description |
|---|---|---|---|
| `BOT_TOKEN` | ✅ | — | Telegram Bot API token |
| `BOT_OWNER_ID` | ✅ | — | Your Telegram user ID |
| `DATABASE_URL` | ❌ | `postgresql+asyncpg://...` | PostgreSQL connection string |
| `REDIS_URL` | ❌ | `redis://localhost:6379/0` | Redis connection string |
| `LOG_LEVEL` | ❌ | `INFO` | Logging level |
| `ENVIRONMENT` | ❌ | `development` | Environment name |

---

## 🗃 Database Schema

The database consists of **10 tables** designed for analytical workloads:

| Table | Purpose |
|---|---|
| `bot_users` | Global user registry |
| `groups` | Registered groups |
| `group_settings` | Per-group configuration |
| `group_admins` | Admin tracking with permissions |
| `invite_links` | Tracked invite link metadata |
| `members` | Per-group membership with invite counters |
| `invite_records` | Core attribution (who invited whom) |
| `member_events` | Immutable audit log |
| `daily_stats` | Pre-aggregated daily statistics |
| `notifications` | Delivery log with retries |

---

## 📁 Project Structure

```
src/bot/
├── __init__.py
├── __main__.py           # Entry point
├── app.py                # Application factory
├── config/               # Pydantic settings
├── core/                 # Enums, types, constants, exceptions
├── database/             # Engine, session, base model
├── models/               # SQLAlchemy ORM models (10)
├── repositories/         # Data access layer + Unit of Work
├── services/             # Business logic layer
├── middlewares/           # DB injection, throttling, logging
├── handlers/             # Telegram update handlers
├── routers/              # Aiogram router tree
├── filters/              # Custom filters
├── keyboards/            # Inline keyboards & callbacks
├── analytics/            # Statistics engine
├── reports/              # CSV/Excel exporters & formatters
├── jobs/                 # APScheduler background tasks
├── security/             # Rate limiting, RBAC
├── logging/              # Structlog processors
├── locales/              # i18n translations
├── states/               # FSM states
└── utils/                # Helpers
```

---

## 📟 Commands

| Command | Description |
|---|---|
| `/start` | Start the bot / welcome message |
| `/help` | Show available commands |
| `/stats` | Show your invite statistics |
| `/leaderboard` | Show the top inviters |

---

## 🧪 Development

### Local setup (without Docker)

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -e ".[dev]"

# Run the bot
python -m bot
```

### Run tests

```bash
make test
# or
pytest tests/ -v
```

### Lint & Format

```bash
make lint      # Run Ruff
make format    # Run Black + Ruff fix
make typecheck # Run Mypy
```

---

## 🚢 Deployment

### Docker Compose (recommended)

```bash
make up      # Start all services
make down    # Stop all services
make logs    # Tail bot logs
make migrate # Run database migrations
```

### CI/CD

The project includes a GitHub Actions pipeline (`.github/workflows/deploy.yml`) that:
1. **Lints** code with Ruff, Black, and Mypy
2. **Tests** against a real PostgreSQL + Redis service
3. **Builds** the Docker image
4. **Deploys** via SSH to your production server

Configure these GitHub Secrets:
- `DEPLOY_HOST` — Server IP/hostname
- `DEPLOY_USER` — SSH username
- `DEPLOY_KEY` — SSH private key

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
