/* Плашка «вышел отчёт новее разбора»: /data/latest.json собирает idx-disclosures/scripts/site_results.py
   (IDX — xlsx биржи, Китай — таблица основных показателей отчёта cninfo). Ставится под карточками #kpis. */
(function () {
  const seg = location.pathname.split("/").filter(Boolean)[0];
  if (!seg) return;
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const dd = s => s ? s.split("-").reverse().join(".") : "";
  fetch(`/data/latest.json?v=${Date.now() / 36e5 | 0}`).then(r => r.ok ? r.json() : null).then(L => {
    if (!L || !L.companies) return;
    const key = Object.keys(L.companies).find(k => k.toLowerCase() === seg.toLowerCase());
    const x = key && L.companies[key];
    if (!x || !x.newer) return;
    const put = () => {
      const at = document.getElementById("kpis");
      if (!at || document.getElementById("fresh-report")) return !!at;
      at.insertAdjacentHTML("afterend", `<div id="fresh-report" class="fresh"><b>Вышел отчёт за ${esc(x.period)} (${dd(x.date)})</b> — разбор ниже от ${dd(x.review)}, вывод ещё не пересмотрен.` +
        (x.lines && x.lines.length ? `<ul>${x.lines.map(l => `<li>${esc(l)}</li>`).join("")}</ul>` : "") +
        `<span class="note"><a href="${esc(x.url)}" target="_blank" rel="noopener">Отчёт</a> · ${esc(x.src || "")}</span></div>`);
      return true;
    };
    if (!put()) new MutationObserver((m, o) => { if (put()) o.disconnect(); }).observe(document.body, { childList: true, subtree: true });
  }).catch(() => {});
})();
