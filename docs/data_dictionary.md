# Data Dictionary

| Field | Description |
| --- | --- |
| month | Reporting month (month-end snapshot), `YYYY-MM` |
| region | NHS England region of the provider's parent Integrated Care Board, from the ODS API (`data/reference/icb_region_lookup.csv`) |
| trust_code | Provider organisation code as published. Includes independent sector providers, not only NHS trusts |
| trust_name | Provider organisation name as published |
| specialty | Treatment function name as published |
| total_waiting_list | Incomplete RTT pathways at month end, English commissioners only |
| within_18_weeks | Pathways waiting up to 18 weeks (weekly bands 0-1 to 17-18) |
| waiting_18_to_52_weeks | Pathways waiting over 18 and up to 52 weeks |
| waiting_52_plus_weeks | Pathways waiting over 52 weeks |
| median_wait_weeks | Estimated median wait, interpolated inside the weekly band that holds the middle pathway |
| avg_median_wait_weeks | Summary tables only: unweighted mean of the row-level median estimates. It is not a pooled median. The pooled national estimate is in `national_reconciliation.csv` |
| performance_18_weeks | within_18_weeks / total_waiting_list |
| long_waiter_share | waiting_52_plus_weeks / total_waiting_list |
| pressure_band | Band created by this project: High if performance is below 60% or 52+ week share is 4% or more; Medium if below 70% or 2.5% or more; otherwise Lower. These thresholds are this project's own, not an NHS standard |
| recovery_priority | Label derived from pressure_band |
