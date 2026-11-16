
from pathlib import Path
import pandas as pd
import numpy as np

# ==========================================
# PATHS
# ==========================================

BASE_DIR = Path(
    r"C:\Users\HP\OneDrive\Desktop\BTP_analysis\OrganizedDataset"
)

RAW_DIR = BASE_DIR / "raw_packets"

rssi_results = []
csi_results = []

files = sorted(RAW_DIR.glob("*.csv"))

# ==========================================
# PROCESS ALL 256 RECORDINGS
# ==========================================

for index, file in enumerate(files, start=1):

    df = pd.read_csv(file)

    # Extract experiment information from filename
    parts = file.stem.split("_")

    room = parts[0]
    receiver = parts[1]
    case = parts[2]
    repetition = parts[3]

    # --------------------------------------
    # RSSI ANALYSIS
    # --------------------------------------

    rssi = pd.to_numeric(
        df["rssi_dbm"], errors="coerce"
    ).dropna()

    rssi_results.append({
        "room": room,
        "receiver": receiver,
        "case": case,
        "repetition": repetition,
        "filename": file.name,
        "packet_count": len(df),
        "rssi_mean": rssi.mean(),
        "rssi_median": rssi.median(),
        "rssi_std": rssi.std(),
        "rssi_min": rssi.min(),
        "rssi_max": rssi.max(),
        "rssi_q25": rssi.quantile(0.25),
        "rssi_q75": rssi.quantile(0.75)
    })

    # --------------------------------------
    # CSI SUBCARRIER ANALYSIS
    # --------------------------------------

    subcarrier_cols = [
        col for col in df.columns
        if col.startswith("subcarrier_")
    ]

    for col in subcarrier_cols:

        values = pd.to_numeric(
            df[col], errors="coerce"
        ).dropna()

        if len(values) == 0:
            continue

        csi_results.append({
            "room": room,
            "receiver": receiver,
            "case": case,
            "repetition": repetition,
            "filename": file.name,
            "subcarrier": col,
            "mean": values.mean(),
            "std": values.std(),
            "min": values.min(),
            "max": values.max(),
            "zero_percentage": (values == 0).mean() * 100
        })

    if index % 25 == 0:
        print(f"Processed {index}/{len(files)} recordings")

# ==========================================
# CREATE REPORTS
# ==========================================

rssi_df = pd.DataFrame(rssi_results)
csi_df = pd.DataFrame(csi_results)

# Save recording-level reports
rssi_df.to_csv(
    BASE_DIR / "rssi_recording_statistics.csv",
    index=False
)

csi_df.to_csv(
    BASE_DIR / "csi_subcarrier_recording_statistics.csv",
    index=False
)

# ==========================================
# GLOBAL SUBCARRIER SUMMARY
# ==========================================

global_csi = csi_df.groupby("subcarrier").agg(
    mean_of_recording_means=("mean", "mean"),
    std_of_recording_means=("mean", "std"),
    average_within_recording_std=("std", "mean"),
    average_zero_percentage=("zero_percentage", "mean"),
    recordings_with_100_percent_zeros=(
        "zero_percentage",
        lambda x: (x == 100).sum()
    )
).reset_index()

global_csi.to_csv(
    BASE_DIR / "csi_global_subcarrier_summary.csv",
    index=False
)

# ==========================================
# PRINT RESULTS
# ==========================================

print("\n========== RSSI SUMMARY ==========")

print(
    rssi_df[
        ["rssi_mean", "rssi_std", "rssi_min", "rssi_max"]
    ].describe().round(3)
)

print("\n========== LOWEST MEAN RSSI RECORDINGS ==========")

print(
    rssi_df.nsmallest(10, "rssi_mean")[
        ["filename", "rssi_mean", "rssi_std"]
    ].to_string(index=False)
)

print("\n========== HIGHEST RSSI VARIABILITY ==========")

print(
    rssi_df.nlargest(10, "rssi_std")[
        ["filename", "rssi_mean", "rssi_std"]
    ].to_string(index=False)
)

print("\n========== GLOBAL CSI SUBCARRIER SUMMARY ==========")

print(global_csi.round(3).to_string(index=False))

print("\n========== REPORTS SAVED ==========")
print("rssi_recording_statistics.csv")
print("csi_subcarrier_recording_statistics.csv")
print("csi_global_subcarrier_summary.csv")
