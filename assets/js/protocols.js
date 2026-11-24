/* Protocol explorer. Network view (isometric blocks with moving packets),
   sequence view (lifelines and arrows), step panel, packet inspector.
   Data comes from protocol-data.js, which tools/build.py writes. */
(function () {
  "use strict";
  const P = window.PROTOCOLS || [];
  const CATS = window.PCATS || {};
  const NS = "http://www.w3.org/2000/svg";
  const RM = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const svgEl = (n, a = {}, p) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); if (p) p.appendChild(e); return e; };
  const SEEN = "sysarch.px.seen";
  const seen = { all() { try { return JSON.parse(localStorage.getItem(SEEN)) || {}; } catch (e) { return {}; } },
    add(id) { const a = this.all(); a[id] = 1; try { localStorage.setItem(SEEN, JSON.stringify(a)); } catch (e) {} } };

  const KIND = { req: "Request", res: "Response", ctl: "Control", sec: "Security or keys", data: "Data", bad: "Failure or attack" };
  const GROUP = { laptop: "dev", phone: "dev", user: "dev", camera: "dev", tv: "dev", router: "net", switch: "net", ap: "net", cloud: "net", globe: "net",
    server: "srv", web: "srv", mail: "srv", folder: "srv", terminal: "srv", dns: "srv", clock: "srv", proxy: "sec", db: "data", queue: "data",
    lock: "sec", key: "sec", shield: "sec", plc: "ot", gateway: "net" };
  /* small upright glyphs, drawn in a 24 by 24 box */
  const ICON = {
    laptop: "M5 6h14v9H5z M3 17h18l-1.5 2h-15z",
    phone: "M8 3h8a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H8a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z M11 18h2",
    user: "M12 12a4 4 0 1 0 0-8a4 4 0 0 0 0 8z M5 20c1-4 4-6 7-6s6 2 7 6",
    camera: "M4 8h11v8H4z M15 11l5-3v8l-5-3",
    tv: "M3 5h18v12H3z M9 21h6 M12 17v4",
    router: "M4 13h16v5H4z M8 13l-2-6 M16 13l2-6 M8 15.5h.01 M11 15.5h.01",
    switch: "M3 9h18v6H3z M6 12h.01 M9 12h.01 M12 12h.01 M15 12h.01 M18 12h.01",
    ap: "M12 18h.01 M8.5 14.5a5 5 0 0 1 7 0 M5.5 11.5a9 9 0 0 1 13 0 M2.5 8.5a13 13 0 0 1 19 0",
    cloud: "M7 18a4 4 0 0 1 0-8a5 5 0 0 1 9.5-1.5A4 4 0 0 1 17 18z",
    globe: "M12 3a9 9 0 1 0 0 18a9 9 0 0 0 0-18z M3 12h18 M12 3c3 3 3 15 0 18 M12 3c-3 3-3 15 0 18",
    gateway: "M4 5h16v14H4z M4 12h16 M12 5v14",
    server: "M5 4h14v5H5z M5 10h14v5H5z M5 16h14v4H5z M8 6.5h.01 M8 12.5h.01",
    web: "M4 5h16v14H4z M4 9h16 M7 7h.01 M9 7h.01",
    mail: "M3 6h18v12H3z M3 6l9 7 9-7",
    folder: "M3 6h7l2 2h9v11H3z",
    terminal: "M3 5h18v14H3z M7 10l3 2-3 2 M12 15h5",
    dns: "M4 4h16v16H4z M8 9h8 M8 12h8 M8 15h5",
    clock: "M12 3a9 9 0 1 0 0 18a9 9 0 0 0 0-18z M12 7v5l3 2",
    proxy: "M4 12h6 M14 12h6 M10 8h4v8h-4z M17 9l3 3-3 3",
    db: "M5 6c0-1.7 3-3 7-3s7 1.3 7 3v12c0 1.7-3 3-7 3s-7-1.3-7-3z M5 6c0 1.7 3 3 7 3s7-1.3 7-3 M5 12c0 1.7 3 3 7 3s7-1.3 7-3",
    queue: "M4 6h16v3H4z M4 11h16v3H4z M4 16h16v3H4z",
    lock: "M6 11h12v9H6z M8 11V8a4 4 0 0 1 8 0v3",
    key: "M8 15a4 4 0 1 1 0-8a4 4 0 0 1 0 8z M11 12h10 M18 12v3 M21 12v2",
    shield: "M12 3l8 3v6c0 5-4 8-8 9c-4-1-8-4-8-9V6z",
    plc: "M5 5h14v14H5z M9 9h6v6H9z M5 9H3 M5 15H3 M19 9h2 M19 15h2"
  };

  /* isometric layout */
  const DX = 84, DY = 48, TW = 50, TH = 29, SIDE = 22;
  const iso = (x, y) => [(x - y) * DX, (x + y) * DY];

  let cur = null, step = 0, view = "net", playing = false, speed = 1, raf = 0, timer = 0, inspected = 0, insView = "fields";
  let netState = null;

  /* ---------- list ---------- */
  let cat = "", q = "";
  function renderList() {
    const rows = $("#px-rows"); if (!rows) return;
    const s = seen.all(), qq = q.trim().toLowerCase();
    const list = P.filter(p => (!cat || p.cat === cat) && (!qq || (p.name + " " + p.full + " " + p.id).toLowerCase().includes(qq)));
    $("#px-count").textContent = list.length;
    rows.innerHTML = list.map(p => `<a class="px-row${cur && cur.id === p.id ? " on" : ""}" href="#/${p.id}" data-id="${p.id}">
      <span class="px-layer mono">L${p.layer}</span><span class="px-nm"><b>${esc(p.name)}</b><small>${esc(p.full)}</small></span>
      <span class="px-mark">${cur && cur.id === p.id ? '<svg viewBox="0 0 24 24" aria-label="Open"><path d="M5 12.5l4.5 4.5L19 7"/></svg>' : s[p.id] ? '<span class="px-seen mono">seen</span>' : ""}</span></a>`).join("")
      || '<p class="small muted" style="padding:12px">No protocol matches. Clear the search.</p>';
  }

  /* ---------- header and facts ---------- */
  function renderHead() {
    const p = cur;
    document.title = `${p.name}. Protocols, animated`;
    $("#px-eyebrow").textContent = `${p.name} / OSI L${p.layer} / ${CATS[p.cat] || ""}`;
    $("#px-title").textContent = p.title;
    $("#px-lede").innerHTML = p.lede;
    $("#px-crumbs").innerHTML = `<a href="index.html">Home</a><span>/</span><a href="#/">Protocols</a><span>/</span><span>${esc(CATS[p.cat] || "")}</span><span>/</span><span>${esc(p.name)}</span>`;
    const facts = [["Layer", `L${p.layer}`], ["Transport", p.transport], ["Port", p.port], ["Steps", p.steps.length]].filter(f => f[1]);
    $("#px-facts").innerHTML = facts.map(([k, v]) => `<span class="px-fact"><span class="mono">${k}</span>${esc(v)}</span>`).join("");
  }

  /* ---------- network view ---------- */
  function pathBetween(a, b) {
    /* breadth first search over links, so a packet travels through routers and the internet */
    const adj = {};
    Object.keys(cur.nodes).forEach(k => (adj[k] = []));
    cur.links.forEach(([x, y]) => { if (adj[x] && adj[y]) { adj[x].push(y); adj[y].push(x); } });
    const prev = { [a]: null }, qu = [a];
    while (qu.length) { const n = qu.shift(); if (n === b) break; adj[n].forEach(m => { if (!(m in prev)) { prev[m] = n; qu.push(m); } }); }
    if (!(b in prev)) return [a, b];
    const out = []; for (let n = b; n !== null; n = prev[n]) out.unshift(n);
    return out;
  }
  function buildNet() {
    const st = $("#px-stage"); st.innerHTML = "";
    const N = cur.nodes, ids = Object.keys(N);
    const pos = {}; ids.forEach(k => (pos[k] = iso(N[k].x, N[k].y)));
    let minX = 1e9, maxX = -1e9, minY = 1e9, maxY = -1e9;
    ids.forEach(k => { const [x, y] = pos[k]; minX = Math.min(minX, x); maxX = Math.max(maxX, x); minY = Math.min(minY, y); maxY = Math.max(maxY, y); });
    const pad = { l: 130, r: 130, t: 96, b: 92 };
    const svg = svgEl("svg", { viewBox: `${minX - pad.l} ${minY - pad.t} ${maxX - minX + pad.l + pad.r} ${maxY - minY + pad.t + pad.b}`, class: "px-net", role: "img", "aria-label": cur.title });
    st.appendChild(svg);
    /* floor */
    const fl = svgEl("g", { class: "px-floor" }, svg);
    const xs = ids.map(k => N[k].x), ys = ids.map(k => N[k].y);
    const gx0 = Math.min(...xs) - 1, gx1 = Math.max(...xs) + 1, gy0 = Math.min(...ys) - 1, gy1 = Math.max(...ys) + 1;
    for (let x = gx0; x <= gx1; x++) { const a = iso(x - .5, gy0 - .5), b = iso(x - .5, gy1 + .5); svgEl("line", { x1: a[0], y1: a[1] + TH, x2: b[0], y2: b[1] + TH }, fl); }
    for (let y = gy0; y <= gy1; y++) { const a = iso(gx0 - .5, y - .5), b = iso(gx1 + .5, y - .5); svgEl("line", { x1: a[0], y1: a[1] + TH, x2: b[0], y2: b[1] + TH }, fl); }
    /* links */
    const lg = svgEl("g", { class: "px-links" }, svg);
    const links = {};
    cur.links.forEach(([a, b]) => {
      if (!N[a] || !N[b]) return;
      const [ax, ay] = pos[a], [bx, by] = pos[b];
      const d = `M${ax} ${ay} L${bx} ${by}`;
      links[a + ">" + b] = svgEl("path", { d, class: "px-lk" }, lg);
    });
    /* nodes, back to front */
    const ng = svgEl("g", {}, svg);
    const order = ids.slice().sort((i, j) => (N[i].x + N[i].y) - (N[j].x + N[j].y));
    const G = {};
    order.forEach(k => {
      const n = N[k], [x, y] = pos[k];
      const g = svgEl("g", { class: `px-nd g-${GROUP[n.icon] || "srv"}`, transform: `translate(${x} ${y - 12})`, "data-id": k }, ng);
      const lift = svgEl("g", { class: "px-lift" }, g);
      svgEl("polygon", { class: "f-l", points: `${-TW},0 0,${TH} 0,${TH + SIDE} ${-TW},${SIDE}` }, lift);
      svgEl("polygon", { class: "f-r", points: `${TW},0 0,${TH} 0,${TH + SIDE} ${TW},${SIDE}` }, lift);
      svgEl("polygon", { class: "f-t", points: `0,${-TH} ${TW},0 0,${TH} ${-TW},0` }, lift);
      const ic = svgEl("g", { class: "px-ic", transform: "translate(-12 -14)" }, lift);
      svgEl("path", { d: ICON[n.icon] || ICON.server }, ic);
      const lb = svgEl("g", { class: "px-chip" }, lift);
      const t = svgEl("text", { x: 0, y: -TH - 18, "text-anchor": "middle", class: "px-lbl" }, lb); t.textContent = n.label;
      if (n.sub) { const s = svgEl("text", { x: 0, y: TH + SIDE + 22, "text-anchor": "middle", class: "px-sub" }, lift); s.textContent = n.sub; }
      const bd = svgEl("g", { class: "px-badge", transform: `translate(${TW - 4} ${-TH})` }, lift);
      svgEl("circle", { r: 10 }, bd); svgEl("path", { d: "" }, bd);
      G[k] = g;
    });
    requestAnimationFrame(() => order.forEach(k => {
      const t = G[k].querySelector(".px-lbl");
      try { const bb = t.getBBox(); const r = svgEl("rect", { x: bb.x - 9, y: bb.y - 5, width: bb.width + 18, height: bb.height + 10, rx: 9, class: "px-chip-bg" }); t.parentNode.insertBefore(r, t); } catch (e) {}
    }));
    const pk = svgEl("g", { class: "px-pkts" }, svg);
    netState = { svg, pos, links, G, pk };
  }
  function linkPath(a, b) {
    const L = netState.links;
    if (L[a + ">" + b]) return { p: L[a + ">" + b], rev: false };
    if (L[b + ">" + a]) return { p: L[b + ">" + a], rev: true };
    return null;
  }
  function paintNet() {
    if (!netState) return;
    const s = cur.steps[step], on = new Set(s.on && s.on.length ? s.on : s.p.flatMap(x => [x.f, x.t]));
    Object.entries(netState.G).forEach(([k, g]) => {
      g.classList.toggle("on", on.has(k));
      g.classList.toggle("dim", on.size > 0 && !on.has(k));
      const bad = (s.bad || []).includes(k);
      const bd = g.querySelector(".px-badge");
      bd.setAttribute("class", "px-badge" + (bad ? " show" : ""));
      bd.querySelector("path").setAttribute("d", bad ? "M-4 -4 L4 4 M4 -4 L-4 4" : "");
    });
    Object.values(netState.links).forEach(p => p.setAttribute("class", "px-lk"));
    cancelAnimationFrame(raf);
    netState.pk.innerHTML = "";
    /* each packet walks its path. Packets start one after another. */
    const trips = s.p.map((x, i) => {
      const hops = pathBetween(x.f, x.t), segs = [];
      for (let h = 0; h < hops.length - 1; h++) { const lp = linkPath(hops[h], hops[h + 1]); if (lp) { segs.push(lp); lp.p.setAttribute("class", "px-lk live k-" + x.k); } }
      const g = svgEl("g", { class: "px-pkt k-" + x.k, "data-i": i }, netState.pk);
      svgEl("circle", { r: 8 }, g);
      const tag = svgEl("g", { class: "px-tag" }, g);
      const tx = svgEl("text", { x: 14, y: -10 }, tag); tx.textContent = x.m.length > 28 ? x.m.slice(0, 27) + "\u2026" : x.m;
      g.addEventListener("click", () => { inspected = i; renderInspector(); });
      return { segs, g, len: segs.reduce((a, sg) => a + sg.p.getTotalLength(), 0) || 1 };
    });
    requestAnimationFrame(() => trips.forEach(tp => {
      const tx = tp.g.querySelector("text");
      try { const bb = tx.getBBox(); const r = svgEl("rect", { x: bb.x - 6, y: bb.y - 3, width: bb.width + 12, height: bb.height + 6, rx: 6 }); tx.parentNode.insertBefore(r, tx); } catch (e) {}
    }));
    const DUR = 1500 / speed, GAP = 650 / speed, t0 = performance.now();
    const total = trips.length ? (trips.length - 1) * GAP + DUR : 0;
    const place = (tp, u) => {
      let d = u * tp.len;
      for (const sg of tp.segs) {
        const L = sg.p.getTotalLength();
        if (d <= L || sg === tp.segs[tp.segs.length - 1]) { const pt = sg.p.getPointAtLength(sg.rev ? L - Math.min(d, L) : Math.min(d, L)); tp.g.setAttribute("transform", `translate(${pt.x} ${pt.y})`); return; }
        d -= L;
      }
    };
    const frame = now => {
      const t = now - t0;
      trips.forEach((tp, i) => {
        if (!tp.segs.length) { tp.g.style.opacity = 0; return; }
        let u = RM ? 1 : (t - i * GAP) / DUR;
        if (u < 0) { tp.g.style.opacity = 0; return; }
        u = Math.min(1, u);
        tp.g.style.opacity = 1;
        place(tp, 1 - Math.pow(1 - u, 2));
      });
      if (!RM && t < total) raf = requestAnimationFrame(frame);
      else onStepDone();
    };
    raf = requestAnimationFrame(frame);
  }

  /* ---------- sequence view ---------- */
  function renderSeq() {
    const st = $("#px-stage"); st.innerHTML = "";
    const ids = Object.keys(cur.nodes).sort((a, b) => (cur.nodes[a].x - cur.nodes[b].x) || (cur.nodes[a].y - cur.nodes[b].y));
    const used = new Set(cur.steps.flatMap(s => s.p.flatMap(x => [x.f, x.t])));
    const cols = ids.filter(k => used.has(k));
    const colW = 170, left = 24, rowH = 36;
    const rows = [];
    cur.steps.forEach((s, si) => { rows.push({ head: si }); s.p.forEach((x, pi) => rows.push({ si, pi, x })); });
    const W = left * 2 + cols.length * colW, H = rows.length * rowH + 24;
    const cx = k => left + cols.indexOf(k) * colW + colW / 2;
    /* sticky column heads */
    const hw = document.createElement("div"); hw.className = "sq-headwrap"; st.appendChild(hw);
    const hs = svgEl("svg", { viewBox: `0 0 ${W} 52`, width: W, height: 52, class: "px-seq" }, hw);
    cols.forEach(k => {
      const x = cx(k);
      svgEl("rect", { x: x - 72, y: 9, width: 144, height: 34, rx: 9, class: "sq-head g-" + (GROUP[cur.nodes[k].icon] || "srv") }, hs);
      const t = svgEl("text", { x, y: 31, "text-anchor": "middle", class: "sq-hl" }, hs); t.textContent = cur.nodes[k].label;
    });
    const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, width: W, height: H, class: "px-seq", role: "img", "aria-label": "Sequence diagram of " + cur.name });
    st.appendChild(svg);
    svgEl("defs", {}, svg).innerHTML = Object.keys(KIND).map(k => `<marker id="sq-${k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" class="mk k-${k}"/></marker>`).join("");
    cols.forEach(k => svgEl("line", { x1: cx(k), y1: 0, x2: cx(k), y2: H, class: "sq-life" }, svg));
    let y = 0, drawn = [], curY = 0;
    rows.forEach(r => {
      y += rowH;
      if (r.head !== undefined) {
        const s = cur.steps[r.head];
        const g = svgEl("g", { class: "sq-step" + (r.head === step ? " cur" : r.head > step ? " future" : "") }, svg);
        svgEl("rect", { x: 4, y: y - 24, width: W - 8, height: 26, rx: 6, class: "sq-band" }, g);
        const t = svgEl("text", { x: 12, y: y - 6, class: "sq-st" }, g); t.textContent = `${String(r.head + 1).padStart(2, "0")}  ${s.t}`;
        g.addEventListener("click", () => go(r.head));
        if (r.head === step) curY = y - 30;
        return;
      }
      const a = cx(r.x.f), b = cx(r.x.t), self = a === b;
      const g = svgEl("g", { class: `sq-msg k-${r.x.k}` + (r.si === step ? " cur" : r.si > step ? " future" : " past") }, svg);
      const d = self ? `M${a} ${y - 16} h40 v14 h-38` : `M${a} ${y - 6} L${b + (b > a ? -3 : 3)} ${y - 6}`;
      const p = svgEl("path", { d, class: "sq-ln" }, g);
      if (r.si !== step) p.setAttribute("marker-end", `url(#sq-${r.x.k})`);
      const t = svgEl("text", { x: self ? a + 46 : (a + b) / 2, y: y - 12, "text-anchor": self ? "start" : "middle", class: "sq-m" }, g); t.textContent = r.x.m;
      g.addEventListener("click", () => { if (r.si !== step) go(r.si); inspected = r.pi; renderInspector(); });
      if (r.si === step) drawn.push({ p, k: r.x.k });
    });
    st.scrollTop = Math.max(0, curY);
    /* draw the current step's arrows in order, then add the arrow heads */
    cancelAnimationFrame(raf);
    const DUR = 700 / speed, GAP = 450 / speed, t0 = performance.now();
    drawn.forEach(o => { const L = o.p.getTotalLength(); o.L = L; o.p.style.strokeDasharray = L; o.p.style.strokeDashoffset = RM ? 0 : L; });
    const total = drawn.length ? (drawn.length - 1) * GAP + DUR : 0;
    const frame = now => {
      const t = now - t0;
      drawn.forEach((o, i) => {
        const u = RM ? 1 : Math.max(0, Math.min(1, (t - i * GAP) / DUR));
        o.p.style.strokeDashoffset = o.L * (1 - u);
        if (u >= 1 && !o.done) { o.done = 1; o.p.setAttribute("marker-end", `url(#sq-${o.k})`); }
      });
      if (!RM && t < total) raf = requestAnimationFrame(frame); else { drawn.forEach(o => o.p.setAttribute("marker-end", `url(#sq-${o.k})`)); onStepDone(); }
    };
    raf = requestAnimationFrame(frame);
  }

  /* ---------- stats, rail, step panel ---------- */
  function renderStats() {
    const s = cur.steps[step];
    const sofar = cur.steps.slice(0, step + 1).reduce((a, x) => a + x.p.length, 0);
    const all = cur.steps.reduce((a, x) => a + x.p.length, 0);
    const kinds = [...new Set(s.p.map(x => x.k))].map(k => KIND[k].toLowerCase()).join(", ") || "none";
    $("#px-stats").innerHTML = [["Step", `${step + 1} / ${cur.steps.length}`], ["Packets this step", s.p.length], ["Packets so far", `${sofar} / ${all}`], ["Kinds", kinds]]
      .map(([k, v]) => `<div class="px-stat"><span class="mono">${k}</span><b>${esc(v)}</b></div>`).join("");
    $("#px-stepno").textContent = `STEP ${String(step + 1).padStart(2, "0")} / ${String(cur.steps.length).padStart(2, "0")}`;
    $("#px-legend").innerHTML = [...new Set(cur.steps.flatMap(x => x.p.map(y => y.k)))].map(k => `<span><i class="lg k-${k}"></i>${KIND[k]}</span>`).join("");
    $("#px-prog").innerHTML = cur.steps.map((x, i) => `<button type="button" class="${i < step ? "past" : i === step ? "on" : ""}" aria-label="Step ${i + 1}. ${esc(x.t)}" title="${esc(x.t)}"></button>`).join("");
    $("#px-rail").innerHTML = cur.steps.map((x, i) => `<button type="button" class="${i < step ? "past" : i === step ? "on" : ""}" aria-label="Step ${i + 1}. ${esc(x.t)}"><span>${i + 1}</span>${i === step ? `<em>${esc(x.t)}</em>` : ""}</button>`).join("");
    $("#px-railno").textContent = `Step ${step + 1} of ${cur.steps.length}`;
  }
  function renderStepTab() {
    const s = cur.steps[step];
    $("#px-tab-step").innerHTML = `
      <div class="px-step-top"><span class="mono">STEP ${step + 1} / ${cur.steps.length}</span>${s.tag ? `<span class="px-tagchip">${esc(s.tag)}</span>` : ""}</div>
      <h2>${esc(s.t)}</h2><div class="prose">${s.d}</div>
      <div class="px-chips">${cur.steps.map((x, i) => `<button type="button" class="${i === step ? "on" : ""}" data-i="${i}"><span class="mono">${String(i + 1).padStart(2, "0")}</span>${esc(x.t)}</button>`).join("")}</div>
      ${s.f.length ? `<dl class="px-kv">${s.f.map(([k, v]) => `<div><dt>${esc(k)}</dt><dd class="mono">${esc(v)}</dd></div>`).join("")}</dl>` : ""}
      ${s.good ? `<div class="plain"><span class="k">Good to know</span><p>${s.good}</p></div>` : ""}`;
    $$("#px-tab-step .px-chips button").forEach(b => b.addEventListener("click", () => go(+b.dataset.i)));
  }
  function renderOverview() {
    $("#px-tab-over").innerHTML = `<div class="prose">${cur.overview}</div>${cur.refs.length ? `<h3>Go deeper</h3><ol class="reflist">${cur.refs.map(r => `<li>${r}</li>`).join("")}</ol>` : ""}`;
  }
  function renderPractice() {
    const box = $("#px-tab-prac");
    const id = "px-" + cur.id;
    box.innerHTML = `<p class="small muted">Answer after you watch all the steps. Every answer shows the reason.</p><div class="qset" data-id="${id}"></div><script type="application/json" data-for="${id}">${JSON.stringify(cur.quiz).replace(/</g, "\\u003c")}<\/script>`;
    if (window.AIC && window.AIC.renderSet) window.AIC.renderSet($(".qset", box));
  }
  function hex(str) {
    const bytes = new TextEncoder().encode(str);
    let out = "";
    for (let i = 0; i < bytes.length; i += 16) {
      const row = Array.from(bytes.slice(i, i + 16));
      out += i.toString(16).padStart(4, "0") + "  " + row.map(b => b.toString(16).padStart(2, "0")).join(" ").padEnd(48) + "  " + row.map(b => (b >= 32 && b < 127 ? String.fromCharCode(b) : ".")).join("") + "\n";
    }
    return out;
  }
  function renderInspector() {
    const s = cur.steps[step], list = $("#px-pk-list"), body = $("#px-pk-body");
    if (!s.p.length) { list.innerHTML = ""; body.innerHTML = '<p class="small muted">No packets in this step. It happens inside one machine.</p>'; return; }
    if (inspected >= s.p.length) inspected = 0;
    list.innerHTML = s.p.map((x, i) => `<button type="button" class="${i === inspected ? "on" : ""}" data-i="${i}"><i class="lg k-${x.k}"></i><span class="mono">${esc(cur.nodes[x.f].label)} &rarr; ${esc(cur.nodes[x.t].label)}</span><b>${esc(x.m)}</b></button>`).join("");
    $$("button", list).forEach(b => b.addEventListener("click", () => { inspected = +b.dataset.i; renderInspector(); }));
    const x = s.p[inspected];
    if (insView === "hex") {
      body.innerHTML = x.raw ? `<pre class="code px-hex"><code>${esc(hex(x.raw))}</code></pre><p class="small muted">Bytes of the text message, shown as hexadecimal and as characters.</p>`
        : '<p class="small muted">The hex view is shown for text based messages. This packet is binary, so read its fields instead.</p>';
    } else {
      const rows = [["From", cur.nodes[x.f].label + (cur.nodes[x.f].sub ? ` (${cur.nodes[x.f].sub})` : "")], ["To", cur.nodes[x.t].label + (cur.nodes[x.t].sub ? ` (${cur.nodes[x.t].sub})` : "")], ["Kind", KIND[x.k]], ...x.fields];
      body.innerHTML = `<dl class="px-kv">${rows.map(([k, v]) => `<div><dt>${esc(k)}</dt><dd class="mono">${esc(v)}</dd></div>`).join("")}</dl>${x.raw ? `<pre class="code"><code>${esc(x.raw)}</code></pre>` : ""}`;
    }
  }

  /* ---------- flow ---------- */
  function onStepDone() {
    if (!playing) return;
    clearTimeout(timer);
    timer = setTimeout(() => { if (!playing) return; if (step < cur.steps.length - 1) go(step + 1); else setPlay(false); }, 1600 / speed);
  }
  function setPlay(v) {
    playing = v;
    const b = $("#px-play"); b.classList.toggle("on", v); b.setAttribute("aria-label", v ? "Pause" : "Play"); b.textContent = v ? "Pause" : "Play";
    clearTimeout(timer);
    if (v) { if (step >= cur.steps.length - 1) go(0); else paint(); }
  }
  function paint() {
    renderStats(); renderStepTab(); renderInspector();
    if (view === "net") paintNet(); else renderSeq();
    $("#px-prev").disabled = step === 0;
    $("#px-next").disabled = step === cur.steps.length - 1;
    history.replaceState(null, "", `#/${cur.id}/${step + 1}`);
    if (step === cur.steps.length - 1) seen.add(cur.id);
  }
  function go(i) {
    step = Math.max(0, Math.min(cur.steps.length - 1, i));
    inspected = 0;
    paint();
  }
  function open(id, st) {
    const p = P.find(x => x.id === id) || P[0];
    if (!p) return;
    const changed = !cur || cur.id !== p.id;
    cur = p;
    if (changed) {
      setPlay(false);
      renderHead(); renderOverview(); renderPractice();
      if (view === "net") buildNet();
      renderList();
      closeDrawer();
      window.scrollTo({ top: 0 });
    }
    go((st || 1) - 1);
  }
  function setView(v) {
    view = v;
    $$(".px-views button").forEach(b => b.setAttribute("aria-pressed", b.dataset.view === v));
    $("#px-stage").classList.toggle("seq", v === "seq");
    if (v === "net") buildNet();
    paint();
  }
  function closeDrawer() { const l = $("#px-list"); if (l) l.classList.remove("open"); document.body.classList.remove("px-drawer"); }
  function fromHash() {
    const m = location.hash.match(/^#\/([\w-]+)(?:\/(\d+))?/);
    open(m ? m[1] : (P[0] && P[0].id), m && m[2] ? +m[2] : 1);
  }

  function init() {
    if (!$("#px") || !P.length) return;
    $$(".px-tabs button").forEach(b => b.addEventListener("click", () => { cat = b.dataset.cat; $$(".px-tabs button").forEach(x => x.setAttribute("aria-pressed", x === b)); renderList(); }));
    $("#px-q").addEventListener("input", e => { q = e.target.value; renderList(); });
    $("#px-rows").addEventListener("click", e => { const a = e.target.closest(".px-row"); if (a) { e.preventDefault(); location.hash = `#/${a.dataset.id}`; } });
    $$(".px-views button").forEach(b => b.addEventListener("click", () => setView(b.dataset.view)));
    $$(".px-tabs2 button").forEach(b => b.addEventListener("click", () => {
      $$(".px-tabs2 button").forEach(x => x.setAttribute("aria-pressed", x === b));
      ["step", "over", "prac"].forEach(t => ($("#px-tab-" + t).hidden = t !== b.dataset.tab));
    }));
    $$(".px-inspect-top button").forEach(b => b.addEventListener("click", () => { insView = b.dataset.ins; $$(".px-inspect-top button").forEach(x => x.setAttribute("aria-pressed", x === b)); renderInspector(); }));
    $("#px-play").addEventListener("click", () => setPlay(!playing));
    $("#px-prev").addEventListener("click", () => { setPlay(false); go(step - 1); });
    $("#px-next").addEventListener("click", () => { setPlay(false); go(step + 1); });
    $("#px-restart").addEventListener("click", () => { setPlay(false); go(0); });
    $("#px-speed").addEventListener("change", e => { speed = +e.target.value; paint(); });
    $("#px-prog").addEventListener("click", e => { const b = e.target.closest("button"); if (b) { setPlay(false); go([...b.parentNode.children].indexOf(b)); } });
    $("#px-rail").addEventListener("click", e => { const b = e.target.closest("button"); if (b) { setPlay(false); go([...b.parentNode.children].indexOf(b)); } });
    $("#px-open").addEventListener("click", () => { $("#px-list").classList.add("open"); document.body.classList.add("px-drawer"); $("#px-q").focus(); });
    $(".px-close").addEventListener("click", closeDrawer);
    document.addEventListener("keydown", e => {
      if (e.target.closest("input, textarea, select") || e.altKey || e.ctrlKey || e.metaKey) return;
      if (e.key === "ArrowRight") { setPlay(false); go(step + 1); }
      else if (e.key === "ArrowLeft") { setPlay(false); go(step - 1); }
      else if (e.key === " " && e.target === document.body) { e.preventDefault(); setPlay(!playing); }
      else if (e.key === "Escape") closeDrawer();
    });
    window.addEventListener("hashchange", fromHash);
    document.addEventListener("themechange", () => { if (view === "net") { buildNet(); paint(); } });
    fromHash();
  }
  document.addEventListener("DOMContentLoaded", init);
})();
