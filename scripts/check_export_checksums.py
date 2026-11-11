import hashlib
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXPORT_DIR = PROJECT_ROOT / "data" / "exports"
OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "ground_truth"
    / "export_checksums.json"
)


def calculate_sha256(file_path):
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def main():

    if not EXPORT_DIR.exists():
        raise FileNotFoundError(
            f"Export directory not found: {EXPORT_DIR}"
        )

    files = sorted(
        file for file in EXPORT_DIR.iterdir()
        if file.is_file()
        and file.suffix.lower() in [".csv", ".json", ".sql"]
        and file.name not in [
            "export_manifest.json",
            "export_summary.json",
        ]
    )

    if not files:
        raise ValueError("No export files found.")

    results = []

    for file_path in files:

        results.append({
            "filename": file_path.name,
            "size_bytes": file_path.stat().st_size,
            "sha256": calculate_sha256(file_path),
        })

    report = {
        "description": (
            "SHA-256 baseline checksums of existing recruitment exports."
        ),
        "total_files": len(results),
        "files": results,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print("\nCHECKSUM REPORT GENERATED")
    print("-------------------------")
    print(f"Files processed: {len(results)}")
    print(f"Output: {OUTPUT_FILE}")

    for item in results:
        print(f"{item['filename']}: {item['sha256']}")


if __name__ == "__main__":
    main()