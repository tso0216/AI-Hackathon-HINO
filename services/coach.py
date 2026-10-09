"""AI 原因說明與建議：司機改善建議與 LINE 週回饋、車輛油耗說明、客戶延誤通知。"""
import json
import threading

from config import Config
from services import engine, live
from services.ai_client import ai
from services.data import DRIVERS, period_label

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


# ---------------- 司機 ----------------
def driver_advice(driver_id, period):
    return _cached(("driver", driver_id, period), lambda: _driver_advice(driver_id, period))


def _driver_advice(driver_id, period):
    d = DRIVERS[driver_id]
    row = next((r for r in engine.driver_scores(period) if r["driver_id"] == driver_id), None)
    if not row:
        return {"findings": [], "actions": [], "line_message": "", "mode": "rule", "headline": "此期間沒有行駛資料"}
    fb = engine.fuel_breakdown(d["plate"], period)
    facts = {
        "driver": d["name"], "nick": d["nick"], "years": d["years"], "plate": d["plate"], "series": row["series"],
        "period": period_label(period), "score": row["score"], "sub": row["sub"],
        "prev": row.get("prev"), "metrics": row["metrics"], "has_dms": row["has_dms"],
        "fuel_breakdown": {k: fb[k] for k in ("l100", "median_l100", "excess_pct", "excess_ntd", "factors")} if fb and fb.get("factors") else None,
        "dms_events_by_hour": engine.event_hours(d["plate"], period, {12, 14, 16}) if row["has_dms"] else None,
        "note": "準時率為模擬資料。HINO 300 沒有 DMS。事件門檻可能各車不同，已同時對照同車型與自身歷史。",
    }

    def fallback():
        weakest = min(row["sub"], key=row["sub"].get)
        label = {"safety": "安全", "eco": "節能", "ontime": "準時", "compliance": "合規"}[weakest]
        return {"headline": f"{label}是目前最需要加強的項目",
                "findings": [f"綜合 {row['score']} 分，{label} {row['sub'][weakest]} 分為最低項"],
                "actions": ["與司機一起看本月事件紀錄", "設定下月具體目標並追蹤"],
                "line_message": f"{d['nick']}辛苦了！本月綜合 {row['score']} 分，{label}還有進步空間，下個月一起加油 💪"}

    system = (
        "你是車隊的 AI 安全與節能教練。根據數據為老闆寫這位司機的分析，並寫一則傳給司機本人的 LINE 週回饋。"
        "繁體中文、具體、不說教。只能使用提供的數字，不可編造或改動，也不要自己加總、相減或換算出新數字。"
        '輸出 JSON：{"headline": "20 字內的一句話結論", "findings": ["…", "…", "…"], "actions": ["…", "…"], "line_message": "…"}。'
        "findings 3 點，每點 35 字內，指出表現好壞與原因（附數字、與同車型或自己上期比較）；"
        "actions 2 點，每點 25 字內，老闆可以採取的具體行動（例如排班、面談、輔導主題）；"
        "line_message 80 字內，用「X師傅」稱呼，先肯定做得好的地方，再提 1 個具體改善目標，語氣像關心的老闆。"
    )
    out, mode = ai.chat_json(system, json.dumps(facts, ensure_ascii=False, default=str), fallback)
    return {**fallback(), **out, "mode": mode}


# ---------------- 車輛 ----------------
def vehicle_explain(plate, period):
    return _cached(("vehicle", plate, period), lambda: _vehicle_explain(plate, period))


def _vehicle_explain(plate, period):
    fb = engine.fuel_breakdown(plate, period)
    if not fb or not fb.get("factors"):
        return {"headline": (fb or {}).get("note") or "此期間沒有足夠資料", "explain": "", "actions": [], "mode": "rule"}
    ms = engine.maintenance_status()[plate]
    facts = {**fb, "driver": engine.DRIVER_BY_PLATE[plate]["name"], "dtc": ms["dtc"], "maintenance": ms,
             "diesel_price": Config.DIESEL_PRICE}
    if fb["excess_l"] <= 0:
        return {"headline": f"油耗 {fb['l100']} L/100km，優於同車型中位數 {fb['median_l100']}", "explain": "維持目前的駕駛習慣即可。",
                "actions": [], "mode": "rule"}

    def fallback():
        f0 = fb["factors"][0]
        return {"headline": f"比同車型多耗 {fb['excess_pct']}%，主因是{f0['name']}",
                "explain": f"{f0['detail']}，約多耗 {f0['liters']} 公升（NT${f0['ntd']:,}）。",
                "actions": ["卸貨等待時熄火", "安排駕駛節能輔導"]}

    system = (
        "你是車隊的 AI 節能顧問，向車隊老闆說明這台車為什麼比較耗油。繁體中文、白話。只能使用提供的數字，不可改動，也不要自己加總、相減或換算出新數字。"
        '輸出 JSON：{"headline": "25 字內結論", "explain": "70 字內，說明主要原因與金額", "actions": ["…", "…", "…"]}。'
        "actions 3 點，每點 22 字內，依效益排序，要具體（例如：卸貨超過 3 分鐘熄火、檢查 DPF）。"
        "若有 DPF 相關故障碼（P2002、P244B），要提醒可能影響油耗。「其他」類別代表行車事件無法解釋的部分，可提醒檢查載重、路線或車況。"
    )
    out, mode = ai.chat_json(system, json.dumps(facts, ensure_ascii=False, default=str), fallback)
    return {**fallback(), **out, "mode": mode}


# ---------------- 客戶延誤通知 ----------------
def customer_notice(task_id, t):
    k = live.task_detail(task_id, t)
    if not k:
        return None
    facts = {"customer": k["customer"], "contact": k["contact"], "window": f"{k['window_start']}–{k['window_end']}",
             "eta": k["eta"], "delay_min": k["delay_min"], "cargo": k["cargo"], "driver": k["driver"][0] + "師傅",
             "reason": (k.get("pred") or {}).get("rain") or "路況", "company": Config.COMPANY}

    def fallback():
        return {"message": f"{k['contact']}您好，這裡是{Config.COMPANY}。今天要送到{k['customer']}的{k['cargo']}，"
                           f"因{facts['reason']}影響，預計 {k['eta']} 左右抵達，比約定的 {k['window_end']} 晚約 {k['delay_min']} 分鐘，"
                           "造成不便非常抱歉。司機抵達前會再跟您聯繫，謝謝您的體諒！"}

    system = (
        f"你是貨運公司「{Config.COMPANY}」的調度助理，替老闆擬一則傳給客戶的 LINE 延誤通知。繁體中文、禮貌、簡潔，90 字內。"
        "要包含：客戶稱呼、貨物、新的預計到達時間、延誤原因、致歉、司機抵達前會再聯繫。只能使用提供的資訊。"
        '輸出 JSON：{"message": "…"}'
    )
    out, mode = ai.chat_json(system, json.dumps(facts, ensure_ascii=False), fallback)
    return {"task": {x: k[x] for x in ("id", "customer", "contact", "eta", "window_end", "delay_min", "cargo", "driver", "plate")},
            "message": out.get("message") or fallback()["message"], "mode": mode}


def mark_sent(task_id, t):
    from services.data import sec_to_hhmm

    live.SENT[task_id] = sec_to_hhmm(t)
    live.snapshot.cache_clear()
