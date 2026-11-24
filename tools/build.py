"""Build every page of the Boxes and Arrows site.

Run from anywhere:
    python tools/build.py

Reads   content/*.yaml, content/learn/*.yaml, content/design/*.yaml
Writes  index.html, basics.html, plan.html, interview.html, library.html,
        learn/*.html, design/*.html

No third-party packages except PyYAML.
"""
import html
import json
import math
import os
import re
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
V = "20261124a"
E = lambda s: html.escape(str(s), quote=True)


def load(p):
    return yaml.safe_load(open(p, encoding="utf-8"))


# ---------------------------------------------------------------- markdown-lite
def inline(s):
    s = E(s)
    codes = []

    def keep(m):
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"
    s = re.sub(r"`([^`]+)`", keep, s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)

    def lk(m):
        t, u = m.group(1), m.group(2)
        ext = u.startswith("http")
        return f'<a href="{u}"{" target=\"_blank\" rel=\"noopener\"" if ext else ""}>{t}</a>'
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lk, s)
    s = re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{codes[int(m.group(1))]}</code>", s)
    return s


BOX = {"!plain": ("plain", "In plain words"), "!warn": ("plain warn", "Careful"), "!eli5": ("plain eli5", "Think of it like this"),
       "!key": ("plain", "Key point"), "!fact": ("plain fact", "Real numbers"), "!tip": ("plain", "Interview tip")}


def md(text):
    if not text:
        return ""
    out = []
    for block in re.split(r"\n\s*\n", str(text).strip()):
        lines = block.strip().split("\n")
        first = lines[0]
        tag = first.split(" ", 1)[0]
        if first.startswith("```"):
            code = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
            out.append(f'<pre class="code"><code>{E(code)}</code></pre>')
        elif tag in BOX:
            cls, label = BOX[tag]
            body = " ".join([first.split(" ", 1)[1] if " " in first else ""] + lines[1:])
            out.append(f'<div class="{cls}"><span class="k">{label}</span><p>{inline(body)}</p></div>')
        elif all(re.match(r"^\s*- ", l) for l in lines):
            out.append("<ul>" + "".join(f"<li>{inline(l.strip()[2:])}</li>" for l in lines) + "</ul>")
        elif all(re.match(r"^\s*\d+\. ", l) for l in lines):
            out.append("<ol>" + "".join(f"<li>{inline(re.sub(r'^\s*\d+\. ', '', l))}</li>" for l in lines) + "</ol>")
        elif first.startswith("### "):
            out.append(f"<h3>{inline(first[4:])}</h3>" + (md("\n".join(lines[1:])) if lines[1:] else ""))
        elif first.startswith("| "):
            rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines if not re.match(r"^\|\s*-", l)]
            out.append(table(rows[0], rows[1:]))
        else:
            out.append(f"<p>{inline(' '.join(l.strip() for l in lines))}</p>")
    return "\n".join(out)


def table(head, rows):
    return ('<div class="table-wrap"><table class="table"><thead><tr>' + "".join(f"<th>{inline(h)}</th>" for h in head)
            + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows)
            + "</tbody></table></div>")


# ---------------------------------------------------------------- diagrams
KIND = {"atk": "box-atk", "def": "box-def", "box": "box", "raised": "box-r", "ink": "box-r"}
LCOL = {"atk": "t-atk", "def": "t-def", "box": "t-mute", "raised": "t-mute", "pen": "t-pen"}
ARROW_DEFS = """<defs>
<marker id="a-ink" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" style="fill:var(--ink-2)"/></marker>
<marker id="a-atk" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" style="fill:var(--atk)"/></marker>
<marker id="a-def" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" style="fill:var(--def)"/></marker>
<marker id="a-pen" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" style="fill:var(--pencil)"/></marker>
</defs>"""
LNC = {"ink": "ln", "atk": "ln-atk", "def": "ln-def", "pen": "ln-pen"}


def mk(c):
    return c if c in ("atk", "def", "pen") else "ink"


def wrap(label, width_px, size=13):
    per = max(6, int(width_px / (size * 0.56)))
    lines = []
    for part in str(label).split("|"):
        cur = ""
        for w in part.split():
            if len(cur) + len(w) + (1 if cur else 0) <= per:
                cur = (cur + " " + w).strip()
            else:
                if cur:
                    lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def text_block(x, cy, lines, cls="t-s", lh=16, anchor="middle"):
    y0 = cy - (len(lines) - 1) * lh / 2 + 4
    return "".join(f'<text x="{x:.0f}" y="{y0 + i * lh:.0f}" text-anchor="{anchor}" class="{cls}">{E(l)}</text>' for i, l in enumerate(lines))


def node(x, y, w, h, label, kind="box", sub=None):
    s = f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="8" class="{KIND.get(kind, "box")}"/>'
    lines = wrap(label, w - 16)
    if sub:
        s += text_block(x + w / 2, y + h / 2 - 7, lines, "t-s")
        s += f'<text x="{x + w / 2:.0f}" y="{y + h - 9:.0f}" text-anchor="middle" class="t-mono">{E(sub)}</text>'
    else:
        s += text_block(x + w / 2, y + h / 2, lines, "t-s")
    return s


