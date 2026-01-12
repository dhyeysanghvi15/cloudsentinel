.PHONY: dev api web test fmt lint deploy-dev deploy-web start-dev stop-dev destroy-dev tf-init tf-apply tf-destroy

PROJECT ?= cloudsentinel
ENV ?= dev

dev:
\tdocker compose up --build

api:
\tdocker compose up --build api dynamodb-local

web:
\tcd web && npm install && npm run dev

test:
\tcd api && python3 -m pytest -q

fmt:
\tcd api && python3 -m ruff format .
\tcd api && python3 -m ruff check --fix .

lint:
\tcd api && python3 -m ruff check .

tf-init:
\tcd infra/terraform && terraform init

tf-apply:
\tcd infra/terraform && terraform apply

tf-destroy:
\tcd infra/terraform && terraform destroy

deploy-dev:
\t./scripts/deploy-dev.sh

deploy-web:
\t@echo "Usage: make deploy-web API_BASE_URL=http://<api-ip>:8000"
\t./scripts/deploy-web.sh "$(API_BASE_URL)"

start-dev:
\t./scripts/ecs-start.sh

stop-dev:
\t./scripts/ecs-stop.sh

destroy-dev:
\t./scripts/destroy-dev.sh
