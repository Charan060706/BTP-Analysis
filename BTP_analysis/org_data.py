
import json
import shutil
from pathlib import Path
import pandas as pd

# ============================================================
# 1. CONFIGURATION
# ============================================================

# CHANGE THIS to the directory containing your original nested folders.
SOURCE_DIR = Path(
    r"C:\Users\HP\OneDrive\Desktop\BTP_analysis\BTP_Data\CSI_Occupancy_Dataset"
)

# Destination directory for the organized dataset.
OUTPUT_DIR = Path(
    r"C:\Users\HP\OneDrive\Desktop\BTP_analysis\OrganizedDataset"
)

RAW_DIR = OUTPUT_DIR / "raw_packets"
SUMMARY_DIR = OUTPUT_DIR / "window_summary"

MANIFEST_PATH = OUTPUT_DIR / "csv_dataset_manifest.csv"

EXPECTED_REPETITIONS = 8

# ============================================================
# 2. CREATE OUTPUT DIRECTORIES
# ============================================================

RAW_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 65)
print("       WIFI CSI DATASET ORGANIZATION")
print("=" * 65)

# ============================================================
# 3. HELPER FUNCTIONS
# ============================================================

def normalize_room(value):
    """Standardize room names such as rooma -> RoomA."""
    value = str(value).strip().lower()

    if value == "rooma":
        return "RoomA"
    elif value == "roomb":
        return "RoomB"

    return str(value).strip()


def normalize_receiver(value):
    """Standardize receiver names."""
    value = str(value).strip().lower()

    if value in ["rx1", "receiver1", "receiver_1"]:
        return "Rx1"
    elif value in ["rx2", "receiver2", "receiver_2"]:
        return "Rx2"

    return str(value).strip()


def normalize_test_case(value):
    """Standardize case names such as c1 -> C1."""
    value = str(value).strip().upper()

    if value.startswith("C"):
        number = value[1:]
        if number.isdigit():
            return f"C{int(number)}"

    return value


def normalize_repetition(value):
    """Standardize repetition names such as 1 -> Rep01."""
    value = str(value).strip()

    if value.lower().startswith("rep"):
        value = value[3:]

    number = int(value)
    return f"Rep{number:02d}"


def get_metadata(repetition_folder):
    """Read metadata.json from the repetition folder."""

    metadata_path = repetition_folder / "metadata.json"

    if not metadata_path.exists():
        raise FileNotFoundError(
            f"metadata.json missing in {repetition_folder}"
        )

    with open(metadata_path, "r", encoding="utf-8") as file:
        return json.load(file)


# ============================================================
# 4. FIND ALL NESTED RECORDINGS
# ============================================================

manifest_records = []

missing_metadata = []
missing_raw = []
missing_summary = []
duplicate_names = []
failed_records = []

# Keep track of destination filenames already encountered.
used_raw_names = set()
used_summary_names = set()

# Expected nested recording folders contain metadata.json.
metadata_files = list(SOURCE_DIR.rglob("metadata.json"))

print(f"\nFound {len(metadata_files)} metadata files.")
print("Starting extraction...\n")

# ============================================================
# 5. PROCESS EACH REPETITION FOLDER
# ============================================================

