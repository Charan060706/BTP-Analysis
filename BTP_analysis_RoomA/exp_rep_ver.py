
import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# =============================================================================
# 1. CONFIGURATION
# =============================================================================

ORGANIZED_DIR = Path(
    r"C:\Users\HP\OneDrive\Desktop\BTP_analysis"
)

MANIFEST_PATH = ORGANIZED_DIR / "csv_dataset_manifest.csv"

OUTPUT_DIR = ORGANIZED_DIR / "batch_rep_results"
PLOTS_DIR = OUTPUT_DIR / "plots"
REPORT_DIR = OUTPUT_DIR / "reports"

PLOTS_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

EXPECTED_REPETITIONS = 8

# Tolerance used to identify subcarriers that are zero throughout
ZERO_TOLERANCE = 1e-10

# Number of subcarriers expected
EXPECTED_SUBCARRIERS = 64


# =============================================================================
# 2. HELPER FUNCTIONS
# =============================================================================

def get_repetition_number(value):
    """Extract repetition number from values such as Rep01 or 1."""

    match = re.search(r"(\d+)", str(value))

    return int(match.group(1)) if match else np.nan


def weighted_mean(values, weights):
    """Calculate weighted mean while ignoring invalid values."""

    values = pd.to_numeric(values, errors="coerce")
    weights = pd.to_numeric(weights, errors="coerce")

    valid = (
        values.notna()
        & weights.notna()
        & np.isfinite(values)
        & np.isfinite(weights)
        & (weights > 0)
    )

    if not valid.any():
        return values.mean()

    return np.average(
        values[valid],
        weights=weights[valid]
    )


def get_subcarrier_columns(df):
    """Identify and numerically sort subcarrier columns."""

    columns = [
        col for col in df.columns
        if re.match(r"subcarrier_\d+$", str(col), re.IGNORECASE)
    ]

    return sorted(
        columns,
        key=lambda col: int(re.search(r"(\d+)$", col).group(1))
    )


def safe_round(value, digits=4):
    """Safely round numerical values."""

    if pd.isna(value):
        return np.nan

    return round(float(value), digits)


# =============================================================================
# 3. LOAD MANIFEST
# =============================================================================

if not MANIFEST_PATH.exists():
    raise FileNotFoundError(
        f"Manifest not found: {MANIFEST_PATH}"
    )

manifest = pd.read_csv(MANIFEST_PATH)

required_columns = [
    "room",
    "receiver",
    "test_case",
    "repetition",
    "file_type",
    "organized_path"
]

missing_columns = [
    col for col in required_columns
    if col not in manifest.columns
]

if missing_columns:
    raise ValueError(
        f"Missing manifest columns: {missing_columns}"
    )

for col in ["room", "receiver", "test_case", "file_type"]:
    manifest[col] = manifest[col].astype(str).str.strip()

manifest["file_type"] = manifest["file_type"].str.lower()

# Only summary CSV files are used in this analysis.
summary_manifest = manifest[
    manifest["file_type"] == "summary"
].copy()

experiments = (
    summary_manifest[
        ["room", "receiver", "test_case"]
    ]
    .drop_duplicates()
    .sort_values(
        ["room", "receiver", "test_case"]
    )
)

print("=" * 75)
print("BATCH CSI/RSSI REPEATABILITY ANALYSIS")
print("=" * 75)

print(f"Scenarios found: {len(experiments)}")
print(f"Expected repetitions per scenario: {EXPECTED_REPETITIONS}")


# =============================================================================
# 4. MASTER RESULT CONTAINERS
# =============================================================================

summary_results = []
quality_results = []

# Stores repetition profiles for each scenario
all_profiles = {}


# =============================================================================
# 5. PROCESS EACH SCENARIO
# =============================================================================

