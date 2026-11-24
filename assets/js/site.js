/* Shared page code. No build step, no framework. */
(function () {
  "use strict";

  const NAV = [
    ["index.html", "Home"],
    ["basics.html", "Start here"],
    ["plan.html", "Plan"],
    ["learn/index.html", "Concepts"],
    ["design/index.html", "Design it"],
    ["interview.html", "Interview"],
    ["library.html", "Library"]
  ];
  const REPO = "https://github.com/NucleiAv/sys-arch";
  const R = (document.body && document.body.dataset.root) || "";
  const TRACK = (document.body && document.body.dataset.track) || "";
  const here = TRACK ? TRACK + "/index.html" : (location.pathname.split("/").pop() || "index.html").toLowerCase();

  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  /* The mark: two boxes joined by an arrow */
  const MARK = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="2" y="3.5" width="8" height="7" rx="2" fill="none" stroke="currentColor" stroke-width="1.5"/><rect x="14" y="13.5" width="8" height="7" rx="2" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M10 7h3.5c1.4 0 2.5 1.1 2.5 2.5V13" fill="none" stroke="var(--pencil)" stroke-width="2" stroke-linecap="round"/><path d="M13.6 11.2 16 13.6l2.4-2.4" fill="none" stroke="var(--pencil)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';

  /* Header and footer */
  function chrome() {
    const top = $("#top");
    if (top) {
      top.className = "top";
      top.innerHTML = `<div class="wrap">
        <a class="brand" href="${R}index.html">${MARK}<span>Boxes and Arrows</span><small>System design, zero to mastery</small></a>
        <button class="theme-btn" type="button" aria-label="Switch light or dark mode" title="Switch light or dark mode"></button>
        <button class="menu-btn" aria-expanded="false" aria-controls="nav">Menu</button>
        <nav class="nav" id="nav" aria-label="Main">${NAV.map(([h, t]) => `<a href="${R}${h}"${h === here ? ' aria-current="page"' : ""}>${t}</a>`).join("")}</nav>
      </div>`;
      const btn = $(".menu-btn", top), nav = $("#nav", top);
      btn.addEventListener("click", () => { const o = nav.classList.toggle("open"); btn.setAttribute("aria-expanded", o); });
      const tb = $(".theme-btn", top);
      const SUN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"/></svg>';
      const MOON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" aria-hidden="true"><path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/></svg>';
      const paint = () => { const d = document.documentElement.dataset.theme === "dark"; tb.innerHTML = d ? SUN : MOON; tb.setAttribute("aria-pressed", d); };
      paint();
      tb.addEventListener("click", () => {
        const t = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
        document.documentElement.dataset.theme = t;
        try { localStorage.setItem("site.theme", t); } catch (e) {}
        paint();
        document.dispatchEvent(new CustomEvent("themechange", { detail: t }));
      });
    }
    const foot = $("#foot");
    if (foot) {
      foot.className = "foot";
      foot.innerHTML = `<div class="wrap">
        <div><p><b style="color:var(--ink)">Boxes and Arrows</b> teaches system design and architecture from zero to mastery, in plain words.</p>
        <p>Built and curated by <a href="https://anmol-vats-portfolio.vercel.app/" target="_blank" rel="noopener">Anmol Vats</a>. Links point to their own sites. Progress, ticks and answers you write here stay in this browser only.</p></div>
        <div><h4>Learn</h4>${NAV.slice(1, 5).map(([h, t]) => `<a href="${R}${h}">${t}</a>`).join("")}</div>
        <div><h4>More</h4>${NAV.slice(5).map(([h, t]) => `<a href="${R}${h}">${t}</a>`).join("")}<a href="${REPO}" target="_blank" rel="noopener">GitHub repository</a><a href="https://anmol-vats-portfolio.vercel.app/" target="_blank" rel="noopener">Author portfolio</a></div>
      </div>`;
    }
  }

  /* Progress store, saved in localStorage */
  const KEY = "sysarch.progress.v1";
  const store = {
    all() { try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { return {}; } },
    get(id) { return !!this.all()[id]; },
    set(id, v) { const a = this.all(); if (v) a[id] = 1; else delete a[id]; try { localStorage.setItem(KEY, JSON.stringify(a)); } catch (e) {} },
    clear(prefix) { const a = this.all(); Object.keys(a).forEach(k => { if (!prefix || k.startsWith(prefix)) delete a[k]; }); try { localStorage.setItem(KEY, JSON.stringify(a)); } catch (e) {} }
  };

  /* One dropdown look everywhere. The native select stays in the page, hidden. */
  let openDrop = null;
  function closeDrop() { if (openDrop) { openDrop.list.hidden = true; openDrop.btn.setAttribute("aria-expanded", "false"); openDrop = null; } }
  document.addEventListener("click", e => { if (openDrop && !openDrop.wrap.contains(e.target)) closeDrop(); });
  function enhanceSelect(sel) {
    if (!sel || sel.dataset.enhanced) return;
    sel.dataset.enhanced = "1";
    const wrap = document.createElement("div");
    wrap.className = "dd";
    sel.parentNode.insertBefore(wrap, sel);
    wrap.appendChild(sel);
    sel.classList.add("dd-native");
    sel.tabIndex = -1;
    sel.setAttribute("aria-hidden", "true");
    const btn = document.createElement("button");
    btn.type = "button"; btn.className = "dd-btn";
    btn.setAttribute("aria-haspopup", "listbox"); btn.setAttribute("aria-expanded", "false");
    const list = document.createElement("ul");
    list.className = "dd-list"; list.setAttribute("role", "listbox"); list.hidden = true;
    wrap.appendChild(btn); wrap.appendChild(list);
    const paint = () => {
      const o = sel.options[sel.selectedIndex];
      btn.innerHTML = `<span>${o ? o.text : ""}</span><i aria-hidden="true"></i>`;
      btn.classList.toggle("placeholder", !sel.value);
      list.innerHTML = Array.from(sel.options).map((o, i) => `<li role="option" data-i="${i}" aria-selected="${i === sel.selectedIndex}"${o.value === "" ? ' class="ph"' : ""}>${o.text}</li>`).join("");
    };
    let active = 0;
    const setActive = i => {
      const items = list.children; if (!items.length) return;
      active = (i + items.length) % items.length;
      Array.from(items).forEach((li, k) => li.classList.toggle("act", k === active));
      items[active].scrollIntoView({ block: "nearest" });
    };
    const choose = i => {
      if (sel.selectedIndex !== i) { sel.selectedIndex = i; sel.dispatchEvent(new Event("change", { bubbles: true })); }
      paint(); closeDrop(); btn.focus();
    };
    const open = () => { closeDrop(); paint(); list.hidden = false; btn.setAttribute("aria-expanded", "true"); openDrop = { wrap, list, btn }; setActive(Math.max(0, sel.selectedIndex)); };
    btn.addEventListener("click", () => (list.hidden ? open() : closeDrop()));
    list.addEventListener("click", e => { const li = e.target.closest("li"); if (li) choose(+li.dataset.i); });
    list.addEventListener("mousemove", e => { const li = e.target.closest("li"); if (li) setActive(+li.dataset.i); });
    btn.addEventListener("keydown", e => {
      if (["ArrowDown", "ArrowUp", "Enter", " "].includes(e.key) && list.hidden) { e.preventDefault(); open(); return; }
      if (list.hidden) return;
      if (e.key === "ArrowDown") { e.preventDefault(); setActive(active + 1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); setActive(active - 1); }
      else if (e.key === "Enter" || e.key === " ") { e.preventDefault(); choose(active); }
      else if (e.key === "Escape" || e.key === "Tab") closeDrop();
    });
    sel.addEventListener("change", paint);
    paint();
  }
  /* label table cells with their column name so tables can stack as cards on phones */
  function labelTables(root) {
    (root || document).querySelectorAll("table.table").forEach(t => {
      const heads = [...t.querySelectorAll("thead th")].map(th => th.textContent.trim());
      if (heads.length < 2) return;
      t.querySelectorAll("tbody tr").forEach(tr => [...tr.children].forEach((c, i) => { if (heads[i]) c.setAttribute("data-label", heads[i]); }));
      t.classList.add("stack");
    });
  }
  function enhanceAll(root) { (root || document).querySelectorAll("select").forEach(enhanceSelect); labelTables(root); }
  document.addEventListener("DOMContentLoaded", () => labelTables(document));
  window.AIC = { store, enhanceSelect, enhanceAll };

  /* ---------- Plan page ---------- */
  function initPlan() {
    if (!$("#plan-bar")) return;
    const boxes = $$("input[data-id^='plan.']");
    const levels = [[0.25, "Foundations are in place. Keep going."], [0.5, "Halfway. You can now sketch most simple systems."], [0.75, "You can hold a real design conversation."], [1, "Plan complete. Do the mock interviews again in a month."]];
    $("#pmax").textContent = boxes.length;
    const update = () => {
      const n = boxes.filter(b => b.checked).length, f = n / boxes.length;
      $("#pts").textContent = n;
      $("#meter").style.transform = `scaleX(${f})`;
      let t = n ? "Good start. Tick tasks as you finish them." : "Nothing ticked yet. Start with week 1.";
      levels.forEach(([x, s]) => { if (f >= x) t = s; });
      $("#level").textContent = t;
      boxes.forEach(b => { const r = b.closest(".task"); if (r) r.classList.toggle("done", b.checked); });
    };
    boxes.forEach(b => b.addEventListener("change", () => setTimeout(update)));
    $("#reset").addEventListener("click", () => {
      if (confirm("Clear every tick on this page? This cannot be undone.")) { store.clear("plan."); boxes.forEach(b => { b.checked = false; }); update(); }
    });
    setTimeout(update);
  }

  /* ---------- Home ---------- */
  function renderHome() {
    const el = $("#home-progress"); if (!el || !window.ROUTE) return;
    const a = store.all();
    const lessons = window.ROUTE.filter(r => a["learn." + r.s]).length;
    const designs = Object.keys(a).filter(k => k.startsWith("design.")).length;
    const basics = Object.keys(a).filter(k => k.startsWith("basics.")).length;
    el.innerHTML = lessons || designs || basics
      ? `You have read ${basics} basics steps, finished <b>${lessons}</b> of ${window.ROUTE.length} lessons and <b>${designs}</b> of ${window.DESIGNS} designs. <a href="learn/index.html">Continue</a>.`
      : `Nothing finished yet. Start with <a href="basics.html">the basics</a>, or jump to <a href="learn/index.html">the concepts</a> if you know some already.`;
  }
  function drawRoute() {
    const svg = $("#route"); if (!svg || !window.ROUTE) return;
    const R_ = window.ROUTE, a = store.all();
    const rows = [[], [], [], [], []];
    R_.forEach(r => rows[(r.l || 1) - 1].push(r));
    const names = ["Foundations", "Data", "Many machines", "Running it for real", "Mastery"];
    const ys = [60, 130, 200, 270, 340];
    let h = "";
    /* snake line through the rows */
    let d = "";
    ys.forEach((y, i) => {
      const lft = 150, rgt = 610;
      if (i === 0) d += `M${lft} ${y} H${rgt}`;
      else if (i % 2) d += ` C${rgt + 30} ${ys[i - 1]} ${rgt + 30} ${y} ${rgt} ${y} H${lft}`;
      else d += ` C${lft - 30} ${ys[i - 1]} ${lft - 30} ${y} ${lft} ${y} H${rgt}`;
    });
    d += ` C${560} 340 560 400 520 400 H330`;
    h += `<path class="ln" d="${d}"/>`;
    ys.forEach((y, i) => {
      h += `<text x="0" y="${y - 2}" class="t-s t-mute">${names[i]}</text><text x="0" y="${y + 14}" class="t-mono">level ${i + 1}</text>`;
      const row = rows[i], n = row.length;
      row.forEach((r, k) => {
        const t = n > 1 ? k / (n - 1) : 0.5;
        const x = i % 2 ? 600 - t * 440 : 160 + t * 440;
        const done = a["learn." + r.s];
        h += `<a href="learn/${r.s}.html"><title>${esc(r.n + ". " + r.t)}</title><circle cx="${x}" cy="${y}" r="8" style="fill:${done ? "var(--pencil)" : "var(--card)"};stroke:${done ? "var(--pencil)" : "var(--ink)"};stroke-width:1.5"/>
          <text x="${x}" y="${y + (k % 2 ? -14 : 24)}" text-anchor="middle" class="t-mono">${r.n}</text></a>`;
      });
    });
    const dd = Object.keys(a).filter(k => k.startsWith("design.")).length;
    h += `<a href="design/index.html"><rect x="300" y="390" width="20" height="20" transform="rotate(45 310 400)" style="fill:${dd ? "var(--pencil)" : "var(--card)"};stroke:var(--pencil);stroke-width:1.5"/>
      <text x="290" y="404" text-anchor="end" class="t-s t-mute">then design ${window.DESIGNS} real systems</text></a>`;
    svg.innerHTML = h;
  }

  /* ---------- Step rail on Start here ---------- */
  function initRail() {
    const rail = $(".rail"); if (!rail) return;
    const links = $$("a[href^='#step-']", rail);
    const update = () => {
      const n = Object.keys(store.all()).filter(k => k.startsWith("basics.")).length;
      const p = $(".progress", rail); if (p) p.textContent = `${n} of ${links.length} steps read`;
      links.forEach(a => a.classList.toggle("seen", store.get("basics." + a.getAttribute("href").slice(1))));
    };
    if ("IntersectionObserver" in window) {
      const io = new IntersectionObserver(es => es.forEach(e => {
        if (!e.isIntersecting) return;
        links.forEach(a => a.classList.toggle("on", a.getAttribute("href") === "#" + e.target.id));
      }), { rootMargin: "-30% 0px -60% 0px" });
      const done = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { store.set("basics." + e.target.dataset.for, 1); update(); } }));
      $$(".step").forEach(s => io.observe(s));
      $$(".step-end").forEach(s => done.observe(s));
    }
    update();
  }

  /* ---------- Scale simulator ---------- */
  function initSim() {
    const sim = $("#scale-sim"); if (!sim) return;
    let users = 1000;
    const out = $(".sim-out", sim);
    const on = id => $("#" + id).checked;
    const fmt = n => n >= 1e6 ? (n / 1e6).toFixed(n % 1e6 ? 1 : 0) + "M" : n >= 1e3 ? Math.round(n / 1e3) + "k" : String(Math.round(n));
    const draw = () => {
      const s = { lb: on("s-lb"), cache: on("s-cache"), rep: on("s-rep"), cdn: on("s-cdn"), q: on("s-q") };
      /* a very small model of a web app. Every user sends about one request every 20 seconds at peak. */
      const rps = users * 0.05;
      const fileShare = 0.6;                         /* images, scripts and styles */
      const appLoad = s.cdn ? rps * (1 - fileShare) : rps;
      const appCap = s.lb ? 300000 : 1000;
      const dyn = rps * (1 - fileShare);
      const reads = dyn * 0.95 * (s.cache ? 0.05 : 1), writes = dyn * 0.05;
      const readCap = 1000 * (s.rep ? 10 : 1), writeCap = 5000 * (s.q ? 3 : 1);
      const parts = [
        ["App servers", appLoad, appCap, s.lb ? "many servers behind a load balancer" : "one server"],
        ["Database reads", reads, readCap, (s.rep ? "main database plus replicas" : "one database") + (s.cache ? ", most reads served by the cache" : "")],
        ["Database writes", writes, writeCap, s.q ? "writes smoothed by a queue" : "writes go straight in"]
      ];
      const cost = 1 + (s.lb ? 3 : 0) + (s.cache ? 1 : 0) + (s.rep ? 2 : 0) + (s.cdn ? 1 : 0) + (s.q ? 1 : 0);
      const worst = parts.reduce((m, p) => (p[1] / p[2] > m[1] / m[2] ? p : m));
      const over = parts.filter(p => p[1] > p[2]);
      const util = worst[1] / worst[2];
      let ms = 120 + (s.cache ? -50 : 0) + (s.cdn ? -30 : 0) + (util > 0.8 ? 400 * (util - 0.8) : 0);
      if (over.length) ms = 9999;
      let verdict, good, why;
      if (over.length) {
        verdict = `Down. ${over.map(p => p[0].toLowerCase()).join(" and ")} cannot keep up`; good = false;
        const p = over[0];
        why = {
          "App servers": "One server can answer about 1,000 requests a second. You now get " + fmt(appLoad) + ". Add a load balancer and more servers. At 10 million users, also move files to a CDN so the servers only do real work.",
          "Database reads": "The database is asked " + fmt(reads) + " reads a second and can do about " + fmt(readCap) + ". A cache answers the same popular questions from memory. Read replicas add more copies that can answer. Big apps need both.",
          "Database writes": "Writes cannot be cached, and every write must reach the main database. A queue lines them up so a burst does not knock the database over. Later you would split the data across many databases, which is called sharding."
        }[p[0]];
      } else if (users === 1000 && cost > 3) {
        verdict = "Works, but you are paying for parts you do not need"; good = true;
        why = "With a thousand users, one server and one database are fine. Every extra part costs money and is one more thing that can break. Good architects add parts when the numbers ask for them, not before.";
      } else {
        verdict = "Healthy"; good = true;
        why = util > 0.7 ? "It works, but the busiest part is above 70 percent. A small spike could tip it over. Leave room to grow." : "Every part has room to spare. This is the right amount of system for this many users.";
      }
      out.innerHTML = `
        <div class="msg"><span class="who">traffic at the busiest minute</span><b>${fmt(rps)}</b> requests a second from ${fmt(users)} users</div>
        ${parts.map(([n, load, cap, note]) => {
          const u = load / cap, pct = Math.min(100, u * 100);
          return `<div class="meterrow"><div class="mr-top"><span>${n}</span><span class="mono">${fmt(load)} of ${fmt(cap)} a second</span></div>
            <div class="mr-bar"><i class="${u > 1 ? "bad" : u > 0.7 ? "warn" : ""}" style="width:${Math.max(2, pct)}%"></i></div><small class="muted">${note}</small></div>`;
        }).join("")}
        <div class="msg doc"><span class="who">what a user feels</span>${over.length ? "Pages time out or show errors." : `Pages load in about ${Math.round(ms)} ms.`} Monthly cost, ${"$".repeat(cost)}</div>
        <div class="verdict ${good ? "good" : "bad"}">${verdict}</div>
        <p class="why">${why}</p>`;
    };
    $$("input", sim).forEach(i => i.addEventListener("change", draw));
    $$(".seg button", sim).forEach(b => b.addEventListener("click", () => { users = +b.dataset.users; $$(".seg button", sim).forEach(x => x.setAttribute("aria-pressed", x === b)); draw(); }));
    draw();
  }

  /* ---------- Interview bank ---------- */
  function initBank() {
    const f = $("#iv-filter"); if (!f) return;
    f.addEventListener("click", e => {
      const b = e.target.closest("button"); if (!b) return;
      $$("button", f).forEach(x => x.setAttribute("aria-pressed", x === b));
      $$(".iv-group").forEach(g => { g.hidden = !!b.dataset.lvl && g.dataset.lvl !== b.dataset.lvl; });
    });
    const rb = $("#iv-random");
    if (rb) rb.addEventListener("click", () => {
      const qs = $$(".iv-group .q").filter(q => !q.closest(".iv-group").hidden);
      if (!qs.length) return;
      $$(".q.pick").forEach(q => q.classList.remove("pick"));
      const q = qs[Math.floor(Math.random() * qs.length)];
      q.classList.add("pick");
      q.scrollIntoView({ behavior: "smooth", block: "center" });
      const t = $("textarea", q); if (t) setTimeout(() => t.focus({ preventScroll: true }), 500);
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    chrome();
    initPlan();
    renderHome();
    drawRoute();
    initRail();
    initSim();
    initBank();
  });
})();
