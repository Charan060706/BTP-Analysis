
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from pathlib import Path

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

# ==========================================================
# 1. CONFIGURATION
# ==========================================================

BASE_DIR = Path(
    r"C:\Users\HP\OneDrive\Desktop\BTP_analysis\OrganizedDataset"
)

SUMMARY_DIR = BASE_DIR / "window_summary"

OUTPUT_DIR = BASE_DIR / "occupancy_model_results"
OUTPUT_DIR.mkdir(exist_ok=True)

ROOM = "RoomA"
RECEIVER = "Rx2"

WINDOW_SIZE = 5
RANDOM_STATE = 42

# C1 = empty; C2-C8 = occupied
CASE_LABELS = {
    "C1": 0,
    "C2": 1,
    "C3": 1,
    "C4": 1,
    "C5": 1,
    "C6": 1,
    "C7": 1,
    "C8": 1
}

ACTIVE_INDICES = (
    list(range(1, 27)) +
    list(range(38, 64))
)

SUBCARRIER_COLS = [
    f"subcarrier_{i:02d}"
    for i in ACTIVE_INDICES
]

# ==========================================================
# 2. CREATE FIVE-SECOND FEATURE WINDOWS
# ==========================================================

samples = []

files = sorted(
    SUMMARY_DIR.glob(
        f"{ROOM}_{RECEIVER}_C*_Rep*_window_summary.csv"
    )
)

print("Files found:", len(files))

for file in files:

    match = re.match(
        r"RoomA_Rx2_(C\d+)_(Rep\d+)_window_summary",
        file.stem
    )

    if not match:
        continue

    case, repetition = match.groups()

    if case not in CASE_LABELS:
        continue

    label = CASE_LABELS[case]

    df = pd.read_csv(file)

    required_cols = (
        SUBCARRIER_COLS +
        [
            "mean_rssi",
            "std_rssi",
            "mean_csi_amplitude",
            "std_csi_amplitude",
            "packet_count"
        ]
    )

    missing = [
        col for col in required_cols
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"{file.name} is missing columns: {missing}"
        )

    df[required_cols] = df[required_cols].apply(
        pd.to_numeric,
        errors="coerce"
    )

    # Consecutive, non-overlapping 5-second windows.
    # Incomplete final windows are discarded.
    for start in range(0, len(df), WINDOW_SIZE):

        chunk = df.iloc[start:start + WINDOW_SIZE]

        if len(chunk) != WINDOW_SIZE:
            continue

        features = {}

        # CSI: mean and temporal variation
        # across five one-second summaries.
        for col in SUBCARRIER_COLS:

            features[f"{col}_mean"] = chunk[col].mean()
            features[f"{col}_std"] = chunk[col].std(ddof=0)

        # RSSI features
        features["rssi_mean"] = chunk["mean_rssi"].mean()

        features["rssi_temporal_std"] = (
            chunk["mean_rssi"].std(ddof=0)
        )

        features["rssi_packet_std_mean"] = (
            chunk["std_rssi"].mean()
        )

        # CSI amplitude summary features
        features["csi_amplitude_mean"] = (
            chunk["mean_csi_amplitude"].mean()
        )

        features["csi_amplitude_temporal_std"] = (
            chunk["mean_csi_amplitude"].std(ddof=0)
        )

        # Packet count is retained as an additional feature.
        features["packet_count_mean"] = (
            chunk["packet_count"].mean()
        )

        # Metadata is stored separately, never used as input.
        features["room"] = ROOM
        features["receiver"] = RECEIVER
        features["case"] = case
        features["repetition"] = repetition
        features["label"] = label
        features["window_start_second"] = start

        samples.append(features)

dataset = pd.DataFrame(samples)

if dataset.empty:
    raise RuntimeError("No feature windows were created.")

print("\n========== DATASET CREATED ==========")
print("Total windows:", len(dataset))
print("Number of recordings:", dataset["repetition"].nunique())

