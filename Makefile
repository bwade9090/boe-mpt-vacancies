.PHONY: setup download build viz forecast lint test

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

download:
	$(PY) -m src.boe_vac.ingest --num-files 20

build:
	$(PY) -m src.boe_vac.transform

viz:
	$(PY) -m src.boe_vac.viz --month 2024-01

forecast:
	$(PY) -m src.boe_vac.forecast --horizon 12

all: download build viz forecast
