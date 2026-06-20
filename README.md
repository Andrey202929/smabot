# ICT SMART MONEY AI SIGNAL BOT

This repository contains a FastAPI-based scanner that finds ICT-style signals (body-based Fair Value Gaps and Order Blocks), scores them with a simple AI scoring engine, stores signals in PostgreSQL, deduplicates with Redis, and sends notifications to Telegram.

Quick start (using docker-compose):

1. Copy .env.example -> .env and fill TELEGRAM_TOKEN and TELEGRAM_CHAT_ID
2. docker-compose up --build
3. FastAPI will be available on http://localhost:8000
4. Endpoints: /signals, /stats, /performance, /winrate

Secrets (GitHub Actions / production):
- TELEGRAM_TOKEN
- TELEGRAM_CHAT_ID
- DATABASE_URL (if not using docker-compose)
- REDIS_URL

Notes:
- Only signals with confidence >= MIN_CONFIDENCE (default 75) are sent to Telegram.
- Duplicates are prevented using a Redis key + unique DB fingerprint.
- Order Block detector is a simple implementation; refine thresholds to your strategy.
