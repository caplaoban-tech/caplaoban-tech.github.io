#!/usr/bin/env python3
"""Проверка сайта перед публикацией. Запускать перед каждым push:

    python3 tools/check_site.py            # проверить всё (статика + рендер в браузере, если есть Playwright)
    python3 tools/check_site.py --fix      # заодно подтянуть цену/вердикт/дату в data/companies.json из data/<тикер>.json
    python3 tools/check_site.py --shots DIR  # сохранить скриншоты страниц на ширине телефона

Ошибки (ERROR) блокируют публикацию, предупреждения (WARN) — нет.
"""
import argparse, datetime as dt, functools, http.server, json, pathlib, re, socketserver, sys, threading

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", ".github", "node_modules", "__pycache__", ".claude"}
errors, warns = [], []
err = lambda m: errors.append(m)
warn = lambda m: warns.append(m)


def public_files(exts, with_templates=False):
    skip = SKIP_DIRS if with_templates else SKIP_DIRS | {"templates"}
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix in exts and not (set(p.relative_to(ROOT).parts) & skip):
            yield p


def rel(p):
    return str(p.relative_to(ROOT))


def check_html():
    for p in public_files({".html"}):
        s = p.read_text(encoding="utf-8", errors="replace")
        if len(s.strip()) < 200 or "</html>" not in s:
            err(f"{rel(p)}: страница пустая или обрезана ({len(s)} байт)")
            continue
        if re.search(r"__(TICKER|NAME|DESCRIPTION|FILE)__", s):
            err(f"{rel(p)}: остались незаменённые метки шаблона")
        if "<title>" not in s:
            err(f"{rel(p)}: нет <title>")
        markup = re.sub(r"<script\b.*?</script>", "", s, flags=re.S | re.I)
        for ref in re.findall(r'(?<![\w-])(?:href|src)="([^"]+)"', markup):
            if re.match(r"^(https?:|mailto:|tel:|#|data:|javascript:)", ref) or "${" in ref:
                continue
            clean = ref.split("?")[0].split("#")[0]
            target = (ROOT / clean.lstrip("/")) if clean.startswith("/") else (p.parent / clean)
            if ref.endswith("/") or target.is_dir():
                target = target / "index.html"
            if not target.exists():
                err(f"{rel(p)}: ссылка на несуществующий файл {ref}")


def check_branding():
    for p in public_files({".html", ".json", ".js", ".css", ".svg"}, with_templates=True):
        s = p.read_text(encoding="utf-8", errors="replace")
        if re.search(r"claude\.ai|anthropic\.com", s, re.I):
            err(f"{rel(p)}: в публичном файле есть ссылка на claude.ai/anthropic — на сайте её быть не должно")


