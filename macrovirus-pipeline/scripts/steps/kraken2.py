#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.perf import run_and_profile
from utils.common import ensure_uncompressed, list_samples


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run kraken2 for all samples")
    parser.add_argument("--results-megahit", required=True, help="Megahit results directory")
    parser.add_argument("--results-kraken2", required=True, help="kraken2 output directory")
    parser.add_argument("--threads", type=int, required=True, help="Thread count")
    parser.add_argument("--db", required=True, help="Kraken2 database path")
    parser.add_argument("--log-dir", required=True, help="Log directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results_megahit = Path(args.results_megahit)
    results_kraken2 = Path(args.results_kraken2)

    samples = list_samples(results_megahit)
    if not samples:
        raise SystemExit("No contigs found in results_megahit")

    for sample in samples:
        contig = ensure_uncompressed(results_megahit, sample)
        outdir = results_kraken2 / sample
        outdir.mkdir(parents=True, exist_ok=True)
        report = outdir / "kraken2_report.txt"
        output = outdir / "kraken2_output.txt"
        cmd: List[str] = [
            "kraken2",
            "--db",
            args.db,
            "--threads",
            str(args.threads),
            "--report",
            str(report),
            "--output",
            str(output),
            str(contig),
        ]
        run_and_profile(cmd, Path(args.log_dir), f"kraken2:{sample}")


if __name__ == "__main__":
    main()
