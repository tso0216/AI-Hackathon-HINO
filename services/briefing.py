"""AI 晨報與績效月報：分析引擎先算出事實與待辦（含影響金額、風險），LLM 只負責寫成老闆看得懂的話。"""
import json
import threading

from config import Config
from services import engine, live
from services.ai_client import ai
from services.data import COMPLAINTS, DRIVERS, MONTHS, period_label, prev_period

MORNING_T = 7 * 3600 + 30 * 60
_cache = {}
_lock = threading.Lock()


def _cached(key, fn):
    with _lock:
        if key in _cache:
            return _cache[key]
    val = fn()
    with _lock:
        _cache[key] = val
    return val


def clear():
    with _lock:
        _cache.clear()


# ---------------- 晨報 ----------------
def morning_facts():
    snap = live.snapshot(MORNING_T)
    prev = engine.day_summary(Config.PREV_DAY)
    month = MONTHS[-1]
    todos = []

    # 1. 工時：上一營運日違規（同一天的多位司機合併成一件事）
    viol = [v for v in engine.hours_violations(month) if v["date"] == Config.PREV_DAY]
    if viol:
        by_driver = {}
        for v in viol:
            by_driver.setdefault((v["driver"], v["plate"]), []).append(v["label"])
        parts = []
        for (name, plate), labels in by_driver.items():
            today_v = next((v for v in snap["vehicles"] if v["plate"] == plate), None)
            parts.append(f"{name}（{plate}）{'、'.join(labels)}"
                         + (f"，今天 {today_v['depart']} 已出車" if today_v and today_v.get("depart") else ""))
        first_plate = viol[0]["plate"]
        nick = engine.DRIVER_BY_PLATE[first_plate]["nick"]
        daily = next((v for v in viol if v["plate"] == first_plate and v["kind"] == "daily"), None)
        title = f"{nick}上一營運日開了 {daily['value']:.1f} 小時" if daily else f"{nick}連續開 {viol[0]['value']:.1f} 小時未休息"
        todos.append({
            "id": "hours", "kind": "hours", "priority": 90, "plate": first_plate, "title": title,
            "fact": f"上一營運日（{Config.PREV_DAY[5:].replace('-', '/')}）工時超標：" + "；".join(parts) + "。",
            "impact": "違反 2026 工時新規，每次罰鍰 NT$9,000–90,000", "impact_value": 90000,
            "action": {"label": "查看工時", "page": "safety", "ref": first_plate},
        })

    # 2. 今日延誤風險
    risky = [k for k in snap["tasks"] if k["risk"] == "high"]
    if risky:
        cities = {}
        for k in risky:
            cities.setdefault(k["city"], []).append(k)
        main_city, ks = max(cities.items(), key=lambda x: len(x[1]))
        todos.append({
            "id": "delay-today", "kind": "delay", "priority": 85, "task_ids": [k["id"] for k in risky],
            "title": f"今天 {len(risky)} 筆配送可能延誤",
            "fact": f"今天預估 {len(risky)} 筆任務可能延誤，其中{main_city} {len(ks)} 筆："
                    + "、".join(f"{k['customer']}（預約 {k['window_end']} 前，預估 {k['eta']}，晚 {k['delay_min']} 分）" for k in ks)
                    + ("；" + "、".join(f"{k['customer']}晚 {k['delay_min']} 分" for k in risky if k["city"] != main_city) if len(risky) > len(ks) else "")
                    + "。已擬好客戶通知（任務與客戶為模擬資料）。",
            "impact": f"{len(risky)} 筆可能遲到，提前通知可避免客訴", "impact_value": 30000,
            "action": {"label": "通知客戶", "page": "delivery", "ref": risky[0]["id"]},
        })

    # 3. 油耗最偏高的車（看全期間，避免單一抽樣日的偶然）
    fuel = []
    for r in engine.vehicle_table("all"):
        fb = engine.fuel_breakdown(r["plate"], "all") if r["active"] else None
        if fb and fb.get("excess_l") and fb["excess_l"] > 0:
            fuel.append(fb)
    if fuel:
        fb = max(fuel, key=lambda f: f["excess_pct"])
        f0 = fb["factors"][0]
        yearly = fb["excess_ntd_per_day"] * 250
        todos.append({
            "id": f"fuel-{fb['plate']}", "kind": "fuel", "priority": 70 + min(15, yearly / 20000), "plate": fb["plate"],
            "title": f"{fb['plate']} 油耗比同型高 {fb['excess_pct']}%",
            "fact": f"{fb['plate']}（{engine.DRIVER_BY_PLATE[fb['plate']]['name']}）2025 年油耗 {fb['l100']} L/100km，"
                    f"比同車型（{fb['series']}）中位數 {fb['median_l100']} 高 {fb['excess_pct']}%；可歸因的最大原因是{f0['name']}（{f0['detail']}）。"
                    f"平均每個營運日多花 NT${fb['excess_ntd_per_day']:,}。",
            "impact": f"一年約多花 NT${yearly:,}（以 250 個營運日估）", "impact_value": yearly,
            "action": {"label": "看原因拆解", "page": "fleet", "ref": fb["plate"]},
        })

    # 4. 安全分數下降最多的司機
    rows = [r for r in engine.driver_scores(month) if r.get("prev")]
    if rows:
        r = min(rows, key=lambda r: r["sub"]["safety"] - r["prev"]["sub"]["safety"])
        drop = r["prev"]["sub"]["safety"] - r["sub"]["safety"]
        if drop >= 8:
            trend = engine.driver_trend(r["driver_id"])
            prev_m = next((m for m in trend if m["month"] == r["prev"]["period"]), None)
            detail = ""
            if r["has_dms"] and prev_m and prev_m["distract_per_h"] is not None:
                detail = f"分心事件每駕駛小時 {prev_m['distract_per_h']} 次 → {r['metrics']['distract_per_h']} 次"
            elif prev_m:
                detail = f"急加減速每百公里 {prev_m['harsh_100']} 次 → {r['metrics']['harsh_100']} 次"
            hours = engine.event_hours(r["plate"], month, {12, 14, 16} if r["has_dms"] else {6, 7})
            peak = max(range(24), key=lambda h: hours[h] + hours[(h + 1) % 24]) if sum(hours) else None
            todos.append({
                "id": f"safety-{r['driver_id']}", "kind": "safety", "priority": 66, "driver_id": r["driver_id"],
                "title": f"{r['nick']}安全分數掉了 {drop} 分",
                "fact": f"{r['name']}（{r['plate']}）安全分數從 {int(r['prev']['period'][5:])} 月的 {r['prev']['sub']['safety']} 分降到 {r['sub']['safety']} 分"
                        + (f"，{detail}" if detail else "") + (f"，集中在 {peak}–{peak + 2} 點" if peak is not None else "") + "。",
                "impact": "事故風險上升", "impact_value": 20000,
                "action": {"label": "看司機績效", "page": "drivers", "ref": r["driver_id"]},
            })

    # 5. 待處理客訴
    pending = [c for c in COMPLAINTS if c["status"] == "待處理"]
    if pending:
        todos.append({
            "id": "complaints", "kind": "complaint", "priority": 60, "title": f"{len(pending)} 件客訴待處理",
            "fact": f"有 {len(pending)} 件客訴待處理（模擬資料）："
                    + "、".join(f"{c['customer']}（{c['text'][:14]}…）" for c in pending[:3]) + "。AI 已調出對應行程事件。",
            "impact": "影響客戶續約", "impact_value": 15000,
            "action": {"label": "處理客訴", "page": "safety", "ref": pending[0]["id"]},
        })

    # 6. 保養與故障碼
    ms = engine.maintenance_status()
    dpf = [(p, m) for p, m in ms.items() if any(c["code"] in ("P2002", "P244B") for c in m["dtc"])]
    overdue = [(p, m) for p, m in ms.items() if m["status"] == "overdue"]
    if dpf or overdue:
        parts = []
        if dpf:
            parts.append("、".join(p for p, _ in dpf[:3]) + " 有 DPF 相關故障碼（P2002／P244B），可能影響油耗")
        if overdue:
            parts.append("、".join(f"{p} 已超過保養里程 {-m['km_left']:,} km" for p, m in overdue[:2]) + "（保養週期為模擬）")
        todos.append({
            "id": "maintenance", "kind": "maintenance", "priority": 55, "fact": "；".join(parts) + "。",
            "title": f"{len(dpf)} 台車有 DPF 故障碼" if dpf else f"{len(overdue)} 台車保養逾期",
            "impact": "延誤保養可能增加油耗與拋錨風險", "impact_value": 10000,
            "action": {"label": "看車隊績效", "page": "fleet", "ref": (dpf or overdue)[0][0]},
        })

    todos.sort(key=lambda x: -x["priority"])
    month_trend = engine.fleet_trend()
    otr = _prev_on_time()
    return {
        "time": "07:30", "date": Config.TODAY,
        "prev_day": {**prev, "on_time_rate": otr,
                     "文字": f"{Config.PREV_DAY[5:].replace('-', '/')} 出車 {prev['vehicles']} 台、行駛 {prev['km']:,} 公里、"
                             f"用油 {prev['fuel']:,} 公升（約 NT${prev['fuel_cost']:,}）、準點率 {otr * 100:.0f}%"},
        "today": {"vehicles_planned": snap["kpi"]["vehicles_planned"], "tasks_total": snap["kpi"]["tasks_total"],
                  "risk_high": snap["kpi"]["risk_high"],
                  "文字": f"今天排 {snap['kpi']['vehicles_planned']} 台車、{snap['kpi']['tasks_total']} 個配送點，"
                          f"預估 {snap['kpi']['risk_high']} 筆可能延誤"},
        "fleet_trend": month_trend[-2:],
        "todos": todos,
    }


