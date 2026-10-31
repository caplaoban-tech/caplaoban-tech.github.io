// Схема владения: данные /data/ownership.json, страница /own/?g=группа&id=узел
(async function () {
  const $ = id => document.getElementById(id);
  const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const pct = x => { let t = (Math.round(x * 100) / 100).toFixed(2); t = t.replace(/0+$/, "").replace(/\.$/, ""); return t.replace(".", ",") + "%"; };
  const NS = "http://www.w3.org/2000/svg";
  const W = 172, H = 58, GX = 34, GY = 84;
  const KIND = { person: "человек / семья", listed: "биржевая компания", private: "частная компания", offshore: "офшорная компания", division: "подразделение" };

  const D = await (await fetch("/data/ownership.json?v=" + (Date.now() / 36e5 | 0))).json();
  const N = D.nodes, E = D.edges;
  const q = new URLSearchParams(location.search);
  const G = D.groups.find(g => g.id === q.get("g")) || D.groups.find(g => q.get("id") && comp(g.root).has(q.get("id"))) || D.groups[0];
  const C = comp(G.root);
  const edges = E.filter(e => C.has(e.from) && C.has(e.to));
  const out = id => edges.filter(e => e.from === id), inn = id => edges.filter(e => e.to === id);
  let sel = C.has(q.get("id")) ? q.get("id") : G.focus;
  let collapsed = new Set();

  function comp(root) { // связная компонента (без учёта направления)
    const s = new Set([root]), st = [root];
    while (st.length) { const x = st.pop(); for (const e of D.edges) { const y = e.from === x ? e.to : e.to === x ? e.from : null; if (y && !s.has(y)) { s.add(y); st.push(y); } } }
    return s;
  }
  function ancestors(id, acc = new Set()) { for (const e of inn(id)) if (!acc.has(e.from)) { acc.add(e.from); ancestors(e.from, acc); } return acc; }
  function chainMode(id) { const keep = ancestors(id); keep.add(id); collapsed = new Set([...C].filter(x => !keep.has(x))); }
  // сквозная доля: сумма по всем путям произведений долей
  function through(from, to, seen = new Set()) {
    if (from === to) return 1;
    let s = 0;
    for (const e of out(from)) if (!seen.has(e.to)) { seen.add(e.to); s += e.pct / 100 * through(e.to, to, seen); seen.delete(e.to); }
    return s;
  }

  // ---------- группы, текст ----------
  $("groups").innerHTML = D.groups.map(g => `<a href="?g=${g.id}" class="${g === G ? "on" : ""}">${esc(g.title)}</a>`).join("");
  $("g-title").textContent = G.title;
  $("group-text").innerHTML = `<h2>Что это значит</h2>${(G.text || []).map(t => `<p>${esc(t)}</p>`).join("")}<p class="note">Источники: ${esc(G.src)}</p>`;
  $("src-note").textContent = D.about + " Обновлено " + D.updated.split("-").reverse().join(".") + ".";

  // ---------- раскладка по уровням ----------
  function layout() {
    const vis = new Set(), st = [];
    for (const id of C) if (!inn(id).length) { vis.add(id); st.push(id); }
    while (st.length) { const x = st.pop(); if (collapsed.has(x)) continue; for (const e of out(x)) if (!vis.has(e.to)) { vis.add(e.to); st.push(e.to); } }
    for (const id of ancestors(sel)) vis.add(id); vis.add(sel);
    const ve = edges.filter(e => vis.has(e.from) && vis.has(e.to));
    const lvl = {};
    const L = id => { if (lvl[id] !== undefined) return lvl[id]; lvl[id] = 0; const ps = ve.filter(e => e.to === id); return lvl[id] = ps.length ? Math.max(...ps.map(e => L(e.from) + 1)) : 0; };
    for (const id of vis) L(id);
    for (const id of vis) { // владелец без своих владельцев — прямо над своей компанией
      const ps = ve.filter(e => e.to === id), cs = ve.filter(e => e.from === id);
      if (!ps.length && cs.length) lvl[id] = Math.min(...cs.map(e => lvl[e.to])) - 1;
    }
    const rows = {};
    for (const id of vis) (rows[lvl[id]] ||= []).push(id);
    const ks = Object.keys(rows).map(Number).sort((a, b) => a - b);
    const x = {};
    const order = [...C]; // исходный порядок — порядок в данных
    for (const k of ks) { rows[k].sort((a, b) => order.indexOf(a) - order.indexOf(b)); rows[k].forEach((id, i) => x[id] = i * (W + GX)); }
    const pack = k => { // убрать наложения, сохраняя желаемые позиции
      const r = rows[k].sort((a, b) => x[a] - x[b]);
      for (let i = 1; i < r.length; i++) x[r[i]] = Math.max(x[r[i]], x[r[i - 1]] + W + GX);
    };
    for (let it = 0; it < 6; it++) {
      for (const k of ks) { for (const id of rows[k]) { const ps = ve.filter(e => e.to === id).map(e => x[e.from]); if (ps.length) x[id] = ps.reduce((a, b) => a + b) / ps.length; } pack(k); }
      for (const k of [...ks].reverse()) { for (const id of rows[k]) { const cs = ve.filter(e => e.from === id).map(e => x[e.to]); if (cs.length) x[id] = (x[id] + cs.reduce((a, b) => a + b) / cs.length) / 2; } pack(k); }
    }
    const pos = {};
    for (const id of vis) pos[id] = { x: x[id], y: (lvl[id] - ks[0]) * (H + GY) };
    return { vis, ve, pos };
  }

  // ---------- рисование ----------
  const svg = $("svg"), vp = $("vp");
  const el = (t, a, p) => { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); if (p) p.appendChild(e); return e; };
  function lines(name) {
    if (name.length <= 22) return [name];
    const w = name.split(" "); let a = "";
    while (w.length && (a + " " + w[0]).trim().length <= 22) a = (a + " " + w.shift()).trim();
    let b = w.join(" "); if (b.length > 24) b = b.slice(0, 23) + "…";
    return [a, b];
  }
  let LAY;
  function draw() {
    LAY = layout();
    const { vis, ve, pos } = LAY;
    vp.innerHTML = "";
    const hl = new Set([...ancestors(sel)].concat(sel));
    const ge = el("g", {}, vp), gl = el("g", {}, vp), gn = el("g", {}, vp);
    ve.forEach((e, i) => {
      const a = pos[e.from], b = pos[e.to];
      const x1 = a.x + W / 2, y1 = a.y + H, x2 = b.x + W / 2, y2 = b.y, my = (y1 + y2) / 2;
      const on = hl.has(e.from) && hl.has(e.to);
      el("path", { d: `M${x1},${y1} C${x1},${my} ${x2},${my} ${x2},${y2 - 6}`, class: "edge" + (on ? " hl" : "") + (e.minor ? " minor" : ""), "marker-end": on ? "url(#arh)" : "url(#ar)" }, ge);
      const t = 0.62, lx = (1 - t) ** 3 * x1 + 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t * t * x2 + t ** 3 * x2;
      const ly = (1 - t) ** 3 * y1 + 3 * (1 - t) ** 2 * t * my + 3 * (1 - t) * t * t * my + t ** 3 * y2;
      const txt = pct(e.pct) + (e.basis === "экономическая" ? " экон." : e.basis === "эффективная" ? " эфф." : "");
      const g = el("g", { class: "elbl" + (on ? " hl" : "") }, gl);
      const w = txt.length * 6.8 + 10;
      el("rect", { x: lx - w / 2, y: ly - 10, width: w, height: 20, rx: 6 }, g);
      el("text", { x: lx, y: ly + 4, "text-anchor": "middle" }, g).textContent = txt;
    });
    for (const id of vis) {
      const n = N[id], p = pos[id];
      const g = el("g", { class: `node ${n.kind}${id === sel ? " sel" : ""}`, transform: `translate(${p.x},${p.y})`, "data-id": id, tabindex: 0 }, gn);
      el("rect", { class: "box", width: W, height: H, rx: n.kind === "person" ? H / 2 : 10 }, g);
      const ls = lines(n.name);
      ls.forEach((s, i) => { el("text", { class: "nm", x: W / 2, y: (ls.length === 1 ? 24 : 18) + i * 15, "text-anchor": "middle" }, g).textContent = s; });
      const sub = el("text", { class: n.ticker ? "tk" : "sub", x: W / 2, y: H - 9, "text-anchor": "middle" }, g);
      sub.textContent = n.ticker ? `${n.ticker} · ${n.exchange || ""}` : (n.kind === "person" ? n.country : KIND[n.kind]);
      const kids = out(id).length;
      if (kids) {
        const hidden = out(id).filter(e => !vis.has(e.to)).length;
        const isCol = hidden > 0;
        const tg = el("g", { class: "tog", transform: `translate(${W - 4},${H - 4})`, "data-tog": id }, g);
        el("circle", { r: 11 }, tg);
        el("text", { y: 4, "text-anchor": "middle" }, tg).textContent = isCol ? "+" + hidden : "−";
      }
    }
  }
  const defs = el("defs", {}, svg);
  for (const [id, col] of [["ar", "var(--steel)"], ["arh", "var(--red)"]]) {
    const m = el("marker", { id, viewBox: "0 0 10 10", refX: 5, refY: 5, markerWidth: 7, markerHeight: 7, orient: "auto-start-reverse" }, defs);
    el("path", { d: "M0,0 L10,5 L0,10 z", style: `fill:${col}` }, m);
  }

  // ---------- масштаб и сдвиг ----------
  let T = { k: 1, x: 0, y: 0 };
  const apply = () => vp.setAttribute("transform", `translate(${T.x},${T.y}) scale(${T.k})`);
  function fit(onlyId) {
    const bb = vp.getBBox(), r = svg.getBoundingClientRect(), pad = 24;
    T.k = Math.min(1.15, (r.width - pad * 2) / bb.width, (r.height - pad * 2) / bb.height);
    T.x = (r.width - bb.width * T.k) / 2 - bb.x * T.k; T.y = (r.height - bb.height * T.k) / 2 - bb.y * T.k;
    if (onlyId && (T.k < 0.42 || (r.width < 600 && T.k < 0.55))) { // на телефоне — крупнее, с центром на выбранном
      T.k = 0.75; const p = LAY.pos[onlyId];
      T.x = r.width / 2 - (p.x + W / 2) * T.k; T.y = r.height / 2.4 - (p.y + H / 2) * T.k;
    }
    apply();
  }
  const zoomAt = (f, cx, cy) => { const k = Math.max(0.2, Math.min(3, T.k * f)); T.x = cx - (cx - T.x) * k / T.k; T.y = cy - (cy - T.y) * k / T.k; T.k = k; apply(); };
  $("z-in").onclick = () => { const r = svg.getBoundingClientRect(); zoomAt(1.25, r.width / 2, r.height / 2); };
  $("z-out").onclick = () => { const r = svg.getBoundingClientRect(); zoomAt(0.8, r.width / 2, r.height / 2); };
  $("z-fit").onclick = () => fit();
  $("x-all").onclick = () => { collapsed = new Set(); draw(); fit(); };
  $("x-path").onclick = () => { chainMode(sel); draw(); fit(sel); };
  svg.addEventListener("wheel", ev => { ev.preventDefault(); const r = svg.getBoundingClientRect(); zoomAt(ev.deltaY < 0 ? 1.12 : 0.89, ev.clientX - r.left, ev.clientY - r.top); }, { passive: false });
  const ptr = new Map(); let moved = 0, pinch = null;
  svg.addEventListener("pointerdown", ev => { svg.setPointerCapture(ev.pointerId); ptr.set(ev.pointerId, { x: ev.clientX, y: ev.clientY }); moved = 0; $("canvas").classList.add("drag"); });
  svg.addEventListener("pointermove", ev => {
    if (!ptr.has(ev.pointerId)) return;
    const p = ptr.get(ev.pointerId), dx = ev.clientX - p.x, dy = ev.clientY - p.y;
    if (ptr.size === 2) {
      ptr.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
      const [a, b] = [...ptr.values()], d = Math.hypot(a.x - b.x, a.y - b.y), r = svg.getBoundingClientRect();
      if (pinch) zoomAt(d / pinch, (a.x + b.x) / 2 - r.left, (a.y + b.y) / 2 - r.top);
      pinch = d; moved = 99; return;
    }
    moved += Math.abs(dx) + Math.abs(dy); T.x += dx; T.y += dy; apply(); ptr.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
  });
  const up = ev => { ptr.delete(ev.pointerId); if (ptr.size < 2) pinch = null; if (!ptr.size) $("canvas").classList.remove("drag"); };
  svg.addEventListener("pointerup", ev => {
    up(ev);
    if (moved > 6) return;
    const t = document.elementFromPoint(ev.clientX, ev.clientY);
    const tog = t && t.closest("[data-tog]"), nd = t && t.closest("[data-id]");
    if (tog) { const id = tog.dataset.tog; const vis = LAY.vis; const anyHidden = out(id).some(e => !vis.has(e.to)); anyHidden ? collapsed.delete(id) : collapsed.add(id); draw(); return; }
    if (nd) select(nd.dataset.id, false);
  });
  svg.addEventListener("pointercancel", up);
  svg.addEventListener("keydown", ev => { const nd = ev.target.closest && ev.target.closest("[data-id]"); if (nd && (ev.key === "Enter" || ev.key === " ")) { ev.preventDefault(); select(nd.dataset.id, false); } });

  // ---------- карточка ----------
  function select(id, refit) {
    sel = id;
    collapsed.delete(id);
    const u = new URL(location); u.searchParams.set("g", G.id); u.searchParams.set("id", id); history.replaceState(null, "", u);
    draw(); if (refit) fit(id);
    card();
  }
  function card() {
    const n = N[sel], ow = inn(sel), hd = out(sel);
    const link = id => `<a class="jump" data-go="${id}">${esc(N[id].name)}</a>`;
    const basis = e => e.basis ? ` <span class="muted">(${esc(e.basis)})</span>` : "";
    const people = [...ancestors(sel)].filter(a => N[a].kind === "person");
    const thr = people.map(p => [p, through(p, sel)]).filter(([, v]) => v > 0.0001).sort((a, b) => b[1] - a[1]);
    $("card").className = "panel own-card";
    $("card").innerHTML = `<div class="eyebrow">Карточка</div><h2>${esc(n.name)}</h2>
      <div class="meta">${esc(KIND[n.kind])}${n.ticker ? " · " + esc(n.ticker) + " · " + esc(n.exchange) : ""} · ${esc(n.country || "")}</div>
      <p>${esc(n.desc || "")}</p>${(n.facts || []).length ? `<ul class="list">${n.facts.map(f => `<li><span class="dot" style="background:var(--ore)"></span><span>${esc(f)}</span></li>`).join("")}</ul>` : ""}
      <div class="cols">
        <div><h3>Кто владеет</h3>${ow.length || n.float ? `<table>${ow.map(e => `<tr><td>${link(e.from)}${basis(e)}</td><td class="p">${pct(e.pct)}</td></tr>`).join("")}${n.float ? `<tr><td>Свободное обращение (публика)</td><td class="p">${pct(n.float)}</td></tr>` : ""}</table>` : `<p class="note">Нет владельцев в схеме.</p>`}</div>
        <div><h3>Чем владеет</h3>${hd.length ? `<table>${hd.map(e => `<tr><td>${link(e.to)}${basis(e)}</td><td class="p">${pct(e.pct)}</td></tr>`).join("")}</table>` : `<p class="note">Владений в схеме нет.</p>`}</div>
      </div>
      ${thr.length ? `<h3 style="margin-top:14px">Сквозная доля в прибыли</h3><table>${thr.map(([p, v]) => `<tr><td>${link(p)}</td><td class="p">${pct(v * 100)}</td></tr>`).join("")}</table><p class="note">Произведение долей вдоль цепочки, сумма по всем путям [Б]. Контроль при этом может быть полным.</p>` : ""}
      <p class="note">Источники долей: ${[...new Set(ow.concat(hd).map(e => e.src))].map(esc).join("; ")} [А].</p>
      <div class="btns">${n.page ? `<a class="main" href="${esc(n.page)}">Разбор ${esc(n.ticker || n.name)} →</a>` : ""}<a href="#" data-chain="1">Цепочка до этой компании</a></div>`;
    $("card").querySelectorAll("[data-go]").forEach(a => a.onclick = ev => { ev.preventDefault(); select(a.dataset.go, true); $("canvas").scrollIntoView({ behavior: "smooth", block: "center" }); });
    $("card").querySelector("[data-chain]").onclick = ev => { ev.preventDefault(); chainMode(sel); draw(); fit(sel); $("canvas").scrollIntoView({ behavior: "smooth", block: "center" }); };
  }

  chainMode(sel);
  draw(); fit(q.get("id") ? sel : null); card();
})();
