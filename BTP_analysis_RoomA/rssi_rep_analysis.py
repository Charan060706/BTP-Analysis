
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# --------------------------------------------------
# PATHS
# --------------------------------------------------

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

# Ensure repetition order is correct
df["rep_number"] = (
    df["repetition"].str.extract(r"(\d+)").astype(int)
)

df = df.sort_values(
    ["room", "receiver", "case", "rep_number"]
)

# --------------------------------------------------
# REPETITION CONSISTENCY SUMMARY
# --------------------------------------------------

summary = (
    df.groupby(["room", "receiver", "case"])
    .agg(
        repetition_count=("rssi_mean", "count"),
        average_rssi=("rssi_mean", "mean"),
        between_rep_std=("rssi_mean", "std"),
        minimum_rssi=("rssi_mean", "min"),
        maximum_rssi=("rssi_mean", "max"),
        average_within_recording_std=("rssi_std", "mean")
    )
    .reset_index()
)

summary["rssi_range"] = (
    summary["maximum_rssi"] - summary["minimum_rssi"]
)

summary.to_csv(
    OUTPUT_DIR / "rssi_repetition_consistency.csv",
    index=False
)

print("\n========== REPETITION CONSISTENCY ==========")
print(summary.round(3).to_string(index=False))

# --------------------------------------------------
# PLOT: ONE FIGURE PER TEST CASE
# --------------------------------------------------

groups = [
    ("RoomA", "Rx1"),
    ("RoomA", "Rx2"),
    ("RoomB", "Rx1"),
    ("RoomB", "Rx2")
]

for case_number in range(1, 9):

    case = f"C{case_number}"

    fig, axes = plt.subplots(
        2, 2,
        figsize=(13, 9),
        sharey=True
    )

    for ax, (room, receiver) in zip(axes.flat, groups):

        data = df[
            (df["room"] == room) &
            (df["receiver"] == receiver) &
            (df["case"] == case)
        ].sort_values("rep_number")

        ax.plot(
            data["rep_number"],
            data["rssi_mean"],
            marker="o",
            linewidth=2
        )

        ax.set_title(f"{room} - {receiver}")
        ax.set_xlabel("Repetition")
        ax.set_ylabel("Mean RSSI (dBm)")

        ax.set_xticks(range(1, 9))
        ax.set_xticklabels(
            [f"Rep{i:02d}" for i in range(1, 9)],
            rotation=35
        )

        ax.grid(alpha=0.3)

    fig.suptitle(
        f"RSSI Consistency Across Repetitions - {case}",
        fontsize=15
    )

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / f"rssi_repetition_{case}.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

print("\nAll 8 repetition comparison graphs saved!")
print("Output directory:", OUTPUT_DIR)
