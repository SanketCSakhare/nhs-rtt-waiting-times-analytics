# NHS Data Source Instructions

Source: [NHS England Consultant-led Referral to Treatment Waiting Times](https://www.england.nhs.uk/statistics/statistical-work-areas/rtt-waiting-times/)

## Automatic download

```powershell
python src/download_nhs_rtt_data.py
```

The script:

1. Reads the statistics page, follows the two most recent yearly pages and collects the monthly "Full CSV data file" zip links. The file names contain upload dates and random suffixes, so they are discovered from the page, not constructed.
2. Downloads the latest 12 months into `data/raw/nhs_england/` (not in git; about 42 MB).
3. Keeps incomplete pathways only (`RTT Part Type = Part_2`), drops the pre-summed `Total` treatment function rows, and drops pathways commissioned outside England (`Commissioner Org Code = NONC`) so that totals match the published England headline.
4. Sums the 105 weekly wait bands across commissioners into one row per month, provider and treatment function.
5. Looks up each provider's parent Integrated Care Board in the NHS ODS API and records its NHS England region in `data/reference/icb_region_lookup.csv`.
6. Writes `data/raw/nhs_rtt_england.csv` and compares monthly totals with NHS England's "RTT Overview Timeseries" workbook in `data/processed/national_reconciliation.csv`.

Output columns: `month`, `region`, `trust_code`, `trust_name`, `specialty`, `total_waiting_list`, `within_18_weeks`, `waiting_18_to_52_weeks`, `waiting_52_plus_weeks`, `median_wait_weeks`.

## Offline fallback (synthetic)

If the real extract is absent, `src/build_nhs_rtt_analysis.py` falls back to `data/raw/nhs_rtt_demo.csv` and prints a warning. Create that file with:

```powershell
python src/generate_demo_data.py
```

It is random synthetic data with made-up trusts. It exists only so the pipeline can be run without a network connection. No figure in the README comes from it.
