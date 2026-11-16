
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import re

# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = Path(
    r"C:\Users\HP\OneDrive\Desktop\BTP_analysis\OrganizedDataset"
)

RAW_DIR = BASE_DIR / "raw_packets"

OUTPUT_DIR = BASE_DIR / "null_subcarrier_analysis"
OUTPUT_DIR.mkdir(exist_ok=True)

# --------------------------------------------------
# PROCESS ALL RAW RECORDINGS
# --------------------------------------------------

records = []

for file in sorted(RAW_DIR.glob("*_raw_packets.csv")):

    match = re.match(
        r"(RoomA|RoomB)_(Rx1|Rx2)_(C\d+)_(Rep\d+)_raw_packets",
        file.stem
    )

    if not match:
        continue

    room, receiver, case, repetition = match.groups()

    df = pd.read_csv(file)

    subcarrier_cols = [
        col for col in df.columns
        if col.startswith("subcarrier_")
    ]

    # Count subcarriers that are zero in every packet
    always_zero = df[subcarrier_cols].eq(0).all(axis=0)

    records.append({
        "room": room,
        "receiver": receiver,
        "case": case,
        "repetition": repetition,
        "always_zero_count": int(always_zero.sum())
    })

record_df = pd.DataFrame(records)

# Save individual recording results
record_df.to_csv(
    OUTPUT_DIR / "casewise_null_subcarrier_recordings.csv",
    index=False
)

print("Total recordings processed:", len(record_df))

# --------------------------------------------------
# CALCULATE CASE-WISE AVERAGES
# --------------------------------------------------

case_summary = (
    record_df
    .groupby(["room", "receiver", "case"])
    ["always_zero_count"]
    .agg(["mean", "min", "max", "std"])
    .reset_index()
)

case_summary["case_number"] = (
    case_summary["case"].str.extract(r"(\d+)").astype(int)
)

case_summary = case_summary.sort_values(
    ["room", "receiver", "case_number"]
)

case_summary.to_csv(
    OUTPUT_DIR / "casewise_null_subcarrier_summary.csv",
    index=False
)

print("\n========== CASE-WISE SUMMARY ==========")
print(case_summary.to_string(index=False))

# --------------------------------------------------
# PLOT: FOUR ROOM-RECEIVER COMBINATIONS
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

    data = case_summary[
        (case_summary["room"] == room) &
        (case_summary["receiver"] == receiver)
    ].sort_values("case_number")

    ax.bar(
        data["case"],
        data["mean"],
        yerr=data["std"].fillna(0),
        capsize=4
    )

    ax.set_title(f"{room} - {receiver}", fontsize=13)
    ax.set_xlabel("Test Case")
    ax.set_ylabel("Average always-zero subcarriers")

    ax.set_xticks(data["case"])
    ax.grid(axis="y", alpha=0.3)

    # Show average values above bars
    for x, y in zip(data["case"], data["mean"]):
        ax.text(
            x, y + 0.05,
            f"{y:.2f}",
            ha="center",
            fontsize=8
        )

fig.suptitle(
    "Case-wise Comparison of Always-Zero Subcarriers",
    fontsize=16
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "casewise_null_subcarrier_comparison.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print("\nGraph and reports saved successfully!")
