// Мини-сайт 3898: общая шапка, рельс вопросов, навигация, форматирование. Данные — /data/3898_lab.json.
export const fmt = (v, d = 1) => Number(v).toLocaleString("ru-RU", {minimumFractionDigits: d, maximumFractionDigits: d}).replace(/ /g, " ");
export const esc = s => String(s).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
export const $ = id => document.getElementById(id);
const ARROW = '<svg class="go" viewBox="0 0 28 28" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 14h15M15 8l6 6-6 6"/></svg>';
export const arrow = ARROW;

export async function boot(current) {
  const D = await (await fetch("/data/3898_lab.json", {cache: "no-cache"})).json();
  const p = D.price, dt = p.date.split("-").reverse().slice(0, 2).join(".");
  const prem = (p.a / (p.h * p.fx) - 1) * 100;
  $("tape").innerHTML = `<div class="tape-in"><a class="brand" href="/" aria-label="Cap Laoban"><img src="/assets/mark.svg" alt=""><span>Cap Laoban</span></a>
    <span class="tk">3898 · H <b>HK$${fmt(p.h, 2)}</b><span class="wide"> · A ¥${fmt(p.a, 2)} · премия A/H ${fmt(prem, 0)}%</span> · ${dt}</span>
    <a class="full" href="/3898/">Полный разбор</a></div>`;
  const qs = D.questions, i = qs.findIndex(q => q.id === current);
  if ($("rail")) $("rail").innerHTML = qs.map((q, k) => `<a href="${q.url}"${k === i ? ' aria-current="page"' : ""}${k < i ? ' class="done"' : ""}><i></i><span>${esc(q.q)}</span></a>`).join("");
  if ($("qhead") && i >= 0) {
    $("qhead").innerHTML = `<span class="qn">Вопрос ${i + 1} из ${qs.length}</span><h1>${esc(qs[i].q)}</h1><p class="lead">${esc(qs[i].a)}</p>`;
    document.title = `${qs[i].q} — 3898 · Cap Laoban`;
  }
  if ($("pager") && i >= 0) {
    const prev = i > 0 ? qs[i - 1] : {url: "./", q: "Все вопросы"}, next = qs[i + 1];
    $("pager").innerHTML = `<a href="${prev.url}"><small>← назад</small>${esc(prev.q)}</a>` + (next ? `<a class="next" href="${next.url}"><small>дальше →</small>${esc(next.q)}</a>` : `<a class="next" href="/3898/"><small>дальше →</small>Полный разбор с калькулятором</a>`);
  }
  return D;
}

// плавное появление числа без скачков
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
