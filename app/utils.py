from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"


@st.cache_data(show_spinner=False)
def list_clean_files() -> list[Path]:
    clean_files = sorted(DATA_DIR.glob("*_clean.csv"))
    if clean_files:
        return clean_files

    # Fallback for local exploration if the cleaned exports are not present yet.
    return sorted(DATA_DIR.glob("*.csv"))


def infer_country_name(path: Path) -> str:
    stem = path.stem.replace("_clean", "")
    label_map = {
        "benin-malanville": "Benin",
        "sierraleone-bumbuna": "Sierra Leone",
        "togo-dapaong_qc": "Togo",
        "benin": "Benin",
        "sierraleone": "Sierra Leone",
        "togo": "Togo",
    }
    return label_map.get(stem.lower(), stem.replace("_", " ").title())


@st.cache_data(show_spinner=False)
def load_country_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        df = df.sort_values("Timestamp")
    return df


def numeric_columns(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include="number").columns.tolist()


def metric_summary(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    if metric not in df.columns:
        raise KeyError(metric)
    summary = df[metric].agg(["count", "mean", "median", "std", "min", "max"]).to_frame().T
    summary.index = [metric]
    return summary.round(2)


def compare_summary(df: pd.DataFrame, country_col: str, metrics: list[str]) -> pd.DataFrame:
    available = [m for m in metrics if m in df.columns]
    summary = df.groupby(country_col)[available].agg(["mean", "median", "std"]).round(2)
    summary.columns = ["_".join(col).strip() for col in summary.columns.to_flat_index()]
    return summary


def metric_boxplot_frame(df: pd.DataFrame, country_col: str, metric: str) -> pd.DataFrame:
    return df[[country_col, metric]].dropna(subset=[country_col, metric]).copy()
