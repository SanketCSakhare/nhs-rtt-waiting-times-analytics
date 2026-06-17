# NHS Data Source Instructions

Intended source: [NHS England Consultant-led Referral to Treatment Waiting Times](https://www.england.nhs.uk/statistics/statistical-work-areas/rtt-waiting-times/)

## Manual Download

1. Open the NHS England RTT waiting times statistics page.
2. Download the latest monthly consultant-led RTT files.
3. Extract the relevant organisation/specialty waiting-list tables.
4. Convert the data to a CSV shaped like:

```text
data/raw/nhs_rtt_demo.csv
```

Expected columns:

- `month`
- `region`
- `trust_code`
- `trust_name`
- `specialty`
- `total_waiting_list`
- `within_18_weeks`
- `waiting_18_to_52_weeks`
- `waiting_52_plus_weeks`
- `median_wait_weeks`

If official data is not downloaded yet, run:

```powershell
python src/generate_demo_data.py
```

The demo data is synthetic but structured to resemble aggregate NHS RTT performance reporting.

