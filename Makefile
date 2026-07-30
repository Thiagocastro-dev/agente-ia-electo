.PHONY: test test-infra-up test-infra-down test-infra-logs

test:
	uv run pytest

test-infra-up:
	docker compose -f docker-compose.test.yml --env-file .env.test up -d

test-infra-down:
	docker compose -f docker-compose.test.yml --env-file .env.test down

test-infra-logs:
	docker compose -f docker-compose.test.yml logs -f
