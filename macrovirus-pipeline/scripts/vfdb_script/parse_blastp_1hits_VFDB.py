#!/usr/bin/env python3
import sys
from Bio import SearchIO

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} output.blast > besthit.tab", file=sys.stderr)
    sys.exit(1)

blast_file = sys.argv[1]

# 输出表头（与 Perl 完全相同）
print("Query\tQuery_function\tSubject\tQueryLen\tSubjectLen\tAlignmentLen\tQuerycov (%)\tSubjectcov (%)\tE_value\tIdentity (%)\tSimilarity (%)\tSymbol\tFunction\tVirulence factor\tVFDB ID\tSource species")

query_count = 0

for result in SearchIO.parse(blast_file, "blast-text"):
    query_count += 1
    query_name = result.id
    query_desc = result.description if result.description else ""

    if len(result.hits) == 0:
        print(f"{query_name}\tNo hit")
        continue

    # 只取第一个 hit（best hit），且只取它的第一个 HSP（与 Perl 脚本逻辑一致）
    hit = result.hits[0]
    hsp = hit.hsps[0]

    subjectname = hit.id
    # 移除括号里的内容（与 Perl $subjectname =~ s/\(.*?\)//g; 一致）
    import re
    subjectname = re.sub(r'\(.*?\)', '', subjectname).strip()

    query_len = result.seq_len
    subject_len = hit.seq_len
    alignment_len = hsp.aln_span   # total alignment length

    querycov = round(hsp.query_span / query_len * 100, 1)
    subjectcov = round(hsp.hit_span / subject_len * 100, 1)
    identity = round(hsp.ident_pct, 1)          # frac_identical('total') * 100
    similarity = round(hsp.positives_pct, 1)    # frac_conserved('total') * 100
    evalue = hsp.evalue

    desc = hit.description

    symbol = subjectdes = virulence = vfdb = species = ""

    # 与 Perl 正则完全一致的解析逻辑
    match = re.match(r'^(\S+)\s+(.*?)\s*\[(.*?)\]\s*\[(.*?)\]', desc)
    if match:
        symbol, subjectdes, temp_vf, species = match.groups()

        # 处理 virulence factor 和 VFDB ID
        if ' ' in temp_vf:
            aaa = temp_vf.split()
        else:
            aaa = temp_vf.split('(')

        vfdb = aaa.pop()
        virulence = " ".join(aaa)

        # 处理类似 (lsgA) 的情况
        m2 = re.match(r'(\S+)\((.*)\)$', vfdb)
        if m2:
            virulence = virulence + " " + m2.group(1)
            vfdb = m2.group(2)
        else:
            vfdb = vfdb.strip('()')

        symbol = symbol.strip('()')

    # 输出一行（与 Perl 完全相同的格式和顺序）
    print(f"{query_name}\t{query_desc}\t{subjectname}\t{query_len}\t{subject_len}\t{alignment_len}\t"
          f"{querycov}\t{subjectcov}\t{evalue}\t{identity}\t{similarity}\t"
          f"{symbol}\t{subjectdes}\t{virulence}\t{vfdb}\t{species}")

print(f"Total queries processed: {query_count}", file=sys.stderr)