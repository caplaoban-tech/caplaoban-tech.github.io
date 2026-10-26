// Страницы-вопросы компании (сейчас — 3898): шапка с ценой, рельс вопросов, навигация, форматирование.
// Модель и словарь — из /assets/company.js (событие cl:ready); вопросы и материалы вне модели — /data/<тикер>_lab.json.
// Ссылки относительные: набор страниц можно переносить в другую папку без правок.
export const fmt = (v, d = 1) => Number(v).toLocaleString("ru-RU", {minimumFractionDigits: d, maximumFractionDigits: d}).replace(/ /g, " ");
export const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
export const $ = id => document.getElementById(id);
export const arrow = '<svg class="go" viewBox="0 0 28 28" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 14h15M15 8l6 6-6 6"/></svg>';

// модель страницы компании: ждём company.js
export const model = () => window.CL ? Promise.resolve(window.CL) : new Promise(r => document.addEventListener("cl:ready", e => r(e.detail), {once: true}));

export async function boot(current) {
  const tk = document.body.dataset.file.replace(/\.json$/, "");
  const L = await (await fetch(`/data/${tk}_lab.json?v=${Date.now() / 36e5 | 0}`)).json();
  const root = current ? "../" : "./";
  // последнее закрытие — из той же истории цен, что дописывает робот; если её нет — цена разбора
  let p = {h: L.price.h, a: L.price.a, fx: L.price.fx, date: L.price.date};
  try {
    const csv = await (await fetch(`/data/history/${tk}_px.csv?v=${Date.now() / 36e5 | 0}`)).text();
    const r = csv.trim().split("\n").slice(1).map(l => l.split(",")).reverse().find(c => c[1] && c[2] && c[3]);
    if (r) p = {date: r[0], a: +r[1], h: +r[2], fx: +r[3]};
  } catch (e) {}
  const dt = p.date.split("-").reverse().slice(0, 2).join(".");
  const prem = (p.a / (p.h * p.fx) - 1) * 100;
  $("tape").innerHTML = `<div class="tape-in"><a class="brand" href="/" aria-label="Cap Laoban — главная"><img src="/assets/mark.svg" alt=""><span>Cap Laoban</span></a>
    <a class="tk" href="${root}">${esc(tk)} · H <b>HK$${fmt(p.h, 2)}</b><span class="wide"> · A ¥${fmt(p.a, 2)} · премия A/H ${fmt(prem, 0)}%</span> · ${dt}</a>
    <a class="full" href="${root}data/"${current === "data" ? ' aria-current="page"' : ""}>Цифры</a></div>`;
  const qs = L.questions, i = qs.findIndex(q => q.id === current);
  if ($("rail")) $("rail").innerHTML = qs.map((q, k) => `<a href="${root}${q.url}"${k === i ? ' aria-current="page"' : ""}${k < i ? ' class="done"' : ""}><i></i><span>${esc(q.q)}</span></a>`).join("");
  let title = null;
  if ($("qhead") && i >= 0) {
    $("qhead").innerHTML = `<span class="qn">Вопрос ${i + 1} из ${qs.length}</span><h1>${esc(qs[i].q)}</h1><p class="lead">${esc(qs[i].a)}</p>`;
    title = `${qs[i].q} — ${tk} · Cap Laoban`;
  }
  if ($("pager")) {
    const prev = i > 0 ? {url: root + qs[i - 1].url, q: qs[i - 1].q} : {url: root, q: "Все вопросы"};
    const next = i >= 0 && i < qs.length - 1 ? {url: root + qs[i + 1].url, q: qs[i + 1].q} : {url: root + "data/", q: "Цифры: цена, отчётность, дивиденды"};
    $("pager").innerHTML = (current === "data" ? `<a href="${root}"><small>← к вопросам</small>Все вопросы</a>` : `<a href="${prev.url}"><small>← назад</small>${esc(prev.q)}</a><a class="next" href="${next.url}"><small>дальше →</small>${esc(next.q)}</a>`);
  }
  // company.js ставит своё название вкладки — возвращаем название вопроса
  if (title) { document.title = title; model().then(() => { document.title = title; }); }
  return L;
}

// плавная смена числа
export function tween(el, to, d = 1, pre = "", post = "") {
  const from = parseFloat(el.dataset.v ?? to), t0 = performance.now(), dur = matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 450;
  el.dataset.v = to;
  const step = now => {
    const k = dur ? Math.min(1, (now - t0) / dur) : 1, e = 1 - Math.pow(1 - k, 4);
    el.textContent = pre + fmt(from + (to - from) * e, d) + post;
    if (k < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}
