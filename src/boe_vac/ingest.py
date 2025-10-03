from __future__ import annotations

import argparse
import hashlib
import logging
import os
import re
import time
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urljoin

import requests
import truststore
from bs4 import BeautifulSoup

truststore.inject_into_ssl()

LOGGER = logging.getLogger("boe_vac.ingest")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)

BASE_URL = "https://www.ons.gov.uk"
SERIES_PATH = (
    "/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/timeseries/ap2y/lms"
)
PREVIOUS_SUFFIX = "/previous"

CSV_PATTERN = re.compile(r"\.csv($|\?)", re.IGNORECASE)


@dataclass
class DownloadedFile:
    url: str
    path: str
    downloaded_at: str


def fetch_html(session: requests.Session, url: str) -> str:
    LOGGER.info("Fetching: %s", url)
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def extract_csv_links_from_html(html: str, base_url: str = BASE_URL) -> list[str]:
    """
    Extract .csv links from ONS time series page HTML.
    Robust to 'generator?format=csv&uri=...' style links and direct .csv.
    """
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a.get("href")
        text = (a.get_text() or "").strip().lower()
        if not href:
            continue
        absolute = urljoin(base_url, href)

        # Prefer links that mention CSV or Downloads explicitly
        if (CSV_PATTERN.search(href) or "download" in text) and "csv" in text:
            links.append(absolute)

    # Deduplicate while preserving order
    seen = set()
    unique_links = []
    for link in links:
        if link not in seen:
            unique_links.append(link)
            seen.add(link)
    return unique_links


def download_file(session: requests.Session, url: str, raw_dir: str) -> DownloadedFile:
    os.makedirs(raw_dir, exist_ok=True)
    # Stable filename from URL hash (no assumption about query params)
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
    fname = f"ap2y_{h}.csv"
    fpath = os.path.join(raw_dir, fname)

    LOGGER.info("Downloading: %s -> %s", url, fpath)
    with session.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(fpath, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    return DownloadedFile(
        url=url, path=fpath, downloaded_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    )


def write_manifest(records: Iterable[DownloadedFile], manifest_path: str) -> None:
    import csv

    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["url", "path", "downloaded_at"])
        for r in records:
            w.writerow([r.url, r.path, r.downloaded_at])
    LOGGER.info("Wrote manifest: %s", manifest_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ONS AP2Y ingestion")
    parser.add_argument(
        "--series-path", default=SERIES_PATH, help="ONS series path (default: AP2Y)"
    )
    parser.add_argument("--num-files", type=int, default=20, help="Number of CSVs to download")
    parser.add_argument("--raw-dir", default="data/raw", help="Directory to store raw CSVs")
    args = parser.parse_args(argv)

    session = requests.Session()

    page = urljoin(BASE_URL, args.series_path + PREVIOUS_SUFFIX)
    try:
        html = fetch_html(session, page)
        unique_links = extract_csv_links_from_html(html, BASE_URL)
        if not unique_links:
            LOGGER.error("No CSV links found. Check the ONS page structure.")
            return 2
        LOGGER.info("Found %d CSV links on %s", len(unique_links), page)
    except Exception as e:
        LOGGER.warning("Failed to parse %s: %s", page, e)

    # Keep latest N (the pages normally list latest + previous in order)
    if len(unique_links) > args.num_files:
        unique_links = unique_links[: args.num_files]

    downloads: list[DownloadedFile] = []
    for url in unique_links:
        time.sleep(2)
        try:
            downloads.append(download_file(session, url, args.raw_dir))
        except Exception as e:
            LOGGER.warning("Failed to download %s: %s", url, e)

    if not downloads:
        LOGGER.error("No files downloaded.")
        return 3

    write_manifest(downloads, os.path.join(args.raw_dir, "manifest.csv"))
    LOGGER.info("Done. Downloaded %d file(s).", len(downloads))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
