
from pathlib import Path
import pandas as pd
import numpy as np
import re

BASE_DIR = Path(
    r"C:\Users\HP\OneDrive\Desktop\BTP_analysis\OrganizedDataset"
)

RAW_DIR = BASE_DIR / "raw_packets"

files = sorted(RAW_DIR.glob("*.csv"))

results = []

for file in files:
    df = pd.read_csv(file)

    timestamps = pd.to_numeric(
        df["timestamp_us"], errors="coerce"
    ).dropna()

    if len(timestamps) < 2:
        continue

    timestamps = timestamps.sort_values().to_numpy(dtype=np.float64)

    duration = (timestamps[-1] - timestamps[0]) / 1_000_000

    packet_count = len(timestamps)

    packet_rate = (
        (packet_count - 1) / duration
        if duration > 0 else np.nan
    )

    intervals = np.diff(timestamps) / 1_000_000

    results.append({
        "filename": file.name,
        "packet_count": packet_count,
        "duration_seconds": duration,
        "packet_rate_pps": packet_rate,
        "mean_interval_ms": np.mean(intervals) * 1000,
        "median_interval_ms": np.median(intervals) * 1000,
        "max_interval_ms": np.max(intervals) * 1000,
        "min_interval_ms": np.min(intervals) * 1000
    })

quality_df = pd.DataFrame(results)

print("\n========== RECORDING QUALITY ==========")
print(quality_df.describe().round(3).to_string())

print("\n========== RECORDINGS WITH DURATION ISSUES ==========")

duration_issues = quality_df[
    (quality_df["duration_seconds"] < 115) |
    (quality_df["duration_seconds"] > 125)
]

print("Number of duration issues:", len(duration_issues))
print(duration_issues.to_string(index=False))

print("\n========== LOW PACKET RATE RECORDINGS ==========")

print(
    quality_df.nsmallest(10, "packet_rate_pps")[
        ["filename", "packet_count", "duration_seconds", "packet_rate_pps"]
    ].to_string(index=False)
)

quality_df.to_csv(
    BASE_DIR / "recording_quality_report.csv",
    index=False
)

print("\nReport saved successfully!")
