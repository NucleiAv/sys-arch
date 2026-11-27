"""Build every page of the Boxes and Arrows site.

Run from anywhere:
    python tools/build.py

Reads   content/*.yaml, content/{learn,infra,design,protocols}/*.yaml
Writes  index.html, basics.html, plan.html, interview.html, library.html,
        protocols.html, learn/*.html, infra/*.html, design/*.html,
        assets/js/protocol-data.js

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
V = "20261127e"
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


def sub_lines(sub, w):
    """mono caption under a node label, wrapped to the node width"""
    return wrap(sub, w - 12, 11.8) if sub else []


def node_h(w, label, sub=None, base=52):
    return max(base, 20 + 16 * len(wrap(label, w - 16)) + 13 * len(sub_lines(sub, w)))


def node(x, y, w, h, label, kind="box", sub=None):
    s = f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="8" class="{KIND.get(kind, "box")}"/>'
    lines = wrap(label, w - 16)
    subs = sub_lines(sub, w)
    if subs:
        sh = 13 * len(subs)
        s += text_block(x + w / 2, y + (h - sh) / 2, lines, "t-s")
        for j, l in enumerate(subs):
            s += f'<text x="{x + w / 2:.0f}" y="{y + h - 9 - (len(subs) - 1 - j) * 13:.0f}" text-anchor="middle" class="t-mono">{E(l)}</text>'
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
        h = max(node_h(w, nd[0], nd[2] if len(nd) > 2 else None) for nd in nodes)
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
                    ws = wrap(lab, gap + 6, 11.8)[:3]
                    for j, l in enumerate(ws):
                        out.append(f'<text x="{(ax + bx) / 2:.0f}" y="{y + h / 2 - 8 - (len(ws) - 1 - j) * 14:.0f}" text-anchor="middle" class="t-mono">{E(l)}</text>')
        y += h + 28
    return W, y - 12, "".join(out)


def d_cycle(d):
    steps = d["nodes"]
    n = len(steps)
    w = 150
    h = max(node_h(w, st[0], st[2] if len(st) > 2 else f"step {i + 1}") for i, st in enumerate(steps))
    W, H = 680, (300 if n <= 4 else 340) + (h - 52)
    cx, cy, rx, ry = W / 2, H / 2, 250, (H / 2 - 14 - h / 2)
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
            st["stats"] = ["yes" if v is True else "no" if v is False else str(v) for v in st["stats"]]
    js = json.dumps(d, ensure_ascii=False).replace("</", "<\\/")
    return f'<div class="scene"><script type="application/json">{js}</script><noscript>{E(sc.get("title", ""))}</noscript></div>'


def scenes_block(items):
    if not items:
        return ""
    return '<p class="small muted">Press Next or Play. Each step lights up one part and moves the requests. Arrow keys move steps after you click the diagram.</p>' + "".join(scene(x) for x in items)


# ---------------------------------------------------------------- questions
def prep_q(it):
    it = dict(it)
    for k in ("q", "why"):
        if k in it and isinstance(it[k], str):
            it[k] = inline(it[k])
    if isinstance(it.get("info"), str):
        it["info"] = md(it["info"])
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
<script src="{r}assets/js/scene.js?v={v}"></script>{extra}
</body>
</html>
"""


def write(path, title, desc, track, main, r="", extra=""):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    out = HEAD.format(title=E(title), desc=E(desc), track=track, r=r, v=V) + main + TAIL.format(r=r, v=V, extra=extra)
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
DOTS = {"learn": "def", "infra": "pen", "design": "atk", "cloud": "cl"}


def side_wrap(track, label, inner):
    dot = DOTS.get(track, "def")
    return (f'<aside class="side" id="side" aria-label="{E(label)}">'
            f'<button class="side-btn" type="button" aria-expanded="false" aria-controls="side-nav">{E(label)}, all pages</button>'
            f'<nav id="side-nav"><p class="side-h"><span class="dot {dot}"></span>{E(label)}</p>{inner}</nav></aside>')


def side_group(num, title, href, cur, items, done=None):
    sub = "".join(f'<a href="{h}"' + (' aria-current="page"' if c else "") + f'><span class="mono">{E(m)}</span>{E(t)}</a>' for h, t, m, c in items)
    return (f'<details class="side-mod{" cur" if cur else ""}"{" open" if cur else ""}>'
            f'<summary{" data-done=" + chr(34) + done + chr(34) if done else ""}><span class="mono">{E(num)}</span><span>{E(title)}</span></summary>'
            f'<a class="side-open" href="{href}"' + (' aria-current="page"' if cur == "page" else "") + f'><span class="mono">&rarr;</span>Open the page</a>{sub}</details>')


# ---------------------------------------------------------------- tracks
LESSON_PARTS = [("idea", "The idea in one minute", "idea"), ("watch", "Watch it, step by step", "scenes"), ("words", "Words you need", "terms"),
                ("how", "How it works", "how"), ("life", "Real life scenarios", "life"), ("trade", "Trade-offs", "tradeoffs"),
                ("mistakes", "Common mistakes", "mistakes"), ("security", "Security lens", "security"), ("quiz", "Practice. Check yourself", "quiz"), ("interview", "Practice. Interview questions", "interview"),
                ("practice", "Practice desk", "desk"), ("refs", "Go deeper", "refs")]
