include .env
export


services:
	docker-compose -f docker-compose.services.yml up

makemigrations:
	PYTHONPATH=. alembic revision -m "${m}" --autogenerate

migrate:
	PYTHONPATH=. alembic upgrade head

downgrade:
	PYTHONPATH=. alembic downgrade head-1

dev:
	uvicorn main:app --host 0.0.0.0 --port 80 --reload

format:
	chmod +x ./.github/lint.sh
	./.github/lint.sh format

run_tests:
	pytest -v -s --color=yes --log-level=INFO .

mypy:
	chmod +x ./.github/lint.sh
	./.github/lint.sh check-mypy

lint:
	chmod +x ./.github/lint.sh
	./.github/lint.sh check-isort
	./.github/lint.sh check-black
	./.github/lint.sh check-flake8
	./.github/lint.sh check-mypy
