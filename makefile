.PHONY: install run format lint typecheck check

install:
	uv sync

run:
	uv run python src/main.py

format:
	uv run ruff check . --fix
	uv run ruff format .

lint:
	uv run ruff check
	uv run ruff format --check

typecheck:
	uv run ty check

check:
	$(MAKE) lint typecheck
