**PR Description: Add ICT Smart Money AI Signal Bot Project**

### Overview
This PR introduces the initial implementation of the ICT Smart Money AI Signal Bot to the repository. The project provides automated detection of trading opportunities based on Smart Money Concepts using an AI-driven signal engine.

### Key Features Added
- **Body-based FVG Detector**: Identifies fair value gaps based on candle body analysis.
- **Order Block Detector**: Detects high-probability order blocks for trade setups.
- **Scanner & Scoring Engine**: Continuously analyzes market data and scores potential signals.
- **Async FastAPI App**: Exposes API endpoints for bot operations and integrations.
- **Database Integration**:
  - **Alembic Migrations**: Handles database schema changes.
  - **PostgreSQL Models**: Persistent storage for signals and configurations.
- **Infrastructure**:
  - **Dockerfile & docker-compose**: Containerized deployment and service orchestration.
  - **Redis Dedupe**: Ensures unique signal notifications.
- **Notification**: Telegram integration for real-time signal alerts.

### Required Environment Variables/Secrets
- `DATABASE_URL` or individual Postgres vars (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT`)
- `REDIS_URL`
- `TELEGRAM_TOKEN`
- `TELEGRAM_CHAT_ID`
- (Optional) `BINANCE_API_KEY`, `BINANCE_API_SECRET`, `BYBIT_API_KEY`, `BYBIT_API_SECRET`

### Quick Start: Docker Compose
```bash
# Copy example env and fill TELEGRAM credentials
cp .env.example .env
# Build and run services
docker-compose up --build
# (Optional) Apply DB migrations
docker-compose exec app alembic upgrade head
```

### Testing Instructions

**Run Unit Tests**
```bash
docker-compose exec app pytest -q
```

**Manual Signal Scan**
```bash
# Run a one-off scan inside the app container
docker-compose exec app python -c "import asyncio; from app.scanner import run_scan_once; print(asyncio.run(run_scan_once()))"
```

---

Please review and suggest any adjustments. The README contains deployment and environment details.