PARTS = {
    "learn": LESSON_PARTS,
    "infra": LESSON_PARTS,
    "cloud": LESSON_PARTS,
    "design": [("ask", "The ask", "ask"), ("reqs", "Pin down the requirements", "reqs"), ("estimate", "Do the math", "estimate"),
               ("api", "The API", "api"), ("data", "The data model", "data"), ("watch", "Watch it work", "scenes"),
               ("hld", "The big picture", "hld"), ("deep", "Deep dives", "deep"), ("trade", "Trade-offs you must name", "tradeoffs"),
               ("security", "Security and abuse", "security"), ("task", "Practice. Your turn", "task"), ("interview", "Practice. Follow-up questions", "interview"), ("practice", "Practice desk", "desk"),
               ("refs", "Go deeper", "refs")],
}


def render_part(kind, L, sid):
    v = L.get(kind)
    if not v:
        return ""
    if kind in ("idea", "ask", "api", "data"):
        return md(v) + "".join(diagram(d) for d in L.get(kind + "_diagrams", []))
    if kind in ("how", "hld"):
        return md(v) + "".join(diagram(d) for d in L.get("diagrams", []))
    if kind == "scenes":
        return scenes_block(v)
    if kind == "terms":
        return '<dl class="terms">' + "".join(f"<dt>{E(a)}</dt><dd>{inline(b)}</dd>" for a, b in v) + "</dl>"
    if kind in ("life", "deep"):
        return "".join(f'<div class="case"><h3>{E(c[0])}</h3>{md(c[1])}</div>' for c in v)
    if kind == "tradeoffs":
        head = L.get("trade_head", ["Choice", "Good at", "Costs you"])
        return (md(L.get("trade_intro")) + table(head, v)) if isinstance(v, list) else md(v)
    if kind == "security":
        return '<div class="seclens">' + md(v) + "</div>"
    if kind == "mistakes":
        return '<ul class="mistakes">' + "".join(f"<li>{inline(m)}</li>" for m in v) + "</ul>"
    if kind == "quiz":
        return qset(v, f"{sid}-quiz")
    if kind == "interview":
        return ('<p class="small muted">Say or write your answer first. Then press Get feedback. The page looks for key words '
                'from each key point in your text, shows a model answer and tells you what a strong answer adds. There is no AI model and no cost. '
                'The check runs in your browser and your text never leaves it. Key words can miss a point you made in other words, so treat it as a guide.</p>' + qset(iv_items(v), f"{sid}-iv"))
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


def rounds_html(dk, sid):
    inner = md(dk.get("situation"))
    for r_i, rnd in enumerate(dk["rounds"]):
        inner += f'<section class="block round" id="r{r_i + 1}"><h2>{E(rnd["title"])}</h2>{md(rnd.get("info"))}{qset(rnd["items"], f"{sid}-r{r_i + 1}")}</section>'
    if dk.get("card"):
        inner += section("card", "Pocket card. Keep this", md(dk["card"]))
    return inner


def desk_body(dk, sid, crumbs, eyebrow, kind):
    return (crumbs + f'<header class="doc-head"><div class="eyebrow"><span class="tag {kind}"><span class="dot {kind}"></span>{E(eyebrow)}</span></div>'
            f'<h1>{E(dk["title"])}</h1><p class="lede">{inline(dk["lede"])}</p></header>'
            + '<nav class="doc-toc" aria-label="Rounds">' + "".join(f'<a href="#r{i + 1}">{E(r["title"])}</a>' for i, r in enumerate(dk["rounds"])) + "</nav>"
            + rounds_html(dk, sid + "-desk"))


TRACKS = {
    "learn": dict(label="Concepts", crumb="Concepts", kind="def", eyebrow="Lesson",
                  ov_title="System design concepts, from zero to mastery",
                  ov_lede="Sixty lessons in eight levels. Each lesson explains one idea in plain words, shows it step by step and ends with practice. Each level ends with a practice page that mixes all its lessons."),
    "infra": dict(label="Infra", crumb="Infra", kind="pen", eyebrow="Lesson",
                  ov_title="Infrastructure, from your first commit to the cloud",
                  ov_lede="Git, GitHub, GitHub Actions, Linux, Docker, Kubernetes, AWS, Terraform and safe deploys. Each lesson ends with practice that includes real commands and config files. Each level ends with a practice page."),
    "cloud": dict(label="Cloud", crumb="Cloud", kind="cl", eyebrow="Lesson", home="../cloud-track.html",
                  ov_title="AWS and cloud, from zero to architect",
                  ov_lede="Eight levels. Cloud basics, identity, networking, compute, storage, databases, serverless, containers, operations, cost, security from both sides, multi-cloud and the SAA-C03 exam, then real designs for every tier of application."),
    "design": dict(label="Design it", crumb="Design it", kind="atk", eyebrow="Design",
                   ov_title="Design real systems, one at a time",
                   ov_lede="Each page is a full design task. You pin down the requirements, do the math, sketch the API and data, watch the system work, study the hard parts and then design it yourself with feedback."),
}


