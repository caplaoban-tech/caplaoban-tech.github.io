#!/bin/bash
# Опубликовать короткий разбор: tools/publish_brief.sh ТИКЕР "сообщение коммита"
# Собирает страницу (tools/brief.py), проверяет сайт (0 ошибок), коммитит от caplaoban-tech и пушит.
set -euo pipefail
cd "$(dirname "$0")/.."
T="$1"; MSG="${2:-Короткий разбор: $1}"
python3 tools/brief.py "$T" > /dev/null
# в ленту главной — только уже опубликованные разборы и текущий (черновики других не светим)
python3 - "$T" <<'PY'
import json, subprocess, sys
pub = set(subprocess.run(["git", "ls-files", "data/briefs"], capture_output=True, text=True).stdout.split())
cur = sys.argv[1].lower()
f = "data/briefs.json"; feed = json.load(open(f))
feed = [b for b in feed if f"data/briefs/{b['ticker'].lower()}.json" in pub or b["ticker"].lower() == cur]
open(f, "w").write(json.dumps(feed, ensure_ascii=False, indent=2) + "\n")
print("в ленте:", ", ".join(b["ticker"] for b in feed))
PY
PY=python3; [ -x /tmp/pwvenv/bin/python ] && PY=/tmp/pwvenv/bin/python
OUT=$(LD_LIBRARY_PATH=/tmp/pwlibs/root/usr/lib/x86_64-linux-gnu $PY tools/check_site.py --fix 2>&1 | tail -1)
echo "$OUT"
case "$OUT" in *"ошибок 0"*) ;; *) echo "проверка не прошла — не публикую"; exit 1;; esac
t=$(echo "$T" | tr 'A-Z' 'a-z')
git add "data/briefs/$t.json" "briefs/$t" data/briefs.json data/companies.json
git -c user.name=caplaoban-tech -c user.email=caplaoban-tech@users.noreply.github.com commit -q -m "$MSG"
git pull -q --rebase --autostash origin main && git push -q origin main
git log --oneline -1
