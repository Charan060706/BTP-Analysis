
from pathlib import Path
import pandas as pd
import re

# --------------------------------------------------
# 1. CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(
    r"C:\Users\HP\OneDrive\Desktop\BTP_analysis\OrganizedDataset"
)

RAW_DIR = BASE_DIR / "raw_packets"
SUMMARY_DIR = BASE_DIR / "window_summary"

EXPECTED_ROOMS = ["RoomA", "RoomB"]
EXPECTED_RECEIVERS = ["Rx1", "Rx2"]
EXPECTED_CASES = [f"C{i}" for i in range(1, 9)]
EXPECTED_REPS = {f"Rep{i:02d}" for i in range(1, 9)}

# Example:
# RoomA_Rx1_C1_Rep01_raw_packets.csv

PATTERN = re.compile(
    r"^(RoomA|RoomB)_(Rx1|Rx2)_(C[1-8])_(Rep\d{2})_(raw_packets|window_summary)\.csv$"
)

# --------------------------------------------------
# 2. CHECK FOLDERS
# --------------------------------------------------

print("========== FOLDER CHECK ==========")

for folder in [RAW_DIR, SUMMARY_DIR]:
    print(folder, "->", "EXISTS" if folder.exists() else "MISSING")

if not RAW_DIR.exists() or not SUMMARY_DIR.exists():
    raise FileNotFoundError("Please check your OrganizedDataset folder paths.")

# --------------------------------------------------
# 3. COLLECT AND IDENTIFY FILES
# --------------------------------------------------

raw_files = list(RAW_DIR.glob("*.csv"))
summary_files = list(SUMMARY_DIR.glob("*.csv"))

print("\n========== FILE COUNTS ==========")
print("Raw packet CSVs:", len(raw_files))
print("Window summary CSVs:", len(summary_files))
print("Total CSVs:", len(raw_files) + len(summary_files))

def parse_filename(path, expected_type):
    match = PATTERN.match(path.name)

    if not match:
        return None

    room, receiver, case, rep, file_type = match.groups()

    if file_type != expected_type:
        return None

    return {
        "room": room,
        "receiver": receiver,
        "case": case,
        "repetition": rep,
        "filename": path.name
    }

raw_records = [
    parse_filename(f, "raw_packets")
    for f in raw_files
]

summary_records = [
    parse_filename(f, "window_summary")
    for f in summary_files
]

raw_records = [r for r in raw_records if r is not None]
summary_records = [r for r in summary_records if r is not None]

raw_df = pd.DataFrame(raw_records)
summary_df = pd.DataFrame(summary_records)

print("\n========== VALID FILENAMES ==========")
print("Valid raw filenames:", len(raw_df))
print("Valid summary filenames:", len(summary_df))

# --------------------------------------------------
# 4. CHECK ALL 32 COMBINATIONS
# --------------------------------------------------

expected_combinations = []

for room in EXPECTED_ROOMS:
    for receiver in EXPECTED_RECEIVERS:
        for case in EXPECTED_CASES:
            expected_combinations.append((room, receiver, case))

def check_combinations(df, file_type):
    print(f"\n========== {file_type.upper()} REPETITION CHECK ==========")

    issues = []
    rows = []

    for room, receiver, case in expected_combinations:

        if df.empty:
            actual_reps = set()
        else:
            selected = df[
                (df["room"] == room) &
                (df["receiver"] == receiver) &
                (df["case"] == case)
            ]
            actual_reps = set(selected["repetition"])

        missing = sorted(EXPECTED_REPS - actual_reps)
        unexpected = sorted(actual_reps - EXPECTED_REPS)

        count = len(selected) if not df.empty else 0

        rows.append({
            "room": room,
            "receiver": receiver,
            "case": case,
            "file_count": count,
            "missing_repetitions": ", ".join(missing),
            "unexpected_repetitions": ", ".join(unexpected),
            "status": "PASS" if count == 8 and not missing and not unexpected
                      else "CHECK"
        })

        if count != 8 or missing or unexpected:
            issues.append((room, receiver, case, missing, unexpected, count))

    result = pd.DataFrame(rows)

    print(result.to_string(index=False))
    print("\nPassing combinations:", (result["status"] == "PASS").sum(), "/ 32")
    print("Problematic combinations:", len(issues))

    return result

raw_check = check_combinations(raw_df, "raw_packets")
summary_check = check_combinations(summary_df, "window_summary")

# --------------------------------------------------
# 5. CHECK MATCHING RAW AND SUMMARY FILES
# --------------------------------------------------

print("\n========== MATCHING FILE CHECK ==========")

raw_keys = set(
    raw_df["filename"].str.replace(
        "_raw_packets.csv", "", regex=False
    )
) if not raw_df.empty else set()

summary_keys = set(
    summary_df["filename"].str.replace(
        "_window_summary.csv", "", regex=False
    )
) if not summary_df.empty else set()

print("Raw files without summary:", len(raw_keys - summary_keys))
print("Summary files without raw:", len(summary_keys - raw_keys))

if raw_keys - summary_keys:
    print("Missing summaries:", sorted(raw_keys - summary_keys))

if summary_keys - raw_keys:
    print("Missing raw files:", sorted(summary_keys - raw_keys))

# --------------------------------------------------
# 6. CHECK CSV STRUCTURE AND READABILITY
# --------------------------------------------------

print("\n========== CSV STRUCTURE CHECK ==========")

def inspect_csv_files(files, file_type):
    results = []
    reference_columns = None

    for file in sorted(files):

        try:
            df = pd.read_csv(file)

            if reference_columns is None:
                reference_columns = list(df.columns)

            results.append({
                "filename": file.name,
                "rows": len(df),
                "columns": len(df.columns),
                "empty": df.empty,
                "same_schema": list(df.columns) == reference_columns,
                "status": "PASS" if (
                    not df.empty and
                    list(df.columns) == reference_columns
                ) else "CHECK"
            })

        except Exception as e:
            results.append({
                "filename": file.name,
                "rows": None,
                "columns": None,
                "empty": None,
                "same_schema": False,
                "status": f"ERROR: {str(e)}"
            })

    result = pd.DataFrame(results)

    if not result.empty:
        print(f"\n{file_type}:")
        print("Readable:", result["rows"].notna().sum(), "/", len(files))
        print("Empty files:", result["empty"].eq(True).sum())
        print("Schema mismatches:", result["same_schema"].eq(False).sum())
        print("Total rows:", result["rows"].sum())

    return result

raw_structure = inspect_csv_files(raw_files, "RAW PACKETS")
summary_structure = inspect_csv_files(summary_files, "WINDOW SUMMARY")

# --------------------------------------------------
# 7. SAVE VALIDATION REPORTS
# --------------------------------------------------

raw_check.to_csv(BASE_DIR / "raw_repetition_validation.csv", index=False)
summary_check.to_csv(BASE_DIR / "summary_repetition_validation.csv", index=False)

raw_structure.to_csv(BASE_DIR / "raw_structure_validation.csv", index=False)
summary_structure.to_csv(BASE_DIR / "summary_structure_validation.csv", index=False)

print("\n========== VALIDATION COMPLETE ==========")
print("Reports saved inside:", BASE_DIR)
