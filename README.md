# Bank of England – MPT – Data Scientist Take‑Home (Vacancy AP2Y)

This repository implements an end‑to‑end, **reproducible** mini‑project for the ONS vacancy series (AP2Y), focusing on:
- **Automated ingestion** of CSV vintages from ONS “previous versions”
- **Vintage‑aware structuring** of monthly observations
- **Revision visualisation**
- **Simple forecasting baselines**
- **Best practices** (tests, lint, CI, Make targets)

> **Target series:** https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/timeseries/ap2y/lms/previous

---

## Commands

- `python -m src.boe_vac.ingest --num-files 20`
  Scrape latest & previous pages, collect CSV links, download into `data/raw/` and write a manifest.

---
