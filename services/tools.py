"""問 AI 可呼叫的查詢函式。回傳的數字全部由分析引擎計算；chart 欄位只給前端畫圖。"""
from config import Config
from services import engine, kb, live
from services.data import DRIVER_BY_PLATE, EVENT_NAMES, MONTHS, VEHICLES, period_label, prev_period

EVENT_BY_NAME = {"急加速": 6, "急減速": 7, "急煞": 7, "超速": 8, "引擎過載": 11, "疲勞": 12, "疲勞駕駛": 12,
                 "未繫安全帶": 13, "安全帶": 13, "使用手機": 14, "手機": 14, "抽菸": 15, "分心": 16, "PCS": 19, "LDWS": 20,
                 "車道偏離": 20}
PERIOD_ENUM = MONTHS + ["all"]
SOURCE_REAL = "iTRAQ 競賽資料"
SOURCE_MOCK = "模擬資料"


def _period(p):
    return p if p in PERIOD_ENUM else MONTHS[-1]


def _p(desc):
    return {"type": "string", "enum": PERIOD_ENUM, "description": desc}


TOOLS = [
    {"type": "function", "name": "get_fleet_overview",
     "description": "今天（demo 時間）車隊即時概況：出車數、配送進度、準點率、延誤風險、即時提醒，以及上一營運日的里程與油耗。",
     "parameters": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"type": "function", "name": "get_fuel_ranking",
     "description": "各車油耗（L/100km）排名，附同車型中位數比較與多花的油錢。",
     "parameters": {"type": "object", "properties": {
         "period": _p("資料月份，或 all 代表全期間"),
         "series": {"type": "string", "enum": ["all", "300", "500", "700"], "description": "車型，all 為全部"}},
         "required": ["period"], "additionalProperties": False}},
    {"type": "function", "name": "get_fuel_breakdown",
     "description": "單一車輛油耗偏高的原因拆解：怠速、高轉速、急加減速、超速、過載各多耗多少公升與金額。",
     "parameters": {"type": "object", "properties": {
         "plate": {"type": "string", "description": "車牌，例如 ABC-1999；也可以給駕駛姓名"},
         "period": _p("資料月份或 all")}, "required": ["plate", "period"], "additionalProperties": False}},
    {"type": "function", "name": "get_driver_ranking",
     "description": "司機綜合分數排名（安全 40%、節能 30%、準時 20%、合規 10%），附與上一期比較。",
     "parameters": {"type": "object", "properties": {
         "period": _p("資料月份或 all"),
         "sort_by": {"type": "string", "enum": ["score", "safety", "eco", "ontime", "compliance", "drop"],
                     "description": "排序依據；drop 為分數下降最多"}},
         "required": ["period"], "additionalProperties": False}},
    {"type": "function", "name": "get_driver_detail",
     "description": "單一司機的分項分數、關鍵指標、各月趨勢，以及疲勞分心事件在一天中的時段分布。",
     "parameters": {"type": "object", "properties": {
         "driver": {"type": "string", "description": "司機姓名、X師傅 或車牌"},
         "period": _p("資料月份或 all")}, "required": ["driver", "period"], "additionalProperties": False}},
    {"type": "function", "name": "get_safety_events",
     "description": "某類安全事件在各車的次數與每百公里（或每駕駛小時）頻率。",
     "parameters": {"type": "object", "properties": {
         "period": _p("資料月份或 all"),
         "event": {"type": "string", "enum": sorted(set(EVENT_BY_NAME)), "description": "事件類型"}},
         "required": ["period", "event"], "additionalProperties": False}},
    {"type": "function", "name": "get_hours_compliance",
     "description": "駕駛工時合規：今天各車已駕駛時數與連續駕駛時數，以及指定期間超過單日 10 小時、連續 4 小時的紀錄。",
     "parameters": {"type": "object", "properties": {"period": _p("歷史紀錄的資料月份或 all")},
                    "required": ["period"], "additionalProperties": False}},
    {"type": "function", "name": "get_deliveries",
     "description": "今天的配送任務與延誤預測（LightGBM），可只看有延誤風險的任務。",
     "parameters": {"type": "object", "properties": {
         "only_risk": {"type": "boolean", "description": "true 只回傳有延誤風險的任務"}},
         "required": ["only_risk"], "additionalProperties": False}},
    {"type": "function", "name": "get_vehicle_status",
     "description": "單一車輛的保養到期、故障碼（DTC）、油耗與今日狀態。",
     "parameters": {"type": "object", "properties": {"plate": {"type": "string", "description": "車牌或駕駛姓名"}},
                    "required": ["plate"], "additionalProperties": False}},
    {"type": "function", "name": "search_knowledge",
     "description": "檢索法規（2026 工時新規）、iTRAQ 事件定義、故障碼說明、系統操作手冊與評分方法。",
     "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"],
                    "additionalProperties": False}},
]


