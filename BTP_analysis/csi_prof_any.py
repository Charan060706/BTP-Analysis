
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(
    r"C:\Users\HP\OneDrive\Desktop\BTP_analysis\OrganizedDataset"
)

RAW_DIR = BASE_DIR / "raw_packets"

OUTPUT_DIR = BASE_DIR / "csi_analysis"
OUTPUT_DIR.mkdir(exist_ok=True)

ROOM = "RoomB"
RECEIVER = "Rx1"
CASE = "C1"

# The 12 consistently zero columns are excluded.
ACTIVE_INDICES = list(range(1, 27)) + list(range(38, 64))

SUBCARRIER_COLS = [
    f"subcarrier_{i:02d}" for i in ACTIVE_INDICES
]

# --------------------------------------------------
# LOAD THE EIGHT REPETITIONS
# --------------------------------------------------

recording_profiles = []
recording_variations = []

for rep in range(1, 9):

    filename = (
        f"{ROOM}_{RECEIVER}_{CASE}_Rep{rep:02d}_raw_packets.csv"
    )

    filepath = RAW_DIR / filename

    if not filepath.exists():
        print("Missing file:", filename)
        continue

    df = pd.read_csv(filepath)

    # Ensure the required columns exist
    missing_cols = [
        col for col in SUBCARRIER_COLS
        if col not in df.columns
    ]

    if missing_cols:
        raise ValueError(
            f"Missing subcarrier columns in {filename}: {missing_cols}"
        )

    # Convert to numeric and calculate statistics
    csi = df[SUBCARRIER_COLS].apply(
        pd.to_numeric, errors="coerce"
    )

    mean_profile = csi.mean(axis=0)
    std_profile = csi.std(axis=0, ddof=0)

    recording_profiles.append(
        mean_profile.to_numpy()
    )

    recording_variations.append(
        std_profile.to_numpy()
    )

    print(
        f"{filename}: "
        f"{len(df)} packets processed"
    )

# --------------------------------------------------
# CONVERT TO ARRAYS
# --------------------------------------------------

mean_matrix = np.array(recording_profiles)
std_matrix = np.array(recording_variations)

if len(mean_matrix) == 0:
    raise RuntimeError("No recordings were successfully loaded.")

subcarrier_indices = np.array(ACTIVE_INDICES)

print("\nMean matrix shape:", mean_matrix.shape)
print("Standard deviation matrix shape:", std_matrix.shape)

# --------------------------------------------------
# GRAPH A: MEAN CSI PROFILE
# --------------------------------------------------

plt.figure(figsize=(15, 6))

for i in range(len(mean_matrix)):

    plt.plot(
        subcarrier_indices,
        mean_matrix[i],
        marker="o",
        markersize=3,
        linewidth=1.5,
        label=f"Rep{i+1:02d}"
    )

plt.title(
    f"CSI Mean Profile Across Repetitions - "
    f"{ROOM} {RECEIVER} {CASE}"
)

plt.xlabel("Subcarrier Index")
plt.ylabel("Mean Stored CSI Subcarrier Value")

plt.xticks(ACTIVE_INDICES, rotation=90)
plt.grid(alpha=0.3)
plt.legend(ncol=4)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "csi_mean_profile_C1.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

# --------------------------------------------------
# GRAPH B: CSI STANDARD DEVIATION PROFILE
# --------------------------------------------------

plt.figure(figsize=(15, 6))

for i in range(len(std_matrix)):

    plt.plot(
        subcarrier_indices,
        std_matrix[i],
        marker="o",
        markersize=3,
        linewidth=1.5,
        label=f"Rep{i+1:02d}"
    )

plt.title(
    f"CSI Standard Deviation Across Repetitions - "
    f"{ROOM} {RECEIVER} {CASE}"
)

plt.xlabel("Subcarrier Index")
plt.ylabel("Within-Recording Standard Deviation")

plt.xticks(ACTIVE_INDICES, rotation=90)
plt.grid(alpha=0.3)
plt.legend(ncol=4)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "csi_std_profile_C1.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

# --------------------------------------------------
# PAIRWISE CORRELATION BETWEEN REPETITIONS
# --------------------------------------------------

correlation_matrix = np.corrcoef(mean_matrix)

correlation_df = pd.DataFrame(
    correlation_matrix,
    index=[f"Rep{i:02d}" for i in range(1, len(mean_matrix)+1)],
    columns=[f"Rep{i:02d}" for i in range(1, len(mean_matrix)+1)]
)

correlation_df.to_csv(
    OUTPUT_DIR / "csi_repetition_correlation_C1.csv"
)

print("\n========== PAIRWISE CSI CORRELATION ==========")
print(correlation_df.round(3))

# --------------------------------------------------
# SAVE NUMERICAL PROFILES
# --------------------------------------------------

mean_df = pd.DataFrame(
    mean_matrix,
    columns=SUBCARRIER_COLS
)

mean_df.insert(
    0, "repetition",
    [f"Rep{i:02d}" for i in range(1, len(mean_matrix)+1)]
)

mean_df.to_csv(
    OUTPUT_DIR / "csi_mean_profiles_C1.csv",
    index=False
)

std_df = pd.DataFrame(
    std_matrix,
    columns=SUBCARRIER_COLS
)

std_df.insert(
    0, "repetition",
    [f"Rep{i:02d}" for i in range(1, len(std_matrix)+1)]
)

std_df.to_csv(
    OUTPUT_DIR / "csi_std_profiles_C1.csv",
    index=False
)

print("\nCSI profile analysis completed!")
print("Results saved in:", OUTPUT_DIR)