def load_track(track):
    """Read the lessons of a track in the order the _order.yaml file gives, and number them per level."""
    files = {f[:-5]: load(f"content/{track}/{f}") for f in os.listdir(f"content/{track}") if f.endswith(".yaml") and not f.startswith("_")}
    order_p = f"content/{track}/_order.yaml"
    if not os.path.exists(order_p):
        ls = [files[k] for k in sorted(files)]
        for L in ls:
            L.setdefault("short", L["title"])
        return ls, []
    O = load(order_p)
    ls = []
    for lv in O["levels"]:
        for i, slug in enumerate(lv["items"]):
            L = files.pop(slug)
            L["slug"], L["level"], L["num"] = slug, lv["n"], f'{lv["n"]}.{i + 1}'
            L.setdefault("short", L["title"])
            if L.get("kind") == "practice":
                L["short"] = f'Level {lv["n"]} practice'
            ls.append(L)
    if files:
        sys.exit(f"{track}: files missing from _order.yaml: {sorted(files)}")
    return ls, O["levels"]


def lvl_name(levels, n):
    for lv in levels:
        if lv["n"] == n:
            return f'Level {n}. {lv["t"]}'
    return ""


def track_side(lessons, levels, cur, track):
    T = TRACKS[track]
    out = [f'<a class="side-top" href="index.html"' + (' aria-current="page"' if cur == "index" else "") + '><span class="mono">0</span>Track overview</a>']
    last = None
    for L in lessons:
        if levels and L.get("level") != last:
            last = L.get("level")
            out.append(f'<p class="side-lvl mono">{E(lvl_name(levels, last))}</p>')
        here = cur in (L["slug"], L["slug"] + "-desk")
        base = "" if cur == L["slug"] else f'{L["slug"]}.html'
        if L.get("kind") == "practice":
            items = [(f"{base}#r{i + 1}", r["title"], "Q", False) for i, r in enumerate(L["rounds"])]
        else:
            items = [(f"{base}#{a}", (L.get("headings") or {}).get(a, t), "#", False) for a, t, k in PARTS["design" if L.get("kind") == "design" else track] if L.get(k) and k != "desk"]
        if L.get("desk"):
            items.append((f'{L["slug"]}-desk.html', "Practice desk", "Q", cur == L["slug"] + "-desk"))
        out.append(side_group(L["num"], L["short"], f'{L["slug"]}.html', "page" if cur == L["slug"] else here, items, f'{track}.{L["slug"]}'))
    return side_wrap(track, T["label"], "".join(out))


def donefoot(track, sid, label="Mark this page done"):
    """The done tick sits at the end of the page, where you finish it."""
    return ('<section class="block donefoot" id="done"><h2>Finished this page?</h2>'
            '<p class="small muted">Tick it. Your route on the home page and your plan fill in.</p>' + donebox(track, sid, label) + "</section>")


def donebox(track, sid, label="Mark this page done"):
    return f'<div class="doc-meta"><label class="donebox"><span class="check"><input type="checkbox" data-id="{track}.{sid}">{TICKSVG}</span>{label}</label></div>'