def _resolve_plate(q):
    q = (q or "").strip().upper()
    if q in VEHICLES:
        return q
    d = engine.driver_by_name(q) or engine.driver_by_name(q.title())
    if d:
        return d["plate"]
    for p in VEHICLES:
        if q and q in p:
            return p
    return None


def execute(name, args, t):
    try:
        fn = globals()[f"_t_{name}"]
    except KeyError:
        return {"error": f"沒有 {name} 這個查詢函式"}
    return fn(t=t, **args)


def _t_get_fleet_overview(t):
    snap = live.snapshot(t)
    prev = engine.day_summary(Config.PREV_DAY)
    return {
        "資料區間": f"今天 {Config.TODAY} {snap['time']}（真實軌跡回放）；上一營運日 {Config.PREV_DAY}",
        "today": snap["kpi"],
        "alerts": [{"time": a["time"], "title": a["title"], "body": a["body"]} for a in snap["alerts"][:8]],
        "prev_day": {k: prev[k] for k in ("vehicles", "km", "fuel", "fuel_cost", "idle_h", "drive_h", "over10", "over4")},
        "sources": [SOURCE_REAL, f"{SOURCE_MOCK}（任務、準點率）"],
    }


def _t_get_fuel_ranking(t, period, series="all"):
    period = _period(period)
    rows = [r for r in engine.vehicle_table(period) if r["active"] and r["l100"] and (series == "all" or r["type"] == series)]
    rows.sort(key=lambda r: -(r["vs_median"] if r["vs_median"] is not None else -999))
    items = [{"plate": r["plate"], "driver": r["driver"], "series": r["series"], "l100": r["l100"],
              "median_l100": r["median_l100"], "vs_median_pct": r["vs_median"], "excess_ntd": r["excess_ntd"],
              "top_factor": r["top_factor"], "data_quality": r["quality"]} for r in rows]
    chart_rows = [r for r in rows if not r["quality"]][:10]
    return {
        "資料區間": period_label(period), "unit": "L/100km", "diesel_price": Config.DIESEL_PRICE,
        "note": "比較以同車型中位數為基準；data_quality 有值的車輛資料異常，不列入比較。",
        "ranking": items, "sources": [SOURCE_REAL],
        "chart": {"type": "bar", "title": f"油耗與同車型中位數差異（{period_label(period)}）", "unit": "%",
                  "items": [{"label": f"{r['plate']}｜{r['driver']}", "value": r["vs_median"], "highlight": i == 0,
                             "note": f"{r['l100']} L/100km"} for i, r in enumerate(chart_rows)]},
    }


def _t_get_fuel_breakdown(t, plate, period):
    period = _period(period)
    p = _resolve_plate(plate)
    if not p:
        return {"error": f"找不到車輛：{plate}"}
    fb = engine.fuel_breakdown(p, period)
    if not fb:
        return {"error": f"{p} 在 {period_label(period)} 沒有行駛資料"}
    out = {"資料區間": period_label(period), "driver": DRIVER_BY_PLATE[p]["name"], **fb, "sources": [SOURCE_REAL]}
    if fb.get("factors"):
        out["chart"] = {"type": "bar", "title": f"{p} 多耗油的原因（公升）", "unit": "L",
                        "items": [{"label": f["name"], "value": f["liters"], "highlight": i == 0, "note": f"NT${f['ntd']:,}"}
                                  for i, f in enumerate(fb["factors"])]}
    return out


