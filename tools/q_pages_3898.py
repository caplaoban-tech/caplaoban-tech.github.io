# Сборщик страниц-вопросов 3898 (обложка + chips/parts/market/peers/risks/data). Запуск: python3 tools/q_pages_3898.py — пишет в 3898/lab/.
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1] / "3898" / "lab"
HEAD = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
{robots}<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="/assets/og.png">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@500;800&family=Golos+Text:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap">
<link rel="stylesheet" href="/assets/style.css?v=13">
<link rel="stylesheet" href="/assets/q.css?v=5">
</head>
<!-- Страница-вопрос 3898. Модель — data/3898.json (через /assets/company.js), прочее — data/3898_lab.json. Разметку блоков модели не переименовывать: id нужны company.js. -->
<body data-file="3898.json">
<div class="tape" id="tape"></div>
<div class="wrap">
{rail}  <main>
{body}
  </main>
  <footer class="bot foot">
    <span id="sources"></span>
    <span>Метки: [А] — цифра из отчётности, [Б] — расчёт, [В] — внешний источник или оценка. Модель — инструмент «что если», не прогноз и не индивидуальная инвестиционная рекомендация.</span>
  </footer>
</div>
<div class="pop" id="pop" role="dialog" aria-modal="false" hidden><button type="button" class="pop-x" id="pop-x" aria-label="Закрыть">×</button><b id="pop-t"></b><p id="pop-d"></p></div>
<script src="/assets/company.js?v=1" defer></script>
{extra}<script type="module">
{script}
</script>
</body>
</html>
"""
RAIL = '  <nav class="rail" id="rail" aria-label="Вопросы"></nav>\n'
PAGER = '    <nav class="pager" id="pager" aria-label="Соседние страницы"></nav>'
ROBOTS = '<meta name="robots" content="noindex, nofollow">\n'

def page(path, title, desc, body, script, rail=True, extra=""):
    f = ROOT / path / "index.html" if path else ROOT / "index.html"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(HEAD.format(robots=ROBOTS, title=title, desc=desc, rail=RAIL if rail else "", body=body, script=script.strip(), extra=extra))

# ---------------- обложка ----------------
page("", "CRRC Times Electric (3898): железная дорога платит за полупроводники — Cap Laoban",
 "CRRC Times Electric (HKEX 3898 / SSE 688187) в пяти вопросах: что за силовые чипы, из чего складывается цена H, дёшево ли H на самом деле, аналоги и листинг дочки, что сломает тезис. Оценка по частям, премия A/H, риск-гейт, калькулятор.",
"""    <section class="cover">
      <h1 id="c-title">CRRC Times Electric</h1>
      <p class="lead" id="c-lead"></p>
      <div class="cover-px">
        <span class="big num" id="price">—</span>
        <span class="muted" id="price-note"></span>
      </div>
      <div class="cover-vd"><span class="chip mute" id="verdict">—</span><span class="note" id="verdict-detail"></span></div>
    </section>
    <section class="kpis" id="kpis" aria-label="Ключевые цифры"></section>
    <section class="panel" aria-label="Справедливая цена">
      <h2>Сколько стоит</h2>
      <div class="fv" id="fv" role="img" aria-label="Шкала справедливой цены"></div>
      <p class="note" id="fv-note"></p>
      <a class="more" href="market/">Как посчитано и калькулятор →</a>
    </section>
    <ol class="qlist" id="qlist" aria-label="Вопросы"></ol>
    <a class="qdata" href="data/"><span><b>Цифры</b>Цена A и H, отчётность по годам и кварталам, дивиденды и почему они такие, словарь</span><svg viewBox="0 0 28 28" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 14h15M15 8l6 6-6 6"/></svg></a>""",
"""import {boot, esc, arrow, $} from "/assets/q.js?v=5";
const L = await boot("");
$("c-title").textContent = L.cover.title; $("c-lead").textContent = L.cover.lead;
document.title = `${L.ticker} CRRC Times Electric: ${L.cover.title.toLowerCase()} — Cap Laoban`;
$("qlist").innerHTML = L.questions.map((q, k) => `<li><a href="${q.url}"><span class="n">${k + 1}</span><span class="t">${esc(q.q)}</span>${arrow}<span class="a">${esc(q.a)}</span></a></li>`).join("");""", rail=False)

