"""客訴助理：分類客訴，調出對應行程的 iTRAQ 真實軌跡與事件作為佐證，產生處理建議與回覆草稿。
客訴內容與客戶為模擬資料；佐證的軌跡與事件為真實資料。"""
import json
import threading

from config import Config
from services.ai_client import ai
from services.data import COMPLAINTS, DRIVERS, EVENT_NAMES, EVENTS, TASKS, TRACKS, hhmm_to_sec, sec_to_hhmm

_cache = {}
_lock = threading.Lock()
WINDOW_BEFORE = 90 * 60


def listing():
    out = []
    for c in COMPLAINTS:
        d = DRIVERS[c["driver"]]
        out.append({**c, "driver_name": d["name"], "status": _status.get(c["id"], c["status"])})
    return out


_status = {}


def set_status(cid, status):
    _status[cid] = status


def clear():
    _status.clear()
    with _lock:
        _cache.clear()


def evidence(c):
    date = Config.PREV_DAY
    task = next(k for k in TASKS[date] if k["id"] == c["task_id"])
    tasks = [k for k in TASKS[date] if k["plate"] == c["plate"]]
    if c["channel"] == "民眾來電":          # 民眾通報以來電時間前後為準
        center = hhmm_to_sec(c["received"][11:16])
        lo, hi = center - 60 * 60, center + 5 * 60
    else:
        lo, hi = task["arrive_sec"] - WINDOW_BEFORE, task["depart_sec"] + 5 * 60
    evs = []
    for t, ty, dur, lat, lon, x in EVENTS[c["plate"]]:
        if t[:10] != date:
            continue
        s = hhmm_to_sec(t[11:16]) + int(t[17:19]) / 60
        if lo <= s <= hi and ty != 9:
            label = EVENT_NAMES.get(ty, str(ty))
            if ty in (6, 7) and x:
                label += f"（速差 {x} km/h）"
            if ty == 8 and x and x[1]:
                label += f"（路段限速 {x[1]} km/h）"
            if dur:
                label += f"，持續 {dur // 60} 分 {dur % 60} 秒" if dur >= 60 else f"，持續 {dur} 秒"
            evs.append({"time": t[11:19], "type": ty, "name": EVENT_NAMES.get(ty, str(ty)), "label": label, "lat": lat, "lon": lon})
    track = TRACKS[date].get(c["plate"], [])
    seg = [p for p in track if lo <= p[0] <= hi]
    at_stop = [p for p in track if task["arrive_sec"] <= p[0] <= task["depart_sec"]]
    engine_on = sum(min(at_stop[i + 1][0] - p[0], 120) for i, p in enumerate(at_stop[:-1]) if p[4] != 0 and p[3] == 0)
    counts = {}
    for e in evs:
        counts[e["name"]] = counts.get(e["name"], 0) + 1
    prev_task = next((k for k in reversed(tasks) if k["depart_sec"] <= task["arrive_sec"] and k["id"] != task["id"]), None)
    return {
        "date": date, "task": {x: task[x] for x in ("id", "customer", "city", "district", "window_start", "window_end",
                                                     "arrive_actual", "depart_actual", "cargo")},
        "late_min": round((task["arrive_sec"] - hhmm_to_sec(task["window_end"])) / 60),
        "stop_minutes": round((task["depart_sec"] - task["arrive_sec"]) / 60),
        "engine_on_at_stop_min": round(engine_on / 60),
        "prev_stop": {"customer": prev_task["customer"], "depart": prev_task["depart_actual"]} if prev_task else None,
        "first_departure": sec_to_hhmm(track[0][0]) if track else None,
        "window": f"{sec_to_hhmm(lo)}–{sec_to_hhmm(hi)}", "event_counts": counts, "events": evs[-40:],
        "max_speed": max((p[3] for p in seg), default=0),
        "track": [[p[1], p[2]] for p in seg][::2], "stop": [task["lat"], task["lon"]],
    }


def analyze(cid):
    with _lock:
        if cid in _cache:
            return _cache[cid]
    c = next(x for x in COMPLAINTS if x["id"] == cid)
    ev = evidence(c)
    d = DRIVERS[c["driver"]]
    facts = {"complaint": {k: c[k] for k in ("channel", "received", "text", "customer", "plate")},
             "driver": d["name"], "driver_years": d["years"],
             "evidence": {k: v for k, v in ev.items() if k not in ("track", "stop", "events")},
             "event_list": [e["time"] + " " + e["label"] for e in ev["events"]]}

    def fallback():
        text = c["text"]
        if "破" in text or "凹" in text:
            cat, sev = "貨損", "高"
        elif "等" in text or "延誤" in text or "才到" in text:
            cat, sev = "延誤", "中"
        elif "熄火" in text or "怠速" in text:
            cat, sev = "怠速擾鄰", "中"
        else:
            cat, sev = "危險駕駛", "高"
        return {"category": cat, "severity": sev,
                "judgement": f"行程中有 {sum(ev['event_counts'].values())} 筆相關事件，需與司機確認。",
                "evidence_summary": [f"{k} {v} 次" for k, v in ev["event_counts"].items()][:4],
                "suggestions": ["調閱行車影像確認", "與司機面談了解狀況", "回覆客戶處理進度"],
                "reply_draft": f"您好，非常抱歉造成您的困擾。我們已調出當天行車紀錄，正在與司機確認，今天內會再回覆您處理方式。{Config.COMPANY} 敬上"}

    system = (
        f"你是貨運公司「{Config.COMPANY}」的客訴處理助理。根據客訴內容與 iTRAQ 行程紀錄，幫老闆判斷並擬回覆。"
        "繁體中文、客觀、不預設立場：證據支持就承認並提出改善，證據不足就說明需要再確認（例如調閱影像）。只能引用提供的數據。"
        '輸出 JSON：{"category": "貨損|延誤|怠速擾鄰|危險駕駛|服務態度|其他", "severity": "高|中|低", '
        '"judgement": "60 字內，依證據判斷客訴是否成立與可能原因", "evidence_summary": ["…", "…", "…"], '
        '"suggestions": ["…", "…", "…"], "reply_draft": "120 字內，給客戶的回覆，誠懇、具體說明後續處理"}。'
        "evidence_summary 每點 30 字內，引用時間與數字；suggestions 每點 22 字內，對內處理（司機輔導、流程改善、賠償評估）。"
    )
    out, mode = ai.chat_json(system, json.dumps(facts, ensure_ascii=False, default=str), fallback)
    res = {"complaint": {**c, "driver_name": d["name"]}, "evidence": ev, "analysis": {**fallback(), **out}, "mode": mode}
    with _lock:
        _cache[cid] = res
    return res