def _prev_on_time():
    from services.data import TASKS
    tasks = TASKS[Config.PREV_DAY]
    ok = sum(1 for k in tasks if k["arrive_sec"] <= sum(int(x) * m for x, m in zip(k["window_end"].split(":"), (3600, 60))))
    return round(ok / len(tasks), 3) if tasks else None


def morning():
    return _cached("morning", _morning)


def _morning():
    facts = morning_facts()
    p = facts["prev_day"]

    def fallback():
        return {
            "summary": [
                f"早安！上一營運日（{Config.PREV_DAY[5:].replace('-', '/')}）{p['vehicles']} 台出車，跑了 {p['km']:,} 公里，"
                f"用油 {p['fuel']:,} 公升（約 NT${p['fuel_cost']:,}），準點率 {p['on_time_rate'] * 100:.0f}%（模擬）。",
                f"今天排了 {facts['today']['vehicles_planned']} 台車、{facts['today']['tasks_total']} 個配送點，"
                f"預估 {facts['today']['risk_high']} 筆可能延誤。",
            ],
            "todos": [{"id": x["id"], "why": x["fact"], "action": x["action"]["label"]}
                      for x in facts["todos"]],
        }

    system = (
        "你是車隊老闆的 AI 助理，負責寫每天 07:30 推播的 LINE 晨報。對象是忙碌的中小型貨運老闆，用繁體中文、口語、像資深調度在跟老闆報告。"
        "只能使用提供的事實與數字，不可新增、不可改動任何數字、人名、車牌，也不要自己計算新數字；數字照抄輸入中已格式化好的寫法。"
        '輸出 JSON：{"summary": ["…", "…"], "todos": [{"id": "與輸入相同", "why": "…", "action": "…"}]}。'
        "summary 剛好 2 句：第 1 句以「早安，」開頭講上一營運日重點（出車台數、里程、油錢、準點率）；第 2 句講今天的排程與最需要注意的事。每句 60 字內，數字與單位之間空一格。"
        "todos 依輸入順序全部輸出（標題已由系統產生，你不用寫）：why 50 字內，補充標題沒講到的原因與影響，保留關鍵數字，不要重複標題；"
        "action 16 字內，老闆今天具體要做的一件事，用動詞開頭，例如「中午前安排王師傅休息點」「下午 1 點前通知兩位客戶」。"
        "稱呼司機用「X師傅」。準點率、任務、客戶、客訴、保養週期是模擬資料，只在 summary 第一次提到時加「（模擬）」。"
    )
    out, mode = ai.chat_json(system, json.dumps(facts, ensure_ascii=False, default=str), fallback)
    by_id = {x["id"]: x for x in facts["todos"]}
    todos = []
    for x in out.get("todos", []):
        src = by_id.get(x.get("id"))
        if src:
            todos.append({**src, "why": x.get("why") or src["fact"],
                          "action_text": x.get("action") or src["action"]["label"]})
    for src in facts["todos"]:          # LLM 漏掉的待辦補回來
        if src["id"] not in {t["id"] for t in todos}:
            todos.append({**src, "why": src["fact"], "action_text": src["action"]["label"]})
    todos.sort(key=lambda x: -x["priority"])
    return {"time": facts["time"], "date": facts["date"], "summary": out.get("summary") or fallback()["summary"],
            "top": todos[:3], "others": todos[3:], "prev_day": p, "mode": mode,
            "data_note": f"資料：iTRAQ {Config.PREV_DAY}、{period_label(MONTHS[-1])}；任務、客戶、準點率、客訴為模擬資料"}


