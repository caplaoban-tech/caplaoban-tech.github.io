"""Квартальная отчётность компаний: прогноз против факта.

Источник — data/quarters/<тикер>.json (что прогнозировали, когда и откуда; что вышло; сверка ожиданий).
Пишет <страница компании>/q/index.html (история по кварталам) и <страница>/q/<id>/index.html (разбор квартала).
Запуск: python3 tools/q_reports.py [тикер ...]  — без аргументов собирает все файлы data/quarters/*.json.
Прогноз в JSON не правится задним числом: новый прогноз — новая запись с новой датой.
"""
import json, sys, html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E = html.escape


def num(x, d=2):
    return f"{x:.{d}f}".replace(".", ",").replace("-", "−")


def dt(s):
    p = s.split("-")
    mon = ["янв.", "февр.", "марта", "апр.", "мая", "июня", "июля", "авг.", "сент.", "окт.", "нояб.", "дек."]
    return f"{int(p[2])}.{p[1]}.{p[0]}" if len(p) == 3 else f"{mon[int(p[1]) - 1]} {p[0]}"


def sgn(x):
    return ("+" if x > 0 else "") + num(x)


def tot(d):
    return d["own"] + d["assoc"] if d else None


HEAD = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@500;800&family=Golos+Text:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap">
<link rel="stylesheet" href="/assets/style.css?v=13">
<style>
.qh{{font-family:var(--display);font-weight:800;font-size:clamp(22px,5vw,32px);line-height:1.15;margin:0}}
.qv p{{margin:0 0 8px}} .qv p:last-child{{margin:0}}
.qchk{{display:grid;grid-template-columns:22px 1fr;gap:2px 10px;padding:10px 0;border-top:1px solid var(--line)}}
.qchk:first-child{{border-top:0}}
.qi{{width:20px;height:20px;border-radius:50%;color:#fff;font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center;margin-top:2px}}
.qi.ok{{background:var(--good)}} .qi.warn{{background:var(--warn)}} .qi.bad{{background:var(--bad)}} .qi.same{{background:var(--muted)}}
.qe{{font-weight:600}} .qr{{color:var(--ink)}}
.qt{{width:100%;border-collapse:collapse;font-size:14px}}
.qt th,.qt td{{padding:7px 8px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}}
.qt th:first-child,.qt td:first-child{{text-align:left;white-space:normal}}
@media(max-width:560px){{.qt{{font-size:13px}} .qt th,.qt td{{padding:6px 5px}} .qt.six th:nth-child(n+5),.qt.six td:nth-child(n+5){{display:none}} .qt.bal th:nth-child(-n+4):not(:first-child),.qt.bal td:nth-child(-n+4):not(:first-child){{display:none}}}} .qt th{{font-size:12px;color:var(--muted);font-weight:600}}
.qcards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:10px}}
.qcard{{border:1px solid var(--line);border-radius:12px;padding:12px 14px;display:flex;flex-direction:column;gap:4px;color:inherit;text-decoration:none}}
a.qcard:hover{{border-color:var(--red)}}
.qcard b{{font-size:15px}} .qcard .num{{font-size:22px;font-weight:600}}
svg text{{font-family:var(--mono);font-size:17px;fill:var(--muted)}} svg .lbl{{fill:var(--ink);font-weight:600;font-size:19px}}
</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <a class="brand" href="/"><img src="/assets/mark.svg" alt="">Cap Laoban</a>
    <nav class="nav">{nav}</nav>
  </header>
  <main class="stack">
{body}
  </main>
  <footer class="bot foot"><span>Метки: [А] — цифра из отчётности, [Б] — расчёт, [В] — внешний источник или оценка. Прогноз показан таким, каким был опубликован, с датой. Не индивидуальная инвестиционная рекомендация.</span></footer>
