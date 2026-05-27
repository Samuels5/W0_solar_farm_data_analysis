from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

try:
    from .utils import (
        DATA_DIR,
        compare_summary,
        infer_country_name,
        list_clean_files,
        load_country_data,
        metric_boxplot_frame,
        metric_summary,
        numeric_columns,
    )
except ImportError:
    from utils import (  # type: ignore
        DATA_DIR,
        compare_summary,
        infer_country_name,
        list_clean_files,
        load_country_data,
        metric_boxplot_frame,
        metric_summary,
        numeric_columns,
    )


st.set_page_config(page_title="Solar Insights Dashboard", page_icon="☀️", layout="wide")
sns.set_theme(style="whitegrid")


def render_metric_boxplot(df: pd.DataFrame, country_col: str, metric: str) -> None:
    plot_df = metric_boxplot_frame(df, country_col, metric)
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.boxplot(data=plot_df, x=country_col, y=metric, palette="Set2", ax=ax)
    ax.set_title(f"{metric} by country")
    ax.set_xlabel("Country")
    ax.set_ylabel(f"{metric} (W/m^2)")
    st.pyplot(fig, clear_figure=True)


def render_average_ranking(df: pd.DataFrame, country_col: str, metric: str) -> None:
    ranking = df.groupby(country_col)[metric].mean().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 4))
    ranking.sort_values().plot(kind="barh", color="#2E86AB", ax=ax)
    ax.set_xlabel(f"Average {metric}")
    ax.set_ylabel("Country")
    ax.set_title(f"Country ranking by average {metric}")
    st.pyplot(fig, clear_figure=True)


def render_timeseries(df: pd.DataFrame, metric: str) -> None:
    if "Timestamp" not in df.columns:
        st.info("No Timestamp column available for time-series view.")
        return
    ts_df = df[["Timestamp", metric]].dropna(subset=["Timestamp", metric]).copy()
    if ts_df.empty:
        st.info("No rows available for the selected time-series view.")
        return
    ts_df = ts_df.set_index("Timestamp").sort_index()
    daily = ts_df.resample("D").mean(numeric_only=True)
    fig, ax = plt.subplots(figsize=(10, 4))
    daily[metric].plot(ax=ax, linewidth=1.6, color="#F18F01")
    ax.set_title(f"Daily mean {metric}")
    ax.set_xlabel("Date")
    ax.set_ylabel(metric)
    st.pyplot(fig, clear_figure=True)


def main() -> None:
    st.title("Solar Insights Dashboard")
    st.caption("Interactive view of the cleaned Benin, Sierra Leone, and Togo solar data.")

    clean_files = list_clean_files()
    if not clean_files:
        st.error(
            f"No cleaned CSV files found in {DATA_DIR}. Add files such as `benin_clean.csv`, `sierraleone_clean.csv`, and `togo_clean.csv`."
        )
        st.stop()

    country_options = {infer_country_name(path): path for path in clean_files}
    selected_country = st.sidebar.selectbox("Country", list(country_options.keys()))
    selected_path = country_options[selected_country]

    df = load_country_data(str(selected_path))
    numeric_cols = numeric_columns(df)
    default_metric = "GHI" if "GHI" in df.columns else (numeric_cols[0] if numeric_cols else None)

    st.sidebar.markdown("### Controls")
    metric = st.sidebar.selectbox(
        "Metric",
        [c for c in ["GHI", "DNI", "DHI", "Tamb", "RH", "WS", "WSgust"] if c in df.columns] or numeric_cols,
        index=0 if default_metric is None else 0,
    )
    view_mode = st.sidebar.radio("View mode", ["Overview", "Time series", "Comparison"], horizontal=False)
    date_filter = None
    if "Timestamp" in df.columns and df["Timestamp"].notna().any():
        min_date = pd.to_datetime(df["Timestamp"].min()).date()
        max_date = pd.to_datetime(df["Timestamp"].max()).date()
        date_filter = st.sidebar.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

    if date_filter and "Timestamp" in df.columns:
        start_date, end_date = date_filter if isinstance(date_filter, tuple) else (date_filter, date_filter)
        mask = df["Timestamp"].dt.date.between(start_date, end_date)
        df = df.loc[mask].copy()

    st.subheader(f"{selected_country}")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Rows", f"{len(df):,}")
    with c2:
        st.metric("Columns", f"{df.shape[1]:,}")
    with c3:
        st.metric("Missing values", f"{int(df.isna().sum().sum()):,}")
    with c4:
        st.metric("Numeric columns", f"{len(numeric_cols):,}")

    if metric in df.columns:
        st.markdown(f"### {metric} Summary")
        st.dataframe(metric_summary(df, metric), use_container_width=True)

    if view_mode == "Overview":
        col_left, col_right = st.columns([2, 1])
        with col_left:
            if metric in df.columns:
                render_metric_boxplot(df.assign(country=selected_country), "country", metric)
        with col_right:
            st.markdown("### Data Preview")
            st.dataframe(df.head(10), use_container_width=True)

    elif view_mode == "Time series":
        if metric in df.columns:
            render_timeseries(df, metric)
        st.markdown("### Recent Rows")
        st.dataframe(df.tail(10), use_container_width=True)

    else:
        if metric not in df.columns:
            st.warning(f"{metric} is not available in the selected file.")
        else:
            full_data = []
            for name, path in country_options.items():
                frame = load_country_data(str(path)).copy()
                frame["country"] = name
                full_data.append(frame)
            combined = pd.concat(full_data, ignore_index=True, sort=False)
            available_metrics = [m for m in ["GHI", "DNI", "DHI"] if m in combined.columns]
            if available_metrics:
                summary = compare_summary(combined, "country", available_metrics)
                st.markdown("### Cross-country summary")
                st.dataframe(summary, use_container_width=True)
                plot_metric = st.selectbox("Metric to compare", available_metrics)
                render_metric_boxplot(combined, "country", plot_metric)
                render_average_ranking(combined, "country", plot_metric)
            else:
                st.info("The cleaned files do not contain the expected comparison metrics.")

    st.markdown("---")
    st.markdown(
        """
        ### How to deploy
        Run locally with:
        ```bash
        streamlit run app/main.py
        ```
        Then push the repo to GitHub and deploy from Streamlit Community Cloud.
        """
    )


if __name__ == "__main__":
    main()