def build_track(track):
    T = TRACKS[track]
    lessons, levels = load_track(track)
    crumb, kind = T["crumb"], T["kind"]
    for i, L in enumerate(lessons):
        sid = L["slug"]
        prev = (f'{lessons[i - 1]["slug"]}.html', lessons[i - 1]["title"]) if i else ("index.html", "Track overview")
        nxt = (f'{lessons[i + 1]["slug"]}.html', lessons[i + 1]["title"]) if i + 1 < len(lessons) else None
        lvl = f'<span>{E(lvl_name(levels, L["level"]))}</span>' if L.get("level") else ""
        crumbs = f'<nav class="crumbs"><a href="../index.html">Home</a><span>/</span><a href="{T.get("home", "index.html")}">{crumb}</a><span>/</span><span>{E(L["num"])}</span></nav>'
        side = track_side(lessons, levels, sid, track)
        if L.get("kind") == "practice":
            body = (crumbs + f'<header class="doc-head"><div class="eyebrow"><span class="tag {kind}"><span class="dot {kind}"></span>{crumb} · Level {L["level"]} practice</span>{lvl}<span>{E(L.get("time", ""))}</span></div>'
                    f'<h1>{E(L["title"])}</h1><p class="lede">{inline(L["lede"])}</p></header>'
                    + '<nav class="doc-toc" aria-label="Rounds">' + "".join(f'<a href="#r{j + 1}">{E(r["title"])}</a>' for j, r in enumerate(L["rounds"])) + "</nav>"
                    + rounds_html(L, sid) + donefoot(track, sid, "Mark this practice done") + pager(prev, nxt))
            page(f"{track}/{sid}.html", jt(L["title"], f'{crumb} level {L["level"]} practice'), L["lede"][:155], track, side, body)
            continue
        parts, toc = [], []
        for pid, title, k in PARTS["design" if L.get("kind") == "design" else track]:
            inner = render_part(k, L, sid)
            if inner.strip():
                title = (L.get("headings") or {}).get(pid, title)
                toc.append((pid, title))
                parts.append(section(pid, title, inner))
        head = (crumbs + f'<header class="doc-head"><div class="eyebrow"><span class="tag {kind}"><span class="dot {kind}"></span>{crumb} · {"Design" if L.get("kind") == "design" else T["eyebrow"]} {E(L["num"])}</span>{lvl}<span>{E(L.get("time", ""))}</span></div>'
                f'<h1>{E(L["title"])}</h1><p class="lede">{inline(L["lede"])}</p></header>'
                + '<nav class="doc-toc" aria-label="On this page">' + "".join(f'<a href="#{a}">{E(b)}</a>' for a, b in toc) + "</nav>")
        dnext = (f'{sid}-desk.html', f'{L["short"]}, practice desk') if L.get("desk") else nxt
        page(f"{track}/{sid}.html", jt(L["title"], f'{"Design" if L.get("kind") == "design" else T["eyebrow"]} {L["num"]}'), L["lede"][:155], track, side, head + "".join(parts) + donefoot(track, sid) + pager(prev, dnext))
        if L.get("desk"):
            dcr = f'<nav class="crumbs"><a href="../index.html">Home</a><span>/</span><a href="{T.get("home", "index.html")}">{crumb}</a><span>/</span><a href="{sid}.html">{E(L["num"])}</a><span>/</span><span>Practice desk</span></nav>'
            page(f"{track}/{sid}-desk.html", jt(L["desk"]["title"], "Practice desk"), L["desk"]["lede"][:155], track,
                 track_side(lessons, levels, sid + "-desk", track),
                 desk_body(L["desk"], sid, dcr, f'{crumb} · {T["eyebrow"]} {L["num"]} · Practice desk', kind) + pager((f"{sid}.html", L["title"]), nxt))

    # overview
    rows, last = "", None
    for L in lessons:
        if levels and L.get("level") != last:
            last = L.get("level")
            lv = next(x for x in levels if x["n"] == last)
            rows += f'<h2 class="lvl-h">{E(lvl_name(levels, last))}</h2><p class="lvl-d">{inline(lv.get("d", ""))}</p>'
        if L.get("kind") == "practice":
            tg = '<span class="tag new">practice</span>'
        else:
            tg = "".join(f'<span class="tag">{E(t)}</span>' for t in L.get("tags", []))
        rows += (f'<a class="lesson-row{" is-practice" if L.get("kind") == "practice" else ""}" href="{L["slug"]}.html" data-done="{track}.{L["slug"]}"><span class="mono">{L["num"]}</span>'
                 f'<span><b>{E(L["title"])}</b><small>{inline(L["lede"])}</small></span><span class="tags">{tg}</span></a>')
    intro = f"content/{track}/_intro.md"
    body = (f'<nav class="crumbs"><a href="../index.html">Home</a><span>/</span><span>{crumb}</span></nav>'
            f'<header class="doc-head"><div class="eyebrow"><span class="tag {kind}"><span class="dot {kind}"></span>{E(T["label"])}</span><span>{len(lessons)} pages</span></div>'
            f'<h1>{E(T["ov_title"])}</h1><p class="lede">{inline(T["ov_lede"])}</p></header>'
            + md(open(intro, encoding="utf-8").read() if os.path.exists(intro) else "")
            + f'<div class="lesson-list">{rows}</div>')
    page(f"{track}/index.html", jt(T["label"], T["ov_title"]), T["ov_lede"][:155], track, track_side(lessons, levels, "index", track), body)
    return lessons, levels


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
            inner += f'<h3>{"Practice" if s.get("practice") else "Practice. Quick check"}</h3>' + qset(s["quiz"], f"basics-{n}")
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
def build_interview(tracks, design):
    groups = []
    for track, (ls, levels) in tracks.items():
        for L in ls:
            if L.get("interview"):
                groups.append((track, L, f'{TRACKS[track]["label"]} level {L["level"]}'))
    for L in design:
        if L.get("interview"):
            groups.append(("design", L, "Design it"))
    total = sum(len(L["interview"]) for _, L, _ in groups)
    body = ""
    for track, L, lvl in groups:
        body += (f'<section class="block iv-group" data-lvl="{E(lvl)}" id="{track}-{L["slug"]}"><h2><a href="{track}/{L["slug"]}.html">{E(L["short"])}</a></h2>'
                 f'<p class="small muted">{E(lvl)} · {TRACKS[track]["eyebrow"].lower()} {E(L["num"])}</p>'
                 + qset(iv_items(L["interview"]), f'bank-{track}-{L["slug"]}') + "</section>")
    chips = ["All"]
    for _, _, lvl in groups:
        if lvl not in chips:
            chips.append(lvl)
    filt = '<div class="chips" id="iv-filter" role="group" aria-label="Filter">' + "".join(
        f'<button type="button" data-lvl="{"" if l == "All" else E(l)}" aria-pressed="{"true" if l == "All" else "false"}">{E(l)}</button>' for l in chips) + "</div>"
    I = load("content/interview.yaml")
    beh = ""
    if I.get("framework"):
        beh = section("method", "The answer method", md(I["framework"]) + "".join(diagram(d) for d in I.get("diagrams", [])))
    if I.get("general"):
        beh += section("general", "Questions about you and your choices", qset(iv_items(I["general"]), "bank-general"))
    main = (f'<main id="main"><section class="page-head"><div class="wrap"><div class="eyebrow">Interview prep · {total + len(I.get("general", []))} questions with feedback</div>'
            f'<h1>Interview questions, answered and explained</h1><p class="lede">{inline(I["lede"])}</p>'
            f'<div class="actions"><button class="btn btn-primary" id="iv-random" type="button">Give me a random question</button></div></div></section>'
            f'<div class="wrap narrow doc iv-page">{md(I.get("intro"))}{beh}<section class="block" id="bank"><h2>The question bank</h2>{filt}</section>{body}</div></main>')
    write("interview.html", "Interview questions. System design", I["lede"][:155], "", main)
    return total + len(I.get("general", []))


