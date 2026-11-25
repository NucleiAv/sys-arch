/* Stepped, animated scenes. A scene is a small board of raised blocks on a
   grid, with packets that move along the links. Each step changes which
   blocks are lit, which links carry traffic, the caption and the stat cards.
   Built from JSON that tools/build.py writes into the page. */
(function () {
  "use strict";
  const NS = "http://www.w3.org/2000/svg";
  const RM = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  const el = (n, a = {}, p) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); if (p) p.appendChild(e); return e; };
  const h = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };

  /* isometric grid */
  const DX = 74, DY = 42, TW = 46, TH = 26, SIDE = 20;
  const iso = (gx, gy) => [(gx - gy) * DX, (gx + gy) * DY];

  function block(g, cls) {
    const b = el("g", { class: "blk " + cls }, g);
    el("polygon", { class: "f-l", points: `${-TW},0 0,${TH} 0,${TH + SIDE} ${-TW},${SIDE}` }, b);
    el("polygon", { class: "f-r", points: `${TW},0 0,${TH} 0,${TH + SIDE} ${TW},${SIDE}` }, b);
    el("polygon", { class: "f-t", points: `0,${-TH} ${TW},0 0,${TH} ${-TW},0` }, b);
    return b;
  }

  function build(root) {
    const spec = JSON.parse(root.querySelector("script").textContent);
    const ids = Object.keys(spec.nodes);
    const P = {};
    ids.forEach(id => { const n = spec.nodes[id]; P[id] = iso(n.x, n.y); });
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    ids.forEach(id => { const [x, y] = P[id]; minX = Math.min(minX, x); maxX = Math.max(maxX, x); minY = Math.min(minY, y); maxY = Math.max(maxY, y); });
    const pad = { l: 120, r: 120, t: 78, b: 80 };
    const vb = [minX - pad.l, minY - pad.t, (maxX - minX) + pad.l + pad.r, (maxY - minY) + pad.t + pad.b];

    root.innerHTML = "";
    const head = h("div", "sc-head");
    head.appendChild(h("div", "sc-title mono", spec.title || "Scene"));
    const stats = h("div", "sc-stats");
    (spec.stats || []).forEach((s, i) => {
      const c = h("div", "sc-stat");
      c.appendChild(h("span", "lbl", s));
      c.appendChild(h("b", "val", "&nbsp;"));
      stats.appendChild(c);
    });
    head.appendChild(stats);
    root.appendChild(head);

    const stage = h("div", "sc-stage");
    const svg = el("svg", { viewBox: vb.join(" "), role: "img", "aria-label": spec.title || "Animated diagram" });
    stage.appendChild(svg);
    root.appendChild(stage);
    root.appendChild(h("div", "scroll-hint", "Swipe sideways to see the whole diagram"));

    /* floor grid */
    const floor = el("g", { class: "floor" }, svg);
    const gx0 = Math.min(...ids.map(i => spec.nodes[i].x)) - 1, gx1 = Math.max(...ids.map(i => spec.nodes[i].x)) + 1;
    const gy0 = Math.min(...ids.map(i => spec.nodes[i].y)) - 1, gy1 = Math.max(...ids.map(i => spec.nodes[i].y)) + 1;
    for (let x = gx0; x <= gx1; x++) { const a = iso(x - 0.5, gy0 - 0.5), b = iso(x - 0.5, gy1 + 0.5); el("line", { x1: a[0], y1: a[1] + TH, x2: b[0], y2: b[1] + TH }, floor); }
    for (let y = gy0; y <= gy1; y++) { const a = iso(gx0 - 0.5, y - 0.5), b = iso(gx1 + 0.5, y - 0.5); el("line", { x1: a[0], y1: a[1] + TH, x2: b[0], y2: b[1] + TH }, floor); }

    /* links: every pair used by any step */
    const pairs = new Map();
    (spec.links || []).forEach(l => pairs.set(l[0] + ">" + l[1], l));
    spec.steps.forEach(s => (s.flow || []).forEach(f => { const k = f[0] + ">" + f[1], r = f[1] + ">" + f[0]; if (!pairs.has(k) && !pairs.has(r)) pairs.set(k, [f[0], f[1]]); }));
    const linkG = el("g", { class: "links" }, svg);
    const paths = {};
    pairs.forEach((l, k) => {
      const a = spec.nodes[l[0]], b = spec.nodes[l[1]];
      const [ax, ay] = P[l[0]], [bx, by] = P[l[1]];
      let d;
      if (a.x === b.x || a.y === b.y) d = `M${ax} ${ay} L${bx} ${by}`;
      else { const [cx, cy] = iso(b.x, a.y); d = `M${ax} ${ay} L${cx} ${cy} L${bx} ${by}`; }
      const p = el("path", { d, class: "lk" }, linkG);
      paths[k] = p;
      if (l[2]) {
        const mid = p.getPointAtLength(p.getTotalLength() / 2);
        const t = el("text", { x: mid.x, y: mid.y - 8, class: "lk-lbl", "text-anchor": "middle" }, linkG);
        t.textContent = l[2];
      }
    });
    const getPath = (a, b) => paths[a + ">" + b] ? { p: paths[a + ">" + b], rev: false } : paths[b + ">" + a] ? { p: paths[b + ">" + a], rev: true } : null;

    /* blocks, drawn back to front */
    const nodeG = el("g", { class: "nodes" }, svg);
    const order = ids.slice().sort((i, j) => (spec.nodes[i].x + spec.nodes[i].y) - (spec.nodes[j].x + spec.nodes[j].y));
    const N = {};
    order.forEach(id => {
      const n = spec.nodes[id], [x, y] = P[id];
      const g = el("g", { class: "nd k-" + (n.kind || "box"), transform: `translate(${x} ${y - 10})` }, nodeG);
      const lift = el("g", { class: "lift" }, g);
      block(lift, "");
      const lbl = el("g", { class: "chip" }, lift);
      const t = el("text", { x: 0, y: -TH - 14, "text-anchor": "middle", class: "nd-lbl" }, lbl);
      t.textContent = n.label;
      if (n.tag) {
        const tg = el("text", { x: 0, y: TH + SIDE + 22, "text-anchor": "middle", class: "nd-tag" }, lift);
        tg.textContent = n.tag;
      }
      const badge = el("g", { class: "badge", transform: `translate(${TW - 6} ${-TH + 2})` }, lift);
      el("circle", { r: 11 }, badge);
      el("path", { d: "", class: "bx" }, badge);
      N[id] = { g, badge };
    });
    /* size the chip background after text exists */
    requestAnimationFrame(() => order.forEach(id => {
      const t = N[id].g.querySelector(".nd-lbl");
      try { const bb = t.getBBox(); const r = el("rect", { x: bb.x - 8, y: bb.y - 4, width: bb.width + 16, height: bb.height + 8, rx: 7, class: "chip-bg" }); t.parentNode.insertBefore(r, t); } catch (e) {}
    }));
    const pk = el("g", { class: "packets" }, svg);

    /* caption and stepper */
    const cap = h("div", "sc-cap");
    cap.innerHTML = '<div class="sc-n mono"></div><h4></h4><p></p>';
    root.appendChild(cap);
    const bar = h("div", "sc-bar");
    const back = h("button", "btn btn-quiet btn-sm sc-back", "Back");
    const dots = h("div", "sc-dots");
    spec.steps.forEach((s, i) => { const d = h("button", "sc-dot", String(i + 1)); d.type = "button"; d.title = s.title; d.setAttribute("aria-label", "Step " + (i + 1) + ". " + s.title); dots.appendChild(d); });
    const play = h("button", "btn btn-quiet btn-sm sc-play", "Play");
    const next = h("button", "btn btn-primary btn-sm sc-next", "Next");
    [back, play, next].forEach(b => b.type = "button");
    bar.appendChild(back); bar.appendChild(dots); bar.appendChild(play); bar.appendChild(next);
    root.appendChild(bar);
    if (spec.legend) root.appendChild(h("div", "sc-legend small muted", spec.legend));

    let cur = -1, timer = null, raf = null, flows = [];
    const ICON = { bad: "M-4 -4 L4 4 M4 -4 L-4 4", ok: "M-4.5 0.5 L-1.5 3.5 L4.5 -3.5", warn: "M0 -5 V1 M0 4 V4.5" };

    function go(i) {
      i = Math.max(0, Math.min(spec.steps.length - 1, i));
      cur = i;
      const s = spec.steps[i];
      const show = s.show ? new Set(s.show) : null, on = new Set(s.on || []), marks = s.mark || {};
      ids.forEach(id => {
        const n = N[id];
        n.g.classList.toggle("ghost", !!show && !show.has(id));
        n.g.classList.toggle("on", on.has(id));
        const m = marks[id];
        n.badge.setAttribute("class", "badge" + (m ? " show m-" + m : ""));
        n.badge.querySelector(".bx").setAttribute("d", m ? ICON[m] || "" : "");
      });
      svg.classList.toggle("focus", on.size > 0);
      Object.values(paths).forEach(p => p.classList.remove("live", "atk", "def", "pen", "bad"));
      flows = (s.flow || []).map((f, k) => {
        const gp = getPath(f[0], f[1]);
        if (!gp) return null;
        gp.p.classList.add("live", f[2] || "ink");
        return { ...gp, kind: f[2] || "ink", delay: k * 520, label: f[3] };
      }).filter(Boolean);
      pk.innerHTML = "";
      flows.forEach(f => { f.dot = el("circle", { r: 6.5, class: "pkt " + f.kind }, pk); f.len = f.p.getTotalLength(); });
      $$(".sc-stat .val", root).forEach((v, k) => {
        const nv = (s.stats || [])[k];
        if (nv != null && v.textContent !== String(nv)) { v.classList.remove("flip"); void v.offsetWidth; v.textContent = nv; v.classList.add("flip"); }
      });
      cap.querySelector(".sc-n").textContent = `Step ${i + 1} of ${spec.steps.length}`;
      cap.querySelector("h4").textContent = s.title;
      cap.querySelector("p").innerHTML = s.text || "";
      $$(".sc-dot", dots).forEach((d, k) => { d.classList.toggle("on", k === i); d.classList.toggle("past", k < i); d.setAttribute("aria-current", k === i ? "step" : "false"); });
      back.disabled = i === 0;
      next.textContent = i === spec.steps.length - 1 ? "Start over" : "Next";
      start();
    }
    function start() {
      cancelAnimationFrame(raf);
      const t0 = performance.now(), DUR = 1300, GAP = 700;
      const cycle = flows.length ? (flows.length - 1) * 520 + DUR + GAP : 0;
      const frame = now => {
        const t = now - t0;
        flows.forEach(f => {
          let u = RM ? 1 : ((t % cycle) - f.delay) / DUR;
          if (u < 0 || u > 1) { f.dot.style.opacity = RM ? 1 : 0; if (!RM) return; u = 1; }
          f.dot.style.opacity = u > 0.92 ? (1 - u) / 0.08 : 1;
          const e = 1 - Math.pow(1 - u, 2);
          const pt = f.p.getPointAtLength((f.rev ? 1 - e : e) * f.len);
          f.dot.setAttribute("cx", pt.x); f.dot.setAttribute("cy", pt.y);
        });
        if (!RM && flows.length && visible) raf = requestAnimationFrame(frame);
      };
      raf = requestAnimationFrame(frame);
    }
    function stopPlay() { clearInterval(timer); timer = null; play.textContent = "Play"; play.setAttribute("aria-pressed", "false"); }
    back.addEventListener("click", () => { stopPlay(); go(cur - 1); });
    next.addEventListener("click", () => { stopPlay(); go(cur === spec.steps.length - 1 ? 0 : cur + 1); });
    dots.addEventListener("click", e => { const d = e.target.closest(".sc-dot"); if (d) { stopPlay(); go([...dots.children].indexOf(d)); } });
    play.addEventListener("click", () => {
      if (timer) return stopPlay();
      play.textContent = "Pause"; play.setAttribute("aria-pressed", "true");
      go(cur === spec.steps.length - 1 ? 0 : cur + 1);
      timer = setInterval(() => { if (cur >= spec.steps.length - 1) return stopPlay(); go(cur + 1); }, 4200);
    });
    root.tabIndex = 0;
    root.addEventListener("keydown", e => {
      if (e.key === "ArrowRight") { e.preventDefault(); e.stopPropagation(); stopPlay(); go(cur + 1); }
      if (e.key === "ArrowLeft") { e.preventDefault(); e.stopPropagation(); stopPlay(); go(cur - 1); }
    });
    let visible = true;
    if ("IntersectionObserver" in window) new IntersectionObserver(es => es.forEach(en => { visible = en.isIntersecting; if (visible) start(); else stopPlay(); })).observe(root);
    go(0);
  }
  function $$(s, r) { return Array.from(r.querySelectorAll(s)); }
  document.addEventListener("DOMContentLoaded", () => document.querySelectorAll(".scene").forEach(s => { try { build(s); } catch (e) { console.error("scene", e); } }));
})();
