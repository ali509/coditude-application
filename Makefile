COMPOSE := docker compose

.PHONY: backend-test frontend-check check compose-config container-build codedeploy-bundles up down logs ps clean

backend-test:
	cd apps/backend && .venv/bin/python -m pytest -v

frontend-check:
	cd apps/frontend && npm run lint && npm run build

check: backend-test frontend-check

compose-config:
	$(COMPOSE) --env-file .env.example config --quiet

container-build:
	docker build --tag coditude-backend:local apps/backend
	docker build --tag coditude-frontend:local apps/frontend

codedeploy-bundles:
	./scripts/build-codedeploy-bundles.sh

up:
	$(COMPOSE) up --build --detach

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs --follow

ps:
	$(COMPOSE) ps

clean:
	$(COMPOSE) down --volumes --remove-orphans