</div>
</body>
</html>
"""


def chart(D):
    """Пары столбцов по кварталам: прогноз (контур) и факт (заливка), каждый — свой бизнес + ассоциаты."""
    Q = D["quarters"]
    mx = max(max(tot(q.get("fact")) or 0, tot(q.get("forecast")) or 0) for q in Q) * 1.15
    W, H, pb, pt = 640, 300, 36, 28
    slot = W / len(Q)
    bw = min(56, slot * .36)
    y = lambda v: H - pb - v / mx * (H - pb - pt)
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Прогноз и факт по кварталам">']
    for f in (.25, .5, .75, 1):
        s.append(f'<line x1="0" x2="{W}" y1="{y(mx * f / 1.15):.1f}" y2="{y(mx * f / 1.15):.1f}" style="stroke:var(--line)"/>')
    for i, q in enumerate(Q):
        cx = slot * i + slot / 2
        for k, (d, solid) in enumerate(((q.get("forecast"), False), (q.get("fact"), True))):
            x = cx - bw - 3 if k == 0 else cx + 3
            if not d:
                s.append(f'<text x="{x + bw / 2:.1f}" y="{H - pb - 6}" text-anchor="middle">—</text>')
                continue
            b = 0
            for part, col in (("own", "--steel"), ("assoc", "--ore")):
                y0, y1 = y(b), y(b + d[part])
                st = f"fill:var({col})" if solid else f"fill:none;stroke:var({col});stroke-width:2;stroke-dasharray:4 3"
                s.append(f'<rect x="{x:.1f}" y="{y1:.1f}" width="{bw:.1f}" height="{max(0, y0 - y1):.1f}" rx="2" style="{st}"/>')
                b += d[part]
            s.append(f'<text class="lbl" x="{x + bw / 2:.1f}" y="{y(b) - 5:.1f}" text-anchor="middle">{num(b, 1)}</text>')
        s.append(f'<text x="{cx:.1f}" y="{H - 10}" text-anchor="middle">{E(q["label"].replace(" 20", " ’"))}</text>')
    s.append("</svg>")
    return "".join(s)


LEGEND = ('<div class="legend"><span><i style="background:var(--steel)"></i>Свой бизнес</span>'
          '<span><i style="background:var(--ore)"></i>Доля прибыли ассоциатов</span>'
          '<span><i style="background:none;border:2px dashed var(--muted)"></i>Прогноз (контур) · факт (заливка)</span></div>')


def index_page(D, base):
    rows = ""
    for q in D["quarters"]:
        fc, fa = q.get("forecast"), q.get("fact")
        dev = sgn(tot(fa) - tot(fc)) if fc and fa else "—"
        link = f'<a href="{q["id"]}/">{E(q["label"])}</a>' if q.get("checks") else E(q["label"])
        rows += (f'<tr><td>{link}</td><td>{num(tot(fc)) + "<br><small class=muted>" + dt(fc["date"]) + "</small>" if fc else "—"}</td>'
                 f'<td>{num(tot(fa)) if fa else "ждём"}</td><td>{dev}</td></tr>')
    cards = ""
    for q in D["quarters"]:
        fc, fa = q.get("forecast"), q.get("fact")
        tag = "a" if q.get("checks") else "div"
        href = f' href="{q["id"]}/"' if q.get("checks") else ""
        line = (q.get("headline") or q.get("short") or (fc or {}).get("note") or "")
        val = f'факт {num(tot(fa))}' if fa else f'прогноз {num(tot(fc))}'
        rep = q.get("report") or {}
        when = ("ждём · " if rep.get("due") else "") + (dt(rep["date"]) if rep.get("date") else "")
        cards += (f'<{tag} class="qcard"{href}><span class="eyebrow">{E(q["label"])} · {E(when)}</span>'
                  f'<span class="num">{val}</span><span class="note">{E(line)}</span></{tag}>')
    body = f"""    <section class="stack" style="padding-block:4px 2px">
      <div class="eyebrow">{E(D["ticker"])} · отчётность по кварталам · обновлено {dt(D["updated"])}</div>
      <h1 class="qh">{E(D["name"])}: что мы прогнозировали и что вышло</h1>
      <p class="note">{E(D["metric"])}, {E(D["unit"])}. Прогноз — каким он был на сайте до отчёта, с датой; факт — из отчётности [А], квартал = накопленный итог минус предыдущий [Б].</p>
    </section>
    <section class="panel">
      <div class="eyebrow">Прогноз и факт</div>
      {chart(D)}
      {LEGEND}
    </section>
    <section class="panel">
      <div class="eyebrow">Сводка</div>
      <div class="tbl"><table class="qt"><thead><tr><th>Квартал</th><th>Прогноз</th><th>Факт</th><th>Разница</th></tr></thead><tbody>{rows}</tbody></table></div>
    </section>
    <section class="qcards">{cards}</section>"""
    nav = f'<a href="{base}">Разбор {E(D["ticker"])}</a>'
    return HEAD.format(title=f'{D["name"]} ({D["ticker"]}) — прогноз и факт по кварталам', desc=f'{D["name"]}: прогноз и факт по кварталам', nav=nav, body=body)


def balance(q):
    """Баланс по концам кварталов и изменение к прошлому кварталу (не к началу года)."""
    B = q.get("balance")
    if not B:
        return ""
    f = lambda x: "—" if x is None else num(x)
    head = "".join(f"<th>{E(l)}</th>" for l in B["labels"]) + "<th>Δ за кв.</th>"
    rows = ""
    for r in B["rows"]:
        v = r["values"]
        dq = "" if r["dq"] is None else ("+" if r["dq"] > 0 else "") + num(r["dq"]) + (" ⚡" if r["jump"] else "")
        rows += f"<tr><td>{E(r['label'])}</td>" + "".join(f"<td>{f(x)}</td>" for x in v[:-1]) + f"<td><b>{f(v[-1])}</b></td><td>{dq}</td></tr>"
    notes = "".join(f'<li><span class="dot" style="background:var(--warn)"></span><span>{E(n)}</span></li>' for n in B["notes"])
    return f"""    <section class="panel">
      <div class="eyebrow">Баланс к прошлому кварталу, {E(B["unit"])}</div>
      <p><b>Как читать:</b> {E(B["read"])}</p>
      <div class="tbl"><table class="qt bal"><thead><tr><th></th>{head}</tr></thead><tbody>{rows}</tbody></table></div>
      <ul class="list">{notes}</ul>
      <p class="note">{E(B["method"])} Источник — балансы в отчётах на IDX [А]. На телефоне показаны два последних квартала, история — в пометках выше.</p>
    </section>"""


def quarter_page(D, q, base):
    fc, fa = q["forecast"], q["fact"]
    cmp_rows = "".join(
        f'<tr><td>{n}</td><td>{num(fc[k]) if k != "t" else num(tot(fc))}</td><td><b>{num(fa[k]) if k != "t" else num(tot(fa))}</b></td>'
        f'<td>{sgn((fa[k] - fc[k]) if k != "t" else tot(fa) - tot(fc))}</td></tr>'
        for n, k in (("Свой бизнес", "own"), ("Доля прибыли ассоциатов", "assoc"), ("<b>Прибыль акционерам</b>", "t")))
    T = q["table"]
    trows = "".join("<tr>" + "".join(f"<td>{c if i == 0 else E(c)}</td>" for i, c in enumerate(r)) + "</tr>" for r in T["rows"])
    icon = {"ok": "✓", "warn": "!", "bad": "✕", "same": "="}
    checks = "".join(f'<div class="qchk"><span class="qi {c["tone"]}">{icon[c["tone"]]}</span><div><div class="qe">{E(c["expected"])}</div>'
                     f'<div class="qr">{E(c["result"])}</div></div></div>' for c in q["checks"])
    rep = q["report"]
    body = f"""    <section class="stack" style="padding-block:4px 2px">
      <div class="eyebrow">{E(D["ticker"])} · {E(q["label"])} · {E(rep["what"])} · {dt(rep["date"])}</div>
      <h1 class="qh">{E(q["headline"])}</h1>
    </section>
    <section class="panel qv">{"".join(f"<p>{E(v)}</p>" for v in q["verdict"])}</section>
    <section class="panel">
      <div class="eyebrow">Прогноз против факта, {E(D["unit"])}</div>
      <div class="tbl"><table class="qt"><thead><tr><th></th><th>Прогноз {dt(fc["date"])}</th><th>Факт</th><th>Разница</th></tr></thead><tbody>{cmp_rows}</tbody></table></div>
      <p class="note">Прогноз: {E(fc["src"])}. {E(fc.get("note", ""))}.</p>
    </section>
    <section class="panel">
      <div class="eyebrow">Квартал отдельно</div>
      <div class="tbl"><table class="qt six"><thead><tr><th></th>{"".join(f"<th>{E(c)}</th>" for c in T["cols"])}</tr></thead><tbody>{trows}</tbody></table></div>
      <p class="note">{E(T["note"])} На телефоне колонки II кв. скрыты.</p>
    </section>
{balance(q)}
    <section class="panel">
      <div class="eyebrow">Что мы ждали — и что вышло</div>
      <p class="note">✓ как ждали или лучше · ✕ хуже · ! внимание · = без изменений</p>
      <div>{checks}</div>
    </section>
    <section class="panel">
      <div class="eyebrow">Что смотреть дальше</div>
      <ul class="list">{"".join(f'<li><span class="dot" style="background:var(--ore)"></span><span>{E(n)}</span></li>' for n in q["next"])}</ul>
      <p class="note">Источники: {"; ".join(E(s) for s in q["sources"])}. <a href="{E(rep["url"])}" target="_blank" rel="noopener">Раскрытия IDX</a>.</p>
    </section>"""
    nav = f'<a href="{base}">Разбор {E(D["ticker"])}</a><a href="../">Все кварталы</a>'
    return HEAD.format(title=f'{D["name"]} — {q["label"]}: прогноз и факт', desc=q["headline"], nav=nav, body=body)


def build(path):
    D = json.loads(path.read_text())
    base = D["page"]
    qdir = ROOT / base.strip("/") / "q"
    qdir.mkdir(parents=True, exist_ok=True)
    (qdir / "index.html").write_text(index_page(D, base))
    out = [qdir / "index.html"]
    for q in D["quarters"]:
        if q.get("checks"):
            d = qdir / q["id"]
            d.mkdir(exist_ok=True)
            (d / "index.html").write_text(quarter_page(D, q, base))
            out.append(d / "index.html")
    return out


if __name__ == "__main__":
    files = [ROOT / "data/quarters" / f"{t.lower()}.json" for t in sys.argv[1:]] or sorted((ROOT / "data/quarters").glob("*.json"))
    for f in files:
        for o in build(f):
            print(o.relative_to(ROOT))
