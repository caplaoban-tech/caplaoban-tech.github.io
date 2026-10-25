"""Модель NCKL (SOTP) — копия формулы из nckl/index.html, чтобы проверка сайта и робот цен считали то же, что видит читатель."""


def model(S, v):
    R = S["fy25_ref"]
    dl = {"lme": lambda x: (x - R["lme"]) / 1000, "co": lambda x: x - R["co"],
          "s": lambda x: x - R["s"], "hpm": lambda x: x - R["hpm"]}
    fcf = dd = 0.0
    for st in S["streams"]:
        f = st["fcf"] + sum(st["sens"][k] * dl[k](v[k]) for k in dl)
        f = max(f, 0) * (v["fx"] / R["fx"]) ** S["fx_elasticity"]
        fcf += f * v["ap"] / 100 if st.get("cash_based") else f
        dd += f - st["fcf"]
    np_ = S["np_fy25"] + dd
    div = max(0, min(np_ * v["po"] / 100, fcf))
    ret = fcf - div
    eq = fcf / (v["y"] / 100) - ret * (1 - v["rv"] / 100) / (v["y"] / 100) - S["net_debt"]
    return eq / S["shares_m"] * 1e6


def scenario(S, sid, **over):
    sc = next(z for z in S["scenarios"] if z["id"] == sid)
    v = {**S["defaults"], **{k: sc[k] for k in ("lme", "co", "s", "hpm", "fx")}, **over}
    return model(S, v)


def drift(d):
    """Оценка «Сейчас» против той, при которой сделан вывод. Возвращает (сейчас, якорь, флаг «вывод устарел»)."""
    S, a, P = d["sotp"], d["sotp"]["anchor"], d["price"]["value"]
    now = scenario(S, "now")
    stale = abs(now / a["ps"] - 1) > a.get("tolerance", 0.10) or now < P
    return now, a, stale
