from __future__ import annotations

"""
Phase 12 visualization utilities.

Read-only plotting functions that consume the generated KPI CSV and
produce static PNGs under `output/plots/`. These functions do not touch
SD/ABM logic. Quarter labels are taken directly from the CSV header and
are not hardcoded to 28 periods, so they work with variable horizons.

Usage:
    from viz.plots import generate_all_plots_from_csv
    generate_all_plots_from_csv(Path('output/Growth_System_Complete_Results.csv'))
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

from src.io_paths import OUTPUT_DIR


def _ensure_plots_dir() -> Path:
    """Ensure `output/plots/` exists and return the path."""
    plots_dir = OUTPUT_DIR / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    return plots_dir


def _read_results_csv(csv_path: Path | str) -> pd.DataFrame:
    """Load the KPI CSV with 'Output Stocks' as the first column index.

    Returns a DataFrame indexed by row labels with period columns as strings.
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Results CSV not found: {csv_path}")
    df = pd.read_csv(csv_path)
    if df.columns.empty or df.columns[0] != "Output Stocks":
        raise ValueError("Unexpected CSV format: first column must be 'Output Stocks'")
    df = df.set_index("Output Stocks")
    return df


def _period_columns(df: pd.DataFrame) -> list[str]:
    """Return the ordered list of period columns taken verbatim from the CSV."""
    return [c for c in df.columns]


