"""
Round 4 引文审计:
  1. 幽灵引文 (refs 中有但正文未引用)
  2. 同姓消歧义 (Demuzere 多年, Di Napoli 多年, Yitzhaki 多年)
  3. 引文格式 (APA: 括号内 &, 叙述 and)
  4. 跨章节数值一致 (摘要 vs 结果 vs 结论)
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
import re
from collections import defaultdict

text = Path("docs/paper/PAPER_FULL.md").read_text(encoding='utf-8')

# ==========================================================
# 1. Ghost references
# ==========================================================
print("=" * 70)
print("CHECK 1: Ghost references")
print("=" * 70)

# 找 # References section 的范围
refs_start = text.find("# References")
tables_start = text.find("# Tables", refs_start)
if refs_start == -1:
    print("  ✗ # References not found")
    sys.exit(1)
refs_text = text[refs_start:tables_start if tables_start > 0 else len(text)]
body_text = text[:refs_start]

# 解析 references — APA pattern: 第一作者姓+缩写, ..., (YYYY). 标题...
references = []
for line in refs_text.split('\n'):
    line = line.strip()
    if not line or line.startswith('#') or line.startswith('*'):
        continue
    # APA: "Surname, F. M., Other, A., & Last, B. (YYYY). Title..."
    m = re.match(r'^([A-ZÀ-Ÿ][a-zA-Zà-ÿ\-Żłś]+),\s+', line)
    yr = re.search(r'\((\d{4})\)', line)
    if m and yr:
        first_author = m.group(1)
        year = yr.group(1)
        references.append((first_author, year, line))

print(f"  Parsed {len(references)} references")

# 在 body 中找每条文献的引用
cited = set()
for fa, yr, _ in references:
    fa_esc = re.escape(fa)
    patterns = [
        rf"{fa_esc}\s+et al\.\s*\({yr}\b",
        rf"\({fa_esc}\s+et al\.,\s*{yr}\b",
        rf"{fa_esc}\s+and\s+\w+\s*\({yr}\b",
        rf"\({fa_esc}\s+&\s+\w+,\s*{yr}\b",
        rf"{fa_esc}\s*\({yr}\b",
        rf"\({fa_esc},\s*{yr}\b",
    ]
    for p in patterns:
        if re.search(p, body_text):
            cited.add((fa, yr))
            break

ghosts = [(fa, yr, l) for fa, yr, l in references if (fa, yr) not in cited]
print(f"  Cited in body: {len(cited)}/{len(references)}")
print(f"  Ghost refs:    {len(ghosts)}")
if ghosts:
    print("\n  Ghost list (in references but never cited in body):")
    for fa, yr, l in ghosts:
        print(f"    {fa:<20} {yr}  : {l[:80]}")

# ==========================================================
# 2. 同姓消歧义
# ==========================================================
print()
print("=" * 70)
print("CHECK 2: Same-surname disambiguation")
print("=" * 70)

surname_count = defaultdict(list)
for fa, yr, l in references:
    surname_count[fa].append((yr, l[:60]))

dupes = {fa: yrs for fa, yrs in surname_count.items() if len(yrs) > 1}
if dupes:
    print(f"\n  Authors with multiple references ({len(dupes)}):")
    for fa, items in dupes.items():
        years = [y for y, _ in items]
        print(f"    {fa}: {len(items)} refs in years {years}")
        # 检查正文中是否存在歧义引用 (Author et al. (year)) 但 year 重复
        body_cites = re.findall(rf"{re.escape(fa)}\s+et al\.\s*\((\d{{4}})\)", body_text)
        body_year_count = defaultdict(int)
        for y in body_cites:
            body_year_count[y] += 1
        # 检查是否同年存在两条 ref
        from collections import Counter
        year_dups = [y for y, c in Counter(years).items() if c > 1]
        if year_dups:
            print(f"      ⚠ 同年多篇 (需要 a/b 后缀): {year_dups}")
        # 显示正文引用
        for y, _ in items:
            n_in_body = body_year_count.get(y, 0)
            print(f"      → {fa} ({y}): cited {n_in_body} times in body")
else:
    print("  ✓ 无同姓多篇文献")

# ==========================================================
# 3. APA 格式: 括号内 & vs 叙述 and
# ==========================================================
print()
print("=" * 70)
print("CHECK 3: APA citation format (& 在括号内, and 在叙述)")
print("=" * 70)

# 错误模式 1: 括号内用 \"and\"
wrong_and_in_paren = re.findall(r'\([A-Z][a-zA-Z]+\s+and\s+[A-Z][a-zA-Z]+,\s*\d{4}\)', body_text)
print(f"\n  括号内误用 'and' (应为 &): {len(wrong_and_in_paren)}")
for x in wrong_and_in_paren[:5]:
    print(f"    {x}")

# 错误模式 2: 叙述中用 &
wrong_amp_narrative = re.findall(r'\b[A-Z][a-zA-Z]+\s+&\s+[A-Z][a-zA-Z]+\s+\(\d{4}\)', body_text)
print(f"\n  叙述中误用 '&' (应为 'and'): {len(wrong_amp_narrative)}")
for x in wrong_amp_narrative[:5]:
    print(f"    {x}")

# 正确格式样本统计
correct_paren = len(re.findall(r'\([A-Z][a-zA-Z]+\s+&\s+[A-Z][a-zA-Z]+,\s*\d{4}\)', body_text))
correct_narr = len(re.findall(r'\b[A-Z][a-zA-Z]+\s+and\s+[A-Z][a-zA-Z]+\s+\(\d{4}\)', body_text))
print(f"\n  ✓ 正确括号内 (X & Y, Year): {correct_paren}")
print(f"  ✓ 正确叙述 X and Y (Year): {correct_narr}")

# ==========================================================
# 4. 跨章节数值一致
# ==========================================================
print()
print("=" * 70)
print("CHECK 4: Cross-section numerical consistency")
print("=" * 70)

# 关键数值列表
critical_values = [
    ("HDH Gini", ["0.0571", "0.057", "0.0558"]),  # 全市 / built-up
    ("within-class share", ["83.5%", "83.5 %", "86.4%", "86.4 %"]),
    ("morphology reduction", ["1.0 pp", "1.03 pp", "1.0 percentage point"]),
    ("topology reduction", ["0.21 pp", "0.2 pp"]),
    ("hybrid reduction", ["0.89 pp", "0.88 pp", "0.9 pp"]),
    ("geography reduction", ["10.81", "10.8 pp", "10.8-pp"]),
    ("Coast+Mountain peak", ["14.29", "14.3 pp"]),
    ("Cross-city Shenzhen", ["4/4", "100 %", "100%"]),
    ("Cross-city Dongguan", ["3/4", "75 %", "75%"]),
    ("Cross-city Guangzhou", ["0/4", "0 %", "0%"]),
    ("Sample size buildings", ["151,896", "151896"]),
    ("Total population", ["14.67 million", "14.30 million"]),
    ("subcategories total", ["39 subcategories", "39 subcategor"]),
    ("Silhouette mean", ["mean Silhouette = 0.81", "Silhouette = 0.81", "0.81"]),
    ("hottest 10 % HDH", ["11.0 %", "11 %", "11.0%"]),
]

for label, values in critical_values:
    print(f"\n  {label}:")
    for v in values:
        n = body_text.count(v)
        if n:
            print(f"    \"{v}\": {n} occurrences")

# 摘要 / 结论中同 number 检查
abstract_match = re.search(r'^# Abstract$([\s\S]*?)(?=^#)', text, re.MULTILINE)
conclusions_match = re.search(r'^# 5\. Conclusions$([\s\S]*?)(?=^#)', text, re.MULTILINE)

print()
print("=== Abstract 中的关键数值 ===")
if abstract_match:
    abs_text = abstract_match.group(1)
    nums = re.findall(r'\b\d+\.?\d*\s*(?:pp|%|°C|million)', abs_text)
    for n in nums:
        print(f"    {n}")

print()
print("=== Conclusions 中的关键数值 ===")
if conclusions_match:
    con_text = conclusions_match.group(1)
    nums = re.findall(r'\b\d+\.?\d*\s*(?:pp|%|°C|million)', con_text)
    for n in nums:
        print(f"    {n}")
