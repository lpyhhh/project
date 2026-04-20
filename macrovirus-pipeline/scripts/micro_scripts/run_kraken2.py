#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import List

import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from utils.common import list_samples

"""
python3 /media/jjz/hdd/lpy/meige/SCUT-zou/scripts/run_kraken2.py \
    --results-megahit /media/jjz/hdd/lpy/meige/SCUT-zou/results/megahit \
    --results-kraken2 /media/jjz/hdd/lpy/meige/SCUT-zou/results/kraken2 \
    --threads 128 \
    --db /media/jjz/hdd/lpy/DB/kraken2 \
    --log-dir /media/jjz/hdd/lpy/meige/SCUT-zou/logs/kraken2
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wrapper to run kraken2 and print sample names")
    parser.add_argument("--results-megahit", required=True, help="Megahit results directory")
    parser.add_argument("--results-kraken2", required=True, help="kraken2 output directory")
    parser.add_argument("--threads", type=int, required=True, help="Thread count")
    parser.add_argument("--db", required=True, help="Kraken2 database path")
    parser.add_argument("--log-dir", required=True, help="Log directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results_megahit = Path(args.results_megahit)
    samples = list_samples(results_megahit)
    if not samples:
        raise SystemExit("No contigs found in results_megahit")

    print("[INFO] Samples:")
    for s in samples:
        print(s)

    cmd: List[str] = [
        "python3",
        str(ROOT / "steps" / "kraken2.py"),
        "--results-megahit",
        str(results_megahit),
        "--results-kraken2",
        args.results_kraken2,
        "--threads",
        str(args.threads),
        "--db",
        args.db,
        "--log-dir",
        args.log_dir,
    ]
    subprocess.run(cmd, check=True)
    cmd: List[str] = [
        "python3",
        str(ROOT / "0mail.py"),
        "--subject",
        " Kraken2 Finished",
        "--body",
        " Kraken2 Finished",
    ]
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    main()
