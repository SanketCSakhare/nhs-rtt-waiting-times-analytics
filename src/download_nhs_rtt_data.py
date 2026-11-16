"""Download NHS England RTT "Full CSV data file" zips and reshape them for the pipeline.

Writes:
  data/raw/nhs_england/*.zip, *.xlsx      raw downloads (not in git)
  data/raw/nhs_rtt_england.csv            provider x treatment function x month (not in git)
  data/reference/icb_region_lookup.csv    ICB -> NHS region, from the ODS API
  data/processed/national_reconciliation.csv   our totals vs NHS England's published series
"""
import json
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

STATS_PAGE = "https://www.england.nhs.uk/statistics/statistical-work-areas/rtt-waiting-times/"
ODS_API = "https://directory.spineservices.nhs.uk/ORD/2-0-0/organisations/"
DOWNLOADS = Path("data/raw/nhs_england")
OUT_CSV = Path("data/raw/nhs_rtt_england.csv")
LOOKUP_CSV = Path("data/reference/icb_region_lookup.csv")
RECON_CSV = Path("data/processed/national_reconciliation.csv")
MONTHS = 12

KEYS = ["month", "region", "trust_code", "trust_name", "specialty"]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def download(url):
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    path = DOWNLOADS / url.rsplit("/", 1)[1]
    if not path.exists():
        path.write_bytes(fetch(url))
    return path


def discover_links():
    """Return ({'2026-09': zip_url, ...}, timeseries_xlsx_url) scraped from the yearly pages."""
    home = fetch(STATS_PAGE).decode("utf-8", "replace")
    year_pages = sorted(set(re.findall(r'href="([^"]*/rtt-data-20\d\d-\d\d)/?"', home)))[-2:]
    zips, timeseries = {}, None
    for page in year_pages:
        html = fetch(page + "/").decode("utf-8", "replace")
        for url, mon, yy in re.findall(r'href="([^"]*Full-CSV-data-file-([A-Z][a-z]{2})(\d\d)[^"]*\.zip)"', html):
            zips[pd.to_datetime(f"{mon} 20{yy}", format="%b %Y").strftime("%Y-%m")] = url
        found = re.findall(r'href="([^"]*RTT-Overview-Timeseries[^"]*\.xlsx)"', html)
        timeseries = found[0] if found else timeseries
    return zips, timeseries


def band_columns(df):
    """Weekly band columns in order: 'Gt 00 To 01 Weeks SUM 1' ... 'Gt 104 Weeks SUM 1'."""
    return [c for c in df.columns if c.startswith("Gt ")]


def median_from_bands(counts):
    """Estimated median wait in weeks from counts per one-week band.

    Finds the band holding the middle pathway and interpolates linearly inside it.
    The last band (104+ weeks) is open-ended, so a median there is reported as its lower edge.
    """
    counts = list(counts)
    half = sum(counts) / 2
    if half == 0:
        return float("nan")
    running = 0
    for week, n in enumerate(counts):
        if n and running + n >= half:
            if week == len(counts) - 1:
                return float(week)
            return week + (half - running) / n
        running += n


def aggregate_bands(df):
    """Collapse weekly bands to one row per month/region/provider/treatment function."""
    bands = band_columns(df)
    grouped = df.groupby(KEYS, as_index=False)[bands].sum()
    out = grouped[KEYS].copy()
    out["total_waiting_list"] = grouped[bands].sum(axis=1).astype(int)
    out["within_18_weeks"] = grouped[bands[:18]].sum(axis=1).astype(int)  # 0 up to 18 weeks
    out["waiting_18_to_52_weeks"] = grouped[bands[18:52]].sum(axis=1).astype(int)
    out["waiting_52_plus_weeks"] = grouped[bands[52:]].sum(axis=1).astype(int)
    out["median_wait_weeks"] = [round(median_from_bands(r), 1) for r in grouped[bands].to_numpy()]
    return out[out["total_waiting_list"] > 0].reset_index(drop=True)