# ---------------- 1. чипы ----------------
page("chips", "Что это за чипы и при чём тут ИИ — 3898 · Cap Laoban", "Силовые полупроводники CRRC Times Electric: путь тока от сети до колеса, IGBT и SiC, Times Semiconductor, связь с ИИ.",
"""    <header class="qhead" id="qhead"></header>
    <section class="sec" aria-labelledby="h-path">
      <h2 id="h-path">Путь тока: от сети до колеса</h2>
      <p class="prose">Компания стоит на трёх участках этого пути из четырёх. Нажмите на станцию — она подсветится.</p>
      <div class="wirebox"><div class="flow" aria-hidden="true"><i></i><i></i><i></i></div><ol class="wire" id="wire"></ol></div>
      <p class="src" id="path-src"></p>
    </section>
    <section class="sec" aria-labelledby="h-pwm">
      <h2 id="h-pwm">Как ключ делает ток</h2>
      <div class="prose"><p>IGBT умеет только «включено» и «выключено». Если переключать его достаточно часто и менять ширину импульсов, мотор «видит» плавную синусоиду: обмотка сглаживает рывки. Чем чаще переключения, тем ровнее ток и тем горячее чип. Поэтому важны потери на переключение — главный параметр, по которому соревнуются производители.</p></div>
      <div class="panel pwm">
        <div class="ctl">
          <label for="pwm-n">Переключений за период <output id="pwm-o">12</output></label>
          <input type="range" id="pwm-n" min="3" max="40" step="1" value="12">
        </div>
        <svg id="pwm-svg" viewBox="0 0 340 150" role="img" aria-label="Импульсы ключа и ток, который видит мотор"></svg>
        <div class="key"><span><i style="background:var(--steel)"></i>импульсы ключа</span><span><i style="background:var(--ore)"></i>ток, который видит мотор</span><span><i class="dash"></i>идеальная синусоида</span></div>
        <p class="src">Иллюстрация принципа (широтно-импульсная модуляция), не данные компании [Б].</p>
      </div>
    </section>
    <section class="sec" aria-labelledby="h-prod">
      <h2 id="h-prod">Что именно выпускает Times Semiconductor</h2>
      <div class="prod" id="prod"></div>
      <p class="src" id="prod-src"></p>
    </section>
    <section class="sec" aria-labelledby="h-ts">
      <h2 id="h-ts">Выручка растёт, маржа падает втрое</h2>
      <div class="stack">
        <div class="panel" style="max-width:520px"><h3>Чистая маржа дочки</h3><div class="bars" id="bars"></div></div>
        <div class="panel"><div class="tbl"><table id="ts-tbl"></table></div></div>
      </div>
      <p class="prose" id="ts-why"></p>
      <p class="src" id="ts-src"></p>
    </section>
    <section class="sec" aria-labelledby="h-ai">
      <h2 id="h-ai">При чём тут ИИ</h2>
      <ul class="rk" id="ai"></ul>
    </section>
""" + PAGER,
r"""import {boot, esc, $} from "/assets/q.js?v=5";
const D = await boot("chips");
const ICON = {
  grid: '<path d="M12 2 7 22M12 2l5 20M5.5 7h13M8.6 13h6.8M7.4 18h9.2"/>',
  conv: '<rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="M6.5 12c1.4-4 3-4 4.5 0s3.1 4 4.5 0"/>',
  igbt: '<rect x="7" y="7" width="10" height="10" rx="1.5"/><path d="M10 2v5M14 2v5M10 17v5M14 17v5M2 10h5M2 14h5M17 10h5M17 14h5"/>',
  motor: '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="2"/><path d="M12 3.5V10M12 14v6.5M3.5 12H10M14 12h6.5"/>'
};
const AI = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="6" rx="1.5"/><rect x="3" y="14" width="18" height="6" rx="1.5"/><path d="M7 7h.01M7 17h.01"/></svg>';
const w = $("wire");
w.innerHTML = D.path.stations.map(s => `<li class="st" tabindex="0" data-id="${s.id}">
  <span class="node"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICON[s.id]}</svg></span>
  <h3>${esc(s.name)}</h3><p class="role">${esc(s.role)}</p>
  <div class="te"><b>${esc(s.fig)}</b><span>${esc(s.te)}</span><small>${esc(s.figk)}</small></div>
  ${s.ai ? `<p class="ai">${AI}<span>${esc(s.ai)}</span></p>` : ""}</li>`).join("");
$("path-src").textContent = D.path.note;
const sts = [...w.querySelectorAll(".st")];
const lite = el => sts.forEach(s => s.classList.toggle("lit", s === el));
sts.forEach(s => { s.addEventListener("click", () => lite(s)); s.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); lite(s); } }); });
const io = new IntersectionObserver(es => es.forEach(e => e.isIntersecting && lite(e.target)), {rootMargin: "-45% 0px -45% 0px"});
sts.forEach(s => io.observe(s));

// ШИМ: синус против пилы; среднее за период несущей — то, что «видит» мотор
const svg = $("pwm-svg"), X0 = 26, X1 = 334, Y0 = 75, A = 52;
function pwm(n) {
  const M = 900, xs = i => X0 + (X1 - X0) * i / M, ys = v => Y0 - v * A, per = M / n;
  const tri = i => { const ph = (i % per) / per; return ph < .5 ? 4 * ph - 1 : 3 - 4 * ph; };
  const out = i => Math.sin(2 * Math.PI * i / M) > tri(i) ? 1 : -1;
  let sq = `M${xs(0)},${ys(out(0))}`, ref = "", avg = "", last = out(0);
  for (let i = 0; i <= M; i++) {
    const o = out(i);
    if (o !== last) { sq += `L${xs(i).toFixed(1)},${ys(last)}L${xs(i).toFixed(1)},${ys(o)}`; last = o; }
    ref += (i ? "L" : "M") + xs(i).toFixed(1) + "," + ys(Math.sin(2 * Math.PI * i / M)).toFixed(1);
  }
  sq += `L${X1},${ys(last)}`;
  for (let j = 0; j <= 120; j++) {
    const c = j / 120, a0 = Math.round(Math.max(0, c - .5 / n) * M), a1 = Math.round(Math.min(1, c + .5 / n) * M);
    let s = 0; for (let i = a0; i <= a1; i++) s += out(i);
    avg += (j ? "L" : "M") + (X0 + (X1 - X0) * c).toFixed(1) + "," + ys(s / (a1 - a0 + 1)).toFixed(1);
  }
  svg.innerHTML = `<line x1="${X0}" x2="${X1}" y1="${Y0}" y2="${Y0}" stroke="var(--line)"/><text x="0" y="${Y0 - A + 4}">+U</text><text x="0" y="${Y0 + A + 4}">−U</text>
    <path d="${sq}" fill="none" stroke="var(--steel)" stroke-width="1.2" opacity=".75"/><path d="${ref}" fill="none" stroke="var(--ink)" stroke-width="1.2" stroke-dasharray="4 4"/><path d="${avg}" fill="none" stroke="var(--ore)" stroke-width="3" stroke-linejoin="round"/>`;
  $("pwm-o").textContent = n;
}
$("pwm-n").addEventListener("input", e => pwm(+e.target.value)); pwm(12);

$("prod").innerHTML = D.products.map(p => `<div><h3>${esc(p.name)}</h3><p>${esc(p.what)}</p><p>${esc(p.where)}</p><p class="s">${esc(p.status)}</p></div>`).join("");
$("prod-src").textContent = D.products_src;
const mx = Math.max(...D.ts.margin.map(m => m.v));
$("bars").innerHTML = D.ts.margin.map(m => `<div><b>${String(m.v).replace(".", ",")}%</b><i style="height:${m.v / mx * 100}%"></i><span>${m.l}</span></div>`).join("");
if (!matchMedia("(prefers-reduced-motion: reduce)").matches) {
  const bio = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.querySelectorAll("i").forEach((i, k) => i.animate([{transform: "scaleY(.04)"}, {transform: "scaleY(1)"}], {duration: 900, delay: k * 120, easing: "cubic-bezier(.16,1,.3,1)", fill: "backwards"})); bio.disconnect(); } }), {threshold: .4});
  bio.observe($("bars"));
}
$("ts-tbl").innerHTML = D.ts.rows.map((r, k) => `<tr>${r.map(c => k ? `<td>${esc(c)}</td>` : `<th>${esc(c)}</th>`).join("")}</tr>`).join("");
$("ts-why").textContent = D.ts.why; $("ts-src").textContent = D.ts.src;
$("ai").innerHTML = D.ai.map(a => `<li><h3>${esc(a.t)}</h3><p>${esc(a.d)}</p></li>`).join("");""")