# ---------------------------------------------------------------- plan
AUTO_NOTE = {
    "basics": '<p class="small muted auto-note">Ticks itself when you have read all the steps.</p>',
    "protocols": '<p class="small muted auto-note">Ticks itself when you have played each of these protocols to its last step.</p>',
    "extra_designs": '<p class="small muted auto-note">Ticks itself when you mark two designs done that are not named elsewhere in the plan.</p>',
    "feedback": '<p class="small muted auto-note">Ticks itself after you get feedback on five questions on the interview page.</p>',
}
def build_plan(all_pages):
    P = load("content/plan.yaml")
    weeks = ""
    for w in P["weeks"]:
        tasks = ""
        for j, t in enumerate(w["tasks"]):
            cid = f'plan.{w["n"]}.{j}'
            pg = t.get("page")
            if pg and pg not in all_pages:
                sys.exit(f"plan.yaml week {w['n']}: unknown page {pg}")
            link = f' <a href="{pg}">{E(t.get("label") or all_pages[pg])}</a>' if pg else ""
            m = re.match(r"^(learn|infra|design)/([\w-]+)\.html$", pg or "")
            dl = f' data-link="{m.group(1)}.{m.group(2)}"' if m and m.group(2) != "index" else ""
            if t.get("done"):
                rule = dict(t["done"])
                if rule.get("protocols"):
                    bad = [x for x in rule["protocols"] if f"protocols.html#/{x}" not in all_pages]
                    if bad:
                        sys.exit(f"plan.yaml week {w['n']}: unknown protocols {bad}")
                if "extra_designs" in rule:
                    rule["skip"] = sorted({re.sub(r"\.html$", "", x["page"].split("/")[1]) for ww in P["weeks"] for x in ww["tasks"]
                                           if str(x.get("page", "")).startswith("design/d")})
                dl += f" data-auto='{E(json.dumps(rule))}'"
            tasks += (f'<div class="task"{dl}>{checkbox(cid, t["t"])}<div class="k">{E(t.get("k", "Do"))}<small>{E(t.get("time", ""))}</small></div>'
                      f'<div class="body"><p>{inline(t["t"])}{link}</p>{AUTO_NOTE.get(next(iter(t["done"])), "") if t.get("done") else ""}</div></div>')
        weeks += (f'<article class="week" id="week-{w["n"]}"><div class="week-num"><b>{w["n"]:02d}</b>Week</div>'
                  f'<div><h3>{E(w["t"])}</h3><p class="small muted">{inline(w.get("d", ""))}</p>{tasks}</div></article>')
    main = (f'<div class="plan-bar" id="plan-bar"><div class="wrap"><div class="score"><b id="pts">0</b><span class="mono muted">of <span id="pmax">0</span> tasks</span></div>'
            f'<div class="meter" aria-hidden="true"><i id="meter"></i></div><div class="level" id="level"></div><button class="btn btn-quiet btn-sm" id="reset" type="button">Reset</button></div></div>'
            f'<main id="main"><section class="page-head"><div class="wrap"><div class="eyebrow">The plan · {len(P["weeks"])} weeks · about 6 hours a week</div>'
            f'<h1>{E(P["title"])}</h1><p class="lede">{inline(P["lede"])}</p></div></section>'
            f'<section class="pmod"><div class="wrap">{weeks}</div></section></main>')
    write("plan.html", "The plan. System design, step by step", P["lede"][:155], "", main)


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


# ---------------------------------------------------------------- protocols
PCATS = {"core": "Core", "app": "Application", "security": "Security", "data": "Data and admin"}
PKINDS = {"req", "res", "ctl", "sec", "data", "bad"}


