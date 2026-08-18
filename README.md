# AI Ride Booking System

Production-oriented FastAPI backend for an AI-enabled ride booking platform.

## Implemented Backend Surface

- FastAPI application factory with health and readiness checks
- PostgreSQL configuration through SQLAlchemy 2.0
- Alembic migrations
- Redis integration
- JWT authentication with refresh token rotation
- Role-based authorization for `customer`, `driver`, and `admin`
- Driver registration, vehicle registration, online/offline status
- Customer profile and ride history
- Ride booking, cancellation, start, completion
- Driver matching by nearest approved online driver
- Fare calculation
- Payment creation
- Ratings and reviews
- Admin user listing and driver/vehicle approval
- WebSocket ride tracking endpoint
- AI module with OpenAI/Claude provider abstraction
- OpenAI embeddings, ChromaDB vector store, RAG service, Redis conversation memory
- AI booking assistant, customer support, and trip summary endpoints

## Run Locally

```bash
python -m pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## Run With Docker

```bash
docker compose up --build
```

## Checks

```bash
python -m compileall app tests alembic
python -m pytest -q tests/unit
```

## Useful URLs

- Health: `GET /health`
- Readiness: `GET /ready`
- Swagger: `/docs`

## Notes

Set real values in `.env` for `JWT_SECRET_KEY`, database credentials, Redis, OpenAI, Anthropic, and ChromaDB before production use.
