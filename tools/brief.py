#!/usr/bin/env python3
"""Короткий разбор на одну страницу: тезис, 6 цифр, графики, деньги акционеру, рост, риски — и новости после отчёта.

    python3 tools/brief.py [тикер ...]     — без аргументов собирает все data/briefs/*.json

Источник: data/briefs/<тикер>.json (формат — как у tools/report/brief_en.py в рабочей папке + ticker, name, date,
period, card, page, en). Пишет briefs/<тикер>/index.html (последний разбор) и briefs/<тикер>/<дата>/index.html (архив),
и data/briefs.json — ленту для главной. Новости после даты разбора страница подгружает сама из data/news.json.
Цифры в JSON — проверенные (Codex) до публикации; генератор их не меняет.
"""
import html, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E = html.escape
COL = {"a": "var(--good)", "b": "var(--steel)", "c": "var(--ore)", "r": "var(--red)"}
QC = ["var(--line)", "#c7c3bb", "var(--steel)", "var(--red)"]


NB = lambda s: __import__("re").sub(r"(?<=\d) (?=\d{3}\b)", "\u00a0", s)      # 1 340 не рвётся на телефоне


def ru(s):
    """1,234.5 → 1 234,5"""
    return s.replace(",", " ").replace(".", ",")


def fmt(ch, v):
    return ru(ch.get("fmt", "{:,.0f}").format(v))