def build_protocols():
    protos = []
    for f in sorted(os.listdir("content/protocols")):
        if f.endswith(".yaml") and not f.startswith("_"):
            for p in load(f"content/protocols/{f}"):
                protos.append(p)
    ids = set()
    out = []
    for p in protos:
        pid = p["id"]
        if pid in ids:
            sys.exit(f"duplicate protocol id {pid}")
        ids.add(pid)
        if p["cat"] not in PCATS:
            sys.exit(f"{pid}: bad cat {p['cat']}")
        nodes = {}
        for k, v in p["nodes"].items():
            label, sub, icon, x, y = v
            nodes[k] = {"label": label, "sub": sub, "icon": icon, "x": x, "y": y}
        links = [list(l) for l in p.get("links", [])]
        steps = []
        for si, st in enumerate(p["steps"]):
            pk = []
            for q in st.get("p", []):
                a, b, lab, kind = q[0], q[1], q[2], q[3]
                if a not in nodes or b not in nodes:
                    sys.exit(f"{pid} step {si + 1}: unknown node in {q}")
                if kind not in PKINDS:
                    sys.exit(f"{pid} step {si + 1}: bad packet kind {kind}")
                extra = q[4] if len(q) > 4 else {}
                pk.append({"f": a, "t": b, "m": lab, "k": kind,
                           "fields": [[str(x), str(y)] for x, y in (extra.get("fields") or {}).items()] if isinstance(extra, dict) else [],
                           "raw": extra.get("raw") if isinstance(extra, dict) else None,
                           "hex": extra.get("hex") if isinstance(extra, dict) else None})
            for n in st.get("on", []):
                if n not in nodes:
                    sys.exit(f"{pid} step {si + 1}: unknown node {n}")
            steps.append({"t": st["t"], "tag": st.get("tag", ""), "d": md(st["d"]), "f": [[str(x), str(y)] for x, y in (st.get("f") or {}).items()],
                          "p": pk, "on": st.get("on", []), "good": inline(st["good"]) if st.get("good") else "", "bad": st.get("bad", [])})
        quiz = [prep_q(q) for q in p.get("quiz", [])]
        out.append({"id": pid, "name": p["name"], "full": p["full"], "layer": p["layer"], "cat": p["cat"], "title": p["title"],
                    "port": p.get("port", ""), "transport": p.get("transport", ""), "lede": inline(p["lede"]),
                    "overview": md(p.get("overview", "")), "nodes": nodes, "links": links, "steps": steps, "quiz": quiz,
                    "refs": [inline(r) for r in p.get("refs", [])]})
    js = "window.PROTOCOLS=" + json.dumps(out, ensure_ascii=False).replace("</", "<\\/") + ";window.PCATS=" + json.dumps(PCATS) + ";"
    open("assets/js/protocol-data.js", "w", encoding="utf-8", newline="\n").write(js)
    intro = load("content/protocols/_page.yaml") if os.path.exists("content/protocols/_page.yaml") else {}
    main = f"""<div class="px" id="px">
  <aside class="px-list" id="px-list" aria-label="Protocols">
    <div class="px-list-head"><h2>All protocols <span class="mono" id="px-count">{len(out)}</span></h2><button class="px-close btn btn-quiet btn-sm" type="button" aria-label="Close the list">Close</button></div>
    <label class="px-search"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/></svg><input type="search" id="px-q" placeholder="Search protocols" aria-label="Search protocols" autocomplete="off"></label>
    <div class="px-tabs" role="group" aria-label="Filter"><button type="button" data-cat="" aria-pressed="true">All</button>{"".join(f'<button type="button" data-cat="{k}" aria-pressed="false">{v}</button>' for k, v in PCATS.items())}</div>
    <div class="px-rows" id="px-rows"></div>
  </aside>
  <main id="main" class="px-main">
    <div class="px-bar"><button class="btn btn-quiet btn-sm px-open" type="button" id="px-open">All protocols</button><nav class="crumbs" id="px-crumbs"></nav></div>
    <header class="px-head"><div class="eyebrow mono" id="px-eyebrow"></div><h1 id="px-title"></h1><p class="lede" id="px-lede"></p><div class="px-facts" id="px-facts"></div></header>
    <div class="px-work"><div class="px-col-a">
    <section class="px-stage-card">
      <div class="px-stage-top"><div class="seg px-views" role="group" aria-label="View"><button type="button" data-view="net" aria-pressed="true">Network</button><button type="button" data-view="seq" aria-pressed="false">Sequence</button></div><span class="mono px-stepno" id="px-stepno"></span></div>
      <div class="px-stats" id="px-stats"></div>
      <div class="px-stage" id="px-stage"></div>
      <div class="px-legend small" id="px-legend"></div>
      <div class="px-controls">
        <button class="px-play" type="button" id="px-play" aria-label="Play">Play</button>
        <button class="btn btn-quiet btn-sm" type="button" id="px-prev" aria-label="Previous step">Back</button>
        <button class="btn btn-quiet btn-sm" type="button" id="px-next" aria-label="Next step">Next</button>
        <div class="px-prog" id="px-prog"></div>
        <select id="px-speed" aria-label="Playback speed"><option value="0.5">0.5x</option><option value="1" selected>1x</option><option value="1.5">1.5x</option><option value="2">2x</option></select>
        <button class="btn btn-quiet btn-sm" type="button" id="px-restart" aria-label="Start over">Restart</button>
      </div>
    </section>
    <section class="px-rail-card"><div class="px-rail-top"><span class="mono">In this protocol</span><span class="mono" id="px-railno"></span></div><div class="px-rail" id="px-rail"></div></section>
    </div><div class="px-col-b">
    <section class="px-detail">
      <div class="seg px-tabs2" role="group" aria-label="Details"><button type="button" data-tab="step" aria-pressed="true">Current step</button><button type="button" data-tab="over" aria-pressed="false">Overview</button><button type="button" data-tab="prac" aria-pressed="false">Practice</button></div>
      <div id="px-tab-step"></div><div id="px-tab-over" hidden></div><div id="px-tab-prac" hidden></div>
    </section>
    <section class="px-inspect"><div class="px-inspect-top"><h3>Packet inspector</h3><div class="seg" role="group" aria-label="Inspector view"><button type="button" data-ins="fields" aria-pressed="true">Fields</button><button type="button" data-ins="hex" aria-pressed="false">Hex</button></div></div><div id="px-pk-list" class="px-pk-list"></div><div id="px-pk-body" class="px-pk-body"></div></section>
    </div></div>
    <div class="px-intro prose">{md(intro.get("intro", ""))}</div>
  </main>
</div>"""
    write("protocols.html", "Protocols, animated step by step", "Network protocols explained with animated network and sequence views, step by step, with packet fields and practice.", "protocols", main,
          extra=f'\n<script src="assets/js/protocol-data.js?v={V}"></script>\n<script src="assets/js/protocols.js?v={V}"></script>')
    return out


