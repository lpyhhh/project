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
    parser = argparse.ArgumentParser(description="Run genomad for all samples")
    parser.add_argument("--results-megahit", required=True, help="Megahit results directory")
    parser.add_argument("--results-genomad", required=True, help="genomad output directory")
    parser.add_argument("--threads", type=int, required=True, help="Thread count")
    parser.add_argument("--db", required=True, help="genomad database path")
    parser.add_argument("--log-dir", required=True, help="Log directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results_megahit = Path(args.results_megahit)
    results_genomad = Path(args.results_genomad)

    samples = list_samples(results_megahit)
    if not samples:
        raise SystemExit("No contigs found in results_megahit")

    for sample in samples:
        contig = ensure_uncompressed(results_megahit, sample)
        outdir = results_genomad / sample
        cmd: List[str] = [
            "genomad",
            "end-to-end",
            "--cleanup",
            "--splits",
            str(args.threads),
            str(contig),
            str(outdir),
            args.db,
        ]
        run_and_profile(cmd, Path(args.log_dir), f"genomad:{sample}")


if __name__ == "__main__":
    main()
