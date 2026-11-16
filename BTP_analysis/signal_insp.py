
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(
    r"C:\Users\HP\OneDrive\Desktop\BTP_analysis\OrganizedDataset"
)

RAW_DIR = BASE_DIR / "raw_packets"

# Choose one recording for initial inspection
FILE = RAW_DIR / "RoomA_Rx1_C1_Rep01_raw_packets.csv"

df = pd.read_csv(FILE)

print("\n========== DATASET INFORMATION ==========")

print("File:", FILE.name)
print("Shape:", df.shape)

print("\n========== COLUMN NAMES ==========")
print(df.columns.tolist())

print("\n========== DATA TYPES ==========")
print(df.dtypes.to_string())

# --------------------------------------------------
# RSSI inspection
# --------------------------------------------------

print("\n========== RSSI INSPECTION ==========")

print("RSSI sample values:")
print(df["rssi_dbm"].head(10).tolist())

print("\nRSSI statistics:")
print(df["rssi_dbm"].describe())

print("\nRSSI missing values:", df["rssi_dbm"].isna().sum())

# --------------------------------------------------
# CSI subcarrier inspection
# --------------------------------------------------

subcarrier_cols = [
    col for col in df.columns
    if col.startswith("subcarrier_")
]

print("\n========== CSI SUBCARRIER INSPECTION ==========")

print("Number of subcarrier columns:", len(subcarrier_cols))

print("\nFirst 5 packets:")
print(df[subcarrier_cols].head())

print("\nSubcarrier data types:")
print(df[subcarrier_cols].dtypes.value_counts())

print("\nSubcarrier statistics:")
print(df[subcarrier_cols].describe().round(3).to_string())

# --------------------------------------------------
# CSI HEX inspection
# --------------------------------------------------

print("\n========== CSI HEX INSPECTION ==========")

if "csi_hex" in df.columns:
    print(df["csi_hex"].head(5).to_string())

# --------------------------------------------------
# CSI validity information
# --------------------------------------------------

print("\n========== CSI VALIDITY ==========")

for col in ["csi_length", "first_word_invalid"]:
    if col in df.columns:
        print(f"\n{col}:")
        print(df[col].value_counts(dropna=False).head(15))

print("\nInspection complete!")