# ---------------- 2. из чего цена ----------------
page("parts", "Из чего складывается цена акции — 3898 · Cap Laoban", "Цена H-акции CRRC Times Electric по частям: деньги, полупроводниковая дочка, железная дорога. Разберите акцию ползунками.",
"""    <header class="qhead" id="qhead"></header>
    <section class="sec" aria-labelledby="h-parts">
      <h2 id="h-parts">Разберите акцию сами</h2>
      <p class="prose">Слева — цена H, разложенная на то, что за неё получает покупатель. Справа — сумма частей по вашим допущениям. Двигайте ползунки и смотрите, сколько остаётся на железную дорогу.</p>
      <div class="split">
        <div class="stickbox stack">
          <div class="cols" id="cols"><div class="col" id="c-px"></div><div class="col" id="c-sum"></div></div>
          <div class="key"><span><i style="background:var(--steel)"></i>деньги минус долг</span><span><i style="background:var(--ore)"></i>Times Semiconductor, 77,86%</span><span><i style="background:var(--red)"></i>ж/д и прочее</span></div>
          <div class="verdict" aria-live="polite">Сумма частей <b class="num" id="v-sum">—</b> <span id="v-txt"></span></div>
        </div>
        <div class="stack">
          <div class="segbtn" id="preset" role="group" aria-label="Сценарий"></div>
          <div class="ctl">
            <span style="font-size:14px">Как оценить полупроводниковую дочку</span>
            <div class="segbtn" id="tsm" role="group" aria-label="Метод оценки дочки"></div>
            <p class="mnote" id="tsm-note"></p>
          </div>
          <div class="ctl">
            <label for="m">Сколько годовых прибылей платить за ж/д <output id="m-o"></output></label>
            <input type="range" id="m" min="4" max="14" step="0.5" value="8">
            <small>Прибыль ж/д и прочего после налога (NOPAT) — 3,2 млрд ¥ за 12 мес. [Б]. Alstom и CRRC торгуются за 9–22 прибыли [В].</small>
          </div>
          <div class="ctl">
            <label for="chg">Прибыль ж/д через год <output id="chg-o"></output></label>
            <input type="range" id="chg" min="-30" max="20" step="1" value="0">
            <small>−15% закупок поездов срезает прибыль ж/д на ~27% (рычаг постоянных расходов) [Б].</small>
          </div>
          <div class="ctl">
            <label for="ck">Сколько денег дойдёт до акционера <output id="ck-o"></output></label>
            <input type="range" id="ck" min="30" max="100" step="5" value="75">
            <small>Госкомпания платит 37% прибыли и остановила выкуп; 2 млрд — в финкомпании контролёра [А]. Почему так — во вкладке «Дивиденды» на странице <a href="../data/">«Цифры»</a>.</small>
          </div>
        </div>
      </div>
      <p class="src" id="src"></p>
    </section>
    <section class="sec" aria-labelledby="h-why">
      <h2 id="h-why">Почему дочку нельзя прибавлять к деньгам по цене раунда</h2>
      <div class="prose">
        <p>Инвесторы 2024 года заплатили за долю в Times Semiconductor живыми деньгами, и эти деньги лежат у дочки. Они уже входят в 15 млрд ¥ денег группы. Если оценить дочку по раунду и прибавить все деньги группы, часть денег посчитается дважды. Поэтому здесь из денег вычтена доля Times Electric в деньгах дочки: 1,5 млрд ¥ — это допущение, отчёт сумму не раскрывает.</p>
        <p>Это проверка другим методом. Основная модель — на странице <a href="../market/">«Дёшево ли H»</a>; на базовых допущениях проверка даёт на 7–10% меньше.</p>
      </div>
    </section>
""" + PAGER,
r"""import {boot, esc, fmt, tween, $} from "/assets/q.js?v=5";
const D = await boot("parts");
const P = D.parts, px = D.price.h, fx = D.price.fx, sh = D.shares_m, st = 0.7786;
const hk = bn => bn * 1000 / sh / fx;
const S = {tsm: "book", m: 8, chg: 0, ck: 75};
const PRE = [
  {id: "bear", name: "Медвежий", v: {tsm: "pe10", m: 6, chg: -27, ck: 50}},
  {id: "base", name: "Базовый", v: {tsm: "book", m: 8, chg: 0, ck: 75}},
  {id: "bull", name: "Бычий", v: {tsm: "round", m: 11, chg: 5, ck: 100}}];
$("preset").innerHTML = PRE.map(p => `<button type="button" data-p="${p.id}">${p.name}</button>`).join("");
$("tsm").innerHTML = P.ts_methods.map(t => `<button type="button" data-t="${t.id}">${esc(t.name)}</button>`).join("");
$("src").textContent = P.src;
const tsVal = id => ({pe10: 10 * P.ts_net, book: P.ts_book, round: P.ts_round, peers: P.ts_peer_pb * P.ts_book})[id];
for (const col of ["c-px", "c-sum"]) $(col).innerHTML = `<div class="cap"><span></span><small>${col === "c-px" ? "цена H, " + D.price.date.split("-").reverse().slice(0, 2).join(".") : "сумма частей"}</small></div>` + ["rail", "ts", "cash"].map(c => `<div class="pc pc-${c}"><span><em></em><b></b></span></div>`).join("");
const LBL = {rail: ["за ж/д", "ж/д"], ts: ["дочка", "дочка"], cash: ["деньги", "деньги"]};
function put(col, k, vals, total, H, capV, capTxt) {
  const c = $(col);
  c.querySelector(".cap").style.bottom = capV / total * H + "px";
  c.querySelector(".cap span").textContent = capTxt;
  for (const [cls, v] of Object.entries(vals)) {
    const el = c.querySelector(".pc-" + cls), h = Math.max(0, v) / total * H;
    el.style.height = h + "px";
    el.querySelector("span").style.visibility = h > 34 ? "visible" : "hidden";
    el.querySelector("em").textContent = LBL[cls][k];
    el.querySelector("b").textContent = fmt(v, 1);
  }
}
function draw() {
  const ck = S.ck / 100;
  const cash = hk(P.cash_avail * ck - P.debt - P.ts_cash_te * ck), ts = hk(tsVal(S.tsm) * st), rail = hk(P.rest_nopat * (1 + S.chg / 100) * S.m);
  const sum = cash + ts + rail, left = px - cash - ts, implied = left / hk(P.rest_nopat);
  const top = Math.max(sum, px) * 1.04, H = $("cols").clientHeight - 64;
  put("c-px", 0, {rail: Math.max(left, 0), ts: Math.min(ts, px - cash), cash: Math.min(cash, px)}, top, H, px, "HK$" + fmt(px, 2));
  put("c-sum", 1, {rail, ts, cash}, top, H, sum, "HK$" + fmt(sum, 1));
  const d = (sum / px - 1) * 100;
  tween($("v-sum"), sum, 1, "HK$");
  $("v-txt").innerHTML = left > 0
    ? `— на <b class="num">${fmt(Math.abs(d), 0)}%</b> ${d >= 0 ? "выше" : "ниже"} цены. За железную дорогу цена H платит <b class="num">${fmt(implied, 1)}</b> годовых прибылей, а вы бы заплатили ${fmt(S.m, 1)}.`
    : `. При такой оценке дочки и денег цена H меньше их суммы: ж/д достаётся бесплатно, и ещё остаётся <b class="num">HK$${fmt(-left, 1)}</b>. Рынок явно не верит в эту оценку дочки.`;
  $("m-o").textContent = fmt(S.m, 1); $("chg-o").textContent = (S.chg > 0 ? "+" : "") + S.chg + "%"; $("ck-o").textContent = S.ck + "%";
  $("m").value = S.m; $("chg").value = S.chg; $("ck").value = S.ck;
  document.querySelectorAll("#tsm button").forEach(b => b.setAttribute("aria-pressed", b.dataset.t === S.tsm));
  $("tsm-note").textContent = P.ts_methods.find(t => t.id === S.tsm).note;
  document.querySelectorAll("#preset button").forEach(b => { const p = PRE.find(x => x.id === b.dataset.p).v; b.setAttribute("aria-pressed", Object.keys(p).every(k => p[k] === S[k])); });
}
$("tsm").addEventListener("click", e => { const b = e.target.closest("button"); if (b) { S.tsm = b.dataset.t; draw(); } });
$("preset").addEventListener("click", e => { const b = e.target.closest("button"); if (b) { Object.assign(S, PRE.find(p => p.id === b.dataset.p).v); draw(); } });
for (const k of ["m", "chg", "ck"]) $(k).addEventListener("input", e => { S[k] = +e.target.value; draw(); });
addEventListener("resize", draw);
draw();""")

