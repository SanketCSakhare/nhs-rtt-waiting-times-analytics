# SYNTHETIC OFFLINE FALLBACK ONLY. Random made-up trusts and numbers, used when the real NHS extract
# (src/download_nhs_rtt_data.py) cannot be downloaded. No published figure in this repo comes from it.
from pathlib import Path

import numpy as np
import pandas as pd


np.random.seed(42)
out = Path("data/raw")
out.mkdir(parents=True, exist_ok=True)

regions = ["London", "South East", "Midlands", "North West", "North East and Yorkshire", "South West", "East of England"]
specialties = ["Trauma and Orthopaedics", "Ophthalmology", "Gynaecology", "ENT", "General Surgery", "Urology", "Gastroenterology", "Dermatology"]
months = pd.period_range("2025-04", "2026-03", freq="M").astype(str)

trusts = []
for i in range(1, 36):
    region = str(np.random.choice(regions))
    trusts.append({"trust_code": f"T{i:03d}", "trust_name": f"NHS Trust {i:03d}", "region": region})

rows = []
for month_idx, month in enumerate(months):
    recovery_factor = 1 - month_idx * 0.006
    for trust in trusts:
        trust_pressure = np.random.normal(1.0, 0.18)
        for specialty in specialties:
            specialty_multiplier = {
                "Trauma and Orthopaedics": 1.8,
                "Ophthalmology": 1.45,
                "Gynaecology": 1.25,
                "ENT": 1.18,
                "General Surgery": 1.10,
                "Urology": 1.05,
                "Gastroenterology": 1.0,
                "Dermatology": 0.75,
            }[specialty]
            waiting = int(max(350, np.random.normal(3900, 900) * specialty_multiplier * trust_pressure * recovery_factor))
            performance = np.clip(np.random.normal(0.70, 0.08) - (specialty_multiplier - 1) * 0.06 + month_idx * 0.004, 0.45, 0.88)
            within_18 = int(waiting * performance)
            long_share = np.clip(np.random.normal(0.022, 0.012) + (specialty_multiplier - 1) * 0.015 - month_idx * 0.0009, 0.001, 0.095)
            waiting_52 = int(waiting * long_share)
            waiting_18_52 = max(0, waiting - within_18 - waiting_52)
            median_wait = round(float(np.clip(np.random.normal(15, 4) + (specialty_multiplier - 1) * 4, 5, 36)), 1)
            rows.append(
                {
                    "month": month,
                    "region": trust["region"],
                    "trust_code": trust["trust_code"],
                    "trust_name": trust["trust_name"],
                    "specialty": specialty,
                    "total_waiting_list": waiting,
                    "within_18_weeks": within_18,
                    "waiting_18_to_52_weeks": waiting_18_52,
                    "waiting_52_plus_weeks": waiting_52,
                    "median_wait_weeks": median_wait,
                }
            )

pd.DataFrame(rows).to_csv(out / "nhs_rtt_demo.csv", index=False)
print("Created data/raw/nhs_rtt_demo.csv")

