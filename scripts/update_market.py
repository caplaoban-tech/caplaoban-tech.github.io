"""Ежедневное обновление рыночных данных для сайта Cap Laoban.

Источники (бесплатные, официальные или общепринятые):
  - никель LME cash settlement — westmetall.com (публикует официальные цены LME за день);
  - цена NCKL — Yahoo Finance (NCKL.JK);
  - терминалы компаний (data/fin/*.json): закрытия A и H и курс HKDCNY=X — Yahoo Finance, в data/history/<тикер>_px.csv;
  - курс USD/IDR — Bank Indonesia JISDOR; запасной вариант — Yahoo (IDR=X).
Каждый источник обновляется независимо: если один не ответил, остальные всё равно обновятся,
а у не обновлённого показателя остаются прежние значение и дата.
"""
import csv, datetime as dt, json, pathlib, re, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "tools"))
from nckl_model import drift  # noqa: E402
UA = {"User-Agent": "Mozilla/5.0 (compatible; caplaoban-bot/1.0; +https://caplaoban-tech.github.io)"}
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july",
                                       "august", "september", "october", "november", "december"], 1)}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

def num(s):
    return float(s.replace(",", "").replace(" ", "").strip())

def parse_date_en(s):
    m = re.search(r"(\d{1,2})\.?\s+([A-Za-z]+)\s+(\d{4})", s)
    if not m:
        return None
    mon = MONTHS.get(m.group(2).lower())
    return dt.date(int(m.group(3)), mon, int(m.group(1))).isoformat() if mon else None

def fetch_lme():
    html = get("https://www.westmetall.com/en/markdaten.php?action=table&field=LME_Ni_cash")
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S | re.I):
        cells = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S | re.I)]
        if len(cells) >= 2:
            d = parse_date_en(cells[0])
            if d and re.match(r"^[\d,.]+$", cells[1]):
                return {"value": round(num(cells[1])), "date": d, "source": "LME cash settlement через westmetall.com",
                        "url": "https://www.westmetall.com/en/markdaten.php?action=table&field=LME_Ni_cash"}
    raise ValueError("таблица westmetall не распознана")