# ---------------- 3. рынок против модели + калькулятор ----------------
page("market", "Дёшево ли H на самом деле — 3898 · Cap Laoban", "Цена H и A CRRC Times Electric против справедливой стоимости: модель на прибыли и на деньгах, калькулятор оценки по частям, входы с источниками.",
"""    <header class="qhead" id="qhead"></header>
    <section class="sec" aria-labelledby="h-mk">
      <h2 id="h-mk">Рынок против модели</h2>
      <div class="plate" id="plate" aria-live="polite"><span class="lamp" aria-hidden="true"></span><p id="plate-t">Считаю модель…</p></div>
      <div class="panel">
        <div class="mhead">
          <div class="tabs" id="rng" role="group" aria-label="Период"><button type="button" data-r="1">1 год</button><button type="button" data-r="3">3 года</button><button type="button" data-r="0">с листинга A</button></div>
          <span class="note" id="last"></span>
        </div>
        <div class="mchart" id="mchart"><svg id="msvg" role="img" aria-label="Цена H и A в гонконгских долларах против полос справедливой стоимости"></svg><div class="mtip" id="mtip" hidden></div></div>
        <div class="key">
          <span><i style="background:var(--ink)"></i>H, HK$</span>
          <span><i style="background:var(--steel)"></i>A в HK$ (по курсу дня)</span>
          <span><i class="band-r"></i>модель на прибыли</span>
          <span><i class="band-o"></i>модель на деньгах</span>
        </div>
        <ul class="evs" id="evs"></ul>
      </div>
      <p class="prose">Полосы считает калькулятор ниже. Подвиньте его ползунки или выберите сценарий — полосы на графике сдвинутся.</p>
    </section>

    <section id="calc" class="panel" aria-label="Оценка">
      <div class="eyebrow" id="val-method"></div>
      <h2 id="val-formula"></h2>
      <p class="note" id="val-comment"></p>
      <div class="seg" role="group" aria-label="Сценарии" id="scen"></div>
      <div class="calc">
        <div class="calc-bar" aria-live="polite"><span>Справедливая цена</span><b class="num" id="bar-fair">—</b><span class="up" id="bar-up">—</span></div>
        <div class="stack" id="controls"></div>
        <div class="result">
          <div class="eyebrow">Справедливая цена</div>
          <div><span class="big num" id="fair">—</span> <span class="muted" id="fair-unit"></span></div>
          <div class="up" id="upside">—</div>
          <div class="tbl"><table class="wf" id="wf"></table></div>
        </div>
      </div>
      <div class="stack">
        <h3>Что сильнее всего двигает цену</h3>
        <p class="note">Каждое допущение меняется в своём разумном диапазоне, остальные — как сейчас. Чем длиннее полоса, тем внимательнее к этому допущению.</p>
        <div id="tornado" class="torn"></div>
      </div>
      <details class="how"><summary>Как посчитан каждый поток и откуда цифры</summary><div class="stack" id="how"></div></details>
      <details class="how" id="noinc-box"><summary>Что модель не учитывает</summary><ul class="list" id="noinc"></ul></details>
    </section>

    <section class="sec" aria-labelledby="h-two">
      <h2 id="h-two">Почему у модели две полосы</h2>
      <div class="prose">
        <p><b>Модель на прибыли</b> (красная полоса) считает, что каждый юань операционной прибыли после налога можно забрать. Это калькулятор выше: от «Сейчас» до «Середины цикла».</p>
        <p><b>Модель на деньгах</b> (охра) берёт только то, что остаётся после поддерживающих капзатрат и роста оборотного капитала. Это 1,8–2,1 млрд ¥ в год вместо 4,4: дебиторка, запасы и векселя группы съедают разницу.</p>
        <p>Если отчёт за 9М покажет, что дебиторка перестала расти быстрее выручки, правдой станет верхняя полоса.</p>
      </div>
      <p class="src" id="msrc"></p>
    </section>

    <section id="market" class="panel" aria-label="Рыночные данные">
      <h2>Входы модели: источник и дата</h2>
      <div class="mk-grid" id="mk"></div>
    </section>
""" + PAGER,
r"""import {boot, esc, fmt, $, model} from "/assets/q.js?v=5";
const L = await boot("market");
const csv = await (await fetch(`/data/history/3898_px.csv?v=${Date.now() / 36e5 | 0}`)).text();
const rows = csv.trim().split("\n").slice(1).map(l => { const [d, a, h, f] = l.split(","); return {d, t: Date.parse(d), a: a ? +a / +f : null, h: h ? +h : null}; }).filter(r => r.h || r.a);
const CL = await model();
const V = CL.V, fx = V.inputs.find(i => i.id === "fx"), shares = V.shares_m * 1e6;
// текущие допущения — прямо из ползунков калькулятора
const cur = () => Object.fromEntries(V.inputs.map(i => [i.id, +document.getElementById("in-" + i.id)?.value || i.now]));
const ps = x => CL.compute(x).ps;
// денежная база: потоки «ж/д» и «новое оборудование» заменяются FCF (юани → HK$ по курсу из модели)
function psCash(x, fcfCny) {
  const r = CL.compute(x), y = x[V.yield_input] / 100;
  const ops = r.parts.filter(p => p.s.id === "rail" || p.s.id === "em").reduce((t, p) => t + p.value, 0);
  return (r.total - ops + fcfCny / x.fx / y) * V.unit_mult / shares;
}
const mid = CL.scens.find(s => s.id === "mid");
const bands = () => { const x = cur(), xm = Object.assign({}, x, mid ? mid.values : {});
  return {prof: [ps(x), ps(xm)].sort((a, b) => a - b), cash: L.fcf.cny.map(f => psCash(x, f)).sort((a, b) => a - b)}; };
const bear = CL.fairOf(CL.D.fair_value.bear), bull = CL.fairOf(CL.D.fair_value.bull);
$("msrc").textContent = L.fcf.src;
const last = [...rows].reverse().find(r => r.h);
$("last").textContent = `последнее закрытие ${last.d.split("-").reverse().join(".")}`;

const svg = $("msvg"), tip = $("mtip"), S = {r: 1};
let X, Y, view, Wd, Ht, pad;
function draw(anim) {
  const b = bands(), t1 = rows.at(-1).t, t0 = S.r ? t1 - S.r * 365.25 * 864e5 : rows[0].t;
  view = rows.filter(r => r.t >= t0);
  Wd = $("mchart").clientWidth; Ht = Math.round(Math.min(400, Math.max(300, Wd * .8)));
  pad = {l: 34, r: 8, t: 12, b: 22};
  const vals = view.flatMap(r => [r.h, r.a]).filter(v => v != null).concat(b.prof, b.cash);
  const lo = Math.max(0, Math.floor(Math.min(...vals) / 5) * 5 - 5), hi = Math.ceil(Math.max(...vals) / 5) * 5 + 5;
  X = t => pad.l + (t - t0) / (t1 - t0) * (Wd - pad.l - pad.r);
  Y = v => pad.t + (hi - v) / (hi - lo) * (Ht - pad.t - pad.b);
  svg.setAttribute("viewBox", `0 0 ${Wd} ${Ht}`);
  const line = k => view.reduce((s, r, i) => r[k] == null ? s : s + (s && view[i - 1]?.[k] != null ? "L" : "M") + X(r.t).toFixed(1) + "," + Y(r[k]).toFixed(1), "");
  const step = hi - lo > 60 ? 20 : 10;
  let g = "";
  for (let v = Math.ceil(lo / step) * step; v <= hi; v += step) g += `<line x1="${pad.l}" x2="${Wd - pad.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--line)"/><text x="2" y="${Y(v) + 4}">${v}</text>`;
  const yrs = []; for (let yv = new Date(t0).getFullYear() + 1; yv <= new Date(t1).getFullYear(); yv++) yrs.push(Date.UTC(yv, 0, 1));
  const xt = (S.r === 1 ? [0, 3, 6, 9].map(k => { const d = new Date(t1); d.setUTCMonth(d.getUTCMonth() - 12 + k); d.setUTCDate(1); return d.getTime(); }) : yrs)
    .filter(t => t > t0).map(t => `<text x="${X(t)}" y="${Ht - 6}" text-anchor="middle">${S.r === 1 ? new Date(t).toLocaleDateString("ru-RU", {month: "short"}).replace(".", "") : new Date(t).getUTCFullYear()}</text>`).join("");
  const band = (r, c, lbl, left) => `<rect x="${pad.l}" width="${Wd - pad.l - pad.r}" y="${Y(r[1])}" height="${Math.max(2, Y(r[0]) - Y(r[1]))}" fill="color-mix(in srgb,var(--${c}) ${c === "ore" ? 30 : 18}%,transparent)" stroke="var(--${c})" stroke-width=".8"/>
    <text class="lbl" x="${left ? pad.l + 4 : Wd - pad.r - 4}" y="${Y(r[1]) - 4}" text-anchor="${left ? "start" : "end"}" style="fill:var(--${c})">${lbl} ${fmt(r[0], 1)}–${fmt(r[1], 1)}</text>`;
  const ref = (v, lbl) => v > lo && v < hi ? `<line x1="${pad.l}" x2="${Wd - pad.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--muted)" stroke-dasharray="2 4"/><text x="${pad.l + 4}" y="${Y(v) - 3}">${lbl}</text>` : "";
  const evs = L.events.map((e, k) => ({...e, k: k + 1, ts: Date.parse(e.d)})).filter(e => e.ts >= t0 && e.ts <= t1);
  const ev = evs.map(e => { const r = view.reduce((p, c) => Math.abs(c.t - e.ts) < Math.abs(p.t - e.ts) ? c : p); const v = r.h ?? r.a;
    return `<g><line x1="${X(e.ts)}" x2="${X(e.ts)}" y1="${Y(v) + 6}" y2="${Ht - pad.b}" stroke="var(--red)" stroke-width=".8" stroke-dasharray="1 3"/><circle cx="${X(e.ts)}" cy="${Y(v)}" r="8" fill="var(--panel)" stroke="var(--red)" stroke-width="1.4"/><text x="${X(e.ts)}" y="${Y(v) + 3.5}" text-anchor="middle" style="fill:var(--red);font-weight:600">${e.k}</text></g>`; }).join("");
  svg.innerHTML = g + xt + band(b.prof, "red", "на прибыли") + band(b.cash, "ore", "на деньгах", true) + ref(bear, `медвежий ${fmt(bear, 1)}`) + ref(bull, `бычий ${fmt(bull, 1)}`) +
    `<path d="${line("a")}" fill="none" stroke="var(--steel)" stroke-width="1.6" stroke-linejoin="round"/><path id="hpath" d="${line("h")}" fill="none" stroke="var(--ink)" stroke-width="2.2" stroke-linejoin="round"/><circle cx="${X(last.t)}" cy="${Y(last.h)}" r="4.5" fill="var(--red)"/>` + ev +
    `<line id="cross" y1="${pad.t}" y2="${Ht - pad.b}" stroke="var(--ink)" stroke-width=".8" visibility="hidden"/>`;
  $("evs").innerHTML = evs.map(e => `<li><b>${e.k}</b><span>${e.d.split("-").reverse().join(".")} — ${esc(e.t)}</span></li>`).join("");
  const hp = $("hpath"), Lh = hp.getTotalLength();
  if (anim && !matchMedia("(prefers-reduced-motion: reduce)").matches) { hp.style.strokeDasharray = Lh; hp.style.strokeDashoffset = Lh; hp.getBoundingClientRect(); hp.style.transition = "stroke-dashoffset 1.1s cubic-bezier(.16,1,.3,1)"; hp.style.strokeDashoffset = 0; }
  const p = last.h; let cls, txt;
  if (p < b.cash[0]) { cls = "good"; txt = `<b>H ниже обеих оценок.</b> HK$${fmt(p, 2)} меньше даже модели на деньгах (${fmt(b.cash[0], 1)}–${fmt(b.cash[1], 1)}). Дёшево и при худшей базе.`; }
  else if (p <= b.cash[1]) { cls = "warn"; txt = `<b>H внутри денежной полосы.</b> HK$${fmt(p, 2)} — ровно столько, сколько стоит компания, если оборотный капитал и дальше съедает поток (${fmt(b.cash[0], 1)}–${fmt(b.cash[1], 1)}). Дёшево только по прибыли: ${fmt(b.prof[0], 1)}–${fmt(b.prof[1], 1)}.`; }
  else if (p < b.prof[0]) { cls = "warn"; txt = `<b>H между двумя оценками.</b> HK$${fmt(p, 2)} выше модели на деньгах (до ${fmt(b.cash[1], 1)}), но ниже модели на прибыли (от ${fmt(b.prof[0], 1)}). Рынок уже ставит на улучшение денежного потока.`; }
  else { cls = "bad"; txt = `<b>H выше модели на прибыли.</b> HK$${fmt(p, 2)} при оценке ${fmt(b.prof[0], 1)}–${fmt(b.prof[1], 1)}: запаса нет.`; }
  $("plate").className = "plate " + cls; $("plate-t").innerHTML = txt;
  document.querySelectorAll("#rng button").forEach(bt => bt.setAttribute("aria-pressed", +bt.dataset.r === S.r));
}
function hover(ev) {
  const r0 = svg.getBoundingClientRect(), x = (ev.clientX - r0.left) * Wd / r0.width;
  if (x < pad.l || x > Wd - pad.r) return out();
  const r = view.reduce((p, c) => Math.abs(X(c.t) - x) < Math.abs(X(p.t) - x) ? c : p);
  const c = $("cross"); c.setAttribute("x1", X(r.t)); c.setAttribute("x2", X(r.t)); c.setAttribute("visibility", "visible");
  tip.hidden = false;
  tip.innerHTML = `${r.d.split("-").reverse().join(".")}<br>H <b>${r.h != null ? fmt(r.h, 2) : "—"}</b> · A <b>${r.a != null ? fmt(r.a, 2) : "—"}</b>${r.h && r.a ? `<br>премия A/H <b>${fmt((r.a / r.h - 1) * 100, 0)}%</b>` : ""}`;
  tip.style.left = Math.min(Math.max(0, X(r.t) * r0.width / Wd - 70), r0.width - 150) + "px";
}
function out() { tip.hidden = true; $("cross")?.setAttribute("visibility", "hidden"); }
svg.addEventListener("pointermove", hover); svg.addEventListener("pointerleave", out);
$("rng").addEventListener("click", e => { const b = e.target.closest("button"); if (b) { S.r = +b.dataset.r; draw(true); } });
// калькулятор двигает полосы
$("calc").addEventListener("input", () => draw());
$("calc").addEventListener("click", e => { if (e.target.closest("button")) setTimeout(() => draw(), 0); });
let rt; addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(() => draw(), 120); });
draw(true);""")