def _t_get_driver_ranking(t, period, sort_by="score"):
    period = _period(period)
    rows = engine.driver_scores(period)
    key = {"score": lambda r: -r["score"], "drop": lambda r: (r["score"] - r["prev"]["score"]) if r.get("prev") else 99}
    rows = sorted(rows, key=key.get(sort_by, lambda r: -r["sub"][sort_by]))
    items = [{"rank": r["rank"], "driver": r["name"], "plate": r["plate"], "series": r["series"], "score": r["score"],
              "sub": r["sub"], "prev_score": r["prev"]["score"] if r.get("prev") else None,
              "prev_sub": r["prev"]["sub"] if r.get("prev") else None, "has_dms": r["has_dms"]} for r in rows]
    pp = prev_period(period)
    return {
        "資料區間": period_label(period), "比較期間": period_label(pp) if pp else None,
        "weights": Config.WEIGHTS, "ranking": items,
        "note": "準時分數來自模擬配送資料；HINO 300 未裝 DMS，安全分數不含 DMS 事件。",
        "sources": [SOURCE_REAL, f"{SOURCE_MOCK}（駕駛身分、準時率）"],
        "chart": ({"type": "bar", "title": f"綜合分數變化（較 {period_label(pp).split('（')[0]}）", "unit": "分",
                   "items": [{"label": r["driver"], "value": r["score"] - r["prev_score"], "highlight": i == 0,
                              "note": f"{r['prev_score']} → {r['score']} 分"} for i, r in enumerate([x for x in items if x["prev_score"] is not None][:10])]}
                  if sort_by == "drop" and pp else
                  {"type": "bar", "title": f"司機分數（{period_label(period).split('（')[0]}）", "unit": "分",
                   "items": [{"label": r["driver"], "value": r["score"] if sort_by == "score" else r["sub"][sort_by],
                              "highlight": i == 0, "note": r["plate"]} for i, r in enumerate(items[:10])]}),
    }


def _t_get_driver_detail(t, driver, period):
    period = _period(period)
    d = engine.driver_by_name(driver) or (DRIVER_BY_PLATE.get(_resolve_plate(driver) or ""))
    if not d:
        return {"error": f"找不到司機：{driver}"}
    row = next((r for r in engine.driver_scores(period) if r["driver_id"] == d["id"]), None)
    trend = engine.driver_trend(d["id"])
    hours = engine.event_hours(d["plate"], period, {12, 14, 16})
    out = {"資料區間": period_label(period), "driver": d["name"], "plate": d["plate"], "years": d["years"],
           "score": row, "trend": trend, "dms_events_by_hour": hours if sum(hours) else None,
           "sources": [SOURCE_REAL, f"{SOURCE_MOCK}（駕駛身分、準時率）"]}
    if not row:
        out["note"] = "此期間沒有行駛資料"
    if sum(hours) >= 5:
        out["chart"] = {"type": "columns", "title": f"{d['name']} 疲勞／分心／手機事件時段分布", "unit": "次",
                        "x": [f"{h}" for h in range(24)], "values": hours}
    elif len(trend) >= 2:
        out["chart"] = {"type": "line", "title": f"{d['name']} 各月綜合分數", "unit": "分",
                        "x": [m["month"][5:] + " 月" for m in trend], "series": [{"name": "綜合分數", "values": [m["score"] for m in trend]}]}
    return out


