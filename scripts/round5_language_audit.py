"""
Round 5 语言质量 & 投稿就绪度审计:
  1. 缩略语规范 (首次给全称)
  2. 高频动词检测 (机械重复)
  3. 长句 (>50 词)
  4. 被动语态密度
  5. 时态一致性 (Methods 过去时)
  6. 投稿就绪度 (占位符、字数、结构)
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
import re
from collections import Counter

text = Path("docs/paper/PAPER_FULL.md").read_text(encoding='utf-8')

# 排除 References + Tables + Figures (这些章节不参与语言审计)
refs_start = text.find("# References")
body_for_lang = text[:refs_start]

# === 1. 缩略语 ===
print("=" * 70)
print("CHECK 1: 缩略语规范 (首次使用应配全称)")
print("=" * 70)

# 在 body 中找所有 (XYZ) 形式的缩略语
abbrev_def = re.findall(r'\b([A-Z]{2,6})\b', body_for_lang)
# 找所有 (Full Form (XYZ)) 形式
defined = re.findall(r'\b([A-Za-z][A-Za-z\s\-]+?)\s*\(([A-Z]{2,6})\)', body_for_lang)
print("\n  正文中所有缩略语首次出现:")
seen = set()
for full, abbr in defined:
    if abbr not in seen:
        seen.add(abbr)
abbr_first_use = {}
for abbr in set(abbrev_def):
    # 找第一次出现位置
    m = re.search(rf'\b{abbr}\b', body_for_lang)
    if m:
        abbr_first_use[abbr] = m.start()

# 哪些缩略语**没有**配全称定义
known_abbrs_with_defn = set(a for _, a in defined)
all_abbrs = set(abbrevs_in_text := re.findall(r'\b([A-Z]{2,6})\b', body_for_lang))

# 排除常见的非缩略语 (年份/月份/单位等)
common_excluded = {
    'I', 'II', 'III', 'IV', 'V', 'VI',  # 罗马数字
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',  # 单字母 (LCZ subcategory)
    'K', 'M', 'X', 'Y', 'Z', 'I',  # 数学
}

# 列出有定义的缩略语 + 还没定义的
print("\n  ✓ 有全称定义的缩略语:")
for full, abbr in sorted(set(defined), key=lambda x: x[1]):
    if abbr not in common_excluded and len(abbr) >= 2:
        print(f"    {abbr:<8} = {full.strip()[:60]}")

# 缩略语单次使用 (出现次数=1)
abbr_count = Counter(abbrevs_in_text)
single_use = [a for a, c in abbr_count.items() if c == 1 and a not in common_excluded and len(a) >= 3]
if single_use:
    print(f"\n  ⚠ 仅出现 1 次的缩略语 (建议直接写全称): {single_use}")

# === 2. 高频动词 ===
print()
print("=" * 70)
print("CHECK 2: 高频动词 (>10 次警示机械重复)")
print("=" * 70)

verbs_to_check = [
    'showed', 'shows', 'show',
    'demonstrated', 'demonstrate', 'demonstrates',
    'reveals', 'revealed', 'reveal',
    'found', 'finds', 'find',
    'observed', 'observes', 'observe',
    'confirms', 'confirmed', 'confirm',
    'indicates', 'indicated', 'indicate',
    'suggests', 'suggested', 'suggest',
    'reports', 'reported', 'report',
    'tested', 'tests', 'test',
    'computed', 'computes', 'compute',
]

# 把动词分组
verb_groups = {
    'show': ['show', 'shows', 'showed', 'showing'],
    'demonstrate': ['demonstrate', 'demonstrates', 'demonstrated', 'demonstrating'],
    'reveal': ['reveal', 'reveals', 'revealed', 'revealing'],
    'find': ['find', 'finds', 'found', 'finding'],
    'observe': ['observe', 'observes', 'observed', 'observing'],
    'confirm': ['confirm', 'confirms', 'confirmed', 'confirming'],
    'indicate': ['indicate', 'indicates', 'indicated', 'indicating'],
    'suggest': ['suggest', 'suggests', 'suggested', 'suggesting'],
    'report': ['report', 'reports', 'reported', 'reporting'],
    'test': ['test', 'tests', 'tested', 'testing'],
    'compute': ['compute', 'computes', 'computed', 'computing'],
    'use': ['use', 'uses', 'used', 'using'],
    'apply': ['apply', 'applies', 'applied', 'applying'],
}

print()
words_lower = re.findall(r"\b[a-zA-Z]+\b", body_for_lang.lower())
for verb_root, forms in verb_groups.items():
    n = sum(words_lower.count(f) for f in forms)
    if n > 10:
        flag = "⚠ HIGH" if n > 20 else "(high)"
        print(f"  {verb_root:<15}  {n:>3} 次  {flag}")
    elif n > 5:
        print(f"  {verb_root:<15}  {n:>3} 次")

# === 3. 长句 ===
print()
print("=" * 70)
print("CHECK 3: 长句 (>=50 词)")
print("=" * 70)

# 仅扫描正文段落 (排除表格/标题/数学)
paragraphs = []
for line in body_for_lang.split('\n'):
    if line.strip().startswith('|') or line.strip().startswith('#') or line.strip().startswith('$'):
        continue
    if not line.strip():
        continue
    paragraphs.append(line)

long_sents = []
for para in paragraphs:
    # 拆句
    for s in re.split(r'(?<=[.!?])\s+', para):
        s = s.strip()
        wc = len(s.split())
        if wc >= 50:
            long_sents.append((wc, s))
long_sents.sort(reverse=True)
print(f"\n  长句 ≥50 词: {len(long_sents)}")
for wc, s in long_sents[:8]:
    print(f"    [{wc}w] {s[:140]}...")

# === 4. 被动语态 ===
print()
print("=" * 70)
print("CHECK 4: 被动语态密度")
print("=" * 70)

# 被动语态简单检测: \"is/are/was/were/been + past_participle\"
passive_patterns = [
    r'\b(is|are|was|were|been|being)\s+\w+ed\b',
    r'\b(is|are|was|were|been|being)\s+(used|done|made|computed|applied|tested|reported|shown|found)\b',
]
passive_count = 0
for p in passive_patterns:
    passive_count += len(re.findall(p, body_for_lang, re.IGNORECASE))
total_sentences = max(1, sum(1 for s in re.split(r'(?<=[.!?])\s+', body_for_lang) if len(s.split()) > 3))
density_pct = passive_count / total_sentences * 100
print(f"\n  被动语态出现: {passive_count} 次")
print(f"  总句数 (>3 词): {total_sentences}")
print(f"  密度: {density_pct:.1f}%")
if density_pct > 30:
    print("  ⚠ SCS / Elsevier 标准: 被动语态 <30% 较好")
else:
    print("  ✓ 在可接受范围 (<30%)")

# === 5. 时态一致性 ===
print()
print("=" * 70)
print("CHECK 5: 时态一致性 (Methods 期望过去时)")
print("=" * 70)

# 在 # 2. Methods 部分检查
methods_match = re.search(r'^# 2\. Methods$([\s\S]*?)(?=^# 3\.)', text, re.MULTILINE)
if methods_match:
    methods_text = methods_match.group(1)
    # 找现在时动词 (We use/apply/run 等)
    present_verbs = re.findall(r'\bWe\s+(use|apply|run|measure|extract|compute|test|build|select|filter|cluster|classify|implement)\b', methods_text)
    past_verbs = re.findall(r'\bWe\s+(used|applied|ran|measured|extracted|computed|tested|built|selected|filtered|clustered|classified|implemented)\b', methods_text)
    n_pres = len(present_verbs)
    n_past = len(past_verbs)
    total = n_pres + n_past
    if total > 0:
        print(f"\n  Methods 中 'We + 动词' 计数:")
        print(f"    现在时: {n_pres}")
        print(f"    过去时: {n_past}")
        print(f"    过去时占比: {n_past/total*100:.1f}%")
        if n_pres > n_past:
            print("    ⚠ 现在时多于过去时 — Methods 通常用过去时")
        else:
            print("    ✓ 过去时为主 (符合 Methods 惯例)")

# === 6. 投稿就绪度 ===
print()
print("=" * 70)
print("CHECK 6: 投稿就绪度")
print("=" * 70)

# 占位符
placeholders = re.findall(r'\[[A-Z][^\]]*\]', text)
unique_ph = sorted(set(placeholders))
print(f"\n  剩余占位符 (需填):")
for ph in unique_ph:
    n = text.count(ph)
    print(f"    {ph}  ({n} 处)")

# 字数统计 (主文)
print()
intro_match = re.search(r'^# 1\. Introduction$([\s\S]*?)(?=^# 6\.)', text, re.MULTILINE)
if intro_match:
    main_text = intro_match.group(1)
    main_words = sum(1 for line in main_text.split('\n')
                     for _ in line.split()
                     if not line.strip().startswith('|') and not line.strip().startswith('#'))
    actual_words = len(re.findall(r'\S+', main_text))
    # 排除表格行
    main_clean = '\n'.join(l for l in main_text.split('\n')
                            if not l.strip().startswith('|') and not l.strip().startswith('#'))
    actual_words = len(re.findall(r'[A-Za-z]\w*', main_clean))
    print(f"  主文字数 (Intro→Conclusions): {actual_words:,}")
    if actual_words > 10000:
        print("    ⚠ SCS 推荐 6,000–10,000 词 — 略偏长")
    elif actual_words < 6000:
        print("    ⚠ 偏短")
    else:
        print("    ✓ 在 SCS 推荐范围")

# 摘要字数
abstract_match = re.search(r'^# Abstract$([\s\S]*?)(?=^# Keywords)', text, re.MULTILINE)
if abstract_match:
    abs_text = abstract_match.group(1).strip()
    abs_words = len(re.findall(r'[A-Za-z]\w*', abs_text))
    print(f"  摘要字数: {abs_words}")
    if abs_words > 300:
        print("    ⚠ SCS 限 300 词")
    else:
        print("    ✓ ≤300 词")

# 章节结构
required = [
    "# Highlights",
    "# Abstract",
    "# Keywords",
    "# 1. Introduction",
    "# 2. Methods",
    "# 3. Results",
    "# 4. Discussion",
    "# 5. Conclusions",
    "# 6. CRediT",
    "# 7. Declaration of competing interest",
    "# 8. Funding",
    "# 9. Data availability",
    "# References",
]
print()
print("  必需章节:")
for r in required:
    found = "✓" if r in text else "✗"
    print(f"    {found}  {r}")
