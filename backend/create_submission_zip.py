import os
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
output_zip = BASE_DIR / "submission_log_analytics_platform.zip"

if output_zip.exists():
    output_zip.unlink()

# Items to include
include_files = [
    "README.md",
    "architecture_design.md",
    "benchmark_report.md",
    "requirements.txt",
    "pytest.ini",
    ".env.example",
    ".gitignore",
]

include_dirs = [
    "backend",
    "frontend",
    "database",
    "reports",
    "prompts",
    "screenshots",
    ".vscode",
    "data/sample",
]

# Patterns/directories to exclude
exclude_patterns = [
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".env",
    ".vite",
    ".pyc",
    ".db",
]

print("Packaging submission zip archive...")

with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
    # 1. Add top-level files
    for fname in include_files:
        fpath = BASE_DIR / fname
        if fpath.exists():
            zipf.write(fpath, arcname=fname)
            print(f"  Added file: {fname}")

    # 2. Add directories recursively with filters
    for dname in include_dirs:
        dpath = BASE_DIR / dname
        if not dpath.exists():
            continue
        for root, dirs, files in os.walk(dpath):
            rel_root = Path(root).relative_to(BASE_DIR)
            
            # Skip excluded directory branches
            if any(ex in str(rel_root).replace("\\", "/") for ex in ["node_modules", "__pycache__", ".pytest_cache", ".git"]):
                continue

            for file in files:
                file_rel = rel_root / file
                file_str = str(file_rel).replace("\\", "/")

                # Exclude unwanted extensions / paths (allow .log under data/sample)
                if any(file_str.endswith(ext) for ext in [".pyc", ".db", ".tmp"]):
                    continue
                if file_str.endswith(".log") and not file_str.startswith("data/sample"):
                    continue
                if "node_modules" in file_str or "__pycache__" in file_str or ".env" == file:
                    continue

                full_path = BASE_DIR / file_rel
                zipf.write(full_path, arcname=str(file_rel))

print(f"\nSuccessfully generated submission ZIP archive:")
print(f"  Path: {output_zip}")
print(f"  Size: {output_zip.stat().st_size / (1024 * 1024):.2f} MB")
