
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# --------------------------------------------------
# PATH
# --------------------------------------------------

BASE_DIR = Path(
    r"C:\Users\HP\OneDrive\Desktop\BTP_analysis\OrganizedDataset"
)

INPUT_FILE = BASE_DIR / "csi_global_subcarrier_summary.csv"

OUTPUT_DIR = BASE_DIR / "null_subcarrier_analysis"
OUTPUT_DIR.mkdir(exist_ok=True)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE)

# Extract subcarrier index
df["subcarrier_index"] = (
    df["subcarrier"].str.extract(r"(\d+)").astype(int)
)

df = df.sort_values("subcarrier_index")

# --------------------------------------------------
# PLOT
# --------------------------------------------------

plt.figure(figsize=(15, 6))

plt.bar(
    df["subcarrier_index"],
    df["recordings_with_100_percent_zeros"] / 256 * 100
)

plt.title(
    "Subcarriers Completely Zero Across All Recordings",
    fontsize=15
)

plt.xlabel("Subcarrier Index", fontsize=12)
plt.ylabel("Recordings with 100% Zero Values (%)", fontsize=12)

plt.xticks(range(0, 64, 2))
plt.xlim(-1, 64)
plt.ylim(0, 110)

plt.grid(axis="y", alpha=0.3)

# Highlight the consistently zero subcarriers
null_sc = df[
    df["recordings_with_100_percent_zeros"] == 256
]["subcarrier_index"].tolist()

for index in null_sc:
    plt.text(index, 102, str(index), ha="center", fontsize=8)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "overall_null_subcarriers.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

# --------------------------------------------------
# PRINT FINDINGS
# --------------------------------------------------

print("\n========== NULL SUBCARRIER ANALYSIS ==========")

print("Total subcarriers:", len(df))
print("Always-zero subcarriers:", len(null_sc))
print("Always-zero indices:", null_sc)

print(
    "Percentage of subcarriers always zero:",
    round(len(null_sc) / len(df) * 100, 2),
    "%"
)

print("\nGraph saved successfully!")
