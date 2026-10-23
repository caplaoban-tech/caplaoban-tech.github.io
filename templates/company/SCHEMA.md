# Формат data/<тикер>.json (schema 1)

Страница компании — это `templates/company/index.html`, скопированная в `<тикер>/index.html`. Она ничего не знает о компании: всё берёт из JSON. Живой пример — `templates/company/example.json`; шаблон с ним открывается по адресу `/templates/company/`.

## Шапка
| Поле | Что это |
|---|---|
| `schema`, `kind` | `1`, `"company"` |
| `ticker`, `name`, `exchange`, `sector` | Тикер, название, биржа, сектор |
| `updated` | Дата разбора, `ГГГГ-ММ-ДД` |
| `headline` | Заголовок-тезис (одна фраза, не название компании) |
| `description` | 1–2 предложения для поисковиков и превью ссылки |
| `price` | `{value, date, currency, source, url?, class}` |
| `verdict` | `{label, detail, tone}`; tone: `good` / `warn` / `bad` / `mute` |
| `risk_gate` | `GREEN` / `AMBER` / `RED` из риск-гейта |
| `kpi[]` | `{v, k, class}` — 4 ключевые цифры |

## Оценка (`valuation`) — структура видна читателю
Стоимость = Σ частей + Σ поправок, затем ÷ акций.

- `inputs[]` — каждый ползунок: `{id, group, label, unit?, fmt?, decimals?, term?, min, max, step, now, range?, source, url?, date?, class, stale_days?, to_company?}`.
  - `group: "market"` — рыночный вход (сырьё, курс, ставка). **Обязательны `source` и `date`**; попадает в блок «Входы модели: источник и дата», через `stale_days` (по умолчанию 7) получает метку «устарело».
  - `group: "model"` — допущение оценки (доходность, пейаут, скидка).
  - `range` — разумный диапазон для «торнадо» (по умолчанию min–max).
  - `to_company` — как вход доходит до компании (лаг, формула цены).
- `yield_input` — id входа с требуемой доходностью, %.
- `streams[]` — части стоимости: `{id, name, kind, base, calc, src, class, sens, sens_note?, haircut_input?}`.
  - `kind: "cf"` — годовой денежный поток, делится на требуемую доходность; `"value"` — уже стоимость (например, P/B × капитал).
  - `base` — значение при `now` всех входов, в `units`.
  - `sens` — `{id_входа: изменение потока на 1 единицу входа}`. Линейно, поэтому чувствительность пишется явно и обосновывается в `sens_note`.
  - `haircut_input` — id входа в %, на который умножается часть (скидка за невыплаченное и т. п.).
  - `calc` и `src` — **обязательны**: как посчитан поток и откуда цифры.
- `adjustments[]` — `{name, value, src, class}`; долг со знаком минус.
- `units`, `unit_mult` (1e12 для «трлн»), `per_share_unit`, `shares_m` (млн акций).
- `scenarios[]` — `{id, name, values:{id: значение}}`; «Сейчас» добавляется сам.
- `not_included[]` — что модель не учитывает.

## Шкала справедливой цены
`fair_value: {bear, lo, hi, bull, note}` — **id сценариев**, а не числа: шкала считается той же моделью, поэтому не расходится с калькулятором.

## Остальное
- `charts[]` — столбцы с накоплением: `{eyebrow, title, decimals?, series:[{key,label,color}], data:[{label, <key>: число}], note}`; цвета: `steel`, `ore`, `red`, `good`, `warn`.
- `peers` — `{eyebrow, title, cols:[компания, аналоги…], rows:[[показатель, …]], note}`; первая колонка значений — сама компания.
- `risks[]` — `{tone, text}`; `triggers[]` — `{when, text}`; `sources[]` — строки.
- `glossary` — `{ключ: {t, d}}`. В любом тексте `{{ключ|слово}}` превращается в сноску-подсказку.

## Метки достоверности
`class`: `А` — из отчётности, `Б` — расчёт, `В` — внешний источник или оценка.
