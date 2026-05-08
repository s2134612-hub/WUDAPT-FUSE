"""
Build a clean release zip for WUDAPT-FUSE.

Output:
    releases/WUDAPT-FUSE_v{version}_{YYYYMMDD}.zip

What's included:
    README.md, LICENSE, CITATION.cff, requirements.txt, environment.yml,
    .gitignore, scripts/, src/, configs/, results/ (CSVs only), figures/
    (PNG+SVG+PDF), docs/paper/PAPER_FULL.md

What's EXCLUDED (saves > 50 GB):
    data/raw/, data/processed/, large rasters, __pycache__, intermediate
    docx files, model weights, virtual environments.

Usage:
    python scripts/make_release_zip.py            # auto-generate version
    python scripts/make_release_zip.py 1.0.0      # specify version
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

PROJECT = Path(__file__).resolve().parents[1]
RELEASE_DIR = PROJECT / "releases"
RELEASE_DIR.mkdir(exist_ok=True)

# === Whitelist of paths to include (relative to project root) ===
INCLUDE = [
    "README.md",
    "LICENSE",
    "CITATION.cff",
    "requirements.txt",
    "environment.yml",
    ".gitignore",
    "scripts/",
    "src/",
    "configs/",
    "results/",
    "figures/",
    "docs/paper/PAPER_FULL.md",
]

# === Patterns to skip even within whitelisted folders ===
EXCLUDE_PATTERNS = [
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ipynb_checkpoints",
    ".DS_Store",
    "Thumbs.db",
    ".pyc",
    ".pyo",
    ".swp",
]
# Skip these specific large/intermediate files
EXCLUDE_EXACT = {
    "scripts/check_torch.py",       # local debug script
    "scripts/hello_world.py",       # demo
    "scripts/debug_alignment.py",   # local debug
    "scripts/quick_check.py",       # local debug
    "scripts/check_status.py",      # local utility
    "scripts/check_accounts.py",    # local utility
}


def should_skip(path: Path) -> bool:
    """Return True if path should be excluded from the zip."""
    s = str(path).replace("\\", "/")
    rel = str(path.relative_to(PROJECT)).replace("\\", "/")

    for pat in EXCLUDE_PATTERNS:
        if pat in s:
            return True
    if rel in EXCLUDE_EXACT:
        return True
    # Skip large rasters even if mistakenly in figures/results
    if path.suffix.lower() in (".nc", ".tif", ".geotiff", ".zarr"):
        return True
    # Skip intermediate docx (keep PAPER_FULL.md only)
    if path.name.startswith("WUDAPT-FUSE_") and path.suffix == ".docx":
        return True
    return False


def collect_files() -> list[Path]:
    """Return list of files to include."""
    files = []
    for entry in INCLUDE:
        target = PROJECT / entry
        if target.is_file():
            if not should_skip(target):
                files.append(target)
        elif target.is_dir():
            for f in target.rglob("*"):
                if f.is_file() and not should_skip(f):
                    files.append(f)
    return files


def main():
    if len(sys.argv) > 1:
        version = sys.argv[1]
    else:
        version = "1.0.0"

    timestamp = datetime.now().strftime("%Y%m%d")
    zip_name = f"WUDAPT-FUSE_v{version}_{timestamp}.zip"
    zip_path = RELEASE_DIR / zip_name

    print(f"Building release: {zip_name}")

    files = collect_files()
    print(f"Collected {len(files)} files")

    # Compute total size
    total_size = sum(f.stat().st_size for f in files)
    print(f"Uncompressed size: {total_size / 1e6:.1f} MB")

    # Write zip
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for f in files:
            arc = f.relative_to(PROJECT)
            # Use forward slashes inside the zip (cross-platform best practice)
            arc_str = "WUDAPT-FUSE/" + str(arc).replace("\\", "/")
            zf.write(f, arc_str)

    zip_size = zip_path.stat().st_size / 1e6
    ratio = zip_size / (total_size / 1e6) * 100
    print()
    print(f"✓ Release built:")
    print(f"  Path:       {zip_path}")
    print(f"  Size:       {zip_size:.1f} MB  (compression {ratio:.0f}%)")
    print(f"  File count: {len(files)}")
    print()
    print("Top-level structure inside zip:")
    print("  WUDAPT-FUSE/")
    seen = set()
    for f in files:
        top = str(f.relative_to(PROJECT)).split(os.sep)[0]
        if top not in seen:
            seen.add(top)
            print(f"  ├── {top}{'/' if (PROJECT / top).is_dir() else ''}")
    print()
    print("Next steps:")
    print(f"  1. Upload to Zenodo:  https://zenodo.org/deposit/new")
    print(f"  2. Or attach to GitHub release: https://github.com/s2134612-hub/WUDAPT-FUSE/releases/new")

    return 0


if __name__ == "__main__":
    sys.exit(main())
