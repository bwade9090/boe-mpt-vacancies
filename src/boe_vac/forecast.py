from __future__ import annotations

import argparse
import logging
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

LOGGER = logging.getLogger("boe_vac.forecast")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")


def load_latest_series(path: str = "data/processed/vacancies_long.csv") -> pd.Series:
    df = pd.read_csv(path, parse_dates=["vintage_date", "observation_month"])
    g = df.dropna(subset=["vintage_date"]).sort_values("vintage_date").groupby("observation_month")
    latest = g["value"].last().dropna().sort_index()
    latest.index = pd.date_range(start=latest.index[0], periods=len(latest), freq="MS")
    latest.name = "Latest vintage"
    return latest


def seasonal_naive_forecast(y: pd.Series, horizon: int) -> np.ndarray:
    if len(y) < 12:
        raise ValueError("Need at least 12 observations for seasonal naive.")
    last_season = y[-12:]
    reps = int(np.ceil(horizon / 12))
    fc = np.tile(last_season.values, reps)[:horizon]
    idx = pd.date_range(start=y.index[-1] + y.index.freq, periods=horizon, freq="MS")
    y_hat = pd.Series(data=fc, index=idx, name="Seasonal Naive")
    return y_hat


def ets_forecast(y: pd.Series, horizon: int) -> np.ndarray:
    model = ExponentialSmoothing(
        y.astype(float),
        trend="add",
        seasonal="add",
        seasonal_periods=12,
        initialization_method="estimated",
    ).fit(optimized=True, use_brute=True)
    y_hat = model.forecast(horizon)
    y_hat.name = "ETS"
    return y_hat


def plot_forecast(y: pd.Series, fc: pd.DataFrame, outdir: str) -> str:
    os.makedirs(outdir, exist_ok=True)

    df = pd.concat([y.tail(12), fc], axis=1)
    for col in fc.columns:
        df[col] = df[col].fillna(y.tail(1))
    plt.figure()
    df.plot()
    plt.title("Vacancies forecast (latest vintage baseline)")
    plt.xlabel("Date")
    plt.ylabel("Vacancies (thousands)")
    plt.legend()
    plt.grid(True)
    out = os.path.join(outdir, "forecast_latest.png")
    plt.tight_layout()
    plt.savefig(out, dpi=150)
    plt.close()
    LOGGER.info("Saved forecasts plot: %s", out)
    return out


def save_numeric_outputs(y: pd.Series, fc: pd.DataFrame, outdir: str) -> str:
    os.makedirs(outdir, exist_ok=True)
    out_df = pd.concat([y, fc], axis=1)  # Wide
    out = os.path.join(outdir, "forecast_latest.csv")
    out_df.to_csv(out)
    LOGGER.info("Saved forecasts csv: %s", out)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Baseline forecasts on latest vintage")
    parser.add_argument("--data", default="data/processed/vacancies_long.csv")
    parser.add_argument("--horizon", type=int, default=12)
    parser.add_argument("--outdir", default="reports/figures")
    args = parser.parse_args(argv)

    y = load_latest_series(args.data)
    fc: pd.DataFrame = pd.DataFrame()  # Wide
    try:
        y_hat = seasonal_naive_forecast(y, args.horizon)
        fc = pd.concat([fc, y_hat], axis=1)
    except Exception as e:
        LOGGER.warning("Failed seasonal naive forecast: %s", e)

    try:
        y_hat = ets_forecast(y, args.horizon)
        fc = pd.concat([fc, y_hat], axis=1)
    except Exception as e:
        LOGGER.warning("Failed ETS forecast: %s", e)

    plot_forecast(y, fc, args.outdir)
    save_numeric_outputs(y, fc, args.outdir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
