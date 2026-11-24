"""Check the writing rules.

Run from anywhere:  python tools/check_style.py

Hard rules, the check fails if one is broken
  - no em or en dashes
  - no emojis
  - no colons in prose (colons inside `code`, code blocks, URLs, times and ports are allowed)

Soft rule, reported as a number
  - ASD-STE100 style. Most sentences have 20 words or fewer for instructions and
    25 or fewer for descriptions. The target is that at least 80 percent of
    sentences have 20 words or fewer.
"""
import glob, os, re, sys
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
BAD = re.compile("[—–\U0001F300-\U0001FAFF☀-➿]")
SKIP_KEYS = {"raw", "u", "f", "fields", "nodes", "links", "p", "keys", "a_code"}
bad = 0
lengths = []
long_ones = []


def prose(text):
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`[^`]*`", "X", text)
    text = re.sub(r"\]\([^)]*\)", "]", text)
    text = re.sub(r"https?://\S+", "", text)
    return text


def walk(v, path, key=""):
    global bad
    if key in SKIP_KEYS:
        return
    if isinstance(v, dict):
        for k, x in v.items():
            walk(x, f"{path}.{k}", str(k))
    elif isinstance(v, list):
        for i, x in enumerate(v):
            walk(x, f"{path}[{i}]", key)
    elif isinstance(v, str):
        text = prose(v)
        if BAD.search(text):
            print("dash or emoji", path, text[:80]); bad += 1
        for m in re.finditer(r"[A-Za-z]:\s", text):
            print("colon", path, "...", text[max(0, m.start() - 40): m.end() + 30].replace("\n", " ")); bad += 1
        if key in ("q", "opts", "t", "short", "title", "label", "tag", "port", "transport", "full", "name"):
            return
        for line in text.split("\n"):
            if line.strip().startswith(("|", "- ", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "#")):
                continue
            for sent in re.split(r"(?<=[.!?])\s+", line):
                n = len(re.findall(r"[A-Za-z0-9']+", sent))
                if n >= 3:
                    lengths.append(n)
                    if n > 30:
                        long_ones.append((n, path, sent.strip()[:110]))


for f in sorted(glob.glob("content/**/*.yaml", recursive=True)):
    walk(yaml.safe_load(open(f, encoding="utf-8")), f)
for f in glob.glob("assets/js/*.js") + glob.glob("content/**/*.md", recursive=True):
    if f.endswith("protocol-data.js"):
        continue
    if BAD.search(open(f, encoding="utf-8").read()):
        print("dash or emoji in", f); bad += 1

if lengths:
    short = sum(1 for n in lengths if n <= 20) / len(lengths)
    mid = sum(1 for n in lengths if n <= 25) / len(lengths)
    print(f"sentences {len(lengths)}, average {sum(lengths) / len(lengths):.1f} words, "
          f"{short * 100:.0f} percent at 20 words or fewer, {mid * 100:.0f} percent at 25 or fewer")
    if "-v" in sys.argv:
        for n, p, s in sorted(long_ones, reverse=True)[:40]:
            print(f"  {n} words  {p}  {s}")
    print(f"sentences over 30 words: {len(long_ones)}")
print("hard rule issues:", bad)
sys.exit(1 if bad else 0)
