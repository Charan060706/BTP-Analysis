
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(
    r"C:\Users\HP\OneDrive\Desktop\BTP_analysis\OrganizedDataset"
)

RAW_DIR = BASE_DIR / "raw_packets"

all_intervals = []
recording_results = []

for file in sorted(RAW_DIR.glob("*.csv")):

    df = pd.read_csv(file)

    timestamps = pd.to_numeric(
        df["timestamp_us"], errors="coerce"
    ).dropna().sort_values().to_numpy(dtype=np.float64)

    if len(timestamps) < 2:
        continue

    intervals = np.diff(timestamps) / 1000  # milliseconds

    all_intervals.extend(intervals)

    recording_results.append({
        "filename": file.name,
        "median_ms": np.median(intervals),
        "mean_ms": np.mean(intervals),
        "gaps_gt_100ms": np.sum(intervals > 100),
        "gaps_gt_250ms": np.sum(intervals > 250),
        "gaps_gt_500ms": np.sum(intervals > 500),
        "gaps_gt_1000ms": np.sum(intervals > 1000)
    })

intervals_df = np.array(all_intervals)
results_df = pd.DataFrame(recording_results)

print("\n========== GLOBAL INTERVAL DISTRIBUTION ==========")

print(
    pd.Series(intervals_df).describe(
        percentiles=[0.5, 0.75, 0.90, 0.95, 0.99]
    ).round(3)
)

print("\n========== GLOBAL GAP COUNTS ==========")

for threshold in [100, 250, 500, 1000]:
    count = np.sum(intervals_df > threshold)

    print(
        f"Gaps > {threshold} ms: {count} "
        f"({count / len(intervals_df) * 100:.3f}%)"
    )

print("\n========== RECORDINGS WITH MOST LARGE GAPS ==========")

print(
    results_df.sort_values(
        "gaps_gt_500ms", ascending=False
    ).head(15).to_string(index=False)
)

print("\n========== RECORDINGS WITH HIGHEST MEDIAN INTERVAL ==========")

print(
    results_df.nlargest(
        10, "median_ms"
    ).to_string(index=False)
)

results_df.to_csv(
    BASE_DIR / "packet_gap_analysis.csv",
    index=False
)

print("\nSaved packet_gap_analysis.csv")
