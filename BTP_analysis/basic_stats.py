from pathlib import Path

# Set root directory (defaults to current directory)
root_dir = Path(r"C:\Users\HP\OneDrive\Desktop\BTP_analysis\OrganizedDataset")

print(f"{'Folder Name':<25} | {'File Count':<10}")
print("-" * 40)

for folder in sorted(root_dir.iterdir()):
    if folder.is_dir():
        # Counts all nested files inside each subdirectory
        file_count = sum(1 for f in folder.rglob("*") if f.is_file())
        print(f"{folder.name:<25} | {file_count:<10}")