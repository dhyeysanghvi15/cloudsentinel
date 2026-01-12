.PHONY: dev api web web-build test fmt lint

PROJECT ?= cloudsentinel

dev:
\tdocker compose up --build api

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