# ---------------- 4. аналоги и IPO ----------------
page("peers", "С кем сравнивать и что даст IPO дочки — 3898 · Cap Laoban", "CRRC Times Electric против аналогов: ж/д производители и китайские чипмейкеры, что даст листинг Times Semiconductor, история листингов.",
"""    <header class="qhead" id="qhead"></header>
    <section id="peers" class="sec" aria-labelledby="peers-title">
      <h2 id="peers-title">Аналоги</h2>
      <div class="panel"><div class="tbl"><table id="peer-table"></table></div><p class="note" id="peers-note"></p></div>
    </section>
    <section class="sec" aria-labelledby="h-semi">
      <h2 id="h-semi">Дочка против китайских чипмейкеров</h2>
      <div class="panel"><div class="tbl"><table id="t-semi"></table></div><p class="src" id="n-semi"></p></div>
      <p class="prose">Маржа дочки выше, чем у StarPower и Silan, а внутри Times Electric её оценивают примерно в один капитал. Аналоги на бирже A стоят 2,5–3,7 капитала при более слабой прибыльности. Это не значит, что дочка недооценена: аналоги торгуются с «технологической» премией STAR, и она может уйти.</p>
    </section>
    <section class="sec" aria-labelledby="h-ipo">
      <h2 id="h-ipo">Что даст листинг дочки</h2>
      <div class="split">
        <div class="stack">
          <div class="ctl">
            <label for="pb">Во сколько капиталов рынок оценит дочку <output id="pb-o"></output></label>
            <input type="range" id="pb" min="0.8" max="4" step="0.1" value="1.6">
            <small>1,0 — по балансу; 1,6 — цена раунда 2024; 3,5 — медиана StarPower, Silan, NCE.</small>
          </div>
          <div class="uplift" id="up"></div>
        </div>
        <div class="prose">
          <p>Если дочку выведут на биржу, рынок впервые назовёт её цену. Каждые +0,5 капитала к оценке добавляют около HK$4,1 к стоимости акции Times Electric.</p>
          <p>Чтобы этот выигрыш дошёл до держателя H, рынок должен переоценить материнскую компанию. Сам по себе листинг денег акционерам не приносит. Компания листинг не объявляла.</p>
        </div>
      </div>
    </section>
    <section class="sec" aria-labelledby="h-tl">
      <h2 id="h-tl">Двадцать лет листингов</h2>
      <ol class="tl" id="tl"></ol>
    </section>
""" + PAGER,
r"""import {boot, esc, fmt, tween, $} from "/assets/q.js?v=5";
const D = await boot("peers");
const T = D.peers_semi;
$("t-semi").innerHTML = `<tr><th></th>${T.cols.map((c, k) => `<th${k ? "" : ' class="me"'}>${esc(c)}</th>`).join("")}</tr>` +
  T.rows.map(r => `<tr>${r.map((c, k) => `<td${k === 1 ? ' class="me"' : ""}>${esc(c)}</td>`).join("")}</tr>`).join("");
$("n-semi").textContent = T.note;
$("tl").innerHTML = D.listings.map(l => `<li${l.d === "сейчас" ? ' class="now"' : ""}><b>${esc(l.d)}</b><span>${esc(l.t)}</span><small>${esc(l.src)}</small></li>`).join("");
const P = D.parts, hk = bn => bn * 1000 / D.shares_m / D.price.fx;
$("up").innerHTML = `<span>Доля 77,86% по этой оценке</span><b id="u-v"></b><span>Она же по балансу</span><b>HK$${fmt(hk(P.ts_book * .7786), 1)}</b><span class="tot">Прибавка на акцию</span><b class="tot" id="u-d"></b><span class="tot">К цене H HK$${fmt(D.price.h, 2)}</span><b class="tot" id="u-p"></b>`;
function upd() {
  const pb = +$("pb").value, v = hk(P.ts_book * pb * .7786), d = v - hk(P.ts_book * .7786);
  $("pb-o").textContent = fmt(pb, 1) + "×";
  tween($("u-v"), v, 1, "HK$"); tween($("u-d"), d, 1, d >= 0 ? "+HK$" : "HK$"); tween($("u-p"), d / D.price.h * 100, 0, d >= 0 ? "+" : "", "%");
}
$("pb").addEventListener("input", upd); upd();""")

