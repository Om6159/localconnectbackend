# LocalConnect — Production-Ready FastAPI Backend

Official Tagline: **Need → Match → Connect**

The complete, production-ready backend for **LocalConnect**, built with Python 3.12+, FastAPI, Pydantic v2, async SQLAlchemy 2.0, asyncpg, PostGIS, and Alembic.

---

## 📌 Features & Highlights

- **Need → Match → Connect Workflow**: Complete implementation of natural language requirement parsing, deterministic provider candidate filtering and ranking, and dual-confirmation connection lifecycles.
- **AI Requirement Parsing ("UNDERSTAND")**: Extracts structured JSON (categories, services, skills, budget, radius, availability) using LLMs (when `AI_API_KEY` is configured) or a robust deterministic English/Hinglish fallback parser.
- **Deterministic Matching Engine ("MATCH")**: Spatial PostGIS radius filtering (`ST_DWithin`, `ST_Distance`), multi-factor weighted scoring (Skill 30%, Distance 20%, Budget 15%, Availability 15%, Trust 10%, Rating 10%), and human-readable match explanations.
- **Canonical Trust System ("TRUST")**: Reusable trust score calculator adhering strictly to the schema weights: Phone (15%), Identity (10%), Profile (15%), Rating (20%), Completion (15%), Community Recommendation (10%), Response Rate (15%).
- **Dual-Confirmation Completion Gate ("CONNECT")**: Prevents unilateral job completion. Job status reaches `completed` only when both requester and provider have confirmed completion.
- **Community Recommendations & Saved Providers**: Verifies completed connections before allowing user recommendations and bookmarks.
- **Supabase & PostGIS Ready**: Native support for PostgreSQL with PostGIS geography point indexing.

---

## 🛠️ Technology Stack

- **Framework**: FastAPI (Async)
- **Language**: Python 3.12+
- **Validation**: Pydantic v2 & Pydantic Settings
- **ORM / Database**: SQLAlchemy 2.0 (asyncio) & `asyncpg`
- **Spatial DB**: PostgreSQL with PostGIS extension (`GeoAlchemy2`)
- **Database Migrations**: Alembic
- **Authentication**: JWT (`PyJWT`) & Argon2 password hashing (`pwdlib`)
- **HTTP Client**: `httpx`
- **Testing**: Pytest & `pytest-asyncio`

---

## 📂 Folder Structure

```text
Backend/
├── app/
│   ├── main.py                    # FastAPI App Entrypoint
│   ├── core/                      # Config, Security (JWT/Argon2), DB engine, Exceptions
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── database.py
│   │   └── exceptions.py
│   ├── models/                    # SQLAlchemy 2.0 Async Models with PostGIS
│   │   ├── enums.py
│   │   ├── profile.py
│   │   ├── category.py
│   │   ├── service.py
│   │   ├── provider.py
│   │   ├── provider_service.py
│   │   ├── location.py
│   │   ├── availability.py
│   │   ├── request.py
│   │   ├── match.py
│   │   ├── connection.py
│   │   ├── review.py
│   │   ├── trust.py
│   │   ├── recommendation.py
│   │   ├── saved_provider.py
│   │   └── notification.py
│   ├── schemas/                   # Pydantic v2 Request/Response DTOs
│   ├── api/                       # REST API Routes
│   │   ├── deps.py
│   │   └── v1/                    # Auth, Providers, Requests, Matches, Connections, etc.
│   ├── services/                  # Business Logic Services
│   │   ├── ai_service.py          # AI requirement parser & fallback
│   │   ├── matching_service.py    # Deterministic matching engine
│   │   └── trust_service.py       # Canonical trust calculator
│   └── utils/
│       ├── seed.py                # Hackathon sample seed script
│       └── geo.py                 # Haversine & spatial utilities
├── alembic/                       # Database migrations
│   ├── env.py
│   └── versions/
├── tests/                         # Pytest test suite
├── .env.example
├── alembic.ini
├── requirements.txt
└── README.md
```

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/localconnect
JWT_SECRET_KEY=localconnect_super_secret_jwt_key_change_in_production_32bytes
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AI Provider API Key (Optional)
AI_API_KEY=

PROJECT_NAME=LocalConnect API
VERSION=1.0.0
ENVIRONMENT=development
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000","http://127.0.0.1:5173","http://127.0.0.1:3000"]
```

---

## 🚀 Quickstart & Local Setup

### 1. Environment Setup

```bash
# Navigate to Backend folder
cd Backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database & Migrations

```bash
# Run database migrations
alembic upgrade head

# Seed realistic sample data
python -m app.utils.seed
```

### 3. Run Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive documentation will be available at:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 🧪 Running Automated Tests

```bash
pytest
```

---

## 🌐 Supabase & Deployment

### Database (Supabase PostgreSQL)
1. Enable **PostGIS** extension in Supabase SQL Editor (`CREATE EXTENSION IF NOT EXISTS postgis;`).
2. Copy the Connection String from Supabase Database settings (pooled or direct).
3. Set `DATABASE_URL` in environment variables using `postgresql+asyncpg://`.

### Deployment (Render / Railway)
- **Build Command**: `pip install -r requirements.txt && alembic upgrade head`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

---

## 📄 License

LocalConnect Hackathon Project — All rights reserved.
