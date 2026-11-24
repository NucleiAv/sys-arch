"""Check the writing rules. No em or en dashes, no emojis, no colons in prose.

Run from anywhere:  python tools/check_style.py
Colons inside `code`, code blocks, URLs and times are allowed.
"""
import glob, os, re, sys
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
BAD = re.compile("[\u2014\u2013\U0001F300-\U0001FAFF\u2600-\u27BF]")
bad = 0


def walk(v, path):
    global bad
    if isinstance(v, dict):
        for k, x in v.items():
            walk(x, f"{path}.{k}")
    elif isinstance(v, list):
        for i, x in enumerate(v):
            walk(x, f"{path}[{i}]")
    elif isinstance(v, str):
        text = re.sub(r"```.*?```", "", v, flags=re.S)
        text = re.sub(r"`[^`]*`", "", text)
        text = re.sub(r"https?://\S+", "", text)
        if BAD.search(text):
            print("dash or emoji", path, text[:80]); bad += 1
        for m in re.finditer(r"\w:\s", text):
            print("colon", path, "...", text[max(0, m.start() - 40): m.end() + 30].replace("\n", " ")); bad += 1


for f in sorted(glob.glob("content/**/*.yaml", recursive=True)):
    walk(yaml.safe_load(open(f, encoding="utf-8")), f)
for f in glob.glob("assets/js/site.js") + glob.glob("content/**/*.md", recursive=True):
    if BAD.search(open(f, encoding="utf-8").read()):
        print("dash or emoji in", f); bad += 1
print("style issues:", bad)
sys.exit(1 if bad else 0)
