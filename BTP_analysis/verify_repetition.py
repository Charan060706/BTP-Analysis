import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# ==============================================================================
# CONFIGURATION
# ==============================================================================
ORGANIZED_DIR = Path(
    r"C:\Users\HP\OneDrive\Desktop\BTP_analysis\OrganizedDataset"
)
MANIFEST_PATH = ORGANIZED_DIR / "csv_dataset_manifest.csv"

# Destination directory for all plots and summary tables
OUTPUT_DIR = ORGANIZED_DIR / "batch_repeatability_results"
PLOTS_DIR = OUTPUT_DIR / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)
# ==============================================================================

# Load Manifest
if not MANIFEST_PATH.exists():
    raise FileNotFoundError(
        f"Manifest not found at {MANIFEST_PATH}. Please run your cleanup/organization script first."
    )

manifest = pd.read_csv(MANIFEST_PATH)

# Retrieve unique combinations of Room, Receiver, and Test Case
experiments = (
    manifest[["room", "receiver", "test_case"]]
    .drop_duplicates()
    .sort_values(by=["room", "receiver", "test_case"])
)

summary_results = []

print(f"Starting batch repeatability analysis for {len(experiments)} scenarios...\n")

for _, exp in experiments.iterrows():
    room = exp["room"]
    rx = exp["receiver"]
    case = exp["test_case"]

    # Filter summary CSV files for this specific scenario across its repetitions
    runs = manifest[
        (manifest["room"].str.upper() == room.upper())
        & (manifest["receiver"].str.upper() == rx.upper())
        & (manifest["test_case"].str.upper() == case.upper())
        & (manifest["file_type"] == "summary")
    ].copy()

    if len(runs) == 0:
        continue

    # Extract numerical repetition order
    runs["rep_num"] = runs["repetition"].str.extract(r"(\d+)").astype(int)
    runs = runs.sort_values("rep_num")

    rep_subcarrier_means = {}
    rssi_summary = []
    existing_sc = []

    for _, row in runs.iterrows():
        rep = row["repetition"]
        try:
            df = pd.read_csv(row["organized_path"])
        except Exception as e:
            print(f"Error reading {row['organized_path']}: {e}")
            continue

        # RSSI statistics
        if "mean_rssi" in df.columns:
            rssi_summary.append(
                {
                    "repetition": rep,
                    "mean_rssi": df["mean_rssi"].mean(),
                    "std_rssi": df["mean_rssi"].std(),
                }
            )

        # Extract subcarrier columns dynamically
        if not existing_sc:
            existing_sc = [
                col
                for col in df.columns
                if col.lower().startswith("subcarrier_")
            ]

        if existing_sc:
            # Mean subcarrier profile across the 120s duration
            mean_sc_profile = df[existing_sc].mean(axis=0).values
            rep_subcarrier_means[rep] = mean_sc_profile

    if not rep_subcarrier_means:
        continue

    # Convert to DataFrames
    rssi_df = pd.DataFrame(rssi_summary)
    sc_profile_df = pd.DataFrame(rep_subcarrier_means, index=existing_sc)

    # --------------------------------------------------------------------------
    # METRICS CALCULATION
    # --------------------------------------------------------------------------
    # 1. RSSI Metrics
    mean_rssi_all = (
        rssi_df["mean_rssi"].mean() if not rssi_df.empty else np.nan
    )
    rssi_max_shift = (
        (rssi_df["mean_rssi"].max() - rssi_df["mean_rssi"].min())
        if not rssi_df.empty
        else np.nan
    )

    # 2. Cross-Run Correlation Matrix (CSI profile similarity across repetitions)
    corr_matrix = sc_profile_df.corr()

    # Extract off-diagonal correlation values to evaluate repetition consistency
    upper_tri_indices = np.triu_indices_from(corr_matrix, k=1)
    pairwise_corrs = corr_matrix.values[upper_tri_indices]

    mean_corr = (
        np.mean(pairwise_corrs) if len(pairwise_corrs) > 0 else 1.0
    )
    min_corr = (
        np.min(pairwise_corrs) if len(pairwise_corrs) > 0 else 1.0
    )

    # 3. Overall Subcarrier Amplitude Variance across repetitions
    overall_sc_std = sc_profile_df.std(axis=1).mean()

    # Record summary entry for Master Report Table
    summary_results.append(
        {
            "Room": room,
            "Receiver": rx,
            "Test_Case": case,
            "Total_Repetitions": len(runs),
            "Mean_RSSI_dBm": round(mean_rssi_all, 2),
            "Max_RSSI_Shift_dBm": round(rssi_max_shift, 2),
            "Mean_CrossRun_Corr": round(mean_corr, 4),
            "Min_CrossRun_Corr": round(min_corr, 4),
            "Mean_Subcarrier_Std": round(overall_sc_std, 4),
        }
    )

    # --------------------------------------------------------------------------
    # PLOTTING & VISUALIZATION (Saved to plots folder)
    # --------------------------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(18, 4.5))

    # Subplot 1: RSSI Stability
    if not rssi_df.empty:
        axes[0].errorbar(
            rssi_df["repetition"],
            rssi_df["mean_rssi"],
            yerr=rssi_df["std_rssi"],
            fmt="-o",
            capsize=4,
            color="navy",
        )
        axes[0].set_title(f"RSSI Stability ({room} {rx} {case})")
        axes[0].set_ylabel("Mean RSSI (dBm)")
        axes[0].tick_params(axis="x", rotation=45)
        axes[0].grid(True, linestyle="--", alpha=0.5)

    # Subplot 2: CSI Subcarrier Profiles
    for rep in sc_profile_df.columns:
        axes[1].plot(
            sc_profile_df.index, sc_profile_df[rep], label=rep, alpha=0.7
        )
    axes[1].set_title(f"CSI Profiles Across Repetitions ({case})")
    axes[1].set_xlabel("Subcarriers")
    axes[1].set_ylabel("Mean Amplitude")
    axes[1].tick_params(axis="x", rotation=90)
    axes[1].legend(loc="upper right", fontsize=7)
    axes[1].grid(True, linestyle="--", alpha=0.5)

    # Subplot 3: Cross-Run Correlation Heatmap
    sns.heatmap(
        corr_matrix,
        annot=True,
        fmt=".2f",
        cmap="Blues",
        ax=axes[2],
        vmin=0.8,
        vmax=1.0,
    )
    axes[2].set_title("Cross-Run Correlation Matrix")

    plt.tight_layout()
    fig_path = PLOTS_DIR / f"{room}_{rx}_{case}_repeatability.png"
    plt.savefig(fig_path, dpi=200)
    plt.close()

# Save Master Summary Matrix
summary_df = pd.DataFrame(summary_results)
summary_df.sort_values(
    by=["Room", "Receiver", "Test_Case"], inplace=True
)
summary_path = OUTPUT_DIR / "repeatability_summary_matrix.csv"
summary_df.to_csv(summary_path, index=False)

print("\n==================================================================")
print("BATCH REPEATABILITY ANALYSIS COMPLETE")
print("==================================================================")
print(f"Total scenarios processed: {len(summary_df)}")
print(f"Master Summary CSV saved to: {summary_path}")
print(f"Individual Plots saved to:   {PLOTS_DIR}\n")

# Display first few rows of the summary table
print("--- Master Repeatability Summary Table Preview ---")
print(summary_df.head(16).to_string(index=False))