def load_json(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        err(f"{rel(p)}: JSON не читается — {e}")
        return None


def age(d):
    try:
        return (dt.date.today() - dt.date.fromisoformat(d)).days
    except Exception:
        return None


def check_company(p, d):
    name = rel(p)
    if "_todo" in d:
        err(f"{name}: заготовка — цифры из демо-примера ещё не заменены (удалите поле _todo, когда данные настоящие)")
    for k in ["ticker", "name", "exchange", "updated", "headline", "price", "verdict", "valuation", "sources"]:
        if k not in d:
            err(f"{name}: нет поля {k}")
    if errors and any(e.startswith(name + ": нет поля") for e in errors):
        return
    if not d["price"].get("source") or not d["price"].get("date"):
        err(f"{name}: у цены акции нет источника или даты")
    V = d["valuation"]
    ids = set()
    for i in V.get("inputs", []):
        ids.add(i["id"])
        for k in ["min", "max", "step", "now", "label"]:
            if k not in i:
                err(f"{name}: вход {i.get('id')} без поля {k}")
        if "min" in i and "max" in i and "now" in i and not (i["min"] <= i["now"] <= i["max"]):
            err(f"{name}: вход {i['id']}: «сейчас» {i['now']} вне диапазона ползунка {i['min']}–{i['max']}")
        if i.get("group") == "market":
            if not i.get("source") or not i.get("date"):
                err(f"{name}: рыночный вход {i['id']} без источника или даты — так публиковать нельзя")
            elif (a := age(i["date"])) is not None and a > i.get("stale_days", 7):
                warn(f"{name}: рыночный вход {i['id']} устарел на {a} дн. ({i['date']})")
    if V.get("yield_input") and V["yield_input"] not in ids:
        err(f"{name}: yield_input «{V['yield_input']}» не найден среди входов")
    kinds = set()
    for s in V.get("streams", []):
        kinds.add(s.get("kind"))
        if not s.get("calc") or not s.get("src"):
            err(f"{name}: часть «{s.get('name')}» без расчёта (calc) или источника (src) — читатель не сможет её проверить")
        for k in s.get("sens", {}):
            if k not in ids:
                err(f"{name}: часть «{s.get('name')}»: чувствительность к неизвестному входу {k}")
        if s.get("haircut_input") and s["haircut_input"] not in ids:
            err(f"{name}: часть «{s.get('name')}»: haircut_input {s['haircut_input']} не найден")
    if "cf" in kinds and not V.get("yield_input"):
        err(f"{name}: есть денежные потоки (kind=cf), но не задан yield_input")
    scen = {"now"} | {s["id"] for s in V.get("scenarios", [])}
    for s in V.get("scenarios", []):
        for k in s.get("values", {}):
            if k not in ids:
                err(f"{name}: сценарий {s['id']}: неизвестный вход {k}")
    for k, v in (d.get("fair_value") or {}).items():
        if k in ("bear", "lo", "hi", "bull") and v not in scen:
            err(f"{name}: fair_value.{k} = «{v}» — такого сценария нет (нужен id сценария, не число)")
    G = d.get("glossary", {})
    blob = json.dumps(d, ensure_ascii=False)
    for t in set(re.findall(r"\{\{([a-z0-9_]+)\|", blob, re.I)) | {i["term"] for i in V.get("inputs", []) if i.get("term")}:
        if t not in G:
            err(f"{name}: термин «{t}» используется, но его нет в словаре (glossary)")
    if (a := age(d["updated"])) is not None and a > 120:
        warn(f"{name}: разбору {a} дн. — пора обновить")


def check_data(fix):
    for p in sorted((ROOT / "data").glob("*.json")):
        d = load_json(p)
        if isinstance(d, dict) and d.get("schema") == 1 and d.get("kind") == "company":
            check_company(p, d)
    cp = ROOT / "data" / "companies.json"
    lst = load_json(cp)
    if not isinstance(lst, list):
        return
    changed = False
    for c in lst:
        if c.get("soon"):
            continue
        url = c.get("url")
        if not url or not (ROOT / url / "index.html").exists():
            err(f"data/companies.json: {c.get('ticker')}: страница {url} не существует")
            continue
        page = (ROOT / url / "index.html").read_text(encoding="utf-8")
        m = re.search(r'data-file="([^"]+)"', page)
        dp = ROOT / "data" / m.group(1) if m else ROOT / "data" / f"{c['ticker'].lower()}.json"
        if m and not dp.exists():
            err(f"{url}index.html: data-file {m.group(1)} не найден в data/")
        if c.get("kind") == "report" or not dp.exists():
            continue
        d = json.loads(dp.read_text(encoding="utf-8"))
        want = {"price": d.get("price", {}).get("value"), "verdict": d.get("verdict", {}).get("label"),
                "tone": d.get("verdict", {}).get("tone"), "updated": d.get("updated")}
        diff = {k: v for k, v in want.items() if v is not None and c.get(k) != v}
        if diff and not c.get("draft"):
            if fix:
                c.update(diff); changed = True
            else:
                warn(f"data/companies.json: {c['ticker']} расходится с {rel(dp)} по {', '.join(diff)} (запустите с --fix)")
    if changed:
        cp.write_text("[\n" + ",\n".join("  " + json.dumps(c, ensure_ascii=False) for c in lst) + "\n]\n", encoding="utf-8")
        print("data/companies.json синхронизирован с данными компаний")


def check_render(shots):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        warn("Playwright не установлен — рендер в браузере не проверен (pip install playwright && playwright install chromium)")
        return
    class Handler(http.server.SimpleHTTPRequestHandler):
        # /__tpl__/ — шаблон страницы компании с демо-данными, как будто он лежит в /<тикер>/
        def translate_path(self, path):
            clean = path.split("?")[0]
            if clean.startswith("/__tpl__/"):
                name = clean[len("/__tpl__/"):] or "index.html"
                return str(ROOT / "templates" / "company" / name)
            return super().translate_path(path)
        def log_message(self, *a):
            pass
    handler = functools.partial(Handler, directory=str(ROOT))
    srv = socketserver.TCPServer(("127.0.0.1", 0), handler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    pages = [rel(p.parent) + "/" if p.parent != ROOT else "" for p in public_files({".html"}) if p.name == "index.html"]
    if (ROOT / "templates" / "company" / "index.html").exists():
        pages.append("__tpl__/")
    if shots:
        pathlib.Path(shots).mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            for url_path in pages:
                pg = b.new_page(viewport={"width": 400, "height": 860}, device_scale_factor=1.5)
                problems = []
                pg.on("pageerror", lambda e: problems.append(f"JS: {e}"))
                pg.on("console", lambda m: problems.append(f"console: {m.text}") if m.type == "error" and "ERR_FAILED" not in m.text else None)
                # внешние шрифты в проверке не нужны — не ждём сеть
                pg.route(re.compile(r"^https?://(?!127\.0\.0\.1)"), lambda r: r.abort())
                pg.goto(f"http://127.0.0.1:{port}/{url_path}", wait_until="load")
                pg.wait_for_timeout(900)
                sw = pg.evaluate("document.documentElement.scrollWidth")
                if sw > 402:
                    problems.append(f"горизонтальная прокрутка на телефоне: ширина {sw}px")
                txt = pg.inner_text("body")
                if re.search(r"\bNaN\b|undefined|Infinity", txt):
                    problems.append("на странице видно NaN/undefined/Infinity")
                if pg.query_selector("#fair") and pg.inner_text("#fair").strip() in ("", "—"):
                    problems.append("калькулятор не посчитал справедливую цену")
                if "Не удалось загрузить" in txt:
                    problems.append("страница не смогла загрузить данные")
                for pr in problems:
                    (warn if pr.startswith("console") else err)(f"{url_path or '/'}: {pr}")
                if shots:
                    pg.screenshot(path=str(pathlib.Path(shots) / ((url_path.strip("/").replace("/", "_") or "home") + ".png")), full_page=False)
                pg.close()
            b.close()
    finally:
        srv.shutdown()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--shots")
    a = ap.parse_args()
    check_html(); check_branding(); check_data(a.fix)
    if not a.no_render:
        check_render(a.shots)
    for w in warns:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"\nИтого: ошибок {len(errors)}, предупреждений {len(warns)}" + (" — публиковать нельзя" if errors else " — можно публиковать"))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