dataset.to_csv(
    OUTPUT_DIR / "labelled_feature_dataset.csv",
    index=False
)

# ==========================================================
# 3. VERIFY LABELS AND CLASS DISTRIBUTION
# ==========================================================

print("\nClass distribution:")
print(dataset["label"].value_counts().sort_index())

print("\nCases and labels:")
print(
    dataset.groupby(["case", "label"])
    .size()
)

# Check that every expected recording exists.
expected_recordings = 64

recording_ids = dataset[
    ["case", "repetition"]
].drop_duplicates()

print(
    "\nUnique case-repetition recordings:",
    len(recording_ids)
)

if len(recording_ids) != expected_recordings:
    print(
        "WARNING: Expected 64 recordings. "
        "Investigate missing or unreadable files."
    )

# ==========================================================
# 4. SPLIT BY REPETITION
# ==========================================================

TRAIN_REPS = [
    f"Rep{i:02d}" for i in range(1, 6)
]

VAL_REPS = ["Rep06"]

TEST_REPS = ["Rep07", "Rep08"]

train_df = dataset[
    dataset["repetition"].isin(TRAIN_REPS)
].copy()

val_df = dataset[
    dataset["repetition"].isin(VAL_REPS)
].copy()

test_df = dataset[
    dataset["repetition"].isin(TEST_REPS)
].copy()

print("\n========== SPLIT INFORMATION ==========")

for name, part in [
    ("TRAIN", train_df),
    ("VALIDATION", val_df),
    ("TEST", test_df)
]:

    print(f"\n{name}")
    print("Windows:", len(part))
    print("Recordings:", len(
        part[["case", "repetition"]].drop_duplicates()
    ))
    print("Class counts:")
    print(part["label"].value_counts().sort_index())

# ==========================================================
# 5. DEFINE FEATURE CONFIGURATIONS
# ==========================================================

CSI_FEATURES = [
    f"{col}_{stat}"
    for col in SUBCARRIER_COLS
    for stat in ["mean", "std"]
]

RSSI_FEATURES = [
    "rssi_mean",
    "rssi_temporal_std",
    "rssi_packet_std_mean"
]

EXTRA_FEATURES = [
    "csi_amplitude_mean",
    "csi_amplitude_temporal_std",
    "packet_count_mean"
]

FEATURE_CONFIGS = {
    "CSI_only": CSI_FEATURES,

    "RSSI_only": RSSI_FEATURES,

    "CSI_RSSI_combined": (
        CSI_FEATURES + RSSI_FEATURES + EXTRA_FEATURES
    )
}

# ==========================================================
# 6. UNDERSAMPLE TRAINING DATA ONLY
# ==========================================================

def balance_training_data(data):

    empty = data[data["label"] == 0].copy()

    occupied = data[data["label"] == 1].copy()

    # Keep all empty training windows.
    # Select occupied windows approximately equally
    # from C2-C8, preserving all seven conditions.

    samples_per_case = len(empty) // 7

    selected_occupied = []

    for case in [
        "C2", "C3", "C4", "C5",
        "C6", "C7", "C8"
    ]:

        case_data = occupied[
            occupied["case"] == case
        ]

        n = min(samples_per_case, len(case_data))

        selected_occupied.append(
            case_data.sample(
                n=n,
                random_state=RANDOM_STATE
            )
        )

    balanced_occupied = pd.concat(
        selected_occupied,
        ignore_index=True
    )

    balanced = pd.concat(
        [empty, balanced_occupied],
        ignore_index=True
    )

    return balanced.sample(
        frac=1,
        random_state=RANDOM_STATE
    ).reset_index(drop=True)

# ==========================================================
# 7. DEFINE MODELS
# ==========================================================

