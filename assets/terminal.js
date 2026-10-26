/* Cap Laoban — «терминал» компании: цена A/H, отчётность по годам и кварталам, дивиденды, сегменты.
   Данные: /data/fin/<тикер>.json (собирает china-reports/terminal/scripts/build_terminal.py)
   и /data/history/<тикер>_px.csv (date,a,h,hkdcny — дописывает робот scripts/update_market.py).
   Подключается на странице компании: <section id="terminal" hidden></section> + этот скрипт. Нет файла — блок скрыт. */
(function () {
  const box = document.getElementById("terminal");
  if (!box) return;
  const tk = (document.body.dataset.file || "").replace(/\.json$/, "");
  if (!tk || tk.startsWith("__")) return;
  const ver = `?v=${Date.now() / 36e5 | 0}`;
  const NS = "http://www.w3.org/2000/svg";
  const el = (t, a = {}, txt) => { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); if (txt != null) e.textContent = txt; return e; };
  const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const nf = (x, d = 1) => x == null || !isFinite(x) ? "—" : x.toLocaleString("ru-RU", { minimumFractionDigits: d, maximumFractionDigits: d });
  const pct = (x, d = 1) => x == null || !isFinite(x) ? "—" : (x > 0 ? "+" : "") + nf(x, d) + "%";
  const dRu = s => s ? `${s.slice(8, 10)}.${s.slice(5, 7)}.${s.slice(0, 4)}` : "";

  Promise.all([
    fetch(`/data/fin/${tk}.json${ver}`).then(r => r.ok ? r.json() : null),
    fetch(`/data/history/${tk}_px.csv${ver}`).then(r => r.ok ? r.text() : null),
  ]).then(([F, csv]) => { if (F && csv) render(F, parse(csv)); }).catch(() => {});

  function parse(t) {
    return t.trim().split("\n").slice(1).map(l => { const [d, a, h, fx] = l.split(","); return { d, a: a ? +a : null, h: h ? +h : null, fx: fx ? +fx : null }; });
  }

  function render(F, P) {
    // «главная» линия: H (HKD) для пар A+H, иначе A (юани, курс = 1)
    const hasH = !!F.h_code, cur = hasH ? "HK$" : "¥";
    const M = p => hasH ? p.h : p.a, FX = p => hasH ? p.fx : 1;
    const last = [...P].reverse().find(p => M(p) != null && FX(p)) || P[P.length - 1];
    const lastA = [...P].reverse().find(p => p.a != null);
    const fx = FX(last), sh = F.shares_mn, cls = ["A", "H", "D"].filter(k => sh[k]), shTot = cls.reduce((t, k) => t + sh[k], 0) * 1e6;
    const year = P.filter(p => M(p) != null && p.d > iso(addDays(last.d, -365)));
    const hi = Math.max(...year.map(M)), lo = Math.min(...year.map(M));
    const prevM = [...P].reverse().filter(p => M(p) != null)[1];
    const px = M(last), prev = prevM ? M(prevM) : px;
    const mcapH = shTot * px * fx / 1e9;               // млрд юаней по главной цене
    const pe = mcapH / F.ttm.net;
    const div12 = F.dividends.filter(d => d.ex_date_a && d.ex_date_a > last.d.replace(/-/g, "").replace(/^(\d{4})/, y => y - 1)).reduce((s, d) => s + d.dps_cny, 0);
    const yldH = div12 / (px * fx) * 100;
    const prem = hasH && lastA && lastA.a ? (lastA.a / (px * fx) - 1) * 100 : null;
    const ncps = F.net_cash ? F.net_cash.value * 1e9 / shTot / fx : null;   // на акцию в валюте главной линии
    const peX = F.net_cash ? (mcapH - F.net_cash.value) / (F.ttm.net - (F.net_cash.interest_after_tax || 0)) : null;   // прибыль без процентов на деньги

    box.hidden = false;
    box.className = "panel term";
    box.innerHTML = `
      <div class="term-head">
        <div><div class="eyebrow">${hasH ? esc(F.h_code) + " · SEHK · HKD" : esc(F.a_code) + (F.a_code.endsWith("SZ") ? " · SZSE" : " · SSE") + " · юани"}</div>
          <div class="term-px"><b class="num">${nf(px, 2)}</b> <span class="up ${px >= prev ? "pos" : "neg"}">${pct((px / prev - 1) * 100, 2)}</span></div>
          <div class="note">закрытие ${dRu(last.d)}${hasH ? ` · A ${esc(F.a_code)}: ${nf(lastA?.a, 2)} юаня (${dRu(lastA?.d)})` : ""}</div></div>
        <div class="term-range"><div class="note">52 недели (закрытия)</div>
          <div class="rng"><span class="num">${nf(lo, 2)}</span><i><em style="left:${hi > lo ? (px - lo) / (hi - lo) * 100 : 50}%"></em></i><span class="num">${nf(hi, 2)}</span></div></div>
      </div>
      <div class="term-stats">
        ${stat(hasH ? "Капитализация по H" : "Капитализация", nf(mcapH, 1) + " млрд ¥", `(${cls.map(k => k + " " + nf(sh[k], 1)).join(" + ")}) млн акций на ${sh.date} × ${cur}${nf(px, 2)}${hasH ? " × " + nf(fx, 4) : ""}`)}
        ${stat("P/E за 12 мес.", nf(pe, 1), `прибыль ${nf(F.ttm.net, 2)} млрд ¥ до ${F.ttm.as_of}`)}
        ${peX != null ? stat("P/E без чистых денег", nf(peX, 1), `(кап. − чистые деньги ${nf(F.net_cash.value, 2)} млрд ¥ на ${F.net_cash.date}) / (прибыль − чистый процентный доход после налога ${nf(F.net_cash.interest_after_tax || 0, 2)})`) : ""}
        ${stat("Дивиденды за 12 мес.", nf(div12, 2) + " ¥", `доходность${hasH ? " по H" : ""} ${nf(yldH, 1)}% до налога, ${nf(yldH * .9, 1)}% после 10%${hasH ? "; юани пересчитаны по текущему курсу (H платят в HKD по курсу объявления — фактическая доходность может отличаться)" : ""}`)}
        ${ncps != null ? stat("Чистые деньги на акцию", cur + nf(ncps, 1), `${nf(ncps / px * 100, 0)}% цены${hasH ? " H" : ""}`) : ""}
        ${prem != null ? stat("Премия A к H", pct(prem, 0), "A стоит дороже H на эту долю") : ""}
      </div>
      <div class="term-ctl">
        <div class="seg sm" id="t-rng">${["1М", "6М", "1Г", "3Г", "Всё"].map((x, i) => `<button type="button" data-r="${[31, 183, 366, 1096, 1e5][i]}"${i == 2 ? ' aria-pressed="true"' : ""}>${x}</button>`).join("")}</div>
        ${hasH ? '<div class="seg sm" id="t-mode"><button type="button" data-m="px" aria-pressed="true">Цена H и A</button><button type="button" data-m="prem">Премия A/H</button></div>' : ""}
      </div>
      <div class="term-chart" id="t-chart"></div>
      <div class="legend" id="t-leg"></div>
      <p class="note">Цена: ${hasH ? `H — ${esc(F.sources.px_h)}; A — ${esc(F.sources.px_a)}; A пересчитана в HKD по курсу ${esc(F.sources.fx)}` : `A — ${esc(F.sources.px_a)}`} [В]. ▲ — даты отсечки дивидендов (A).${F.net_cash ? " Как посчитаны чистые деньги: " + esc(F.net_cash.text) : ""}</p>

      <div class="term-tabs" role="tablist" id="t-tabs">${[["pl", "Прибыль"], ["cf", "Деньги"], ["bs", "Баланс"], ["dv", "Дивиденды"], ["sg", "Сегменты"]].filter(t => t[0] !== "sg" || (F.segments && F.segments.items)).map(([k, n], i) => `<button type="button" role="tab" data-t="${k}"${i == 0 ? ' aria-selected="true"' : ""}>${n}</button>`).join("")}</div>
      <div class="term-ctl"><div class="seg sm" id="t-per"><button type="button" data-p="y" aria-pressed="true">По годам</button><button type="button" data-p="q">По кварталам</button></div><span class="note" id="t-hint">Нажмите строку — график покажет её.</span></div>
      <div class="term-bars" id="t-bars"></div>
      <div class="tbl term-tbl" id="t-tbl"></div>
      <p class="note" id="t-src"></p>
      <div class="dvs" id="t-story" hidden></div>`;

    // ---------- график цены ----------
    let range = 366, mode = "px";
    const drawPx = () => {
      const from = iso(addDays(last.d, -range));
      const S = P.filter(p => p.d >= from);
      const ser = !hasH ? [{ k: "a", name: "A, юани", col: "var(--red)", v: S.map(p => p.a) }]
        : mode === "px"
        ? [{ k: "h", name: "H, HKD", col: "var(--red)", v: S.map(p => p.h) }, { k: "a", name: "A в HKD", col: "var(--steel)", v: S.map(p => p.a != null && p.fx ? p.a / p.fx : null) }]
        : [{ k: "p", name: "Премия A к H, %", col: "var(--ore)", v: S.map(p => p.a != null && p.h != null && p.fx ? (p.a / (p.h * p.fx) - 1) * 100 : null) }];
      const ex = mode === "px" ? F.dividends.map(d => d.ex_date_a && `${d.ex_date_a.slice(0, 4)}-${d.ex_date_a.slice(4, 6)}-${d.ex_date_a.slice(6)}`).filter(d => d && d >= from) : [];
      line("t-chart", S.map(p => p.d), ser, ex, mode === "px" ? 2 : 0, mode === "px" ? "" : "%");
      document.getElementById("t-leg").innerHTML = ser.map(s => `<span><i style="background:${s.col}"></i>${s.name}</span>`).join("");
    };
    seg("t-rng", b => { range = +b.dataset.r; drawPx(); });
    if (hasH) seg("t-mode", b => { mode = b.dataset.m; drawPx(); });
    drawPx();

    // ---------- отчётность ----------
    const A = F.annual, Q = F.quarterly;
    const ttmCol = { revenue: F.ttm.revenue, net: F.ttm.net, net_dedt: F.ttm.net_dedt, ocf: F.ttm.ocf, capex: F.ttm.capex, fcf: F.ttm.ocf - F.ttm.capex };
    const TABS = {
      pl: [["revenue", "Выручка", 2], ["gross_profit", "Валовая прибыль", 2], ["gm", "Валовая маржа, %", 1, "%"], ["rd", "Расходы на R&D", 2], ["op_profit", "Операционная прибыль", 2],
           ["net", "Чистая прибыль акционерам", 2], ["net_dedt", "То же без разовых статей", 2], ["nm", "Чистая маржа, %", 1, "%"], ["eps", "Прибыль на акцию, ¥", 2, "¥"], ["roe", "ROE, %", 1, "%"]],
      cf: [["ocf", "Операционный денежный поток", 2], ["capex", "Капзатраты", 2], ["fcf", "Свободный денежный поток", 2], ["div_paid", "Выплачено дивидендов и процентов", 2]],
      bs: [["cash", "Денежные средства + торговые фин. активы", 2], ["deposits", "Внеоборотные к погашению + прочие внеоборотные (в основном срочные вклады)", 2], ["debt", "Процентный долг", 2],
           ["receivables", "Дебиторка (с векселями)", 2], ["inventories", "Запасы", 2], ["assets", "Активы", 2], ["equity", "Капитал акционеров", 2], ["bps", "Капитал на акцию, ¥", 2, "¥"]],
      dv: [["dps", "Дивиденд на акцию за год, ¥", 2, "¥"], ["div_total", "Всего начислено", 3], ["payout", "Доля прибыли, %", 0, "%"]],
    };
    const QOK = { revenue: 1, gross_profit: 1, gm: 1, net: 1, net_dedt: 1, ocf: 1, capex: 1, cash: 1, deposits: 1, receivables: 1 };
    let tab = "pl", per = "y", sel = { pl: "revenue", cf: "ocf", bs: "cash", dv: "dps", sg: "revenue" };
    const drawTab = () => {
      const tblEl = document.getElementById("t-tbl"), bars = document.getElementById("t-bars"), src = document.getElementById("t-src");
      document.getElementById("t-per").style.display = tab === "sg" || tab === "dv" ? "none" : "";
      drawStory();
      if (tab === "sg") return drawSeg();
      const isQ = per === "q" && tab !== "dv";
      const rows = TABS[tab].filter(r => !isQ || QOK[r[0]]);
      if (!rows.find(r => r[0] === sel[tab])) sel[tab] = rows[0][0];
      // во вкладке «Дивиденды» — только годы, где есть данные
      const from = tab === "dv" ? Math.max(0, A.lines.dps.findIndex(x => x != null)) : 0;
      const cols = isQ ? Q.labels.slice(-12) : A.years.map(String).slice(from);
      const get = k => isQ ? (Q.lines[k] || []).slice(-12) : (A.lines[k] || []).slice(from);
      const showTTM = !isQ && tab !== "bs" && tab !== "dv";
      tblEl.innerHTML = `<table><thead><tr><th>${isQ ? "Квартал" : "Год"}, ${esc(F.unit)}</th>${cols.map(c => `<th>${c.replace(" ", "<br>")}</th>`).join("")}${showTTM ? `<th>12 мес.<br>${F.ttm.as_of.slice(3)}</th>` : ""}</tr></thead><tbody>${
        rows.map(([k, n, d, u]) => `<tr data-k="${k}"${k === sel[tab] ? ' class="on"' : ""}><td>${esc(n)}</td>${get(k).map(x => `<td class="num${x < 0 ? " neg" : ""}">${nf(x, d)}</td>`).join("")}${showTTM ? `<td class="num">${k in ttmCol ? nf(ttmCol[k], d) : ""}</td>` : ""}</tr>`).join("")}</tbody></table>`;
      tblEl.querySelectorAll("tbody tr").forEach(tr => tr.onclick = () => { sel[tab] = tr.dataset.k; drawTab(); });
      tblEl.scrollLeft = tblEl.scrollWidth;   // последние периоды видны сразу
      const r = rows.find(r => r[0] === sel[tab]);
      bar(bars, cols, get(r[0]), r[1] + (r[3] ? "" : `, ${F.unit}`), r[2]);
      src.textContent = tab === "dv"
        ? `${F.sources.div}.${F.div_note ? " " + F.div_note : ""} Последние выплаты по дате отсечки: ` + F.dividends.slice(-8).map(d => `${d.period} — ${nf(d.dps_cny, 2)} ¥ (${nf(d.total_bn, 2)} млрд)`).join("; ") + "."
        : `${F.sources.fin}. Квартал = разность накопленных итогов. ${tab === "bs" ? "Строка «денежные средства» баланса не видит депозиты в прочих статьях — см. отдельную строку; чистые деньги по примечаниям — " + nf(F.net_cash.value, 2) + " млрд на " + F.net_cash.date + "." : ""}`;
    };
    // «Чья дочка и почему так платят» — только во вкладке «Дивиденды», если раздел заполнен
    const drawStory = () => {
      const el = document.getElementById("t-story"), S = F.div_story;
      el.hidden = !(S && tab === "dv");
      if (el.hidden || el.dataset.done) return;
      const mx = Math.max(...S.cmp.rows.flatMap(r => r[1]));
      el.innerHTML = `<h3>${esc(S.title)}</h3>
        <ol class="dvs-chain">${S.chain.map(c => `<li><b>${esc(c.n)}</b><span>${esc(c.d)}</span></li>`).join("")}</ol>
        <p class="note">${esc(S.chain_src)}</p>
        <div class="dvs-cmp" role="table" aria-label="Доля прибыли, выплаченная дивидендами">
          <div class="dvs-row dvs-head" role="row"><span role="columnheader"></span>${S.cmp.years.map(y => `<span role="columnheader">${y}</span>`).join("")}</div>
          ${S.cmp.rows.map((r, j) => `<div class="dvs-row" role="row"><span role="rowheader">${esc(r[0])}</span>${r[1].map(v => `<span role="cell"><i style="height:${v / mx * 100}%;background:${j ? "var(--steel)" : "var(--red)"}"></i><b class="num">${v}%</b></span>`).join("")}</div>`).join("")}
        </div>
        <p class="note">${esc(S.cmp.src)}</p>
        <p>${esc(S.history)}</p>
        <ul class="dvs-list">${S.why.map(w => `<li><b>${esc(w.t)}.</b> ${esc(w.d)} <span class="note">${esc(w.src)}</span></li>`).join("")}</ul>
        <h3>${esc(S.minor_title)}</h3>
        <p>${esc(S.minor_lead)}</p>
        <ul class="dvs-list">${S.minor.map(w => `<li><b>${esc(w.t)}.</b> ${esc(w.d)} <span class="note">${esc(w.src)}</span></li>`).join("")}</ul>
        <p class="dvs-verdict">${esc(S.verdict)}</p>`;
      el.dataset.done = 1;
    };
    const drawSeg = () => {
      const S = F.segments; if (!S || !S.items) return;
      const ann = S.periods.map((p, i) => [p, i]).filter(([p]) => !/H/.test(p));
      const k = sel.sg;
      document.getElementById("t-tbl").innerHTML = `<table><thead><tr><th>Сегмент, ${esc(S.unit)}</th>${S.periods.map(p => `<th>${p.replace("H1", "<br>1П")}</th>`).join("")}</tr></thead><tbody>${
        ["revenue", "gross_profit"].map(m => `<tr class="grp"><td colspan="${S.periods.length + 1}">${m === "revenue" ? "Выручка" : "Валовая прибыль"}</td></tr>` + S.items.map(it => `<tr data-k="${m}"${m === k ? ' class="on"' : ""}><td>${esc(it.name)}</td>${it[m].map(x => `<td class="num">${nf(x, 2)}</td>`).join("")}</tr>`).join("")).join("")}</tbody></table>`;
      document.getElementById("t-tbl").querySelectorAll("tbody tr[data-k]").forEach(tr => tr.onclick = () => { sel.sg = tr.dataset.k; drawSeg(); });
      stack(document.getElementById("t-bars"), ann.map(a => a[0]), S.items.map((it, j) => ({ name: it.name, col: ["var(--steel)", "var(--ore)", "var(--line)"][j] || "var(--muted)", v: ann.map(a => it[k][a[1]]) })), (k === "revenue" ? "Выручка" : "Валовая прибыль") + " по сегментам за год, " + S.unit);
      document.getElementById("t-src").textContent = S.src + ". Полугодия (1П) — в таблице.";
    };
    seg("t-per", b => { per = b.dataset.p; drawTab(); });
    document.getElementById("t-tabs").querySelectorAll("button").forEach(b => b.onclick = () => {
      document.getElementById("t-tabs").querySelectorAll("button").forEach(x => x.removeAttribute("aria-selected")); b.setAttribute("aria-selected", "true"); tab = b.dataset.t; drawTab(); });
    drawTab();
    let rt; window.addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(() => { drawPx(); drawTab(); }, 200); });
  }

  // ---------- вспомогательные ----------
  function stat(n, v, sub) { return `<div class="ts"><span>${esc(n)}</span><b class="num">${v}</b><em>${esc(sub)}</em></div>`; }
  function seg(id, fn) { const g = document.getElementById(id); g.querySelectorAll("button").forEach(b => b.onclick = () => { g.querySelectorAll("button").forEach(x => x.removeAttribute("aria-pressed")); b.setAttribute("aria-pressed", "true"); fn(b); }); }
  function addDays(s, n) { const d = new Date(s + "T00:00:00Z"); d.setUTCDate(d.getUTCDate() + n); return d; }
  function iso(d) { return d.toISOString().slice(0, 10); }
  function ticks(min, max, n = 4) { const st = Math.pow(10, Math.floor(Math.log10((max - min) / n || 1))); const step = [1, 2, 2.5, 5, 10].map(m => m * st).find(s => (max - min) / s <= n) || st * 10; const out = []; for (let v = Math.ceil(min / step) * step; v <= max + 1e-9; v += step) out.push(+v.toFixed(6)); return out; }

  function line(id, dates, ser, marks, dec, unit) {
    const host = document.getElementById(id), W = Math.max(300, Math.round(host.clientWidth || 760)), H = W < 560 ? 230 : 280, pl = 8, pr = 46, pt = 12, pb = 24;
    const all = ser.flatMap(s => s.v).filter(v => v != null);
    if (!all.length) { host.textContent = "Нет данных за период"; return; }
    let mn = Math.min(...all), mx = Math.max(...all); const pad = (mx - mn) * .08 || 1; mn -= pad; mx += pad;
    const n = dates.length, x = i => pl + (n < 2 ? 0 : i / (n - 1)) * (W - pl - pr), y = v => pt + (1 - (v - mn) / (mx - mn)) * (H - pt - pb);
    const s = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": ser.map(s => s.name).join(", ") });
    ticks(mn, mx).forEach(t => { s.appendChild(el("line", { x1: pl, x2: W - pr, y1: y(t), y2: y(t), style: "stroke:var(--line)" })); s.appendChild(el("text", { x: W - pr + 6, y: y(t) + 4 }, nf(t, Math.abs(mx - mn) < 10 && dec ? 1 : 0) + unit)); });
    if (unit === "%" && mn < 0 && mx > 0) s.appendChild(el("line", { x1: pl, x2: W - pr, y1: y(0), y2: y(0), style: "stroke:var(--muted);stroke-dasharray:3 3" }));
    // подписи дат: начало, середина, конец
    (W < 560 ? [0, n - 1] : [0, Math.floor((n - 1) / 2), n - 1]).forEach((i, j, arr) => s.appendChild(el("text", { x: x(i), y: H - 6, "text-anchor": arr.length === 2 ? ["start", "end"][j] : ["start", "middle", "end"][j] }, dRu(dates[i]))));
    ser.forEach(se => {
      let d = "", pen = false;
      se.v.forEach((v, i) => { if (v == null) return;  // праздники бирж не совпадают — линию не рвём
 d += (pen ? "L" : "M") + x(i).toFixed(1) + " " + y(v).toFixed(1); pen = true; });
      s.appendChild(el("path", { d, fill: "none", style: `stroke:${se.col};stroke-width:2;stroke-linejoin:round` }));
      const li = se.v.map((v, i) => v != null ? i : -1).filter(i => i >= 0).pop();
      if (li != null) { s.appendChild(el("circle", { cx: x(li), cy: y(se.v[li]), r: 3.5, style: `fill:${se.col}` })); }
    });
    marks.forEach(m => { const i = dates.findIndex(d => d >= m); if (i >= 0) s.appendChild(el("path", { d: `M${x(i) - 5} ${H - pb} L${x(i) + 5} ${H - pb} L${x(i)} ${H - pb - 8}Z`, style: "fill:var(--good)" }, null)); });
    // перекрестие и подсказка
    const g = el("g", { style: "display:none" }), vl = el("line", { y1: pt, y2: H - pb, style: "stroke:var(--muted);stroke-dasharray:2 3" }); g.appendChild(vl);
    const dots = ser.map(se => { const c = el("circle", { r: 4, style: `fill:${se.col};stroke:var(--panel);stroke-width:2` }); g.appendChild(c); return c; });
    s.appendChild(g);
    const tip = document.createElement("div"); tip.className = "term-tip"; tip.hidden = true;
    const hit = el("rect", { x: pl, y: pt, width: W - pl - pr, height: H - pt - pb, style: "fill:transparent;cursor:crosshair" }); s.appendChild(hit);
    const move = ev => {
      const r = s.getBoundingClientRect(), cx = ((ev.touches ? ev.touches[0].clientX : ev.clientX) - r.left) / r.width * W;
      const i = Math.max(0, Math.min(n - 1, Math.round((cx - pl) / (W - pl - pr) * (n - 1))));
      g.style.display = ""; vl.setAttribute("x1", x(i)); vl.setAttribute("x2", x(i));
      ser.forEach((se, j) => { const v = se.v[i]; dots[j].style.display = v == null ? "none" : ""; if (v != null) { dots[j].setAttribute("cx", x(i)); dots[j].setAttribute("cy", y(v)); } });
      tip.hidden = false; tip.innerHTML = `<b>${dRu(dates[i])}</b>` + ser.map(se => `<span><i style="background:${se.col}"></i>${se.name}: <b class="num">${nf(se.v[i], dec)}${unit}</b></span>`).join("");
      const px = x(i) / W * r.width; tip.style.left = Math.min(Math.max(px - 80, 0), r.width - 170) + "px";
    };
    hit.addEventListener("mousemove", move); hit.addEventListener("touchmove", e => { move(e); }, { passive: true }); hit.addEventListener("touchstart", move, { passive: true });
    hit.addEventListener("mouseleave", () => { g.style.display = "none"; tip.hidden = true; });
    host.replaceChildren(s, tip);
  }

  function bar(host, labels, vals, title, dec) {
    const W = Math.max(300, Math.round(host.clientWidth || 760)), H = W < 560 ? 190 : 210, pt = 26, pb = 30, n = labels.length, slot = W / n, bw = Math.min(46, slot * .62), every = Math.ceil(n / Math.floor(W / 44));
    const v = vals.map(x => x == null ? null : x), ok = v.filter(x => x != null);
    const mx = Math.max(0, ...ok), mn = Math.min(0, ...ok), span = (mx - mn) || 1;
    const y = val => pt + (mx - val) / span * (H - pt - pb);
    const s = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": title });
    s.appendChild(el("text", { x: 0, y: 12, class: "lbl" }, title));
    s.appendChild(el("line", { x1: 0, x2: W, y1: y(0), y2: y(0), style: "stroke:var(--line)" }));
    v.forEach((val, i) => {
      const cx = slot * i + slot / 2;
      if (val != null) {
        s.appendChild(el("rect", { x: cx - bw / 2, y: Math.min(y(val), y(0)), width: bw, height: Math.max(1, Math.abs(y(val) - y(0))), rx: 2, style: `fill:${val < 0 ? "var(--bad)" : i === n - 1 ? "var(--red)" : "var(--steel)"}` }));
        if ((n - 1 - i) % every === 0) s.appendChild(el("text", { x: cx, y: val >= 0 ? y(val) - 5 : y(val) + 12, "text-anchor": "middle", class: "lbl" }, nf(val, dec)));
      }
      const lb = labels[i]; if ((n - 1 - i) % every === 0) s.appendChild(el("text", { x: cx, y: H - 8, "text-anchor": "middle" }, /Q/.test(lb) ? lb.replace(/^20(\d\d) /, "$1 ") : (W < 560 && n > 6 ? "’" + lb.slice(2) : lb)));
    });
    host.replaceChildren(s);
  }

  function stack(host, labels, ser, title) {
    const W = Math.max(300, Math.round(host.clientWidth || 760)), H = 220, pt = 26, pb = 26, n = labels.length, slot = W / n, bw = Math.min(54, slot * .6);
    const tot = i => ser.reduce((t, s) => t + (s.v[i] || 0), 0), mx = Math.max(...labels.map((_, i) => tot(i))) * 1.12 || 1;
    const y = v => H - pb - v / mx * (H - pt - pb);
    const s = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": title });
    s.appendChild(el("text", { x: 0, y: 12, class: "lbl" }, title));
    labels.forEach((lb, i) => {
      const x0 = slot * i + (slot - bw) / 2; let b = 0;
      ser.forEach(se => { const v = se.v[i] || 0; s.appendChild(el("rect", { x: x0, y: y(b + v), width: bw, height: Math.max(0, y(b) - y(b + v)), rx: 2, style: `fill:${se.col}` })); b += v; });
      s.appendChild(el("text", { x: x0 + bw / 2, y: y(b) - 5, "text-anchor": "middle", class: "lbl" }, nf(b, 1)));
      s.appendChild(el("text", { x: x0 + bw / 2, y: H - 8, "text-anchor": "middle" }, lb));
    });
    host.replaceChildren(s);
    const lg = document.createElement("div"); lg.className = "legend"; lg.innerHTML = ser.map(se => `<span><i style="background:${se.col}"></i>${esc(se.name)}</span>`).join(""); host.appendChild(lg);
  }
})();
