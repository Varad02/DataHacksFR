"""
Demo launcher -- opens key pipeline notebooks in Marimo UI.
Each notebook opens in a separate browser tab.

Usage:
    python demo_marimo.py            # opens all notebooks
    python demo_marimo.py --step 11  # opens the single demo notebook
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NOTEBOOKS = [
    ("11", ROOT / "notebooks/11_demo_run.py"),
    ("02", ROOT / "notebooks/02_extract_shaking_features.py"),
    ("04", ROOT / "notebooks/04_spatial_join.py"),
    ("05", ROOT / "notebooks/05_damage_model.py"),
    ("06", ROOT / "notebooks/06_loss_aggregation.py"),
    ("09", ROOT / "notebooks/09_monte_carlo.py"),
]

def launch(path: Path, port: int):
    print(f"  Launching {path.name} on http://localhost:{port}")
    return subprocess.Popen(
        [sys.executable, "-m", "marimo", "edit", str(path), "--port", str(port), "--no-token"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", help="Run a single notebook by number prefix, e.g. 05")
    parser.add_argument("--sphinx", action="store_true", help="Also build and open Sphinx docs")
    args = parser.parse_args()

    targets = NOTEBOOKS
    if args.step:
        targets = [(k, v) for k, v in NOTEBOOKS if k == args.step]
        if not targets:
            print(f"No notebook with prefix {args.step}. Available: {[k for k,_ in NOTEBOOKS]}")
            sys.exit(1)

    print("Starting Marimo notebooks...")
    procs = []
    base_port = 2718
    for i, (_, path) in enumerate(targets):
        procs.append(launch(path, base_port + i))
        time.sleep(0.5)  # stagger so ports don't collide

    if args.sphinx:
        docs_dir = ROOT / "docs"
        print("\nBuilding Sphinx docs...")
        result = subprocess.run(["make", "html"], cwd=docs_dir, capture_output=True, text=True)
        if result.returncode == 0:
            html_index = docs_dir / "_build/html/index.html"
            subprocess.Popen(["open", str(html_index)])
            print(f"  Opened {html_index}")
        else:
            print("  Sphinx build failed:\n", result.stderr[-500:])

    print(f"\nAll notebooks running. Press Ctrl+C to stop.\n")
    print("URLs:")
    for i, (_, path) in enumerate(targets):
        print(f"  {path.name:45s}  http://localhost:{base_port + i}")

    try:
        for p in procs:
            p.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
        for p in procs:
            p.terminate()

if __name__ == "__main__":
    main()