for _, exp in experiments.iterrows():

    room = exp["room"]
    rx = exp["receiver"]
    case = exp["test_case"]

    print(f"\nProcessing: {room} | {rx} | {case}")

    # -------------------------------------------------------------------------
    # Get all repetitions belonging to this scenario
    # -------------------------------------------------------------------------

    runs = summary_manifest[
        (summary_manifest["room"].str.upper() == room.upper())
        & (summary_manifest["receiver"].str.upper() == rx.upper())
        & (summary_manifest["test_case"].str.upper() == case.upper())
    ].copy()

    runs["rep_num"] = runs["repetition"].apply(
        get_repetition_number
    )

    runs = runs.dropna(subset=["rep_num"])

    runs["rep_num"] = runs["rep_num"].astype(int)

    runs = runs.sort_values("rep_num")

    # Avoid accidentally counting duplicate manifest entries.
    runs = runs.drop_duplicates(
        subset=["rep_num"],
        keep="first"
    )

    # -------------------------------------------------------------------------
    # Containers for individual repetition metrics
    # -------------------------------------------------------------------------

    repetition_profiles = {}
    repetition_temporal_stds = {}

    rssi_summary = []

    successfully_loaded = 0
    failed_files = []

    # -------------------------------------------------------------------------
    # Read each repetition
    # -------------------------------------------------------------------------

    for _, row in runs.iterrows():

        rep = f"Rep{row['rep_num']:02d}"
        file_path = Path(str(row["organized_path"]))

        try:

            if not file_path.exists():
                raise FileNotFoundError(file_path)

            df = pd.read_csv(file_path)

            if df.empty:
                raise ValueError("CSV is empty")

            successfully_loaded += 1

            # Convert numerical columns
            for col in df.columns:
                if (
                    col.lower() in [
                        "mean_rssi",
                        "std_rssi",
                        "packet_count"
                    ]
                    or col.lower().startswith("subcarrier_")
                ):
                    df[col] = pd.to_numeric(
                        df[col],
                        errors="coerce"
                    )

            # -------------------------------------------------------------
            # A. RSSI analysis
            # -------------------------------------------------------------

            if "mean_rssi" in df.columns:

                rssi_values = df["mean_rssi"].dropna()

                if len(rssi_values) > 0:

                    if "packet_count" in df.columns:
                        repetition_mean_rssi = weighted_mean(
                            df["mean_rssi"],
                            df["packet_count"]
                        )
                    else:
                        repetition_mean_rssi = df["mean_rssi"].mean()

                    # Temporal variation of per-second RSSI means
                    temporal_rssi_std = df["mean_rssi"].std()

                    # Average within-second packet-level RSSI variation
                    if "std_rssi" in df.columns:
                        within_second_rssi_std = df["std_rssi"].mean()
                    else:
                        within_second_rssi_std = np.nan

                    rssi_summary.append({
                        "repetition": rep,
                        "mean_rssi": repetition_mean_rssi,
                        "temporal_rssi_std": temporal_rssi_std,
                        "within_second_rssi_std": within_second_rssi_std
                    })

            # -------------------------------------------------------------
            # B. CSI subcarrier analysis
            # -------------------------------------------------------------

            sc_columns = get_subcarrier_columns(df)

            if not sc_columns:
                raise ValueError("No subcarrier columns found")

            # Calculate mean CSI profile for this repetition
            if "packet_count" in df.columns:

                mean_profile = [
                    weighted_mean(
                        df[col],
                        df["packet_count"]
                    )
                    for col in sc_columns
                ]

            else:

                mean_profile = df[sc_columns].mean(axis=0).values

            repetition_profiles[rep] = np.asarray(
                mean_profile,
                dtype=float
            )

            # Temporal standard deviation of each subcarrier
            temporal_std = df[sc_columns].std(axis=0)

            repetition_temporal_stds[rep] = temporal_std.values

            # -------------------------------------------------------------
            # C. Quality information
            # -------------------------------------------------------------

            quality_results.append({
                "Room": room,
                "Receiver": rx,
                "Test_Case": case,
                "Repetition": rep,
                "Rows_In_Summary": len(df),
                "Subcarrier_Count": len(sc_columns),
                "Missing_Subcarrier_Values": int(
                    df[sc_columns].isna().sum().sum()
                ),
                "File_Status": "Success"
            })

        except Exception as e:

            failed_files.append({
                "Repetition": rep,
                "File": str(file_path),
                "Error": str(e)
            })

            quality_results.append({
                "Room": room,
                "Receiver": rx,
                "Test_Case": case,
                "Repetition": rep,
                "Rows_In_Summary": np.nan,
                "Subcarrier_Count": np.nan,
                "Missing_Subcarrier_Values": np.nan,
                "File_Status": f"Failed: {e}"
            })

            print(f"  Could not process {rep}: {e}")

    # -------------------------------------------------------------------------
    # Skip scenarios with no usable CSI profiles
    # -------------------------------------------------------------------------

    if not repetition_profiles:

        print("  No valid CSI profiles. Skipping scenario.")
        continue

    # -------------------------------------------------------------------------
    # 6. CONSTRUCT DATAFRAMES
    # -------------------------------------------------------------------------

    profile_df = pd.DataFrame(
        repetition_profiles,
        index=sc_columns
    )

    # Ensure all repetitions use the same subcarrier columns.
    # The DataFrame above uses the last successfully read column list.
    # If the schema differs, rebuild using common columns.
    if any(
        len(profile) != len(sc_columns)
        for profile in repetition_profiles.values()
    ):
        print("  Warning: inconsistent subcarrier counts.")

    temporal_std_df = pd.DataFrame(
        repetition_temporal_stds,
        index=sc_columns
    )

    rssi_df = pd.DataFrame(rssi_summary)

    # -------------------------------------------------------------------------
    # 7. IDENTIFY ALWAYS-ZERO SUBCARRIERS
    # -------------------------------------------------------------------------

    # A subcarrier is considered always-zero only if its profile
    # is approximately zero in every successfully loaded repetition.

    zero_mask = (
        profile_df.abs().max(axis=1) <= ZERO_TOLERANCE
    )

    always_zero_sc = profile_df.index[zero_mask].tolist()

    active_profile_df = profile_df.loc[~zero_mask]

    active_temporal_std_df = temporal_std_df.loc[~zero_mask]

    active_count = len(active_profile_df)

    print(f"  Valid repetitions: {successfully_loaded}")
    print(f"  Active subcarriers: {active_count}")
    print(f"  Always-zero subcarriers: {len(always_zero_sc)}")

    # -------------------------------------------------------------------------
    # 8. RSSI METRICS
    # -------------------------------------------------------------------------

    if not rssi_df.empty:

        mean_rssi = rssi_df["mean_rssi"].mean()

        # Difference between highest and lowest repetition mean
        rssi_max_shift = (
            rssi_df["mean_rssi"].max()
            - rssi_df["mean_rssi"].min()
        )

        # Variation of average RSSI between repetitions
        between_run_rssi_std = rssi_df["mean_rssi"].std()

        # Average temporal RSSI fluctuation within recordings
        mean_temporal_rssi_std = (
            rssi_df["temporal_rssi_std"].mean()
        )

        # Average packet-level RSSI variation within each second
        mean_within_second_rssi_std = (
            rssi_df["within_second_rssi_std"].mean()
        )

    else:

        mean_rssi = np.nan
        rssi_max_shift = np.nan
        between_run_rssi_std = np.nan
        mean_temporal_rssi_std = np.nan
        mean_within_second_rssi_std = np.nan

    # -------------------------------------------------------------------------
    # 9. CROSS-RUN CORRELATION
    # -------------------------------------------------------------------------

    if active_count >= 2 and successfully_loaded >= 2:

        corr_matrix = active_profile_df.corr(method="pearson")

        upper_indices = np.triu_indices_from(
            corr_matrix.values,
            k=1
        )

        pairwise_corrs = corr_matrix.values[upper_indices]

        valid_corrs = pairwise_corrs[
            np.isfinite(pairwise_corrs)
        ]

        mean_corr = (
            np.mean(valid_corrs)
            if len(valid_corrs) > 0
            else np.nan
        )

        min_corr = (
            np.min(valid_corrs)
            if len(valid_corrs) > 0
            else np.nan
        )

    else:

        corr_matrix = pd.DataFrame(
            index=active_profile_df.columns,
            columns=active_profile_df.columns
        )

        mean_corr = np.nan
        min_corr = np.nan

    # -------------------------------------------------------------------------
    # 10. BETWEEN-RUN CSI VARIATION
    # -------------------------------------------------------------------------

    # For each subcarrier, calculate its standard deviation
    # across the repetition-level mean profiles.

    between_run_sc_std = active_profile_df.std(axis=1)

    mean_between_run_sc_std = (
        between_run_sc_std.mean()
        if not between_run_sc_std.empty
        else np.nan
    )

    # -------------------------------------------------------------------------
    # 11. WITHIN-RUN TEMPORAL CSI VARIATION
    # -------------------------------------------------------------------------

    # For each repetition, average temporal standard deviation
    # across active subcarriers.

    temporal_std_per_rep = active_temporal_std_df.mean(axis=0)

    mean_temporal_csi_std = (
        temporal_std_per_rep.mean()
        if not temporal_std_per_rep.empty
        else np.nan
    )

    # -------------------------------------------------------------------------
    # 12. MASTER SUMMARY ENTRY
    # -------------------------------------------------------------------------

    summary_results.append({

        "Room": room,
        "Receiver": rx,
        "Test_Case": case,

        "Expected_Repetitions": EXPECTED_REPETITIONS,
        "Valid_Repetitions": successfully_loaded,
        "Failed_Repetitions": EXPECTED_REPETITIONS - successfully_loaded,

        "Mean_RSSI_dBm": safe_round(mean_rssi, 4),

        "Max_RSSI_Shift_dBm": safe_round(
            rssi_max_shift, 4
        ),

        "Between_Run_RSSI_Std_dBm": safe_round(
            between_run_rssi_std, 4
        ),

        "Mean_Temporal_RSSI_Std_dBm": safe_round(
            mean_temporal_rssi_std, 4
        ),

        "Mean_Within_Second_RSSI_Std_dBm": safe_round(
            mean_within_second_rssi_std, 4
        ),

        "Mean_CrossRun_Corr": safe_round(
            mean_corr, 4
        ),

        "Min_CrossRun_Corr": safe_round(
            min_corr, 4
        ),

        "Active_Subcarrier_Count": active_count,

        "Always_Zero_Subcarrier_Count": len(always_zero_sc),

        "Always_Zero_Subcarriers": ", ".join(
            always_zero_sc
        ),

        "Mean_Between_Run_Subcarrier_Std": safe_round(
            mean_between_run_sc_std, 4
        ),

        "Mean_Temporal_CSI_Std": safe_round(
            mean_temporal_csi_std, 4
        )
    })

    # Store profile data for future analysis
    all_profiles[(room, rx, case)] = active_profile_df.copy()

    # -------------------------------------------------------------------------
    # 13. GENERATE VISUALIZATIONS
    # -------------------------------------------------------------------------

    fig, axes = plt.subplots(
        1, 3,
        figsize=(20, 5)
    )

    fig.suptitle(
        f"Repeatability Analysis: {room} | {rx} | {case}",
        fontsize=14,
        fontweight="bold"
    )

    # =====================================================================
    # PLOT 1: RSSI STABILITY
    # =====================================================================

    if not rssi_df.empty:

        axes[0].errorbar(
            rssi_df["repetition"],
            rssi_df["mean_rssi"],
            yerr=rssi_df["temporal_rssi_std"],
            fmt="-o",
            capsize=4,
            color="navy"
        )

        axes[0].set_title("RSSI Stability Across Repetitions")

        axes[0].set_xlabel("Repetition")

        axes[0].set_ylabel("Mean RSSI (dBm)")

        axes[0].tick_params(
            axis="x",
            rotation=45
        )

        axes[0].grid(
            True,
            linestyle="--",
            alpha=0.5
        )

        axes[0].legend(
            ["Mean RSSI ± temporal SD"],
            fontsize=8
        )

    else:

        axes[0].set_title("RSSI Data Unavailable")

    # =====================================================================
    # PLOT 2: CSI PROFILES
    # =====================================================================

    for rep in active_profile_df.columns:

        axes[1].plot(
            active_profile_df.index,
            active_profile_df[rep],
            marker=".",
            markersize=3,
            label=rep,
            alpha=0.8
        )

    axes[1].set_title(
        "CSI Mean Profiles Across Repetitions"
    )

    axes[1].set_xlabel("Subcarriers")

    axes[1].set_ylabel("Mean Recorded CSI Value")

    axes[1].tick_params(
        axis="x",
        rotation=90
    )

    axes[1].legend(
        fontsize=7,
        ncol=2
    )

    axes[1].grid(
        True,
        linestyle="--",
        alpha=0.5
    )

    # =====================================================================
    # PLOT 3: CROSS-RUN CORRELATION
    # =====================================================================

    if not corr_matrix.empty:

        sns.heatmap(
            corr_matrix,
            annot=True,
            fmt=".2f",
            cmap="coolwarm",
            vmin=-1,
            vmax=1,
            center=0,
            square=True,
            ax=axes[2]
        )

        axes[2].set_title(
            "Cross-Run Pearson Correlation"
        )

    else:

        axes[2].set_title(
            "Insufficient Data for Correlation"
        )

    plt.tight_layout()

    fig_path = (
        PLOTS_DIR /
        f"{room}_{rx}_{case}_repeatability.png"
    )

    plt.savefig(
        fig_path,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close(fig)

    # -------------------------------------------------------------------------
    # 14. SAVE INDIVIDUAL SCENARIO REPORTS
    # -------------------------------------------------------------------------

    if not corr_matrix.empty:

        corr_matrix.to_csv(
            REPORT_DIR /
            f"{room}_{rx}_{case}_correlation.csv"
        )

    active_profile_df.to_csv(
        REPORT_DIR /
        f"{room}_{rx}_{case}_CSI_profiles.csv"
    )

    temporal_std_df.to_csv(
        REPORT_DIR /
        f"{room}_{rx}_{case}_temporal_CSI_std.csv"
    )

    if not rssi_df.empty:

        rssi_df.to_csv(
            REPORT_DIR /
            f"{room}_{rx}_{case}_RSSI_metrics.csv",
            index=False
        )


# =============================================================================
# 15. SAVE MASTER REPORTS
# =============================================================================

summary_df = pd.DataFrame(summary_results)

if not summary_df.empty:

    summary_df = summary_df.sort_values(
        ["Room", "Receiver", "Test_Case"]
    )

    summary_path = (
        OUTPUT_DIR /
        "repeatability_summary_matrix.csv"
    )

    summary_df.to_csv(
        summary_path,
        index=False
    )

quality_df = pd.DataFrame(quality_results)

quality_path = (
    OUTPUT_DIR /
    "experiment_quality_report.csv"
)

quality_df.to_csv(
    quality_path,
    index=False
)


# =============================================================================
# 16. FINAL OUTPUT
# =============================================================================

print("\n" + "=" * 75)
print("BATCH REPEATABILITY ANALYSIS COMPLETE")
print("=" * 75)

print(f"Scenarios processed: {len(summary_df)}")

print(
    f"Individual plots saved in:\n{PLOTS_DIR}"
)

print(
    f"\nMaster summary saved in:\n"
    f"{OUTPUT_DIR / 'repeatability_summary_matrix.csv'}"
)

print(
    f"\nQuality report saved in:\n{quality_path}"
)

print("\n--- MASTER REPEATABILITY SUMMARY ---")

if not summary_df.empty:

    print(
        summary_df.to_string(index=False)
    )

print("\n--- EXPERIMENT QUALITY REPORT ---")

if not quality_df.empty:

    print(
        quality_df["File_Status"]
        .value_counts()
        .to_string()
    )

print("\nAnalysis finished successfully.")
