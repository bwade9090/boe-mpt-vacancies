.PHONY: setup lint test

PY := python

setup:
	pip install -U pip
	pip install -r requirements.txt
	pip install -r requirements-dev.txt || true

lint:
	ruff check .
	black --check . || true

test:
	pytest -q
