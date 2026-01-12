.PHONY: dev api web web-build test fmt lint

PROJECT ?= cloudsentinel

dev:
	docker compose up --build api

api:
	$(MAKE) dev

web:
	cd web && npm ci && npm run dev

web-build:
	cd web && npm ci && NEXT_PUBLIC_BASE_PATH="/$(PROJECT)" npm run build

test:
	docker compose run --rm api pytest -q

fmt:
	docker compose run --rm api ruff format .
	docker compose run --rm api ruff check --fix .

lint:
	docker compose run --rm api ruff check .
