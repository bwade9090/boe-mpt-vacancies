from __future__ import annotations

import argparse
import logging
import os

import matplotlib.pyplot as plt
import pandas as pd

LOGGER = logging.getLogger("boe_vac.viz")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)


def load_long(path: str = "data/processed/vacancies_long.csv") -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["vintage_date", "observation_month"])
    return df


def plot_revision_path(df: pd.DataFrame, month: str, outdir: str = "reports/figures") -> str:
    """
    Plot how the estimate for a fixed observation month evolves across vintages.
    """
    os.makedirs(outdir, exist_ok=True)
    m = pd.Timestamp(month)
    dt = df[df["observation_month"] == m].dropna(subset=["vintage_date"]).copy()
    if dt.empty:
        raise ValueError(f"No data for observation month {month}")
    dt = dt.sort_values("vintage_date")

    plt.figure(figsize=(10, 4.5))
    plt.plot(dt["vintage_date"], dt["value"], marker="o")
    plt.xlabel("Vintage (Release date)")
    plt.ylabel("Vacancies (thousands)")
    plt.title(f"Revision path for observation {m.strftime('%Y-%m')}")
    plt.grid(True)
    out = os.path.join(outdir, f"revision_path_{m.strftime('%Y-%m')}.png")
    plt.tight_layout()
    plt.savefig(out, dpi=150)
    plt.close()
    LOGGER.info("Saved revision path plot: %s", out)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Visualisations for revisions")
    parser.add_argument("--data", default="data/processed/vacancies_long.csv")
    parser.add_argument("--month", default="2024-01")
    parser.add_argument("--outdir", default="reports/figures")
    args = parser.parse_args(argv)

    df = load_long(args.data)
    plot_revision_path(df, args.month, args.outdir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
