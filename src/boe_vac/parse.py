from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass

import pandas as pd

LOGGER = logging.getLogger("boe_vac.parse")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)


@dataclass
class ParsedCSV:
    metadata: dict[str, str]
    data: pd.DataFrame  # columns ['Period','Value']


def split_metadata_and_table(text: str) -> tuple[list[str], list[str]]:
    lines = text.splitlines()
    table_start = None
    # Accept '2024' or '2024 Q1' or '2024 Jan' etc.
    PERIOD_RE = re.compile(r'^\s*"\d{4}["\s]')
    for i, line in enumerate(lines):
        if PERIOD_RE.search(line):
            table_start = i
            break
    if table_start is None:
        raise ValueError("Could not find period in CSV.")
    meta_lines = [line for line in lines[:table_start] if line.strip() != ""]
    table_lines = lines[table_start:]
    return meta_lines, table_lines


def parse_metadata(meta_lines: list[str]) -> dict[str, str]:
    meta: dict[str, str] = {}
    for raw in meta_lines:
        key, val = raw.strip().split(",")
        key = key.strip().strip('"')
        val = val.strip().strip('"')
        meta[key] = val
    return meta


def parse_table(table_lines: list[str]) -> pd.DataFrame:
    buf = io.StringIO("\n".join(table_lines))
    df = pd.read_csv(buf, names=["Period", "Value"])
    return df


def load_and_parse_csv(path: str) -> ParsedCSV:
    with open(path, encoding="utf-8-sig") as f:
        txt = f.read()
    meta_lines, table_lines = split_metadata_and_table(txt)
    meta = parse_metadata(meta_lines)
    df = parse_table(table_lines)
    return ParsedCSV(metadata=meta, data=df)


def normalise_monthly(parsed: ParsedCSV) -> pd.DataFrame:
    """
    Convert parsed CSV to long-format rows for monthly observations.
    Returns columns: ['series_id','vintage_date','observation_month','value','unit','seasonal_adjustment','dataset','source_url','downloaded_at']
    """
    meta = parsed.metadata
    df = parsed.data

    # Filter monthly period
    def is_monthly(period: str) -> bool:
        return re.fullmatch(r"(\d{4})\s+([A-Z]{3})", period) is not None

    df_monthly = df[df["Period"].apply(is_monthly)].copy()

    # Parse monthly period
    df_monthly["Period"] = df_monthly["Period"].apply(pd.Timestamp)

    # Coerce numeric value
    df_monthly["Value"] = pd.to_numeric(df_monthly["Value"], errors="coerce")

    # Rename
    df_monthly = df_monthly.rename(columns={"Period": "observation_month", "Value": "value"})

    # Meta fields
    df_monthly["series_id"] = meta.get("CDID", None)
    df_monthly["dataset_id"] = meta.get("Source dataset ID", None)
    df_monthly["pre_unit"] = meta.get("PreUnit", None)
    df_monthly["unit"] = meta.get("Unit", None)

    vintage_date = meta.get("Release date", None)
    if vintage_date is None:
        LOGGER.warning("Vintage date not found in metadata; setting to NaT")
        df_monthly["vintage_date"] = None
    else:
        df_monthly["vintage_date"] = pd.to_datetime(vintage_date, dayfirst=True)

    return df_monthly
