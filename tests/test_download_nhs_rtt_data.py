import math

import pandas as pd

from download_nhs_rtt_data import aggregate_bands, band_columns, median_from_bands

# same band layout as the NHS England file: 104 one-week bands plus an open 104+ band
BANDS = [f"Gt {w:02d} To {w + 1:02d} Weeks SUM 1" for w in range(104)] + ["Gt 104 Weeks SUM 1"]


def make_row(counts, commissioner="A"):
    row = {"month": "2026-09", "region": "London", "trust_code": "R1", "trust_name": "Trust", "specialty": "Urology",
           "Commissioner Org Code": commissioner}
    row.update({band: counts.get(i, 0) for i, band in enumerate(BANDS)})
    return row


def test_band_columns_found_in_order():
    assert band_columns(pd.DataFrame([make_row({})])) == BANDS


def test_aggregation_sums_commissioner_rows_and_splits_at_18_and_52_weeks():
    df = pd.DataFrame([
        make_row({0: 10, 17: 5, 18: 3, 51: 2, 52: 1, 104: 4}, "A"),
        make_row({17: 5, 18: 7}, "B"),
    ])
    out = aggregate_bands(df)
    assert len(out) == 1
    row = out.iloc[0]
    assert row["total_waiting_list"] == 37
    assert row["within_18_weeks"] == 20  # bands 0-17: the 17-18 week band counts as within 18 weeks
    assert row["waiting_18_to_52_weeks"] == 12  # bands 18-51
    assert row["waiting_52_plus_weeks"] == 5  # bands 52 and over, including 104+
    assert row["within_18_weeks"] + row["waiting_18_to_52_weeks"] + row["waiting_52_plus_weeks"] == row["total_waiting_list"]
    assert math.isclose(row["within_18_weeks"] / row["total_waiting_list"], 20 / 37)


def test_empty_groups_are_dropped():
    assert aggregate_bands(pd.DataFrame([make_row({})])).empty


def test_median_interpolates_inside_band():
    assert median_from_bands([10, 10]) == 1.0  # middle pathway sits at the band edge
    assert median_from_bands([0, 0, 100, 0]) == 2.5
    assert math.isclose(median_from_bands([4, 0, 0, 12, 0]), 3 + 4 / 12)


def test_median_edge_cases():
    assert math.isnan(median_from_bands([0, 0, 0]))
    assert median_from_bands([1, 0, 10]) == 2.0  # open-ended last band reports its lower edge