# ---------------- 5. риски ----------------
page("risks", "Что сломает тезис — 3898 · Cap Laoban", "Риски CRRC Times Electric: форензика оборотного капитала и векселей группы CRRC, деньги у контролёра, остановленный выкуп, календарь проверок.",
"""    <header class="qhead" id="qhead"></header>
    <section class="sec" aria-labelledby="h-fx">
      <h2 id="h-fx">Где застревают деньги</h2>
      <p class="prose">Деньги реальны: операционный поток — 92% прибыли, аудитор KPMG, залогов нет. Риск в другом: деньги приходят поздно, оседают в группе и не возвращаются акционерам. Риск-гейт — AMBER.</p>
      <ul class="rk" id="rk"></ul>
    </section>
    <section id="risks" class="sec" aria-labelledby="h-rk">
      <h2 id="h-rk">Что может сломать историю</h2>
      <div class="panel"><ul class="list" id="risk-list"></ul></div>
    </section>
    <section class="sec" aria-labelledby="h-trg">
      <h2 id="h-trg">Что ждём</h2>
      <div class="panel"><ul class="list" id="trig-list"></ul></div>
    </section>
""" + PAGER,
r"""import {boot, esc, $} from "/assets/q.js?v=5";
const D = await boot("risks");
$("rk").innerHTML = D.risks.map(r => `<li><h3>${esc(r.t)}</h3><p>${esc(r.d)}</p><p class="src">${esc(r.src)}</p></li>`).join("");""")

