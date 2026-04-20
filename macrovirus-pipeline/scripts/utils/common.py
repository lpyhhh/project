from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


def list_samples(results_megahit: Path) -> List[str]:
    names = set()
    for path in results_megahit.glob("*.contig.ok.fa.gz"):
        names.add(path.name.replace(".contig.ok.fa.gz", ""))
    for path in results_megahit.glob("*.contig.ok.fa"):
        names.add(path.name.replace(".contig.ok.fa", ""))
    return sorted(names)


def ensure_uncompressed(results_megahit: Path, sample: str) -> Path:
    contig_gz = results_megahit / f"{sample}.contig.ok.fa.gz"
    contig = results_megahit / f"{sample}.contig.ok.fa"
    if contig.exists():
        return contig
    if contig_gz.exists():
        if not contig.exists() or contig_gz.stat().st_mtime > contig.stat().st_mtime:
            with contig.open("wb") as fh:
                subprocess.run(["gunzip", "-c", str(contig_gz)], check=True, stdout=fh)
        return contig
    raise FileNotFoundError(f"Missing contig for {sample}")


def list_samples_from_reads(raw_data: Path, raw_data_alt: Optional[Path]) -> List[str]:
    names = set()
    roots = [raw_data]
    if raw_data_alt:
        roots.append(raw_data_alt)
    for root in roots:
        if not root.exists():
            continue
        for path in root.glob("*_R1_kneaddata_paired_1.fastq.gz"):
            name = path.name.replace("_R1_kneaddata_paired_1.fastq.gz", "")
            names.add(name)
    return sorted(names)


def find_read_pair(
    raw_data: Path,
    raw_data_alt: Optional[Path],
    sample: str,
) -> Optional[Tuple[Path, Path]]:
    def _candidate(root: Path) -> Optional[Tuple[Path, Path]]:
        r1 = root / f"{sample}_R1_kneaddata_paired_1.fastq.gz"
        r2 = root / f"{sample}_R1_kneaddata_paired_2.fastq.gz"
        if r1.exists() and r2.exists():
            return r1, r2
        return None

    primary = _candidate(raw_data)
    if primary:
        return primary
    if raw_data_alt:
        return _candidate(raw_data_alt)
    return None
