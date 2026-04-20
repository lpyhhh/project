#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.perf import run_and_profile
from utils.common import find_read_pair, list_samples_from_reads


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run megahit for all samples")
    parser.add_argument("--raw-data", required=True, help="Reads directory")
    parser.add_argument("--raw-data-alt", default="", help="Alternative reads directory")
    parser.add_argument("--results-megahit", required=True, help="Megahit results directory")
    parser.add_argument("--threads", type=int, required=True, help="Thread count")
    parser.add_argument("--min-contig-len", type=int, default=500, help="Minimum contig length")
    parser.add_argument("--log-dir", required=True, help="Log directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raw_data = Path(args.raw_data)
    raw_data_alt = Path(args.raw_data_alt) if args.raw_data_alt else None
    results_megahit = Path(args.results_megahit)

    samples = list_samples_from_reads(raw_data, raw_data_alt)
    if not samples:
        raise SystemExit("No reads found for megahit")

    for sample in samples:
        pair = find_read_pair(raw_data, raw_data_alt, sample)
        if not pair:
            continue
        r1, r2 = pair
        outdir = results_megahit / sample
        cmd: List[str] = [
            "megahit",
            "-1",
            str(r1),
            "-2",
            str(r2),
            "--min-contig-len",
            str(args.min_contig_len),
            "-t",
            str(args.threads),
            "-o",
            str(outdir),
        ]
        run_and_profile(cmd, Path(args.log_dir), f"megahit:{sample}")


if __name__ == "__main__":
    main()
