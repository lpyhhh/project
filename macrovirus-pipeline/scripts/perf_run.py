#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make utils importable when running directly
CUR = Path(__file__).resolve().parent
UTILS = CUR / "utils"
if str(UTILS) not in sys.path:
    sys.path.insert(0, str(UTILS))

from perf import run_and_profile  # type: ignore


def main() -> int:
    p = argparse.ArgumentParser(description="Run a command and record time/resource metrics")
    p.add_argument("--name", required=True, help="Logical name for this run (used for log files)")
    p.add_argument("--log-dir", required=True, help="Directory to write logs and metrics.jsonl")
    p.add_argument("--work-dir", default=None, help="Working directory to run the command in")
    p.add_argument("cmd", nargs=argparse.REMAINDER, help="Command to run (prefix with --)")
    args = p.parse_args()

    cmd = args.cmd
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        print("[ERROR] No command provided. Use: perf_run.py --name <n> --log-dir <d> -- <cmd> ...", file=sys.stderr)
        return 2

    log_dir = Path(args.log_dir)
    work_dir = Path(args.work_dir) if args.work_dir else None

    metrics = run_and_profile(cmd, log_dir=log_dir, name=args.name, work_dir=work_dir)

    # Short human summary to stdout
    print(
        f"[PERF] name={metrics.name} exit={metrics.exit_code} elapsed={metrics.elapsed_sec:.2f}s "
        f"user={metrics.user_time_sec} sys={metrics.sys_time_sec} rss_kb={metrics.max_rss_kb} cpu%={metrics.cpu_percent}"
    )

    return int(metrics.exit_code or 0)


if __name__ == "__main__":
    raise SystemExit(main())
