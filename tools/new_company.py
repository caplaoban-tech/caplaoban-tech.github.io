#!/usr/bin/env python3
"""Заготовка страницы новой компании.

    python3 tools/new_company.py TLKM "Telkom Indonesia" "Телеком" --exchange IDX

Создаёт:
  data/<тикер>.json      — копия templates/company/example.json с подставленной шапкой (цифры надо заменить);
  <тикер>/index.html     — страница из templates/company/index.html;
и добавляет/обновляет строку в data/companies.json (пока с "draft": true — на главной не видна).

Обновить уже существующую страницу из свежего шаблона, не трогая данные:
    python3 tools/new_company.py TLKM --refresh-page
"""
import argparse, datetime as dt, html, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TPL = ROOT / "templates" / "company"


def page_html(ticker, name, desc):
    s = (TPL / "index.html").read_text(encoding="utf-8")
    return (s.replace("__TICKER__", html.escape(ticker)).replace("__NAME__", html.escape(name))
             .replace("__DESCRIPTION__", html.escape(desc, quote=True)).replace("__FILE__", f"{ticker.lower()}.json"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ticker")
    ap.add_argument("name", nargs="?")
    ap.add_argument("sector", nargs="?", default="")
    ap.add_argument("--exchange", default="IDX")
    ap.add_argument("--refresh-page", action="store_true", help="пересобрать <тикер>/index.html из шаблона по существующему JSON")
    ap.add_argument("--force", action="store_true", help="перезаписать существующий JSON")
    a = ap.parse_args()

    t = a.ticker.upper()
    slug = t.lower()
    data_p = ROOT / "data" / f"{slug}.json"
    page_p = ROOT / slug / "index.html"

    if a.refresh_page:
        d = json.loads(data_p.read_text(encoding="utf-8"))
        page_p.parent.mkdir(exist_ok=True)
        page_p.write_text(page_html(t, d["name"], d.get("description", d["name"])), encoding="utf-8")
        print(f"Страница {page_p.relative_to(ROOT)} пересобрана из шаблона")
        return

    if not a.name:
        sys.exit("Нужно название компании: new_company.py TICKER \"Name\" \"Сектор\"")
    if data_p.exists() and not a.force:
        sys.exit(f"{data_p.relative_to(ROOT)} уже есть. Для пересборки страницы: --refresh-page; перезаписать данные: --force")

    d = json.loads((TPL / "example.json").read_text(encoding="utf-8"))
    d.pop("_comment", None)
    today = dt.date.today().isoformat()
    desc = f"{a.name} ({t}): справедливая цена, из чего она складывается, сравнение с аналогами, риски и калькулятор «что если»."
    d.update({"ticker": t, "name": a.name, "exchange": a.exchange, "sector": a.sector, "updated": today,
              "headline": f"{a.name}: ЗАМЕНИТЬ на тезис одной фразой", "description": desc,
              "_todo": "Заготовка: все цифры ниже из демо-примера и должны быть заменены. Проверка tools/check_site.py не пропустит публикацию, пока это поле на месте."})
    data_p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    page_p.parent.mkdir(exist_ok=True)
    page_p.write_text(page_html(t, a.name, desc), encoding="utf-8")

    cp = ROOT / "data" / "companies.json"
    lst = json.loads(cp.read_text(encoding="utf-8"))
    row = {"ticker": t, "name": a.name, "sector": a.sector, "price": None, "verdict": None, "tone": "mute",
           "updated": today, "url": f"{slug}/", "draft": True}
    for i, c in enumerate(lst):
        if c["ticker"] == t:
            lst[i] = row
            break
    else:
        lst.append(row)
    cp.write_text("[\n" + ",\n".join("  " + json.dumps(c, ensure_ascii=False) for c in lst) + "\n]\n", encoding="utf-8")
    print(f"Создано: {data_p.relative_to(ROOT)}, {page_p.relative_to(ROOT)}; строка в data/companies.json (draft)")


if __name__ == "__main__":
    main()