# ---------------- цифры ----------------
page("data", "Цифры: цена, отчётность, дивиденды — 3898 · Cap Laoban", "CRRC Times Electric: цена H и A с премией, отчётность по годам и кварталам, дивиденды и доля прибыли, чья это дочка, словарь.",
"""    <header class="qhead"><h1>Цифры</h1><p class="lead">Цена A и H с премией, отчётность по годам и кварталам, дивиденды — и почему они такие, сегменты, словарь.</p></header>
    <section id="terminal" aria-label="Цена и отчётность" hidden></section>
    <section class="sec" aria-labelledby="h-ch">
      <h2 id="h-ch">Графики разбора</h2>
      <div class="grid2" id="charts"></div>
    </section>
    <section id="glossary" class="sec" aria-labelledby="h-gl">
      <h2 id="h-gl">Словарь</h2>
      <div class="panel"><dl class="gloss" id="gloss"></dl></div>
    </section>
""" + PAGER,
r"""import {boot} from "/assets/q.js?v=5";
await boot("data");
document.title = "Цифры: цена, отчётность, дивиденды — 3898 · Cap Laoban";
import("/assets/q.js?v=5").then(m => m.model()).then(() => { document.title = "Цифры: цена, отчётность, дивиденды — 3898 · Cap Laoban"; });""",
 extra='<script src="/assets/terminal.js?v=6" defer></script>\n')
print("ok")
