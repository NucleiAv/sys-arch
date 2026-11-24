/* Lesson pages. Question sets, embedded course pages, sidebar, done marks. */
(function () {
  "use strict";
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
  const store = window.AIC.store;
  const NOTES = "sysarch.notes.v1";
  const notes = {
    all() { try { return JSON.parse(localStorage.getItem(NOTES)) || {}; } catch (e) { return {}; } },
    get(k) { return this.all()[k] || ""; },
    set(k, v) { const a = this.all(); if (v) a[k] = v; else delete a[k]; try { localStorage.setItem(NOTES, JSON.stringify(a)); } catch (e) {} }
  };
  const TICK = '<span class="box"></span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 13c2 1.4 3.7 3.2 5.2 5.4C11.6 12.6 15.4 7.4 21 3"/></svg>';
  const norm = s => String(s).toLowerCase().replace(/[^a-z0-9.]/g, "");

  /* ---------- question sets ---------- */
  function renderSet(box) {
    const id = box.dataset.id;
    const src = $(`script[data-for="${id}"]`);
    if (!src) return;
    const items = JSON.parse(src.textContent);
    box.innerHTML = items.map((it, i) => {
      const qid = `${id}.${i}`;
      const num = `<span class="qn mono">${items.length > 1 ? "Q" + (i + 1) : "Q"}</span>`;
      const info = it.info ? `<div class="qinfo">${it.info}</div>` : "";
      if (it.type === "mcq") {
        return `<div class="q mcq" data-q="${qid}">${num}<p class="qq">${it.q}</p>${info}
          <div class="opts">${it.opts.map((o, j) => `<button type="button" data-j="${j}">${o}</button>`).join("")}</div>
          <div class="why">${it.why || ""}</div></div>`;
      }
      if (it.type === "sort") {
        return `<div class="q sort" data-q="${qid}">${num}<p class="qq">${it.q}</p>${info}
          <div class="rows">${it.rows.map((r, j) => `<label class="srow"><span>${r[0]}</span><select data-j="${j}"><option value="">Choose</option>${it.opts.map(o => `<option>${o}</option>`).join("")}</select><i class="mark" aria-hidden="true"></i></label>`).join("")}</div>
          <button type="button" class="btn btn-quiet btn-sm check-btn">Check my answers</button><div class="why">${it.why || ""}</div></div>`;
      }
      if (it.type === "num") {
        return `<div class="q num" data-q="${qid}">${num}<p class="qq">${it.q}</p>${info}
          <div class="numrow"><input type="text" inputmode="decimal" aria-label="Your answer" value="${(notes.get(qid) || "").replace(/"/g, "&quot;")}"><span class="mono">${it.unit || ""}</span>
          <button type="button" class="btn btn-quiet btn-sm check-btn">Check</button><span class="res" aria-live="polite"></span></div>
          <div class="why">${it.why || ""}</div></div>`;
      }
      if (it.type === "fill") {
        const parts = String(it.q).split("____");
        return `<div class="q fill" data-q="${qid}">${num}<p class="qq">${parts[0]}<input type="text" class="blank" aria-label="Fill the blank" autocomplete="off" spellcheck="false">${parts.slice(1).join("____")}</p>${info}
          <div class="row"><button type="button" class="btn btn-quiet btn-sm check-btn">Check</button><button type="button" class="btn btn-quiet btn-sm show-btn">Show answer</button><span class="res" aria-live="polite"></span></div>
          <div class="why">${it.why || ""}</div></div>`;
      }
      if (it.type === "iv") {
        return `<div class="q open iv" data-q="${qid}">${num}<p class="qq">${it.q}</p>${info}
          <textarea rows="5" placeholder="Answer as if you were in the interview. It saves in this browser." aria-label="Your answer">${(notes.get(qid) || "").replace(/</g, "&lt;")}</textarea>
          <div class="row"><button type="button" class="btn btn-primary btn-sm reveal">Get feedback</button><span class="saved mono"></span></div>
          <div class="model"><div class="fbk"></div><span class="k mono">A strong answer</span>${it.a || ""}${it.fb ? `<div class="fb-more"><span class="k mono">What makes it great</span>${it.fb}</div>` : ""}</div></div>`;
      }
      /* open */
      return `<div class="q open" data-q="${qid}">${num}<p class="qq">${it.q}</p>${info}
        <textarea rows="4" placeholder="Write your answer here. It saves in this browser." aria-label="Your answer">${(notes.get(qid) || "").replace(/</g, "&lt;")}</textarea>
        <div class="row"><button type="button" class="btn btn-quiet btn-sm reveal">Show model answer</button><span class="saved mono"></span></div>
        <div class="model">${it.a || ""}</div></div>`;
    }).join("");

    $$(".q", box).forEach((q, i) => {
      const it = items[i], qid = q.dataset.q;
      if (it.type === "mcq") {
        q.addEventListener("click", e => {
          const b = e.target.closest("button"); if (!b || q.classList.contains("done")) return;
          q.classList.add("done");
          const ok = +b.dataset.j === it.a;
          $$("button", q).forEach(x => { if (+x.dataset.j === it.a) x.classList.add("right"); });
          if (!ok) b.classList.add("wrong");
          $(".why", q).insertAdjacentHTML("afterbegin", `<b>${ok ? "Correct." : "Not quite."}</b> `);
          store.set("q." + qid, ok ? 1 : 0);
          score(box);
        });
      } else if (it.type === "sort") {
        $(".check-btn", q).addEventListener("click", () => {
          let good = 0;
          $$("select", q).forEach(s => {
            const want = it.rows[+s.dataset.j][1];
            const ok = s.value === want;
            if (ok) good++;
            s.closest(".srow").classList.toggle("right", ok);
            s.closest(".srow").classList.toggle("wrong", !ok);
            s.closest(".srow").querySelector(".mark").textContent = ok ? "" : want;
          });
          q.classList.add("done");
          const w = $(".why", q);
          w.querySelector(".tally") ? w.querySelector(".tally").remove() : null;
          w.insertAdjacentHTML("afterbegin", `<b class="tally">${good} of ${it.rows.length} right. </b>`);
        });
      } else if (it.type === "num") {
        const inp = $("input", q);
        $(".check-btn", q).addEventListener("click", () => {
          const v = parseFloat(String(inp.value).replace(/[, $%]/g, ""));
          const tol = it.tol != null ? it.tol : Math.abs(it.a) * 0.01;
          const ok = !isNaN(v) && Math.abs(v - it.a) <= tol;
          notes.set(qid, inp.value);
          $(".res", q).textContent = ok ? "Correct" : "Not yet. Try again or read the working below";
          $(".res", q).className = "res " + (ok ? "good" : "bad");
          q.classList.add("done");
        });
      } else if (it.type === "fill") {
        const inp = $("input", q), res = $(".res", q);
        const ok = v => it.a.some(x => norm(x) === norm(v));
        const check = () => {
          if (!inp.value.trim()) { res.textContent = "Type an answer first"; res.className = "res bad"; return; }
          const good = ok(inp.value);
          inp.classList.toggle("right", good); inp.classList.toggle("wrong", !good);
          res.textContent = good ? "Correct" : "Not yet. Try again, or show the answer";
          res.className = "res " + (good ? "good" : "bad");
          if (good) { q.classList.add("done"); store.set("q." + qid, 1); }
        };
        $(".check-btn", q).addEventListener("click", check);
        inp.addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); check(); } });
        $(".show-btn", q).addEventListener("click", () => { inp.value = it.a[0]; inp.classList.add("shown"); res.textContent = "The answer is filled in. Read why below"; res.className = "res"; q.classList.add("done"); });
      } else if (it.type === "iv") {
        const ta = $("textarea", q), sv = $(".saved", q), fb = $(".fbk", q);
        let t;
        ta.addEventListener("input", () => { clearTimeout(t); t = setTimeout(() => { notes.set(qid, ta.value.trim()); sv.textContent = "saved"; }, 400); });
        $(".reveal", q).addEventListener("click", e => {
          const open = !q.classList.contains("shown");
          if (open) fb.innerHTML = feedback(ta.value, it.keys || []);
          q.classList.toggle("shown", open);
          e.target.textContent = open ? "Hide feedback" : "Get feedback";
        });
      } else {
        const ta = $("textarea", q), sv = $(".saved", q);
        let t;
        ta.addEventListener("input", () => { clearTimeout(t); t = setTimeout(() => { notes.set(qid, ta.value.trim()); sv.textContent = "saved"; }, 400); });
        $(".reveal", q).addEventListener("click", e => {
          q.classList.toggle("shown");
          e.target.textContent = q.classList.contains("shown") ? "Hide model answer" : "Show model answer";
        });
      }
    });
  }
  /* Feedback on a written answer. Each key point lists words that show you covered it. */
  function feedback(text, keys) {
    const t = " " + String(text).toLowerCase().replace(/[^a-z0-9%.]+/g, " ") + " ";
    const words = t.trim().split(/\s+/).filter(Boolean).length;
    if (!keys.length) return "";
    if (words < 4) return `<p class="fb-line"><b>You have not written an answer yet.</b> Try first, even three lines. Then compare. Here are the points a strong answer covers.</p><ul class="fb-list">${keys.map(k => `<li class="miss">${k[0]}</li>`).join("")}</ul>`;
    const hit = keys.map(k => k[1].some(w => t.includes(" " + w) || t.includes(w + " ") || (w.length > 4 && t.includes(w))));
    const n = hit.filter(Boolean).length, f = n / keys.length;
    const line = f === 1 ? "Excellent. You covered every key point. Now check the model answer for the order and the words used."
      : f >= 0.6 ? "Good answer. You covered most of it. Add the missing points below and it becomes a strong answer."
      : f >= 0.3 ? "A fair start. You have the core idea, but an interviewer will want more. Read the missing points and try again."
      : "Not there yet. That is fine. Read the model answer, close it, and write it again in your own words.";
    return `<p class="fb-line"><b>${n} of ${keys.length} key points.</b> ${line}</p><ul class="fb-list">${keys.map((k, i) => `<li class="${hit[i] ? "hit" : "miss"}">${hit[i] ? "" : "Missing. "}${k[0]}</li>`).join("")}</ul>
      <p class="small muted">This check looks for key words, so it can miss a point you said in other words. Use it as a guide, not a grade.</p>`;
  }
  function score(box) {
    const qs = $$(".q.mcq", box);
    if (qs.length < 2) return;
    const done = qs.filter(q => q.classList.contains("done"));
    if (done.length !== qs.length) return;
    const right = qs.filter(q => $(".right.wrong", q) === null && !$(".wrong", q)).length;
    let s = $(".qscore", box);
    if (!s) { s = document.createElement("p"); s.className = "qscore"; box.appendChild(s); }
    s.innerHTML = `<b>${right} of ${qs.length}</b> right. ${right === qs.length ? "Well done. Mark the lesson done at the top." : "Read the explanations above, then go back to the part you missed."}`;
  }

  /* ---------- sidebar and done marks ---------- */
  function initSide() {
    const btn = $(".side-btn"), nav = $("#side-nav"), side = $(".side");
    if (btn && nav) btn.addEventListener("click", () => { const o = nav.classList.toggle("open"); btn.setAttribute("aria-expanded", o); });
    $$("[data-done]").forEach(a => { if (store.get(a.dataset.done)) a.classList.add("is-done"); });
    /* bring the current group into view inside the sidebar */
    const cur = $(".side .side-mod.cur") || $(".side [aria-current='page']");
    if (cur && side && window.innerWidth > 1000) side.scrollTop = Math.max(0, cur.offsetTop - 90);
    /* highlight the part of the page you are reading */
    const links = $$(".side-mod.cur a[href^='#']");
    if (links.length && "IntersectionObserver" in window) {
      const map = new Map(links.map(l => [l.getAttribute("href").slice(1), l]));
      const io = new IntersectionObserver(es => es.forEach(e => {
        if (!e.isIntersecting) return;
        links.forEach(l => l.classList.remove("spy"));
        const l = map.get(e.target.id); if (l) l.classList.add("spy");
      }), { rootMargin: "-20% 0px -70% 0px" });
      map.forEach((l, id) => { const t = document.getElementById(id); if (t) io.observe(t); });
      links.forEach(l => l.addEventListener("click", () => { if (nav) nav.classList.remove("open"); }));
    }
    /* left and right arrow keys move between pages */
    document.addEventListener("keydown", e => {
      if (e.target.closest("input, textarea, select, [contenteditable], .scene") || e.altKey || e.ctrlKey || e.metaKey) return;
      const pg = e.key === "ArrowRight" ? $(".pager .next") : e.key === "ArrowLeft" ? $(".pager .prev") : null;
      if (pg && pg.href) location.href = pg.href;
    });
    $$("input[data-id]").forEach(i => {
      i.checked = store.get(i.dataset.id);
      i.addEventListener("change", () => {
        store.set(i.dataset.id, i.checked);
        $$(`[data-done="${i.dataset.id}"]`).forEach(a => a.classList.toggle("is-done", i.checked));
      });
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    $$(".qset").forEach(renderSet);
    if (window.AIC.enhanceAll) window.AIC.enhanceAll(document);
    initSide();
  });
})();
