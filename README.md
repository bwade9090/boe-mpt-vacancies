# Bank of England – MPT – Data Scientist Take‑Home (Vacancy AP2Y)

This repository implements an end‑to‑end, **reproducible** mini‑project for the ONS vacancy series (AP2Y), focusing on:
- **Automated ingestion** of CSV vintages from ONS “previous versions”
- **Vintage‑aware structuring** of monthly observations
- **Revision visualisation**
- **Simple forecasting baselines**
- **Best practices** (tests, lint, CI, Make targets)

> **Target series:** https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/timeseries/ap2y/lms/previous

---

## Design choices (high‑level)

- **Vintage = CSV header `Release date`** (parsed from each file’s metadata). When absent, log a warning.
- **Monthly only**: `Period` is parsed with robust regex for `YYYY MON` formats. Quarterly/Yearly rows are dropped.
- **Schema (long)**:
  - `vintage_date` (YYYY‑MM‑DD), `observation_month` (YYYY‑MM‑01), `value` (int)
  - extra: `series_id`, `dataset_id`, `pre_unit`, `unit`
- **Reproducibility**: zero hard‑coded absolute paths; `Makefile` targets; deterministic outputs; tests use **mock HTML & CSV** (no network needed).

---

## Commands

- `python -m src.boe_vac.ingest --num-files 20`
  Scrape latest & previous pages, collect CSV links, download into `data/raw/` and write a manifest.

- `python -m src.boe_vac.transform`
  Parse raw CSVs → extract metadata (incl. `vintage_date`) and monthly data → write `data/processed/vacancies_long.csv`.

---