def _t_get_safety_events(t, period, event):
    period = _period(period)
    ty = EVENT_BY_NAME.get(event, 7)
    stats = engine.vehicle_stats(period)
    per_hour = ty in (12, 13, 14, 15, 16)
    rows = []
    for p, s in stats.items():
        if per_hour and not s["has_dms"]:
            continue
        rows.append({"plate": p, "driver": DRIVER_BY_PLATE[p]["name"], "series": s["series"], "count": s["events"].get(ty, 0),
                     "rate": s["rate_h"].get(ty, 0) if per_hour else s["rate"].get(ty, 0)})
    rows.sort(key=lambda r: -r["count"])
    total = sum(r["count"] for r in rows) or 1
    unit = "次/駕駛小時" if per_hour else "次/百公里"
    return {"資料區間": period_label(period), "event": EVENT_NAMES[ty], "unit": unit, "total": sum(r["count"] for r in rows),
            "top4_share": round(sum(r["count"] for r in rows[:4]) / total, 3), "by_vehicle": rows,
            "note": "各車事件門檻可能由客戶自行設定，比較時宜搭配該車自身歷史。" + ("HINO 300 未裝 DMS，不列入。" if per_hour else ""),
            "sources": [SOURCE_REAL],
            "chart": {"type": "bar", "title": f"{EVENT_NAMES[ty]}（{unit}）", "unit": "",
                      "items": [{"label": f"{r['plate']}｜{r['driver']}", "value": round(r["rate"], 2), "highlight": i == 0,
                                 "note": f"{r['count']} 次"} for i, r in enumerate(sorted(rows, key=lambda r: -r['rate'])[:10])]}}


def _t_get_hours_compliance(t, period):
    period = _period(period)
    snap = live.snapshot(t)
    today = sorted([{"plate": v["plate"], "driver": v["driver"], "drive_h": v["drive_h"], "cont_h": v["cont_h"], "state": v["state"]}
                    for v in snap["vehicles"] if v.get("drive_h")], key=lambda v: -v["cont_h"])
    viol = engine.hours_violations(period)
    return {"資料區間": f"今天 {snap['time']}；歷史 {period_label(period)}",
            "rule": f"單日駕駛上限 {Config.DAILY_LIMIT_H} 小時、連續駕駛 {Config.CONT_LIMIT_H} 小時須休息 30 分鐘（2026/5/8 施行）",
            "today": today, "violations": viol, "sources": [SOURCE_REAL],
            "chart": {"type": "bar", "title": f"今天連續駕駛時數（{snap['time']}）", "unit": "小時",
                      "items": [{"label": f"{v['driver']}｜{v['plate']}", "value": v["cont_h"], "highlight": v["cont_h"] >= 3.5,
                                 "note": f"今日 {v['drive_h']} 小時"} for v in today[:10]]}}


def _t_get_deliveries(t, only_risk=True):
    snap = live.snapshot(t)
    tasks = [k for k in snap["tasks"] if not only_risk or k["risk"] in ("high", "medium")]
    return {"資料區間": f"今天 {Config.TODAY} {snap['time']}", "kpi": snap["kpi"],
            "tasks": [{x: k[x] for x in ("id", "customer", "city", "district", "driver", "plate", "window_end", "eta",
                                         "delay_min", "status", "risk", "notified")} | {"rain": (k.get("pred") or {}).get("rain")}
                      for k in tasks],
            "sources": [f"{SOURCE_REAL}（軌跡）", f"{SOURCE_MOCK}（任務、客戶、天氣）"]}


def _t_get_vehicle_status(t, plate):
    p = _resolve_plate(plate)
    if not p:
        return {"error": f"找不到車輛：{plate}"}
    ms = engine.maintenance_status()[p]
    s = engine.vehicle_stats("all").get(p, {})
    v = next((x for x in live.snapshot(t)["vehicles"] if x["plate"] == p), {})
    return {"plate": p, "series": VEHICLES[p]["series"], "driver": DRIVER_BY_PLATE[p]["name"],
            "maintenance": ms, "l100_all_period": s.get("l100"), "today": v,
            "sources": [SOURCE_REAL, f"{SOURCE_MOCK}（保養週期）"]}


def _t_search_knowledge(t, query):
    r = kb.search(query)
    return {"results": [{"title": x["title"], "source": x["source"], "text": x["text"]} for x in r["results"]],
            "sources": [x["source"] for x in r["results"]]}
