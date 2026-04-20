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
python3 scripts/run_checkv.py \
    --results-megahit /media/jjz/hdd/lpy/meige/SCUT-zou/results/megahit \
    --results-checkv /media/jjz/hdd/lpy/meige/SCUT-zou/results/checkv \
    --threads 16 \
    --db /media/jjz/hdd/lpy/DB/checkv-db-v1.5 \
    --log-dir /media/jjz/hdd/lpy/meige/SCUT-zou/logs/checkv
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wrapper to run checkv and print sample names")
    parser.add_argument("--results-megahit", required=True, help="Megahit results directory")
    parser.add_argument("--results-checkv", required=True, help="CheckV output directory")
    parser.add_argument("--threads", type=int, required=True, help="Thread count")
    parser.add_argument("--db", required=True, help="CheckV database path")
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
        str(ROOT / "steps" / "checkv.py"),
        "--results-megahit",
        str(results_megahit),
        "--results-checkv",
        args.results_checkv,
        "--threads",
        str(args.threads),
        "--db",
        args.db,
        "--log-dir",
        args.log_dir,
    ]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
