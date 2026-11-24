"""Quote plain YAML values that contain ': ' or ' #', which YAML would misread."""
import glob, re, sys
pat = re.compile(r'^(\s*(?:- )?)([a-z_]+): (.*)$')
for f in sys.argv[1:] or glob.glob("content/**/*.yaml", recursive=True):
    lines = open(f, encoding="utf-8").read().split("\n")
    changed = False
    for i, l in enumerate(lines):
        m = pat.match(l)
        if not m:
            continue
        v = m.group(3)
        if not v or v[0] in "\"'|>[{&*!" or not (": " in v or " #" in v or v.endswith(":")):
            continue
        lines[i] = f'{m.group(1)}{m.group(2)}: "' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
        changed = True
        print(f, i + 1)
    if changed:
        open(f, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