def create_models(class_weight):

    return {
        "LogisticRegression": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(
                max_iter=2000,
                class_weight=class_weight,
                random_state=RANDOM_STATE
            ))
        ]),

        "RandomForest": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("model", RandomForestClassifier(
                n_estimators=300,
                max_depth=None,
                class_weight=class_weight,
                random_state=RANDOM_STATE,
                n_jobs=-1
            ))
        ]),

        "SVM": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", SVC(
                kernel="rbf",
                class_weight=class_weight,
                probability=True,
                random_state=RANDOM_STATE
            ))
        ])
    }

# ==========================================================
# 8. TRAIN AND EVALUATE
# ==========================================================

results = []

strategies = {
    "Class_weighting": {
        "data": train_df,
        "class_weight": "balanced"
    },

    "Undersampling": {
        "data": balance_training_data(train_df),
        "class_weight": None
    }
}

for strategy_name, strategy in strategies.items():

    current_train = strategy["data"]

    print("\n\n====================================")
    print("STRATEGY:", strategy_name)
    print("Training class counts:")
    print(current_train["label"].value_counts())
    print("====================================")

    for feature_name, feature_cols in FEATURE_CONFIGS.items():

        X_train = current_train[feature_cols]
        y_train = current_train["label"]

        X_val = val_df[feature_cols]
        y_val = val_df["label"]

        X_test = test_df[feature_cols]
        y_test = test_df["label"]

        models = create_models(
            strategy["class_weight"]
        )

        for model_name, model in models.items():

            print(
                f"\nTraining {model_name} | "
                f"{feature_name} | {strategy_name}"
            )

            model.fit(X_train, y_train)

            # Validation evaluation
            val_pred = model.predict(X_val)

            print(
                "Validation F1:",
                round(
                    f1_score(
                        y_val,
                        val_pred,
                        zero_division=0
                    ),
                    4
                )
            )

            # Final held-out test evaluation
            test_pred = model.predict(X_test)

            accuracy = accuracy_score(
                y_test, test_pred
            )

            precision = precision_score(
                y_test,
                test_pred,
                zero_division=0
            )

            recall = recall_score(
                y_test,
                test_pred,
                zero_division=0
            )

            f1 = f1_score(
                y_test,
                test_pred,
                zero_division=0
            )

            cm = confusion_matrix(
                y_test,
                test_pred,
                labels=[0, 1]
            )

            results.append({
                "strategy": strategy_name,
                "features": feature_name,
                "model": model_name,
                "accuracy": accuracy,
                "precision_occupied": precision,
                "recall_occupied": recall,
                "f1_occupied": f1,
                "macro_f1": f1_score(
                    y_test,
                    test_pred,
                    average="macro",
                    zero_division=0
                )
            })

            print("\nTest classification report:")
            print(
                classification_report(
                    y_test,
                    test_pred,
                    labels=[0, 1],
                    target_names=["Empty", "Occupied"],
                    zero_division=0
                )
            )

            # Save confusion matrix
            plt.figure(figsize=(5, 4))

            sns.heatmap(
                cm,
                annot=True,
                fmt="d",
                cmap="Blues",
                xticklabels=["Empty", "Occupied"],
                yticklabels=["Empty", "Occupied"]
            )

            plt.xlabel("Predicted label")
            plt.ylabel("Actual label")

            plt.title(
                f"{model_name}\n"
                f"{feature_name} - {strategy_name}"
            )

            plt.tight_layout()

            plot_name = (
                f"{strategy_name}_"
                f"{feature_name}_"
                f"{model_name}_confusion.png"
            )

            plt.savefig(
                OUTPUT_DIR / plot_name,
                dpi=250,
                bbox_inches="tight"
            )

            plt.close()

# ==========================================================
# 9. SAVE MODEL COMPARISON
# ==========================================================

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    "macro_f1",
    ascending=False
)

results_df.to_csv(
    OUTPUT_DIR / "model_comparison.csv",
    index=False
)

print("\n\n========== FINAL MODEL COMPARISON ==========")
print(results_df.round(4).to_string(index=False))

print("\nAll results saved in:")
print(OUTPUT_DIR)
