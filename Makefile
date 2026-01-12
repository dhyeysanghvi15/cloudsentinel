.PHONY: dev api web web-build test fmt lint

PROJECT ?= cloudsentinel

dev:
\tcd api && python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

api:
\t$(MAKE) dev

web:
\tcd web && npm install && npm run dev

web-build:
\tcd web && npm install && NEXT_PUBLIC_BASE_PATH="/$(PROJECT)" npm run build

test:
\tcd api && python3 -m pytest -q

fmt:
\tcd api && python3 -m ruff format .
\tcd api && python3 -m ruff check --fix .

lint:
\tcd api && python3 -m ruff check .