def _save_fig(fig: plt.Figure, filename: str) -> Path:
    plots_dir = _ensure_plots_dir()
    out_path = plots_dir / filename
    fig.savefig(out_path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    return out_path


def plot_revenue_total_and_by_sector(df: pd.DataFrame) -> Path:
    """Plot total revenue and revenue by sector lines.

    Note: Intentionally excludes material revenue series to keep this
    view focused on sectoral composition. Material revenues are handled
    by `plot_revenue_by_material`.
    """
    periods = _period_columns(df)
    x = range(len(periods))
    fig, ax = plt.subplots(figsize=(10, 5))

    # Total revenue
    if "Revenue" not in df.index:
        raise ValueError("Missing 'Revenue' row in CSV")
    ax.plot(x, df.loc["Revenue", periods].values, label="Revenue (Total)")

    # By sector: restrict to known sector rows to avoid mixing with materials
    known_sectors = {
        "Revenue Defense",
        "Revenue Nuclear",
        "Revenue Semiconductors",
        "Revenue Aviation",
    }
    for row in df.index:
        if row in known_sectors:
            ax.plot(x, df.loc[row, periods].values, label=row)

    ax.set_title("Revenue: Total and by Sector/Material")
    ax.set_xticks(list(x))
    ax.set_xticklabels(periods, rotation=45, ha="right")
    ax.set_ylabel("Revenue (currency)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8, ncol=2)
    return _save_fig(fig, "revenue_total_and_by_sector.png")


def plot_revenue_by_material(df: pd.DataFrame) -> Path:
    """Plot revenue by material only (filter out sectors)."""
    periods = _period_columns(df)
    x = range(len(periods))
    fig, ax = plt.subplots(figsize=(10, 5))

    for row in df.index:
        if row.startswith("Revenue ") and row not in (
            "Revenue",
            "Revenue Defense",
            "Revenue Nuclear",
            "Revenue Semiconductors",
            "Revenue Aviation",
        ):
            ax.plot(x, df.loc[row, periods].values, label=row)

    ax.set_title("Revenue by Material")
    ax.set_xticks(list(x))
    ax.set_xticklabels(periods, rotation=45, ha="right")
    ax.set_ylabel("Revenue (currency)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8, ncol=2)
    return _save_fig(fig, "revenue_by_material.png")


def plot_leads_and_clients(df: pd.DataFrame) -> Path:
    """Plot Anchor Leads (total), Other Leads (total), and Other Clients by material."""
    periods = _period_columns(df)
    x = range(len(periods))
    fig, ax = plt.subplots(figsize=(10, 5))

    for row in ("Anchor Leads", "Other Leads"):
        if row in df.index:
            ax.plot(x, df.loc[row, periods].values, label=row)

    for row in df.index:
        if row.startswith("Other Clients "):
            ax.plot(x, df.loc[row, periods].values, label=row)

    ax.set_title("Leads and Clients")
    ax.set_xticks(list(x))
    ax.set_xticklabels(periods, rotation=45, ha="right")
    ax.set_ylabel("Count")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8, ncol=2)
    return _save_fig(fig, "leads_and_clients.png")


def plot_order_basket_vs_delivery(df: pd.DataFrame) -> Path:
    """For each material, plot Order Basket vs Order Delivery on the same axes."""
    periods = _period_columns(df)
    x = range(len(periods))
    fig, ax = plt.subplots(figsize=(10, 5))

    # Total comparison
    if "Order Basket" in df.index and "Order Delivery" in df.index:
        ax.plot(x, df.loc["Order Basket", periods].values, label="Order Basket (Total)")
        ax.plot(x, df.loc["Order Delivery", periods].values, label="Order Delivery (Total)")

    # Per material
    for row in df.index:
        if row.startswith("Order Basket ") or row.startswith("Order Delivery "):
            ax.plot(x, df.loc[row, periods].values, label=row, alpha=0.7)

    ax.set_title("Order Basket vs Delivery (Total and by Material)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(periods, rotation=45, ha="right")
    ax.set_ylabel("Units per quarter")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8, ncol=2)
    return _save_fig(fig, "order_basket_vs_delivery.png")


def plot_capacity_utilization(df: pd.DataFrame) -> Path:
    """Plot per-material utilization lines and total utilization.

    Primary computation: use precomputed `Capacity Utilization <material>` rows.
    Fallback computation when missing: (Order Delivery <m>) / (Production Capacity <m>)
    with a secondary fallback to Order Basket <m> if capacity is missing/zero.
    Values are clipped to [0, 1]. Also plot total utilization using totals.
    """
    periods = _period_columns(df)
    if "Order Delivery" not in df.index:
        return _ensure_plots_dir() / "capacity_utilization_skipped.txt"

    # Prepare figure
    x = range(len(periods))
    fig, ax = plt.subplots(figsize=(10, 5))

    # Per-material lines
    plotted_any = False
    for row in df.index:
        if row.startswith("Capacity Utilization "):
            series = df.loc[row, periods].astype(float).clip(lower=0.0, upper=1.0)
            ax.plot(x, series.values, label=row)
            plotted_any = True

    # Fallback: compute per-material utilization if precomputed rows are missing
    if not plotted_any:
        for row in df.index:
            if row.startswith("Order Delivery "):
                mat = row[len("Order Delivery "):]
                del_series = df.loc[f"Order Delivery {mat}", periods].astype(float)
                if f"Production Capacity {mat}" in df.index:
                    denom_series = df.loc[f"Production Capacity {mat}", periods].astype(float).clip(lower=1e-9)
                elif f"Order Basket {mat}" in df.index:
                    denom_series = df.loc[f"Order Basket {mat}", periods].astype(float).clip(lower=1e-9)
                else:
                    continue
                util_series = (del_series / denom_series).clip(lower=0.0, upper=1.0)
                ax.plot(x, util_series.values, label=f"Capacity Utilization {mat}")
                plotted_any = True

    # Total utilization line (Delivery total / Capacity total, else / Basket total)
    delivery_total = df.loc["Order Delivery", periods].astype(float)
    if "Production Capacity" in df.index:
        denom_total = df.loc["Production Capacity", periods].astype(float).clip(lower=1e-9)
    elif "Order Basket" in df.index:
        denom_total = df.loc["Order Basket", periods].astype(float).clip(lower=1e-9)
    else:
        denom_total = None
    if denom_total is not None:
        util_total = (delivery_total / denom_total).clip(lower=0.0, upper=1.0)
        ax.plot(x, util_total.values, label="Capacity Utilization (Total)", linewidth=2.5)

    ax.set_title("Capacity Utilization (Per Material and Total)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(periods, rotation=45, ha="right")
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8, ncol=2)
    return _save_fig(fig, "capacity_utilization.png")


def generate_all_plots_from_csv(csv_path: Path | str) -> list[Path]:
    """High-level helper to load CSV and generate all Phase 12 plots.

    Returns a list of output file paths for created images.
    """
    df = _read_results_csv(csv_path)
    outputs: list[Path] = []
    outputs.append(plot_revenue_total_and_by_sector(df))
    outputs.append(plot_revenue_by_material(df))
    outputs.append(plot_leads_and_clients(df))
    outputs.append(plot_order_basket_vs_delivery(df))
    outputs.append(plot_capacity_utilization(df))
    return outputs