def d_flow(d):
    lanes = d.get("lanes") or [{"nodes": d["nodes"], "edges": d.get("edges", []), "label": d.get("label"), "color": d.get("color", "ink")}]
    W = 680
    out, y = [], 0
    for lane in lanes:
        nodes = lane["nodes"]
        edges = lane.get("edges", [])
        n = len(nodes)
        gap = 64 if any(edges) else 36
        w = min(170, (W - (n - 1) * gap) / n)
        total = n * w + (n - 1) * gap
        x0 = (W - total) / 2
        if lane.get("label"):
            out.append(f'<text x="0" y="{y + 14}" class="t-mono {LCOL.get(lane.get("labelkind", "box"), "")}">{E(lane["label"])}</text>')
            y += 24
        h = max(52, 18 + 16 * max(len(wrap(nd[0], w - 16)) for nd in nodes) + (14 if any(len(nd) > 2 for nd in nodes) else 0))
        col = lane.get("color", "ink")
        for i, nd in enumerate(nodes):
            x = x0 + i * (w + gap)
            out.append(node(x, y, w, h, nd[0], nd[1] if len(nd) > 1 else "box", nd[2] if len(nd) > 2 else None))
            if i < n - 1:
                ax, bx = x + w + 4, x + w + gap - 4
                ec = col
                lab = edges[i] if i < len(edges) else ""
                if isinstance(lab, list):
                    lab, ec = lab[0], lab[1]
                out.append(f'<path class="{LNC.get(ec, "ln")}" d="M{ax:.0f} {y + h / 2:.0f} H{bx:.0f}" marker-end="url(#a-{mk(ec)})"/>')
                if lab:
                    ws = wrap(lab, gap + 6, 11)[:3]
                    for j, l in enumerate(ws):
                        out.append(f'<text x="{(ax + bx) / 2:.0f}" y="{y + h / 2 - 8 - (len(ws) - 1 - j) * 12:.0f}" text-anchor="middle" class="t-mono">{E(l)}</text>')
        y += h + 28
    return W, y - 12, "".join(out)


