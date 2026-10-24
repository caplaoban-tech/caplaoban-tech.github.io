"""Ежедневное обновление рыночных данных для сайта Cap Laoban.

Источники (бесплатные, официальные или общепринятые):
  - никель LME cash settlement — westmetall.com (публикует официальные цены LME за день);
  - цена NCKL — Yahoo Finance (NCKL.JK);
  - курс USD/IDR — Bank Indonesia JISDOR; запасной вариант — Yahoo (IDR=X).
Каждый источник обновляется независимо: если один не ответил, остальные всё равно обновятся,
а у не обновлённого показателя остаются прежние значение и дата.
"""
import csv, datetime as dt, json, pathlib, re, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
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

def main():
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
    nk["updated"] = dt.date.today().isoformat()
    save(DATA / "nckl.json", nk)

    if "px" in got:
        cos = load(DATA / "companies.json")
        for c in cos:
            if c["ticker"] == "NCKL": c["price"] = got["px"]["value"]; c["updated"] = got["px"]["date"]
        save(DATA / "companies.json", cos)

    for k, name in (("lme", "lme_nickel"), ("px", "nckl"), ("fx", "usd_idr")):
        if k in got: history(name, got[k]["date"], got[k]["value"])
    if errors: print("Не обновились:", "; ".join(errors))
    return 0

if __name__ == "__main__":
    sys.exit(main())
