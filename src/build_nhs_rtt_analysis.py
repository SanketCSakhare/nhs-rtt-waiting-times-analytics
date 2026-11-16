from pathlib import Path

import pandas as pd


REAL_PATH = Path("data/raw/nhs_rtt_england.csv")  # from src/download_nhs_rtt_data.py
DEMO_PATH = Path("data/raw/nhs_rtt_demo.csv")  # synthetic offline fallback from src/generate_demo_data.py
PROCESSED = Path("data/processed")
CHARTS = Path("dashboard/screenshots")


def pressure_band(row):
    if row["performance_18_weeks"] < 0.60 or row["long_waiter_share"] >= 0.04:
        return "High pressure"
    if row["performance_18_weeks"] < 0.70 or row["long_waiter_share"] >= 0.025:
        return "Medium pressure"
    return "Lower pressure"


def recovery_priority(row):
    if row["pressure_band"] == "High pressure":
        return "Priority recovery support"
    if row["pressure_band"] == "Medium pressure":
        return "Targeted monitoring"
    return "Business as usual"


def svg_bar_chart(df, label_col, value_col, title, output_path, value_format="{:.1%}"):
    width = 980
    margin_left = 275
    margin_right = 90
    margin_top = 72
    bar_gap = 16
    bar_height = 38
    height = margin_top + len(df) * (bar_height + bar_gap) + 20
    plot_width = width - margin_left - margin_right
    max_value = max(df[value_col].max(), 0.01)
    rows = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="32" y="42" font-family="Arial" font-size="24" font-weight="700" fill="#172033">{title}</text>',
    ]
    for idx, row in df.reset_index(drop=True).iterrows():
        y = margin_top + idx * (bar_height + bar_gap)
        bar_width = int((row[value_col] / max_value) * plot_width)
        rows.extend(
            [
                f'<text x="32" y="{y + 25}" font-family="Arial" font-size="14" fill="#172033">{row[label_col]}</text>',
                f'<rect x="{margin_left}" y="{y}" width="{bar_width}" height="{bar_height}" rx="4" fill="#005eb8"/>',
                f'<text x="{margin_left + bar_width + 12}" y="{y + 25}" font-family="Arial" font-size="14" fill="#172033">{value_format.format(row[value_col])}</text>',
            ]
        )
    rows.append("</svg>")
    output_path.write_text("\n".join(rows), encoding="utf-8")


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    CHARTS.mkdir(parents=True, exist_ok=True)

    raw_path = REAL_PATH if REAL_PATH.exists() else DEMO_PATH
    if raw_path == DEMO_PATH:
        print("WARNING: real NHS data not found, using SYNTHETIC demo data. Outputs are not real figures.")
    df = pd.read_csv(raw_path)
    df["performance_18_weeks"] = df["within_18_weeks"] / df["total_waiting_list"]
    df["long_waiter_share"] = df["waiting_52_plus_weeks"] / df["total_waiting_list"]
    df["pressure_band"] = df.apply(pressure_band, axis=1)
    df["recovery_priority"] = df.apply(recovery_priority, axis=1)

    latest_month = df["month"].max()
    latest = df[df["month"] == latest_month].copy()

    specialty_summary = (
        latest.groupby("specialty", as_index=False)
        .agg(
            total_waiting_list=("total_waiting_list", "sum"),
            within_18_weeks=("within_18_weeks", "sum"),
            waiting_52_plus_weeks=("waiting_52_plus_weeks", "sum"),
            avg_median_wait_weeks=("median_wait_weeks", "mean"),
        )
    )
    specialty_summary["performance_18_weeks"] = specialty_summary["within_18_weeks"] / specialty_summary["total_waiting_list"]
    specialty_summary["long_waiter_share"] = specialty_summary["waiting_52_plus_weeks"] / specialty_summary["total_waiting_list"]
    specialty_summary = specialty_summary.sort_values("performance_18_weeks")

    trust_summary = (
        latest.groupby(["trust_code", "trust_name", "region"], as_index=False)
        .agg(
            total_waiting_list=("total_waiting_list", "sum"),
            within_18_weeks=("within_18_weeks", "sum"),
            waiting_52_plus_weeks=("waiting_52_plus_weeks", "sum"),
            avg_median_wait_weeks=("median_wait_weeks", "mean"),
        )
    )
    trust_summary["performance_18_weeks"] = trust_summary["within_18_weeks"] / trust_summary["total_waiting_list"]
    trust_summary["long_waiter_share"] = trust_summary["waiting_52_plus_weeks"] / trust_summary["total_waiting_list"]
    trust_summary["pressure_band"] = trust_summary.apply(pressure_band, axis=1)
    trust_summary["recovery_priority"] = trust_summary.apply(recovery_priority, axis=1)
    trust_summary = trust_summary.sort_values(["long_waiter_share", "total_waiting_list"], ascending=[False, False])

    region_summary = (
        latest.groupby("region", as_index=False)
        .agg(
            total_waiting_list=("total_waiting_list", "sum"),
            within_18_weeks=("within_18_weeks", "sum"),
            waiting_52_plus_weeks=("waiting_52_plus_weeks", "sum"),
            avg_median_wait_weeks=("median_wait_weeks", "mean"),
        )
    )
    region_summary["performance_18_weeks"] = region_summary["within_18_weeks"] / region_summary["total_waiting_list"]
    region_summary["long_waiter_share"] = region_summary["waiting_52_plus_weeks"] / region_summary["total_waiting_list"]
    region_summary = region_summary.sort_values("long_waiter_share", ascending=False)

    monthly_summary = (
        df.groupby("month", as_index=False)
        .agg(
            total_waiting_list=("total_waiting_list", "sum"),
            within_18_weeks=("within_18_weeks", "sum"),
            waiting_52_plus_weeks=("waiting_52_plus_weeks", "sum"),
            avg_median_wait_weeks=("median_wait_weeks", "mean"),
        )
    )
    monthly_summary["performance_18_weeks"] = monthly_summary["within_18_weeks"] / monthly_summary["total_waiting_list"]
    monthly_summary["long_waiter_share"] = monthly_summary["waiting_52_plus_weeks"] / monthly_summary["total_waiting_list"]

    # small independent providers swing wildly on a few pathways, so also count the large ones
    large = trust_summary[trust_summary["total_waiting_list"] >= 10000]

    executive = pd.DataFrame(
        [
            {
                "latest_month": latest_month,
                "total_waiting_list": int(latest["total_waiting_list"].sum()),
                "performance_18_weeks": round(latest["within_18_weeks"].sum() / latest["total_waiting_list"].sum(), 4),
                "waiting_52_plus_weeks": int(latest["waiting_52_plus_weeks"].sum()),
                "long_waiter_share": round(latest["waiting_52_plus_weeks"].sum() / latest["total_waiting_list"].sum(), 4),
                "providers_reporting": len(trust_summary),
                "trusts_below_60_percent": int((trust_summary["performance_18_weeks"] < 0.60).sum()),
                "providers_10k_plus": len(large),
                "providers_10k_plus_below_60_percent": int((large["performance_18_weeks"] < 0.60).sum()),
                "highest_pressure_specialty": specialty_summary.iloc[0]["specialty"],
            }
        ]
    )

    df.to_csv(PROCESSED / "rtt_waiting_list_assessed.csv", index=False)
    specialty_summary.to_csv(PROCESSED / "specialty_summary.csv", index=False)
    trust_summary.to_csv(PROCESSED / "trust_pressure_summary.csv", index=False)
    region_summary.to_csv(PROCESSED / "region_summary.csv", index=False)
    monthly_summary.to_csv(PROCESSED / "monthly_trend_summary.csv", index=False)
    executive.to_csv(PROCESSED / "executive_kpi_summary.csv", index=False)

    chart_specialty = specialty_summary.sort_values("performance_18_weeks", ascending=True)
    svg_bar_chart(
        chart_specialty,
        "specialty",
        "performance_18_weeks",
        "18-Week Performance by Specialty",
        CHARTS / "performance_by_specialty.svg",
    )
    svg_bar_chart(
        region_summary,
        "region",
        "long_waiter_share",
        "Long Waiter Share by Region",
        CHARTS / "long_waiter_share_by_region.svg",
    )
    svg_bar_chart(
        monthly_summary,
        "month",
        "performance_18_weeks",
        "18-Week Performance by Month",
        CHARTS / "performance_by_month.svg",
    )
    print("Created NHS RTT KPI outputs and dashboard preview charts.")


if __name__ == "__main__":
    main()