def d_cycle(d):
    steps = d["nodes"]
    n = len(steps)
    W, H = 680, 300 if n <= 4 else 340
    cx, cy, rx, ry = W / 2, H / 2, 250, (H / 2 - 40)
    w, h = 150, 52
    pts = [(cx + rx * math.cos(-math.pi / 2 + 2 * math.pi * i / n), cy + ry * math.sin(-math.pi / 2 + 2 * math.pi * i / n)) for i in range(n)]
    out = []
    col = d.get("color", "ink")
    for i in range(n):
        (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L

        def edge(px, py, sx, sy):
            tx = (w / 2 + 6) / abs(sx) if sx else 1e9
            ty = (h / 2 + 6) / abs(sy) if sy else 1e9
            t = min(tx, ty)
            return px + sx * t, py + sy * t
        sx1, sy1 = edge(x1, y1, ux, uy)
        ex2, ey2 = edge(x2, y2, -ux, -uy)
        mx, my = (sx1 + ex2) / 2, (sy1 + ey2) / 2
        qx, qy = mx + (mx - cx) * 0.18, my + (my - cy) * 0.18
        out.append(f'<path class="{LNC.get(col, "ln")}" d="M{sx1:.0f} {sy1:.0f} Q{qx:.0f} {qy:.0f} {ex2:.0f} {ey2:.0f}" marker-end="url(#a-{mk(col)})"/>')
    for i, (x, y) in enumerate(pts):
        s = steps[i]
        out.append(node(x - w / 2, y - h / 2, w, h, s[0], s[1] if len(s) > 1 else "box", s[2] if len(s) > 2 else f"step {i + 1}"))
    if d.get("center"):
        out.append(text_block(cx, cy, wrap(d["center"], 220), "t-m t-mute", 18))
    return W, H, "".join(out)


def d_layers(d):
    """A request falls through layers. Each layer either answers it (stop) or lets it pass."""
    W = 680
    layers = d["layers"]
    h, gap, y = 46, 10, 34
    out = [f'<text x="0" y="14" class="t-mono t-def">{E(d.get("attack", "request"))}</text>']
    stop_y = None
    for L in layers:
        name, note = L[0], L[1] if len(L) > 1 else ""
        status = L[2] if len(L) > 2 else "pass"
        cls = "box-def" if status == "stop" else ("box" if status == "pass" else "box-r")
        out.append(f'<rect x="70" y="{y}" width="{W - 70}" height="{h}" rx="8" class="{cls}"/>')
        out.append(f'<text x="86" y="{y + 20}" class="t-s" style="font-weight:600">{E(name)}</text>')
        for l in wrap(note, W - 220, 12)[:1]:
            out.append(f'<text x="86" y="{y + 37}" class="t-s t-mute" style="font-size:12px">{E(l)}</text>')
        tag = {"stop": "answers here", "pass": "passes on", "partial": "sometimes"}.get(status, status)
        out.append(f'<text x="{W - 12}" y="{y + 20}" text-anchor="end" class="t-mono {"t-def" if status == "stop" else "t-mute"}">{E(tag)}</text>')
        if status == "stop" and stop_y is None:
            stop_y = y + h / 2
        y += h + gap
    end = stop_y if stop_y else y
    out.insert(1, f'<path class="ln-def" d="M30 22 V{end:.0f} H66" marker-end="url(#a-def)"/>')
    return W, y, "".join(out)


def d_split(d):
    """one source fans out to several targets"""
    src = d["source"]
    targets = d["targets"]
    n = len(targets)
    h = 44
    H = max(n * (h + 14), 80)
    out = [node(0, H / 2 - 28, 170, 56, src[0], src[1] if len(src) > 1 else "box")]
    col = d.get("color", "ink")
    for i, t in enumerate(targets):
        ty = i * (h + 14)
        out.append(f'<path class="{LNC.get(col, "ln")}" d="M170 {H / 2:.0f} C230 {H / 2:.0f} 230 {ty + h / 2:.0f} 290 {ty + h / 2:.0f}" marker-end="url(#a-{mk(col)})"/>')
        out.append(node(294, ty, 180, h, t[0], t[1] if len(t) > 1 else "box"))
        if len(t) > 2:
            for j, l in enumerate(wrap(t[2], 190, 12)[:2]):
                out.append(f'<text x="490" y="{ty + 18 + j * 15}" class="t-s t-mute" style="font-size:12px">{E(l)}</text>')
    return 680, H, "".join(out)


DIAG = {"flow": d_flow, "cycle": d_cycle, "layers": d_layers, "split": d_split}


def diagram(d):
    W, H, body = DIAG[d.get("type", "flow")](d)
    cap = d.get("caption", "")
    title = d.get("title", "")
    return (f'<figure class="diagram"><div class="sheet">'
            + (f'<div class="sheet-cap"><span>{E(title)}</span><span>{E(d.get("note", ""))}</span></div>' if title else "")
            + f'<svg class="dg" viewBox="-4 -4 {W + 8} {H + 8}" role="img" aria-label="{E(title + ". " + cap)}">{ARROW_DEFS}{body}</svg>'
            + '</div><div class="scroll-hint">Swipe sideways to see the whole diagram</div>'
            + f'{f"<figcaption>{inline(cap)}</figcaption>" if cap else ""}</figure>')


# ---------------------------------------------------------------- scenes
def scene(sc):
    d = dict(sc)
    d["steps"] = [dict(st, text=inline(st.get("text", ""))) for st in sc["steps"]]
    for st in d["steps"]:
        st["flow"] = [list(f) for f in st.get("flow", [])]
        if "stats" in st:
            st["stats"] = [str(v) for v in st["stats"]]
    js = json.dumps(d, ensure_ascii=False).replace("</", "<\\/")
    return f'<div class="scene"><script type="application/json">{js}</script><noscript>{E(sc.get("title", ""))}</noscript></div>'


def scenes_block(items):
    if not items:
        return ""
    return '<p class="small muted">Press Next or Play. Each step lights up one part and moves the requests. Arrow keys move steps after you click the diagram.</p>' + "".join(scene(x) for x in items)


# ---------------------------------------------------------------- questions
def prep_q(it):
    it = dict(it)
    for k in ("q", "why", "info"):
        if k in it and isinstance(it[k], str):
            it[k] = inline(it[k])
    t = it.get("type")
    if t in ("open", "iv") and isinstance(it.get("a"), str):
        it["a"] = md(it["a"])
    if t == "iv":
        if it.get("fb"):
            it["fb"] = md(it["fb"])
        it["keys"] = [[inline(k[0]), [str(w).lower() for w in k[1]]] for k in it.get("keys", [])]
    if t in ("mcq", None) and "opts" in it:
        it["opts"] = [inline(o) for o in it["opts"]]
        it["type"] = "mcq"
    if t == "sort":
        it["rows"] = [[inline(r[0]), r[1]] for r in it["rows"]]
    if t == "fill":
        it["a"] = [str(x) for x in (it["a"] if isinstance(it["a"], list) else [it["a"]])]
    return it


def qset(items, sid):
    data = [prep_q(it) for it in items or []]
    js = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return f'<div class="qset" data-id="{E(sid)}"></div><script type="application/json" data-for="{E(sid)}">{js}</script>'


def iv_items(items):
    return [dict(type="iv", **x) for x in items or []]


# ---------------------------------------------------------------- shell
HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<script>(function(){{try{{var t=localStorage.getItem("site.theme");if(t!=="dark"&&t!=="light")t=matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light";document.documentElement.dataset.theme=t}}catch(e){{}}}})()</script>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="icon" href="{r}assets/img/mark.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400&family=Newsreader:opsz,wght@6..72,400;6..72,500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{r}assets/css/site.css?v={v}">
</head>
<body data-root="{r}" data-track="{track}">
<a class="skip" href="#main">Skip to content</a>
<header id="top"></header>
"""
TAIL = """<footer id="foot"></footer>
<script src="{r}assets/js/site.js?v={v}"></script>
<script src="{r}assets/js/learn.js?v={v}"></script>
<script src="{r}assets/js/scene.js?v={v}"></script>
</body>
</html>
"""


def write(path, title, desc, track, main, r=""):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    out = HEAD.format(title=E(title), desc=E(desc), track=track, r=r, v=V) + main + TAIL.format(r=r, v=V)
    open(path, "w", encoding="utf-8", newline="\n").write(out)


def page(path, title, desc, track, side, body):
    write(path, title, desc, track, f'<div class="shell">{side}<main id="main" class="doc">{body}</main></div>', "../")


def pager(prev, nxt):
    p = f'<a class="pg prev" href="{prev[0]}"><span class="mono">Previous</span>{E(prev[1])}</a>' if prev else "<span></span>"
    n = f'<a class="pg next" href="{nxt[0]}"><span class="mono">Next</span>{E(nxt[1])}</a>' if nxt else "<span></span>"
    return f'<nav class="pager" aria-label="Lesson pages">{p}{n}</nav>'


def section(sid, title, inner):
    return f'<section class="block" id="{sid}"><h2>{E(title)}</h2>{inner}</section>'


def jt(a, b):
    a = str(a).rstrip()
    return f"{a} {b}" if a.endswith(("?", "!", ".")) else f"{a}. {b}"


TICKSVG = '<span class="box"></span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 13c2 1.4 3.7 3.2 5.2 5.4C11.6 12.6 15.4 7.4 21 3"/></svg>'


def checkbox(cid, label=""):
    return f'<label class="check" title="{E(label)}"><input type="checkbox" data-id="{E(cid)}" aria-label="{E(label)}">{TICKSVG}</label>'


# ---------------------------------------------------------------- sidebars
def side_wrap(track, label, inner):
    dot = {"learn": "def", "design": "atk"}.get(track, "def")
    return (f'<aside class="side" id="side" aria-label="{E(label)}">'
            f'<button class="side-btn" type="button" aria-expanded="false" aria-controls="side-nav">{E(label)}, all pages</button>'
            f'<nav id="side-nav"><p class="side-h"><span class="dot {dot}"></span>{E(label)}</p>{inner}</nav></aside>')


def side_group(num, title, href, cur, items, done=None):
    sub = "".join(f'<a href="{h}"' + (' aria-current="page"' if c else "") + f'><span class="mono">{E(m)}</span>{E(t)}</a>' for h, t, m, c in items)
    return (f'<details class="side-mod{" cur" if cur else ""}"{" open" if cur else ""}>'
            f'<summary{" data-done=" + chr(34) + done + chr(34) if done else ""}><span class="mono">{E(num)}</span><span>{E(title)}</span></summary>'
            f'<a class="side-open" href="{href}"' + (' aria-current="page"' if cur == "page" else "") + f'><span class="mono">&rarr;</span>Open the page</a>{sub}</details>')


# ---------------------------------------------------------------- tracks
LEVELS = {1: "Level 1. Foundations", 2: "Level 2. Data", 3: "Level 3. Many machines", 4: "Level 4. Running it for real", 5: "Level 5. Mastery"}

PARTS = {
    "learn": [("idea", "The idea in one minute", "idea"), ("watch", "Watch it, step by step", "scenes"), ("words", "Words you need", "terms"),
              ("how", "How it works", "how"), ("life", "Real life scenarios", "life"), ("trade", "Trade-offs", "tradeoffs"),
              ("mistakes", "Common mistakes", "mistakes"), ("quiz", "Check yourself", "quiz"), ("interview", "Interview questions", "interview"),
              ("practice", "Practice desk", "desk"), ("refs", "Go deeper", "refs")],
    "design": [("ask", "The ask", "ask"), ("reqs", "Pin down the requirements", "reqs"), ("estimate", "Do the math", "estimate"),
               ("api", "The API", "api"), ("data", "The data model", "data"), ("watch", "Watch it work", "scenes"),
               ("hld", "The big picture", "hld"), ("deep", "Deep dives", "deep"), ("trade", "Trade-offs you must name", "tradeoffs"),
               ("task", "Your turn", "task"), ("interview", "Follow-up questions", "interview"), ("practice", "Practice desk", "desk"),
               ("refs", "Go deeper", "refs")],
}


def render_part(kind, L, sid):
    v = L.get(kind)
    if not v:
        return ""
    if kind in ("idea", "how", "ask", "api", "data", "hld"):
        extra = "".join(diagram(d) for d in L.get(kind + "_diagrams", [])) if kind != "how" else "".join(diagram(d) for d in L.get("diagrams", []))
        if kind == "hld":
            extra = "".join(diagram(d) for d in L.get("diagrams", []))
        return md(v) + extra
    if kind == "scenes":
        return scenes_block(v)
    if kind == "terms":
        return '<dl class="terms">' + "".join(f"<dt>{E(a)}</dt><dd>{inline(b)}</dd>" for a, b in v) + "</dl>"
    if kind in ("life", "deep"):
        return "".join(f'<div class="case"><h3>{E(c[0])}</h3>{md(c[1])}</div>' for c in v)
    if kind == "tradeoffs":
        head = L.get("trade_head", ["Choice", "Good at", "Costs you"])
        return (md(L.get("trade_intro")) + table(head, v)) if isinstance(v, list) else md(v)
    if kind == "mistakes":
        return '<ul class="mistakes">' + "".join(f"<li>{inline(m)}</li>" for m in v) + "</ul>"
    if kind == "quiz":
        return qset(v, f"{sid}-quiz")
    if kind == "interview":
        return ('<p class="small muted">Say or write your answer first. Then press Get feedback. The page checks which key points you covered, '
                'shows a model answer and tells you what a strong answer adds. Your text stays in this browser.</p>' + qset(iv_items(v), f"{sid}-iv"))
    if kind == "reqs":
        out = ""
        for k, t in (("func", "What it must do"), ("nonfunc", "How well it must do it"), ("out", "Out of scope, say it out loud")):
            if v.get(k):
                out += f"<h3>{t}</h3><ul>" + "".join(f"<li>{inline(x)}</li>" for x in v[k]) + "</ul>"
        return md(v.get("intro")) + out
    if kind == "estimate":
        return md(v.get("intro")) + (qset(v["items"], f"{sid}-est") if v.get("items") else "") + md(v.get("after"))
    if kind == "task":
        return md(v.get("intro")) + qset(iv_items(v.get("items")), f"{sid}-task")
    if kind == "desk":
        return f'<p>{inline(v.get("blurb", "Scenario questions with instant feedback and a reason for every answer."))}</p><a class="btn btn-primary" href="{sid}-desk.html">Open the practice desk</a>'
    if kind == "refs":
        return '<ol class="reflist">' + "".join(f"<li>{inline(r)}</li>" for r in v) + "</ol>"
    return ""


def desk_body(dk, sid, crumbs, eyebrow, kind):
    inner = md(dk.get("situation"))
    for r_i, rnd in enumerate(dk["rounds"]):
        inner += f'<section class="block round" id="r{r_i + 1}"><h2>{E(rnd["title"])}</h2>{md(rnd.get("info"))}{qset(rnd["items"], f"{sid}-desk-r{r_i + 1}")}</section>'
    if dk.get("card"):
        inner += section("card", "Pocket card. Keep this", md(dk["card"]))
    return (crumbs + f'<header class="doc-head"><div class="eyebrow"><span class="tag {kind}"><span class="dot {kind}"></span>{E(eyebrow)}</span></div>'
            f'<h1>{E(dk["title"])}</h1><p class="lede">{inline(dk["lede"])}</p></header>'
            + '<nav class="doc-toc" aria-label="Rounds">' + "".join(f'<a href="#r{i + 1}">{E(r["title"])}</a>' for i, r in enumerate(dk["rounds"])) + "</nav>"
            + inner)


TRACKS = {
    "learn": dict(label="Concepts", crumb="Concepts", kind="def", eyebrow="Lesson",
                  ov_title="System design concepts, from zero to mastery",
                  ov_lede="Twenty two lessons in five levels. Each one explains a single idea in plain words, shows it moving step by step, gives you real life scenarios, a quiz with fill-ups, interview questions with feedback and a practice desk."),
    "design": dict(label="Design it", crumb="Design it", kind="atk", eyebrow="Design",
                   ov_title="Design real systems, one at a time",
                   ov_lede="Each page is a full design task. You pin down the requirements, do the math, sketch the API and data, watch the system work, dig into the hard parts and then design it yourself with feedback."),
}


def track_side(lessons, cur, track):
    T = TRACKS[track]
    out = [f'<a class="side-top" href="index.html"' + (' aria-current="page"' if cur == "index" else "") + '><span class="mono">00</span>Track overview</a>']
    last = None
    for L in lessons:
        if track == "learn" and L.get("level") != last:
            last = L.get("level")
            out.append(f'<p class="side-lvl mono">{E(LEVELS.get(last, ""))}</p>')
        here = cur in (L["slug"], L["slug"] + "-desk")
        base = "" if cur == L["slug"] else f'{L["slug"]}.html'
        items = [(f"{base}#{a}", t, "#", False) for a, t, k in PARTS[track] if L.get(k) and k != "desk"]
        if L.get("desk"):
            items.append((f'{L["slug"]}-desk.html', "Practice desk", "Q", cur == L["slug"] + "-desk"))
        out.append(side_group(L["num"], L["short"], f'{L["slug"]}.html', "page" if cur == L["slug"] else here, items, f'{track}.{L["slug"]}'))
    return side_wrap(track, T["label"], "".join(out))


def build_track(track):
    T = TRACKS[track]
    files = sorted(f for f in os.listdir(f"content/{track}") if f.endswith(".yaml"))
    lessons = [load(f"content/{track}/{f}") for f in files]
    for L in lessons:
        L.setdefault("short", L["title"])
    crumb, kind = T["crumb"], T["kind"]
    for i, L in enumerate(lessons):
        sid = L["slug"]
        prev = (f'{lessons[i - 1]["slug"]}.html', lessons[i - 1]["title"]) if i else ("index.html", "Track overview")
        nxt = (f'{lessons[i + 1]["slug"]}.html', lessons[i + 1]["title"]) if i + 1 < len(lessons) else None
        parts, toc = [], []
        for pid, title, k in PARTS[track]:
            inner = render_part(k, L, sid)
            if inner.strip():
                title = (L.get("headings") or {}).get(pid, title)
                toc.append((pid, title))
                parts.append(section(pid, title, inner))
        lvl = f'<span>{E(LEVELS[L["level"]])}</span>' if L.get("level") else ""
        head = (f'<nav class="crumbs"><a href="../index.html">Home</a><span>/</span><a href="index.html">{crumb}</a><span>/</span><span>{E(L["num"])}</span></nav>'
                f'<header class="doc-head"><div class="eyebrow"><span class="tag {kind}"><span class="dot {kind}"></span>{crumb} · {T["eyebrow"]} {E(L["num"])}</span>{lvl}<span>{E(L.get("time", ""))}</span></div>'
                f'<h1>{E(L["title"])}</h1><p class="lede">{inline(L["lede"])}</p>'
                f'<div class="doc-meta"><label class="donebox"><span class="check"><input type="checkbox" data-id="{track}.{sid}">{TICKSVG}</span>Mark this page done</label></div></header>'
                + '<nav class="doc-toc" aria-label="On this page">' + "".join(f'<a href="#{a}">{E(b)}</a>' for a, b in toc) + "</nav>")
        dnext = (f'{sid}-desk.html', f'{L["short"]}, practice desk') if L.get("desk") else nxt
        page(f"{track}/{sid}.html", jt(L["title"], f'{T["eyebrow"]} {L["num"]}'), L["lede"][:155], track, track_side(lessons, sid, track),
             head + "".join(parts) + pager(prev, dnext))
        if L.get("desk"):
            crumbs = f'<nav class="crumbs"><a href="../index.html">Home</a><span>/</span><a href="index.html">{crumb}</a><span>/</span><a href="{sid}.html">{E(L["num"])}</a><span>/</span><span>Practice desk</span></nav>'
            page(f"{track}/{sid}-desk.html", jt(L["desk"]["title"], "Practice desk"), L["desk"]["lede"][:155], track,
                 track_side(lessons, sid + "-desk", track),
                 desk_body(L["desk"], sid, crumbs, f'{crumb} · {T["eyebrow"]} {L["num"]} · Practice desk', kind) + pager((f"{sid}.html", L["title"]), nxt))

    # overview
    rows, last = "", None
    for L in lessons:
        if track == "learn" and L.get("level") != last:
            last = L.get("level")
            rows += f'<h2 class="lvl-h">{E(LEVELS[last])}</h2>'
        tg = "".join(f'<span class="tag">{E(t)}</span>' for t in L.get("tags", []))
        rows += (f'<a class="lesson-row" href="{L["slug"]}.html" data-done="{track}.{L["slug"]}"><span class="mono">{L["num"]}</span>'
                 f'<span><b>{E(L["title"])}</b><small>{inline(L["lede"])}</small></span><span class="tags">{tg}</span></a>')
    intro = f"content/{track}/_intro.md"
    body = (f'<nav class="crumbs"><a href="../index.html">Home</a><span>/</span><span>{crumb}</span></nav>'
            f'<header class="doc-head"><div class="eyebrow"><span class="tag {kind}"><span class="dot {kind}"></span>{E(T["label"])}</span><span>{len(lessons)} pages</span></div>'
            f'<h1>{E(T["ov_title"])}</h1><p class="lede">{inline(T["ov_lede"])}</p></header>'
            + md(open(intro, encoding="utf-8").read() if os.path.exists(intro) else "")
            + f'<div class="lesson-list">{rows}</div>')
    page(f"{track}/index.html", jt(T["label"], T["ov_title"]), T["ov_lede"][:155], track, track_side(lessons, "index", track), body)
    return lessons


# ---------------------------------------------------------------- basics
def build_basics():
    B = load("content/basics.yaml")
    rail = "".join(f'<li><a href="#step-{i + 1}"><span>{i + 1:02d}</span>{E(s["short"])}</a></li>' for i, s in enumerate(B["steps"]))
    steps = ""
    for i, s in enumerate(B["steps"]):
        n = i + 1
        inner = md(s.get("body")) + "".join(diagram(d) for d in s.get("diagrams", []))
        if s.get("scenes"):
            inner += scenes_block(s["scenes"])
        if s.get("more"):
            inner += md(s["more"])
        if s.get("sim"):
            inner += SIM
        if s.get("terms"):
            inner += '<dl class="terms">' + "".join(f"<dt>{E(a)}</dt><dd>{inline(b)}</dd>" for a, b in s["terms"]) + "</dl>"
        if s.get("quiz"):
            inner += '<h3>Quick check</h3>' + qset(s["quiz"], f"basics-{n}")
        steps += (f'<section class="step" id="step-{n}"><span class="mono k">Step {n:02d}</span><h2>{E(s["title"])}</h2>'
                  f'<div class="prose">{inner}</div><div class="step-end" data-for="step-{n}"></div></section>')
    main = (f'<main id="main"><section class="page-head"><div class="wrap"><div class="eyebrow">Start here · {len(B["steps"])} steps · about 2 hours</div>'
            f'<h1>{E(B["title"])}</h1><p class="lede">{inline(B["lede"])}</p></div></section>'
            f'<div class="wrap learn"><aside class="rail" aria-label="Steps"><ol>{rail}</ol><p class="progress"></p></aside><div>{steps}'
            f'<nav class="pager" aria-label="Next"><span></span><a class="pg next" href="learn/index.html"><span class="mono">Next</span>Concepts, level 1</a></nav></div></div></main>')
    write("basics.html", "Start here. System design from zero", B["lede"][:155], "", main)
    return len(B["steps"])


SIM = """<div class="sim scale-sim" id="scale-sim">
  <div class="sim-ctrl">
    <h4>How many people use your app?</h4>
    <div class="seg" role="group" aria-label="Users">
      <button type="button" data-users="1000" aria-pressed="true">1 thousand</button>
      <button type="button" data-users="100000" aria-pressed="false">100 thousand</button>
      <button type="button" data-users="10000000" aria-pressed="false">10 million</button>
    </div>
    <h4>What do you add?</h4>
    <label><input type="checkbox" id="s-lb"><span><b>Load balancer and more app servers</b><small>Spread requests over many copies of your app.</small></span></label>
    <label><input type="checkbox" id="s-cache"><span><b>Cache</b><small>Keep popular answers in fast memory.</small></span></label>
    <label><input type="checkbox" id="s-rep"><span><b>Read replicas</b><small>Copies of the database that answer reads.</small></span></label>
    <label><input type="checkbox" id="s-cdn"><span><b>CDN</b><small>Serve images and files from servers near the user.</small></span></label>
    <label><input type="checkbox" id="s-q"><span><b>Queue for writes</b><small>Line up writes so the database takes them at its own pace.</small></span></label>
  </div>
  <div class="sim-out" aria-live="polite"></div>
</div>"""


# ---------------------------------------------------------------- interview bank
def build_interview(learn, design):
    groups = []
    for L in learn:
        if L.get("interview"):
            groups.append(("learn", L, LEVELS.get(L.get("level"), "")))
    for L in design:
        if L.get("interview"):
            groups.append(("design", L, "Design it"))
    total = sum(len(L["interview"]) for _, L, _ in groups)
    body = ""
    for track, L, lvl in groups:
        body += (f'<section class="block iv-group" data-lvl="{E(lvl)}" id="{track}-{L["slug"]}"><h2><a href="{track}/{L["slug"]}.html">{E(L["short"])}</a></h2>'
                 f'<p class="small muted">{E(lvl)} · from {"lesson" if track == "learn" else "design"} {E(L["num"])}</p>'
                 + qset(iv_items(L["interview"]), f'bank-{track}-{L["slug"]}') + "</section>")
    lvls = ["All"] + [v for v in LEVELS.values()] + ["Design it"]
    filt = '<div class="chips" id="iv-filter" role="group" aria-label="Filter">' + "".join(
        f'<button type="button" data-lvl="{"" if l == "All" else E(l)}" aria-pressed="{"true" if l == "All" else "false"}">{E(l)}</button>' for l in lvls) + "</div>"
    I = load("content/interview.yaml")
    tips = md(I.get("intro"))
    beh = ""
    if I.get("framework"):
        beh = section("method", "The answer method", md(I["framework"]) + "".join(diagram(d) for d in I.get("diagrams", [])))
    if I.get("general"):
        beh += section("general", "Questions about you and your choices", qset(iv_items(I["general"]), "bank-general"))
    main = (f'<main id="main"><section class="page-head"><div class="wrap"><div class="eyebrow">Interview prep · {total + len(I.get("general", []))} questions with feedback</div>'
            f'<h1>Interview questions, answered and explained</h1><p class="lede">{inline(I["lede"])}</p>'
            f'<div class="actions"><button class="btn btn-primary" id="iv-random" type="button">Give me a random question</button></div></div></section>'
            f'<div class="wrap narrow doc iv-page">{tips}{beh}<section class="block" id="bank"><h2>The question bank</h2>{filt}</section>{body}</div></main>')
    write("interview.html", "Interview questions. System design", I["lede"][:155], "", main)
    return total


# ---------------------------------------------------------------- plan
def build_plan(learn, design):
    P = load("content/plan.yaml")
    titles = {f"learn/{L['slug']}.html": L["title"] for L in learn}
    titles.update({f"design/{L['slug']}.html": L["title"] for L in design})
    weeks = ""
    for w in P["weeks"]:
        tasks = ""
        for j, t in enumerate(w["tasks"]):
            cid = f'plan.{w["n"]}.{j}'
            link = f' <a href="{t["page"]}">{E(titles.get(t["page"], t.get("label", "Open")))}</a>' if t.get("page") else ""
            tasks += (f'<div class="task">{checkbox(cid, t["t"])}<div class="k">{E(t.get("k", "Do"))}<small>{E(t.get("time", ""))}</small></div>'
                      f'<div class="body"><p>{inline(t["t"])}{link}</p></div></div>')
        weeks += (f'<article class="week" id="week-{w["n"]}"><div class="week-num"><b>{w["n"]:02d}</b>Week</div>'
                  f'<div><h3>{E(w["t"])}</h3><p class="small muted">{inline(w.get("d", ""))}</p>{tasks}</div></article>')
    main = (f'<div class="plan-bar" id="plan-bar"><div class="wrap"><div class="score"><b id="pts">0</b><span class="mono muted">of <span id="pmax">0</span> tasks</span></div>'
            f'<div class="meter" aria-hidden="true"><i id="meter"></i></div><div class="level" id="level"></div><button class="btn btn-quiet btn-sm" id="reset" type="button">Reset</button></div></div>'
            f'<main id="main"><section class="page-head"><div class="wrap"><div class="eyebrow">The plan · {len(P["weeks"])} weeks · about 5 hours a week</div>'
            f'<h1>{E(P["title"])}</h1><p class="lede">{inline(P["lede"])}</p></div></section>'
            f'<section class="pmod"><div class="wrap">{weeks}</div></section></main>')
    write("plan.html", "The plan. System design in 10 weeks", P["lede"][:155], "", main)


# ---------------------------------------------------------------- library
def build_library():
    Lb = load("content/library.yaml")
    body = ""
    for g in Lb["groups"]:
        rows = "".join(f'<div><div><a class="title" href="{E(x["u"])}" target="_blank" rel="noopener">{E(x["t"])}</a>'
                       f'<div class="note">{inline(x.get("n", ""))}</div></div><span class="meta">{E(x.get("type", g["t"]))}</span></div>' for x in g["items"])
        body += f'<section class="section"><div class="wrap"><h2 class="section-title">{E(g["t"])}</h2><p class="section-sub">{inline(g.get("d", ""))}</p><div class="rows">{rows}</div></div></section>'
    main = (f'<main id="main"><section class="page-head"><div class="wrap"><div class="eyebrow">Library</div><h1>{E(Lb["title"])}</h1>'
            f'<p class="lede">{inline(Lb["lede"])}</p></div></section>{body}</main>')
    write("library.html", "Library. System design resources", Lb["lede"][:155], "", main)


# ---------------------------------------------------------------- home
def build_home(learn, design, nb, niv):
    H = load("content/home.yaml")
    route = [{"s": L["slug"], "n": L["num"], "t": L["short"], "l": L.get("level")} for L in learn]
    nq = 0
    for L in learn + design:
        nq += len(L.get("quiz", [])) + sum(len(r["items"]) for r in (L.get("desk") or {}).get("rounds", []))
        nq += len((L.get("estimate") or {}).get("items", []))
    stats = [(nb, "short steps in Start here, with a scale simulator"), (len(learn), "concept lessons in five levels, each with an animated diagram"),
             (len(design), "full design tasks, from a link shortener to an AI chat app"), (nq, "quiz, fill-up and scenario questions with reasons"),
             (niv, "interview questions with model answers and feedback")]
    cards = "".join(f'<a class="card" href="{c["href"]}"><span class="num">{inline(c["num"])}</span><h3>{E(c["t"])}</h3><p>{inline(c["d"])}</p><span class="go">{E(c["go"])}</span></a>' for c in H["cards"])
    loop = "".join(f'<div><span class="mono">{E(x[0])}</span><h3>{E(x[1])}</h3><p>{inline(x[2])}</p></div>' for x in H["loop"])
    main = f"""<main id="main">
  <section class="hero"><div class="wrap"><div>
    <div class="eyebrow rise"><span class="tag def"><span class="dot def"></span>Concepts</span><span class="tag atk"><span class="dot atk"></span>Design it</span><span>System design and architecture</span></div>
    <h1 class="rise d1">{E(H["title"])}</h1>
    <p class="lede rise d2">{inline(H["lede"])}</p>
    <div class="actions rise d3"><a class="btn btn-primary" href="basics.html">Start here</a><a class="btn btn-quiet" href="plan.html">Open the plan</a></div>
    <p class="small muted rise d3" id="home-progress" style="margin-top:20px"></p>
  </div>
  <div class="hero-visual rise d2"><div class="sheet"><div class="sheet-cap"><span>Your route, basic to mastery</span><span>stations fill in as you finish lessons</span></div>
    <svg id="route" class="dg" viewBox="0 0 640 430" role="img" aria-label="Route map of the five levels of concept lessons, from foundations to mastery, then the design tasks."></svg></div></div>
  </div></section>
  <section class="section"><div class="wrap"><div class="stats stats-5">{"".join(f'<div class="stat"><b>{n}</b><span>{E(t)}</span></div>' for n, t in stats)}</div></div></section>
  <section class="section"><div class="wrap"><h2 class="section-title">How every lesson works</h2><p class="section-sub">{inline(H["loop_sub"])}</p><div class="loop">{loop}</div></div></section>
  <section class="section"><div class="wrap"><h2 class="section-title">Ways in</h2><p class="section-sub">Pick the one that fits you today. They all link to each other.</p><div class="grid grid-3">{cards}</div></div></section>
  <section class="section"><div class="wrap narrow"><h2 class="section-title">{E(H["end_t"])}</h2><div class="prose">{md(H["end"])}</div></div></section>
</main>
<script>window.ROUTE={json.dumps(route)};window.DESIGNS={len(design)};</script>"""
    write("index.html", "Boxes and Arrows. System design from zero to mastery", H["lede"][:155], "", main)


if __name__ == "__main__":
    learn = build_track("learn")
    design = build_track("design")
    nb = build_basics()
    niv = build_interview(learn, design)
    build_plan(learn, design)
    build_library()
    build_home(learn, design, nb, niv)
    print(f"built {nb} basics steps, {len(learn)} concept lessons, {len(design)} designs, {niv} interview questions")