# ---------------------------------------------------------------- cloud landing
def build_cloud_landing(lessons, levels):
    C = load("content/cloud/_landing.yaml")
    rows, last = "", None
    for L in lessons:
        if L.get("level") != last:
            last = L.get("level")
            lv = next(x for x in levels if x["n"] == last)
            rows += f'<h3 class="lvl-h">{E(lvl_name(levels, last))}</h3><p class="lvl-d">{inline(lv.get("d", ""))}</p>'
        if L.get("kind") == "practice":
            tg = '<span class="tag new">practice</span>'
        elif L.get("kind") == "design":
            tg = '<span class="tag atk">design</span>'
        else:
            tg = "".join(f'<span class="tag">{E(t)}</span>' for t in L.get("tags", [])[:3])
        rows += (f'<a class="lesson-row{" is-practice" if L.get("kind") == "practice" else ""}" href="cloud/{L["slug"]}.html" data-done="cloud.{L["slug"]}" data-lv="{L.get("level")}"><span class="mono">{L["num"]}</span>'
                 f'<span><b>{E(L["title"])}</b><small>{inline(L["lede"])}</small></span><span class="tags">{tg}</span></a>')
    n = len(lessons)
    tracker = (f'<div class="trk" id="cl-trk" data-total="{n}"><div class="trk-top"><b id="cl-trk-n">0</b><span class="mono muted">of {n} pages done</span>'
               f'<a class="btn btn-quiet btn-sm" id="cl-trk-next" href="cloud/{lessons[0]["slug"]}.html">Start the first lesson</a></div>'
               f'<div class="trk-bar" aria-hidden="true"><i id="cl-trk-bar"></i></div>'
               f'<div class="trk-lv">' + "".join(
                   f'<span data-lv="{lv["n"]}"><b class="mono">L{lv["n"]}</b>{E(lv["t"])}<em class="mono" data-lvc="{lv["n"]}">0/{sum(1 for L in lessons if L.get("level") == lv["n"])}</em></span>'
                   for lv in levels) + '</div></div>')
    labs = ""
    for g in C["labs"]:
        cards = "".join(f'<a class="lab" href="{E(x["u"])}" target="_blank" rel="noopener"><span class="tag {E(x.get("kind", ""))}">{E(x["type"])}</span>'
                        f'<b>{E(x["t"])}</b><small>{inline(x["n"])}</small></a>' for x in g["items"])
        labs += f'<h3>{E(g["t"])}</h3><p class="small muted">{inline(g["d"])}</p><div class="labs">{cards}</div>'
    res = "".join(f'<li><a href="{E(x["u"])}" target="_blank" rel="noopener">{E(x["t"])}</a>. {inline(x["n"])}</li>' for x in C["resources"])
    main = (f'<main id="main"><section class="page-head"><div class="wrap"><div class="eyebrow"><span class="tag cl"><span class="dot cl"></span>Cloud track</span>'
            f'<span>{n} pages · {len(levels)} levels</span></div><h1>{E(C["title"])}</h1><p class="lede">{inline(C["lede"])}</p>'
            f'<div class="actions"><a class="btn btn-primary" href="cloud/{lessons[0]["slug"]}.html">Start lesson 1.1</a>'
            f'<a class="btn btn-quiet" href="#route">See all levels</a><a class="btn btn-quiet" href="#labs">Hands on labs</a></div></div></section>'
            f'<div class="wrap narrow doc">'
            + section("tracker", "Your progress", f'<p class="small muted">{inline(C["tracker_note"])}</p>' + tracker)
            + section("why", C["why_t"], md(C["why"]) + "".join(diagram(d) for d in C.get("diagrams", [])))
            + section("how", "How this track works", md(C["how"]))
            + section("route", "All levels and pages", f'<div class="lesson-list">{rows}</div>')
            + section("labs", "Free hands on labs, building, defending and attacking", md(C["labs_intro"]) + labs)
            + section("resources", "SAA-C03 study resources", md(C["resources_intro"]) + f'<ol class="reflist">{res}</ol>')
            + "</div></main>")
    write("cloud-track.html", "AWS and cloud track. From zero to architect", C["lede"][:155], "cloud", main)