def region_for(icb_code, cache):
    """NHS England region of an ICB via the ODS API (relationship RE2 to a role RO209 organisation)."""
    if icb_code not in cache:
        try:
            org = json.loads(fetch(ODS_API + icb_code))["Organisation"]
            rels = [r for r in org.get("Rels", {}).get("Rel", [])
                    if r["id"] == "RE2" and r["Target"]["PrimaryRoleId"]["id"] == "RO209"]
            # merged ICBs have closed relationships, so take the most recent rather than the active one
            latest = max(rels, key=lambda r: max(d["Start"] for d in r["Date"]))
            region_code = latest["Target"]["OrgId"]["extension"]
            name = json.loads(fetch(ODS_API + region_code))["Organisation"]["Name"]
            cache[icb_code] = (region_code, name.replace(" COMMISSIONING REGION", "").title().replace(" Of ", " of ").replace(" And ", " and "))
        except Exception as exc:  # keep the row, flag it, never guess a region
            print(f"ODS lookup failed for {icb_code}: {exc}", file=sys.stderr)
            cache[icb_code] = ("", "Unmapped")
    return cache[icb_code]


def load_month(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        df = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
    df = df[(df["RTT Part Type"] == "Part_2") & (df["Treatment Function Code"] != "C_999")]  # incomplete pathways, no 'Total' rows
    df = df[df["Commissioner Org Code"] != "NONC"].copy()  # match the published England (commissioner basis) headline
    df["month"] = pd.to_datetime(df["Period"].str.replace("RTT-", ""), format="%B-%Y").dt.strftime("%Y-%m")
    return df.rename(columns={"Provider Org Code": "trust_code", "Provider Org Name": "trust_name",
                              "Treatment Function Name": "specialty"})


def published_series(xlsx_path):
    """Month, total, within 18 weeks, >52 weeks and median from NHS England's overview time series."""
    raw = pd.read_excel(xlsx_path, header=None)
    header = raw.index[raw[2] == "Month"][0]
    labels = raw.iloc[header + 1]
    assert labels[3] == "Median wait (weeks)" and labels[5] == "No. within 18 weeks", "time series layout changed"
    assert labels[11] == "No. > 52 weeks" and labels[21] == "Total waiting (mil)", "time series layout changed"
    assert labels[22] == "Total waiting (mil) with estimates for missing data", "time series layout changed"
    body = raw.iloc[header + 2:, [2, 3, 5, 11, 21, 22]].copy()
    body.columns = ["month", "published_median", "published_within_18", "published_52_plus", "published_total",
                    "published_total_with_estimates_for_missing_trusts"]
    body["month"] = pd.to_datetime(body["month"], errors="coerce").dt.strftime("%Y-%m")
    return body.dropna()


def main():
    zips, timeseries_url = discover_links()
    months = sorted(zips)[-MONTHS:]
    print("Months:", months[0], "to", months[-1])

    cache, frames, national = {}, [], []
    for month in months:
        df = load_month(download(zips[month]))
        bands = band_columns(df)
        pooled = df[bands].sum()
        national.append({"month": month, "our_total": int(pooled.sum()), "our_within_18": int(pooled[:18].sum()),
                         "our_52_plus": int(pooled[52:].sum()), "our_median_estimate": round(median_from_bands(pooled), 2)})
        df["region"] = [region_for(code, cache)[1] for code in df["Provider Parent Org Code"]]
        frames.append(aggregate_bands(df))
        national[-1]["providers_reporting"] = frames[-1]["trust_code"].nunique()
        print(month, "rows:", len(frames[-1]))

    pd.concat(frames).to_csv(OUT_CSV, index=False)

    LOOKUP_CSV.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([(k, *v) for k, v in sorted(cache.items())],
                 columns=["icb_code", "region_code", "region"]).to_csv(LOOKUP_CSV, index=False)

    recon = pd.DataFrame(national).merge(published_series(download(timeseries_url)), on="month", how="left")
    recon["total_difference"] = recon["our_total"] - recon["published_total"]
    recon["our_performance_18_weeks"] = (recon["our_within_18"] / recon["our_total"]).round(4)
    recon["published_performance_18_weeks"] = (recon["published_within_18"] / recon["published_total"]).round(4)
    recon["published_median"] = recon["published_median"].astype(float).round(2)
    RECON_CSV.parent.mkdir(parents=True, exist_ok=True)
    recon.to_csv(RECON_CSV, index=False)
    print(recon.to_string(index=False))


if __name__ == "__main__":
    main()
