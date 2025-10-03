from __future__ import annotations

import argparse
import glob
import logging
import os
import re

import pandas as pd

from .parse import load_and_parse_csv, normalise_monthly

LOGGER = logging.getLogger("boe_vac.transform")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)


def build_long(raw_dir: str = "data/raw", processed_dir: str = "data/processed") -> pd.DataFrame:
    csvs = glob.glob(os.path.join(raw_dir, "*.csv"))
    csvs = list(filter(lambda csv: re.search("manifest.csv$", csv) is None, csvs))
    if not csvs:
        raise FileNotFoundError(f"No CSVs in {raw_dir}. Run ingestion first.")

    frames: list[pd.DataFrame] = []
    for path in csvs:
        try:
            parsed = load_and_parse_csv(path)
            rows = normalise_monthly(parsed)
            frames.append(rows)
        except Exception as e:
            LOGGER.warning("Failed to parse %s: %s", path, e)
    if not frames:
        raise RuntimeError("No parsable CSVs found.")
    df = pd.concat(frames, ignore_index=True)

    # Dedupe (same vintage & observation_month)
    df = (
        df.sort_values(["vintage_date", "observation_month"], kind="mergesort")
        .drop_duplicates(subset=["series_id", "vintage_date", "observation_month"], keep="last")
        .reset_index(drop=True)
    )

    os.makedirs(processed_dir, exist_ok=True)
    out_csv = os.path.join(processed_dir, "vacancies_long.csv")
    df.to_csv(out_csv, index=False)
    LOGGER.info("Wrote: %s (rows=%d)", out_csv, len(df))
    return df


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build long-format processed dataset")
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument("--processed-dir", default="data/processed")
    args = parser.parse_args(argv)
    build_long(args.raw_dir, args.processed_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