# ---------------- 月報與獎金建議 ----------------
BONUS_RULE = [(88, 3000), (80, 1500), (72, 500)]


def monthly(period=None):
    period = period or MONTHS[-1]
    return _cached(f"monthly-{period}", lambda: _monthly(period))


def _monthly(period):
    rows = engine.driver_scores(period)
    pp = prev_period(period)
    table = []
    for r in rows:
        bonus = next((b for th, b in BONUS_RULE if r["score"] >= th), 0)
        hold = r["sub"]["compliance"] < 60
        table.append({"driver_id": r["driver_id"], "name": r["name"], "plate": r["plate"], "score": r["score"],
                      "prev_score": r["prev"]["score"] if r.get("prev") else None, "sub": r["sub"],
                      "bonus": 0 if hold else bonus, "hold": hold,
                      "hold_reason": f"工時違規 {r['metrics']['over10'] + r['metrics']['over4']} 次" if hold else None})
    total = sum(x["bonus"] for x in table)
    trend = engine.fleet_trend()
    facts = {"period": period_label(period), "compare": period_label(pp) if pp else None,
             "bonus_rule": "綜合 ≥88 分 NT$3,000；80–87 分 NT$1,500；72–79 分 NT$500；有工時違規者暫緩",
             "drivers": table, "bonus_total": total,
             "車隊趨勢": [f"{int(x['month'][5:])} 月：HINO 300 油耗 {x['300']}、HINO 500 油耗 {x['500']}、HINO 700 油耗 {x['700']} L/100km，"
                      f"急加減速每百公里 {x['harsh_100']} 次，怠速占比 {x['idle_share'] * 100:.0f}%"
                      for x in trend if x["month"] in (period, pp)],
             "violations": engine.hours_violations(period)}

    def fallback():
        best = table[0]
        worst = table[-1]
        return {"summary": [f"{facts['period']}平均分數 {sum(x['score'] for x in table) / len(table):.0f} 分，"
                            f"建議獎金合計 NT${total:,}。",
                            f"表現最好的是{best['name']}（{best['score']} 分），最需要輔導的是{worst['name']}（{worst['score']} 分）。"],
                "next_focus": ["持續追蹤怠速占比高的車輛", "工時違規者先面談再發獎金", "分心事件增加者安排輔導"],
                "notes": {x["driver_id"]: "" for x in table}}

    system = (
        "你是車隊老闆的 AI 助理，負責寫月底績效月報。繁體中文、精簡、具體。只能使用提供的數字，不可改動，也不要自己加總、相減或換算出新數字。"
        '輸出 JSON：{"summary": ["…", "…", "…"], "next_focus": ["…", "…", "…"], "notes": {"D01": "20 字內：這位司機本月表現的重點或獎金暫緩原因", …}}。'
        "summary 3 句：整體表現與趨勢、表現最好與最需輔導的人、獎金建議合計。next_focus 為下月改善重點 3 點，每點 20 字內。"
        "notes 每位司機都要有。準時分數來自模擬資料。"
    )
    out, mode = ai.chat_json(system, json.dumps(facts, ensure_ascii=False, default=str), fallback)
    notes = out.get("notes") or {}
    for x in table:
        x["note"] = notes.get(x["driver_id"], "")
    return {"period": period, "period_label": facts["period"], "compare": facts["compare"], "summary": out.get("summary", []),
            "next_focus": out.get("next_focus", []), "drivers": table, "bonus_total": total,
            "bonus_rule": facts["bonus_rule"], "mode": mode, "n_drivers": len(DRIVERS)}