def fetch_yahoo(symbol):
    j = json.loads(get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=5d&interval=1d"))
    meta = j["chart"]["result"][0]["meta"]
    d = dt.datetime.utcfromtimestamp(meta["regularMarketTime"]).date().isoformat()
    return meta["regularMarketPrice"], d

def fetch_nckl():
    v, d = fetch_yahoo("NCKL.JK")
    return {"value": round(v), "date": d, "source": "Yahoo Finance (NCKL.JK), закрытие", "url": "https://finance.yahoo.com/quote/NCKL.JK"}

def fetch_fx():
    try:
        html = get("https://www.bi.go.id/en/statistik/informasi-kurs/jisdor/Default.aspx")
        text = re.sub(r"<[^>]+>", " ", html)
        m = re.search(r"(\d{1,2}\s+[A-Za-z]+\s+\d{4})\s+Rp\s*([\d,]+\.\d+)", text)
        if m:
            return {"value": round(num(m.group(2))), "date": parse_date_en(m.group(1)), "source": "Bank Indonesia, JISDOR",
                    "url": "https://www.bi.go.id/en/statistik/informasi-kurs/jisdor/Default.aspx", "class": "А"}
    except Exception as e:  # noqa: BLE001
        print("JISDOR недоступен:", e)
    v, d = fetch_yahoo("IDR=X")
    return {"value": round(v), "date": d, "source": "Yahoo Finance (IDR=X), рыночный курс", "url": "https://finance.yahoo.com/quote/IDR=X", "class": "В"}

def load(p): return json.loads(p.read_text(encoding="utf-8"))
def save(p, o): p.write_text(json.dumps(o, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def history(name, date, value):
    p = DATA / "history" / f"{name}.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    rows = list(csv.reader(p.open(encoding="utf-8"))) if p.exists() else [["date", "value"]]
    if not any(r[0] == date for r in rows[1:]):
        rows.append([date, str(value)])
        with p.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

def yahoo_series(symbol):
    """Дневные закрытия за 5 дней: {дата: цена}."""
    j = json.loads(get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=5d&interval=1d"))
    r = j["chart"]["result"][0]; off = r["meta"].get("gmtoffset", 0)
    cl = r["indicators"]["quote"][0]["close"]
    return {dt.datetime.utcfromtimestamp(t + off).date().isoformat(): round(c, 4) for t, c in zip(r["timestamp"], cl) if c is not None}

def ysym(code):
    """Код Tushare → символ Yahoo: 688187.SH → 688187.SS, 03898.HK → 3898.HK."""
    n, ex = code.split(".")
    return {"SH": f"{n}.SS", "SZ": f"{n}.SZ", "HK": f"{int(n):04d}.HK"}[ex]

def update_terminals():
    """Терминалы компаний (data/fin/*.json): дописать закрытия A, H и курс HKD→CNY в data/history/<тикер>_px.csv."""
    fx = None
    for f in sorted((DATA / "fin").glob("*.json")):
        F = load(f); tk = F["ticker"]; csv_p = DATA / "history" / f"{tk}_px.csv"
        try:
            a = yahoo_series(ysym(F["a_code"])) if F.get("a_code") else {}
            h = yahoo_series(ysym(F["h_code"])) if F.get("h_code") else {}
            if fx is None: fx = yahoo_series("HKDCNY=X")
        except Exception as e:  # noqa: BLE001
            print("ошибка терминал", tk, e, file=sys.stderr); continue
        rows = {r["date"]: r for r in csv.DictReader(csv_p.open())} if csv_p.exists() else {}
        last_fx = next((rows[d]["hkdcny"] for d in sorted(rows, reverse=True) if rows[d].get("hkdcny")), "")
        for d in sorted(set(a) | set(h)):
            r = rows.get(d, {"date": d, "a": "", "h": "", "hkdcny": ""})
            if d in a: r["a"] = a[d]
            if d in h: r["h"] = h[d]
            if d in fx: r["hkdcny"] = round(fx[d], 5); last_fx = r["hkdcny"]
            elif not r["hkdcny"]: r["hkdcny"] = last_fx
            rows[d] = r
        with csv_p.open("w", newline="") as fh:
            w = csv.DictWriter(fh, ["date", "a", "h", "hkdcny"]); w.writeheader()
            for d in sorted(rows): w.writerow(rows[d])
        print("терминал", tk, "A", a, "H", h)

def main():
    update_terminals()
    got, errors = {}, []
    for key, fn in (("lme", fetch_lme), ("px", fetch_nckl), ("fx", fetch_fx)):
        try:
            got[key] = fn(); print(key, got[key])
        except Exception as e:  # noqa: BLE001
            errors.append(f"{key}: {e}"); print("ошибка", key, e, file=sys.stderr)
    if not got:
        print("Ничего не обновлено"); return 1

    mk = load(DATA / "markets.json")
    for s in mk["series"]:
        if s["id"] in got:
            g = got[s["id"]]
            s.update({"value": g["value"], "date": g["date"], "source": g["source"], "url": g["url"]})
            if "class" in g: s["class"] = g["class"]
    mk["updated"] = dt.date.today().isoformat()
    mk["update_mode"] = ("Автоматически каждый рабочий день: никель LME, курс рупии, цена акции (GitHub Actions). "
                         "Вручную раз в неделю: сера, MHP, payable, руда, HMA.")
    save(DATA / "markets.json", mk)

    nk = load(DATA / "nckl.json")
    if "px" in got:
        nk["price"].update({"value": got["px"]["value"], "date": got["px"]["date"], "source": got["px"]["source"]})
    sotp = nk["sotp"]
    for k in ("lme", "fx"):
        if k in got:
            sotp["defaults"][k] = got[k]["value"]
            for sc in sotp["scenarios"]:
                if sc["id"] == "now": sc[k] = got[k]["value"]
                elif k == "fx" and sc["id"] != "fy25": sc[k] = got[k]["value"]
    # nk["updated"] — дата разбора, робот её не трогает; свежесть цен видна в markets.json и у каждого входа
    save(DATA / "nckl.json", nk)
    now, a, stale = drift(nk)
    print(f"NCKL: модель «Сейчас» {now:.0f} при цене {nk['price']['value']} (вывод сделан при {a['ps']} / {a['price']})"
          + (" — ВЫВОД УСТАРЕЛ, на странице плашка" if stale else ""))

    if "px" in got:
        cos = load(DATA / "companies.json")
        for c in cos:
            if c["ticker"] == "NCKL": c["price"] = got["px"]["value"]
        save(DATA / "companies.json", cos)

    for k, name in (("lme", "lme_nickel"), ("px", "nckl"), ("fx", "usd_idr")):
        if k in got: history(name, got[k]["date"], got[k]["value"])
    if errors: print("Не обновились:", "; ".join(errors))
    return 0

if __name__ == "__main__":
    sys.exit(main())