for index, metadata_path in enumerate(metadata_files, start=1):

    repetition_folder = metadata_path.parent

    try:
        # Read metadata.
        with open(metadata_path, "r", encoding="utf-8") as file:
            metadata = json.load(file)

        # Extract identifiers from metadata.
        room = normalize_room(metadata["room"])
        receiver = normalize_receiver(metadata["receiver"])
        test_case = normalize_test_case(metadata["test_case"])
        repetition = normalize_repetition(metadata["repetition"])

        # Construct standardized base filename.
        base_name = (
            f"{room}_{receiver}_{test_case}_{repetition}"
        )

        # Original CSV paths.
        raw_source = repetition_folder / "raw_packets.csv"
        summary_source = repetition_folder / "window_summary.csv"

        # Check whether both files exist.
        if not raw_source.exists():
            missing_raw.append(str(repetition_folder))

        if not summary_source.exists():
            missing_summary.append(str(repetition_folder))

        if not raw_source.exists() or not summary_source.exists():
            print(f"[MISSING CSV] {base_name}")
            continue

        # Destination filenames.
        raw_filename = f"{base_name}_raw_packets.csv"
        summary_filename = f"{base_name}_window_summary.csv"

        raw_destination = RAW_DIR / raw_filename
        summary_destination = SUMMARY_DIR / summary_filename

        # Avoid silently overwriting files.
        if raw_filename in used_raw_names or raw_destination.exists():
            duplicate_names.append(str(raw_destination))
            print(f"[DUPLICATE RAW NAME] {raw_filename}")
            continue

        if summary_filename in used_summary_names or summary_destination.exists():
            duplicate_names.append(str(summary_destination))
            print(f"[DUPLICATE SUMMARY NAME] {summary_filename}")
            continue

        # Copy files into their respective folders.
        shutil.copy2(raw_source, raw_destination)
        shutil.copy2(summary_source, summary_destination)

        used_raw_names.add(raw_filename)
        used_summary_names.add(summary_filename)

        # Add a record to the manifest.
        manifest_records.append({
            "base_name": base_name,
            "room": room,
            "receiver": receiver,
            "test_case": test_case,
            "repetition": repetition,

            "file_type": "raw",
            "filename": raw_filename,
            "organized_path": str(raw_destination),

            "capture_datetime": metadata.get("capture_datetime"),
            "people": metadata.get("people"),
            "motion": metadata.get("motion"),
            "router": metadata.get("router"),
            "duration_seconds": metadata.get("duration_seconds"),
            "valid_csi_records": metadata.get("valid_csi_records"),
        })

        manifest_records.append({
            "base_name": base_name,
            "room": room,
            "receiver": receiver,
            "test_case": test_case,
            "repetition": repetition,

            "file_type": "summary",
            "filename": summary_filename,
            "organized_path": str(summary_destination),

            "capture_datetime": metadata.get("capture_datetime"),
            "people": metadata.get("people"),
            "motion": metadata.get("motion"),
            "router": metadata.get("router"),
            "duration_seconds": metadata.get("duration_seconds"),
            "valid_csi_records": metadata.get("valid_csi_records"),
        })

        print(
            f"[{index}/{len(metadata_files)}] "
            f"Copied: {base_name}"
        )

    except Exception as error:
        failed_records.append({
            "folder": str(repetition_folder),
            "error": str(error)
        })

        print(f"[ERROR] {repetition_folder}: {error}")


# ============================================================
# 6. GENERATE DATASET MANIFEST
# ============================================================

manifest_df = pd.DataFrame(manifest_records)

if not manifest_df.empty:

    manifest_df.sort_values(
        by=[
            "room",
            "receiver",
            "test_case",
            "repetition",
            "file_type"
        ],
        inplace=True
    )

    manifest_df.to_csv(MANIFEST_PATH, index=False)

    print("\nManifest successfully generated.")

else:
    print("\nWARNING: No valid recordings were copied.")
    print("Manifest was not generated.")


# ============================================================
# 7. FINAL DATASET REPORT
# ============================================================

raw_count = len(list(RAW_DIR.glob("*.csv")))
summary_count = len(list(SUMMARY_DIR.glob("*.csv")))

print("\n" + "=" * 65)
print("                 FINAL DATASET REPORT")
print("=" * 65)

print(f"\nRaw packet CSV files       : {raw_count}")
print(f"Window summary CSV files  : {summary_count}")
print(f"Total organized CSV files : {raw_count + summary_count}")

print(f"\nExpected raw files        : 256")
print(f"Expected summary files    : 256")
print(f"Expected total files      : 512")

print(f"\nMissing raw CSVs          : {len(missing_raw)}")
print(f"Missing summary CSVs      : {len(missing_summary)}")
print(f"Duplicate filenames       : {len(duplicate_names)}")
print(f"Failed recordings         : {len(failed_records)}")

print("\nFiles per room/receiver/case:")

if not manifest_df.empty:
    counts = (
        manifest_df[manifest_df["file_type"] == "raw"]
        .groupby(["room", "receiver", "test_case"])
        .size()
        .reset_index(name="repetitions_copied")
    )

    print(counts.to_string(index=False))

print("\nOutput locations:")
print(f"Raw packets    : {RAW_DIR}")
print(f"Window summary : {SUMMARY_DIR}")
print(f"Manifest       : {MANIFEST_PATH}")

print("\nDataset organization completed!")
print("=" * 65)