def line(ch, w=440, h=200):
    pts = ch["data"]; vs = [p[1] for p in pts]; lo, hi = min(vs) * .95, max(vs) * 1.05; col = COL.get(ch.get("color", "b"))
    x = lambda i: 46 + (w - 58) * i / (len(vs) - 1); y = lambda v: 14 + (h - 46) * (hi - v) / (hi - lo)
    o = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{E(ch["title"])}">']
    for k in range(4):
        v = lo + (hi - lo) * k / 3
        o.append(f'<line x1="46" x2="{w-12}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="var(--line)"/><text x="42" y="{y(v)+4:.1f}" font-size="10.5" text-anchor="end" fill="var(--muted)">{fmt(ch, v)}</text>')
    o.append('<polyline points="' + " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(vs)) + f'" fill="none" stroke="{col}" stroke-width="2"/>')
    o.append(f'<circle cx="{x(len(vs)-1):.1f}" cy="{y(vs[-1]):.1f}" r="4" fill="{col}"/><text x="{x(len(vs)-1)-6:.1f}" y="{y(vs[-1])-8:.1f}" font-size="11" text-anchor="end" fill="{col}" font-weight="600">{fmt(ch, vs[-1])}</text>')
    for i in range(0, len(pts), max(1, len(pts) // 6)):
        o.append(f'<text x="{x(i):.1f}" y="{h-10}" font-size="10.5" text-anchor="middle" fill="var(--muted)">{E(str(pts[i][0])[:7])}</text>')
    return "".join(o) + f'<text x="46" y="10" font-size="10.5" fill="var(--muted)">{E(ch.get("label", ""))}</text></svg>'


def qbars(ch, w=440, h=215):
    d = ch["data"]; yrs = list(d); vals = [v for yy in yrs for v in d[yy] if v is not None]; mx = max(vals) * 1.12; top, ph = 14, h - 54
    gw = (w - 40) / 4; bw = gw / (len(yrs) + 1); y = lambda v: top + ph * (1 - max(v, 0) / mx); cols = QC[-len(yrs):]
    o = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{E(ch["title"])}"><line x1="30" x2="{w}" y1="{y(0)}" y2="{y(0)}" stroke="var(--line)"/>']
    for q in range(4):
        for i, yy in enumerate(yrs):
            v = d[yy][q] if q < len(d[yy]) else None
            if v is None:
                continue
            xx = 34 + q * gw + i * bw
            o.append(f'<rect x="{xx:.1f}" y="{y(v):.1f}" width="{bw*.88:.1f}" height="{y(0)-y(v):.1f}" rx="2" fill="{cols[i]}"><title>{yy} кв. {q+1}: {ru(f"{v:.2f}")}</title></rect>')
            if i == len(yrs) - 1:
                o.append(f'<text x="{xx+bw*.44:.1f}" y="{y(v)-4:.1f}" font-size="10.5" text-anchor="middle" fill="var(--ink)" font-weight="600">{ru(f"{v:.2f}")}</text>')
        o.append(f'<text x="{34+q*gw+gw/2-bw/2:.1f}" y="{h-24}" font-size="11.5" text-anchor="middle" fill="var(--muted)">{["I", "II", "III", "IV"][q]} кв.</text>')
    lx = 34
    for i, yy in enumerate(yrs):
        o.append(f'<rect x="{lx}" y="{h-13}" width="10" height="10" fill="{cols[i]}"/><text x="{lx+14}" y="{h-4}" font-size="11" fill="var(--muted)">{E(yy)}</text>'); lx += 62
    return "".join(o) + "</svg>"


def gbars(ch, w=440, h=230):
    G = ch["groups"]; S = ch["series"]; mx = max(max(s["values"]) for s in S) * 1.15; top, ph = 14, h - 58
    gw = (w - 40) / len(G); bw = gw / (len(S) + 1); y = lambda v: top + ph * (1 - max(v, 0) / mx); f = ch.get("fmt", "{:.1f}")
    o = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{E(ch["title"])}"><line x1="30" x2="{w}" y1="{y(0)}" y2="{y(0)}" stroke="var(--line)"/>']
    for i, g in enumerate(G):
        for j, s in enumerate(S):
            v = s["values"][i]; xx = 36 + i * gw + j * bw
            o.append(f'<rect x="{xx:.1f}" y="{y(v):.1f}" width="{bw*.85:.1f}" height="{y(0)-y(v):.1f}" rx="2" fill="{COL.get(s["color"], s["color"])}"/><text x="{xx+bw*.42:.1f}" y="{y(v)-4:.1f}" font-size="10" text-anchor="middle" fill="var(--ink)">{ru(f.format(v))}</text>')
        o.append(f'<text x="{36+i*gw+bw*len(S)/2:.1f}" y="{h-28}" font-size="11.5" text-anchor="middle" fill="var(--muted)">{E(g)}</text>')
    lx = 36
    for s in S:
        o.append(f'<rect x="{lx}" y="{h-14}" width="10" height="10" fill="{COL.get(s["color"], s["color"])}"/><text x="{lx+14}" y="{h-5}" font-size="11" fill="var(--muted)">{E(s["name"])}</text>'); lx += 14 + 7 * len(s["name"]) + 16
    return "".join(o) + "</svg>"


DRAW = {"line": line, "qbars": qbars, "gbars": gbars}
dd = lambda s: ".".join(reversed(s.split("-")))


def page(c, depth):
    up = "../" * depth
    th = next((t for t in json.loads((ROOT / "data" / "themes.json").read_text()) if c["ticker"] in t["tickers"]), None) \
        if (ROOT / "data" / "themes.json").exists() else None
    back = f'<a href="/#{th["id"]}">{E(th["name"])}</a>' if th else ""
    charts = "".join(f'<div class="panel"><h2>{E(ch["title"])}</h2>{DRAW[ch["type"]](ch)}<p class="note">{E(ch.get("note", ""))}</p></div>' for ch in c["charts"])
    secs = ""
    for s in c["sections"]:
        tag = "ol" if s.get("ordered") else "ul"
        items = "".join(f"<li>{it}</li>" for it in s["items"])       # items могут содержать <b> — пишем сами
        secs += f'<section class="panel{" risk" if s.get("tone") == "risk" else ""}"><h2>{E(s["title"])}</h2><{tag}>{items}</{tag}></section>'
    kpi = "".join(f'<div class="kpi"><b class="num">{E(NB(v))}</b><span>{E(NB(k))}</span></div>' for v, k in c["kpis"])
    links = (f'<a href="{E(c["page"])}">Подробный разбор и калькулятор оценки</a>' if c.get("page") else "") + \
            (f' · <a href="{E(c["en"])}">English version</a>' if c.get("en") else "")
    desc = E(c.get("card") or c["title"])
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{E(c['ticker'])}: {desc} — Cap Laoban</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{E(c['ticker'])}: {desc}">
<meta property="og:description" content="{E(c['name'])} · {E(c.get('period', ''))}">
<meta property="og:image" content="/assets/og.png">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@500;800&family=Golos+Text:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap">
<link rel="stylesheet" href="/assets/style.css?v=16">
</head>
<body>
<div class="wrap narrow">
  <header class="top">
    <a class="brand" href="/"><img src="/assets/mark.svg" alt="">Cap Laoban</a>
    <nav class="nav">{back}<a href="/">Все разборы</a>{f'<a href="{E(c["page"])}">Подробно</a>' if c.get("page") else ""}<a href="#news">Новости</a></nav>
  </header>
  <main class="stack brief">
    <section class="stack" style="padding-block:8px 0">
      <div class="eyebrow">{E(c['ticker'])} · {E(c['name'])} · {E(c.get('period', ''))} · разбор от {dd(c['date'])}</div>
      <h1>{E(c['title'])}</h1>
      <p class="muted">{E(c['sub'])}</p>
    </section>
    <section class="panel thesis"><p><b>Главное.</b> {c['thesis']}</p></section>
    <section class="kpis six">{kpi}</section>
    <section class="bgrid">{charts}</section>
    {secs}
    <section id="news" class="panel"><h2>Что вышло после разбора</h2><ul class="feed" id="bnews"><li><span></span><span class="note">Загружаю…</span></li></ul></section>
    <p class="note">{links}</p>
    <p class="note">{c['sources']}</p>
  </main>
  <footer class="bot"><span>Cap Laoban Investments. Аналитика и личное мнение автора, не индивидуальная инвестиционная рекомендация.</span></footer>
</div>
<script>
(function () {{
  const T = {json.dumps(c['ticker'])}, D = {json.dumps(c['date'])};
  const esc = s => String(s).replace(/[&<>"]/g, c => ({{"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}}[c]));
  const el = document.getElementById("bnews");
  fetch("/data/news.json?v=" + (Date.now() / 36e5 | 0)).then(r => r.json()).then(items => {{
    const xs = items.filter(n => (n.tickers || []).includes(T) && n.date > D);
    el.innerHTML = xs.length ? xs.map(n => `<li><time datetime="${{n.date}}">${{n.date.slice(8)}}.${{n.date.slice(5, 7)}}</time><span>${{n.url ? `<a href="${{esc(n.url)}}" target="_blank" rel="noopener">${{esc(n.title)}}</a>` : esc(n.title)}}<br><span class="src">${{esc(n.src || "")}}</span></span></li>`).join("")
      : '<li><span></span><span class="note">Пока ничего существенного. Новые раскрытия и отчёты появятся здесь сами.</span></li>';
  }}).catch(() => {{ el.innerHTML = '<li><span></span><span class="note">Не удалось загрузить новости.</span></li>'; }});
}})();
</script>
<script src="/assets/latest.js?v=1" defer></script>
</body>
</html>
"""


def main():
    files = [ROOT / "data" / "briefs" / f"{t.lower()}.json" for t in sys.argv[1:]] or sorted((ROOT / "data" / "briefs").glob("*.json"))
    for f in files:
        c = json.loads(f.read_text(encoding="utf-8"))
        slug = c["ticker"].lower()
        for d, depth in ((ROOT / "briefs" / slug, 2), (ROOT / "briefs" / slug / c["date"], 3)):
            d.mkdir(parents=True, exist_ok=True)
            (d / "index.html").write_text(page(c, depth), encoding="utf-8")
        print("briefs/" + slug + "/")
    feed = []
    for f in sorted((ROOT / "data" / "briefs").glob("*.json")):
        c = json.loads(f.read_text(encoding="utf-8"))
        feed.append({"ticker": c["ticker"], "name": c["name"], "date": c["date"], "period": c.get("period", ""), "card": c.get("card") or c["title"],
                     "kpis": [[NB(v), NB(k)] for v, k in c["kpis"][:3]], "url": f"briefs/{c['ticker'].lower()}/", "page": c.get("page"), "tone": c.get("tone", "mute")})
    feed.sort(key=lambda x: x["date"], reverse=True)
    (ROOT / "data" / "briefs.json").write_text(json.dumps(feed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