# ---------------------------------------------------------------- home
def build_home(tracks, design, nb, niv, protos):
    H = load("content/home.yaml")
    learn = tracks["learn"][0]
    route = [{"s": L["slug"], "n": L["num"], "t": L["short"], "l": L.get("level"), "p": L.get("kind") == "practice"} for L in learn]
    nq = 0
    for ls in [t[0] for t in tracks.values()] + [design]:
        for L in ls:
            nq += len(L.get("quiz", [])) + sum(len(r["items"]) for r in (L.get("desk") or {}).get("rounds", []))
            nq += len((L.get("estimate") or {}).get("items", [])) + sum(len(r["items"]) for r in L.get("rounds", []) if L.get("kind") == "practice")
    nq += sum(len(p["quiz"]) for p in protos)
    nl = sum(1 for L in learn if L.get("kind") != "practice")
    ni = sum(1 for L in tracks["infra"][0] if L.get("kind") != "practice")
    stats = [(nl, "concept lessons in eight levels, each with an animated diagram"), (ni, "infra lessons, from Git to Kubernetes, AWS and Terraform"),
             (len(protos), "network protocols, animated packet by packet"), (len(design) - 1, "full design tasks, from a link shortener to payments and a secure AI agent platform"),
             (nq, "quiz, fill-up, code and scenario questions with reasons"), (niv, "interview questions with model answers and feedback")]
    cards = "".join(f'<a class="card" href="{c["href"]}"><span class="num">{inline(c["num"])}</span><h3>{E(c["t"])}</h3><p>{inline(c["d"])}</p><span class="go">{E(c["go"])}</span></a>' for c in H["cards"])
    loop = "".join(f'<div><span class="mono">{E(x[0])}</span><h3>{E(x[1])}</h3><p>{inline(x[2])}</p></div>' for x in H["loop"])
    main = f"""<main id="main">
  <section class="hero"><div class="wrap"><div>
    <div class="eyebrow rise"><span class="tag def"><span class="dot def"></span>Concepts</span><span class="tag pen"><span class="dot pen"></span>Infra</span><span class="tag atk"><span class="dot atk"></span>Design it</span></div>
    <h1 class="rise d1">{E(H["title"])}</h1>
    <p class="lede rise d2">{inline(H["lede"])}</p>
    <div class="actions rise d3"><a class="btn btn-primary" href="basics.html">Start here</a><a class="btn btn-quiet" href="plan.html">Open the plan</a><a class="btn btn-quiet" href="protocols.html">See protocols move</a></div>
    <p class="small muted rise d3" id="home-progress" style="margin-top:20px"></p>
  </div>
  <div class="hero-visual rise d2"><div class="sheet"><div class="sheet-cap"><span>Your route, basic to mastery</span><span>stations fill in as you finish lessons</span></div>
    <svg id="route" class="dg" viewBox="0 0 640 446" role="img" aria-label="Route map of the eight levels of concept lessons, from foundations to mastery, then the design tasks."></svg></div></div>
  </div></section>
  <section class="section"><div class="wrap"><div class="stats stats-6">{"".join(f'<div class="stat"><b>{n}</b><span>{E(t)}</span></div>' for n, t in stats)}</div></div></section>
  <section class="section"><div class="wrap"><h2 class="section-title">How every lesson works</h2><p class="section-sub">{inline(H["loop_sub"])}</p><div class="loop">{loop}</div></div></section>
  <section class="section"><div class="wrap"><h2 class="section-title">Ways in</h2><p class="section-sub">Pick the one that fits you today. They all link to each other.</p><div class="grid grid-3">{cards}</div></div></section>
  <section class="section"><div class="wrap narrow"><h2 class="section-title">{E(H["end_t"])}</h2><div class="prose">{md(H["end"])}</div></div></section>
</main>
<script>window.ROUTE={json.dumps(route)};window.DESIGNS={len(design) - 1};</script>"""
    write("index.html", "Boxes and Arrows. System design from zero to mastery", H["lede"][:155], "", main)


if __name__ == "__main__":
    tracks = {"learn": build_track("learn"), "infra": build_track("infra"), "cloud": build_track("cloud")}
    build_cloud_landing(*tracks["cloud"])
    design, _ = build_track("design")
    nb = build_basics()
    protos = build_protocols()
    niv = build_interview(tracks, design)
    pages = {"basics.html": "Start here", "interview.html": "Interview questions", "protocols.html": "Protocols", "cloud-track.html": "Cloud track",
             "learn/index.html": "Concepts", "infra/index.html": "Infra", "design/index.html": "All designs"}
    for t, (ls, _) in list(tracks.items()) + [("design", (design, None))]:
        for L in ls:
            pages[f"{t}/{L['slug']}.html"] = f'{L["num"]}. {L["title"]}' if t != "design" else L["title"]
    for p in protos:
        pages[f"protocols.html#/{p['id']}"] = p["name"]
    build_plan(pages)
    build_library()
    build_home(tracks, design, nb, niv, protos)
    print(f"built {nb} basics steps, " + ", ".join(f"{len(v[0])} {k} pages" for k, v in tracks.items())
          + f", {len(design)} designs, {len(protos)} protocols, {niv} interview questions")
