
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# --------------------------------------------------
# PATHS
# --------------------------------------------------

# Run this script from your BTP_analysis directory.
BASE_DIR = Path(
    r"C:\Users\HP\OneDrive\Desktop\BTP_analysis\OrganizedDataset"
)

INPUT_FILE = BASE_DIR / "rssi_recording_statistics.csv"

OUTPUT_DIR = BASE_DIR / "rssi_analysis"
OUTPUT_DIR.mkdir(exist_ok=True)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE)

print("Total recordings:", len(df))
print("Columns:", df.columns.tolist())

# --------------------------------------------------
# CASE-WISE STATISTICS ACROSS REPETITIONS
# --------------------------------------------------

summary = (
    df.groupby(["room", "receiver", "case"])["rssi_mean"]
    .agg(
        mean_rssi="mean",
        std_across_repetitions="std",
        min_rssi="min",
        max_rssi="max",
        repetition_count="count"
    )
    .reset_index()
)

summary["case_number"] = (
    summary["case"].str.extract(r"(\d+)").astype(int)
)

summary = summary.sort_values(
    ["room", "receiver", "case_number"]
)

summary.to_csv(
    OUTPUT_DIR / "rssi_casewise_summary.csv",
    index=False
)

print("\n========== CASE-WISE RSSI SUMMARY ==========")
print(summary.to_string(index=False))

# --------------------------------------------------
# PLOT FOUR ROOM-RECEIVER COMBINATIONS
# --------------------------------------------------

groups = [
    ("RoomA", "Rx1"),
    ("RoomA", "Rx2"),
    ("RoomB", "Rx1"),
    ("RoomB", "Rx2")
]

fig, axes = plt.subplots(
    2, 2,
    figsize=(15, 10),
    sharey=True
)

for ax, (room, receiver) in zip(axes.flat, groups):

    data = summary[
        (summary["room"] == room) &
        (summary["receiver"] == receiver)
    ].sort_values("case_number")

    ax.errorbar(
        data["case"],
        data["mean_rssi"],
        yerr=data["std_across_repetitions"].fillna(0),
        marker="o",
        capsize=5,
        linewidth=2
    )

    ax.set_title(f"{room} - {receiver}")
    ax.set_xlabel("Test Case")
    ax.set_ylabel("Mean RSSI (dBm)")

    ax.set_xticks(data["case"])
    ax.grid(alpha=0.3)

fig.suptitle(
    "Case-wise RSSI Comparison Across Repetitions",
    fontsize=16
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "rssi_casewise_comparison.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print("\nGraph saved successfully!")
