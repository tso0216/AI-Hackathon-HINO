"""分析引擎：所有數字都在這裡由程式計算，AI 只負責解釋與建議。"""
import math
from collections import Counter, defaultdict
from functools import lru_cache
from statistics import median

from config import Config
from services.data import (
    DAYS, DMS_TYPES, DRIVER_BY_PLATE, DRIVERS, DTC_NAMES, EVENTS, EVENT_NAMES, MAINTENANCE, MONTHS, ONTIME,
    VEHICLES, period_days, period_label, prev_period,
)

SUM_KEYS = ["km", "fuel", "idle_fuel", "drive_h", "idle_h", "high_rpm_min", "high_rpm_fuel", "speeding_min", "overload_min"]
HAS_DMS = {p for p, evs in EVENTS.items() if any(e[1] in DMS_TYPES for e in evs)}

# 原因拆解用的估算係數（每次事件或每分鐘多耗的油，公升）
HARSH_L = {"300": 0.02, "500": 0.04, "700": 0.06}
SPEEDING_EXTRA = 0.15       # 超速時油耗約增加 15%
OVERLOAD_EXTRA = 0.20       # 過載時油耗約增加 20%


def _clip(x, lo, hi):
    return max(lo, min(hi, x))


def _ratio_score(value, base, k, center=80, lo=20, hi=100):
    """value 相對 base 的比值換成分數：等於基準 = center 分，加倍扣 k 分，減半加 k 分。"""
    if base is None or value is None:
        return None
    r = (value + 1e-6) / (base + 1e-6)
    return _clip(center - k * math.log2(max(r, 1e-3)), lo, hi)


def _moved(d):
    """當日里程太少（原地發動、資料異常）時，「行駛中」時數不代表真的在開車，不列入工時檢查。"""
    return d["km"] >= 20


# ---------------- 車輛彙總 ----------------
@lru_cache(maxsize=64)
def vehicle_stats(period):
    """每台車在 period 內的彙總指標。"""
    agg = defaultdict(lambda: {"n_days": 0, "ev": Counter(), "over10": 0, "over4": 0, "max_cont_h": 0, "dates": []})
    for d in period_days(period):
        a = agg[d["plate"]]
        for k in SUM_KEYS:
            a[k] = a.get(k, 0) + d[k]
        a["n_days"] += 1
        a["dates"].append(d["date"])
        a["ev"].update({int(k): v for k, v in d["events"].items()})
        if _moved(d):
            a["over10"] += d["drive_h"] > Config.DAILY_LIMIT_H
            a["over4"] += sum(1 for s in d["segments"] if s["hours"] > Config.CONT_LIMIT_H)
        a["max_cont_h"] = max(a["max_cont_h"], d["max_cont_h"])

    out = {}
    for plate, a in agg.items():
        v = VEHICLES[plate]
        km_eff = max(a["km"], a["drive_h"] * 20, 1)
        engine_h = a["drive_h"] + a["idle_h"]
        s = {
            "plate": plate, "type": v["type"], "series": v["series"], "n_days": a["n_days"], "dates": a["dates"],
            **{k: round(a[k], 1) for k in SUM_KEYS},
            "l100": round(a["fuel"] / a["km"] * 100, 1) if a["km"] >= 30 else None,
            "idle_share": round(a["idle_h"] / engine_h, 3) if engine_h else 0,
            "km_per_day": round(a["km"] / a["n_days"], 1),
            "drive_h_per_day": round(a["drive_h"] / a["n_days"], 1),
            "events": dict(a["ev"]),
            "rate": {t: round(c / km_eff * 100, 1) for t, c in a["ev"].items()},          # 每百公里
            "rate_h": {t: round(c / max(a["drive_h"], 0.5), 2) for t, c in a["ev"].items()},  # 每駕駛小時
            "harsh_100": round((a["ev"][6] + a["ev"][7]) / km_eff * 100, 1),
            "over10": a["over10"], "over4": a["over4"], "max_cont_h": a["max_cont_h"],
            "has_dms": plate in HAS_DMS,
            "fuel_cost": round(a["fuel"] * Config.DIESEL_PRICE),
        }
        s["cost_per_km"] = round(Config.DIESEL_PRICE * s["l100"] / 100, 2) if s["l100"] else None
        out[plate] = s

    # 同車型中位數；里程與油耗比例明顯不合理的車視為資料異常，不納入基準
    for t in ("300", "500", "700"):
        group = [s for s in out.values() if s["type"] == t and s["l100"]]
        if len(group) >= 3:
            m = median(s["l100"] for s in group)
            for s in group:
                if s["l100"] < m * 0.45 or s["l100"] > m * 2.2 and s["km"] < 400:
                    s["quality"] = "里程與油耗比例不合理，疑似 CAN 里程或油耗感測異常"
    for s in out.values():
        s.setdefault("quality", None)
    return out


@lru_cache(maxsize=64)
def type_benchmarks(period):
    stats = vehicle_stats(period)
    bm = {}
    for t in ("300", "500", "700"):
        g = [s for s in stats.values() if s["type"] == t]
        good = [s for s in g if s["l100"] and not s["quality"]]
        km = lambda s: max(s["km"], 1)  # noqa: E731
        bm[t] = {
            "l100": round(median(s["l100"] for s in good), 1) if good else None,
            "idle_share": median(s["idle_share"] for s in g) if g else None,
            "idle_fuel_per_km": median(s["idle_fuel"] / km(s) for s in good) if good else 0,
            "high_rpm_fuel_per_km": median(s["high_rpm_fuel"] / km(s) for s in good) if good else 0,
            "harsh_100": median(s["harsh_100"] for s in g) if g else None,
            "speeding_min_per_km": median(s["speeding_min"] / km(s) for s in good) if good else 0,
            "overload_min_per_km": median(s["overload_min"] / km(s) for s in good) if good else 0,
            "n": len(g),
        }
    return bm


# ---------------- 油耗原因拆解 ----------------
def fuel_breakdown(plate, period):
    s = vehicle_stats(period).get(plate)
    if not s:
        return None
    bm = type_benchmarks(period)[s["type"]]
    base = {"plate": plate, "type": s["type"], "series": s["series"], "period": period, "period_label": period_label(period),
            "l100": s["l100"], "median_l100": bm["l100"], "km": s["km"], "fuel": s["fuel"], "n_days": s["n_days"],
            "quality": s["quality"]}
    if not s["l100"] or not bm["l100"] or s["quality"]:
        return {**base, "excess_l": None, "factors": [], "note": s["quality"] or "里程不足，無法計算"}
    expected = s["km"] * bm["l100"] / 100
    excess = s["fuel"] - expected
    km = s["km"]
    per_min_fuel = s["fuel"] / max(s["drive_h"] * 60, 1)
    raw = [
        ("idle", "怠速", s["idle_fuel"] - km * bm["idle_fuel_per_km"],
         f"怠速 {s['idle_h']:.1f} 小時，耗油 {s['idle_fuel']:.0f} 公升"),
        ("rpm", "高轉速", s["high_rpm_fuel"] - km * bm["high_rpm_fuel_per_km"],
         f"超出經濟轉速區 {s['high_rpm_min']:.0f} 分鐘"),
        ("harsh", "急加減速", (s["harsh_100"] - (bm["harsh_100"] or 0)) * km / 100 * HARSH_L[s["type"]],
         f"每百公里 {s['harsh_100']:.1f} 次（同車型中位數 {bm['harsh_100']:.1f}）"),
        ("speeding", "超速", (s["speeding_min"] - km * bm["speeding_min_per_km"]) * per_min_fuel * SPEEDING_EXTRA,
         f"超速累計 {s['speeding_min']:.0f} 分鐘"),
        ("overload", "引擎過載", (s["overload_min"] - km * bm["overload_min_per_km"]) * per_min_fuel * OVERLOAD_EXTRA,
         f"過載累計 {s['overload_min']:.0f} 分鐘"),
    ]
    factors = [{"key": k, "name": n, "liters": max(0.0, l), "detail": dt} for k, n, l, dt in raw]
    total = sum(f["liters"] for f in factors)
    if excess > 0 and total > excess:
        for f in factors:
            f["liters"] *= excess / total
        total = excess
    if excess > 0:
        factors.append({"key": "other", "name": "其他（路線、載重、車況）", "liters": max(0.0, excess - total),
                        "detail": "無法由行車事件解釋的部分"})
    for f in factors:
        f["liters"] = round(f["liters"], 1)
        f["ntd"] = round(f["liters"] * Config.DIESEL_PRICE)
        f["share"] = round(f["liters"] / excess, 3) if excess > 0 else 0
    factors.sort(key=lambda f: (f["key"] == "other", -f["liters"]))
    return {**base, "expected_l": round(expected, 1), "excess_l": round(excess, 1),
            "excess_ntd": round(excess * Config.DIESEL_PRICE),
            "excess_pct": round((s["l100"] / bm["l100"] - 1) * 100),
            "excess_ntd_per_day": round(excess * Config.DIESEL_PRICE / s["n_days"]),
            "idle_h": s["idle_h"], "idle_share": s["idle_share"], "factors": factors}


# ---------------- 司機評分 ----------------
def _ontime(driver_id, period):
    rows = [r for r in ONTIME if r["driver"] == driver_id and (period == "all" or r["month"] == period)]
    n = sum(r["tasks"] for r in rows)
    return (sum(r["on_time"] for r in rows) / n, n) if n else (None, 0)


def _dms_rate(s):
    e = s["events"]
    w = e.get(12, 0) * 3 + e.get(16, 0) + e.get(14, 0) * 2 + e.get(13, 0) * 0.5 + e.get(15, 0) + e.get(17, 0)
    return w / max(s["drive_h"], 0.5)


def _dyn_rate(s):
    return s["harsh_100"] + s["rate"].get(8, 0) * 0.5 + (s["rate"].get(19, 0) * 3 + s["rate"].get(20, 0))


@lru_cache(maxsize=64)
def driver_scores(period, weights=None):
    """weights 為 ((key, value), ...) 的 tuple（方便快取），None 表示用預設權重。"""
    w_param = weights
    weights = dict(weights) if weights else Config.WEIGHTS
    wsum = sum(weights.values()) or 1
    stats = vehicle_stats(period)
    own = vehicle_stats("all")
    bm = type_benchmarks(period)
    dms_med = {t: median([_dms_rate(s) for s in stats.values() if s["type"] == t and s["has_dms"]] or [0])
               for t in ("300", "500", "700")}
    dyn_med = {t: median([_dyn_rate(s) for s in stats.values() if s["type"] == t] or [0]) for t in ("300", "500", "700")}

    rows = []
    for plate, s in stats.items():
        dv = DRIVER_BY_PLATE[plate]
        t = s["type"]
        dyn = _dyn_rate(s)
        safety_dyn = 0.5 * _ratio_score(dyn, dyn_med[t], 22) + 0.5 * _ratio_score(dyn, _dyn_rate(own[plate]), 22)
        if s["has_dms"]:
            dms = _dms_rate(s)
            safety_dms = 0.5 * _ratio_score(dms, dms_med[t], 22) + 0.5 * _ratio_score(dms, _dms_rate(own[plate]), 22)
            safety = 0.5 * safety_dyn + 0.5 * safety_dms
        else:
            safety = safety_dyn
        if s["l100"] and bm[t]["l100"] and not s["quality"]:
            fuel_part = _ratio_score(s["l100"], bm[t]["l100"], 70)
        else:
            fuel_part = 75
        idle_part = _ratio_score(s["idle_share"] + 0.02, (bm[t]["idle_share"] or 0) + 0.02, 15)
        eco = 0.7 * fuel_part + 0.3 * idle_part
        rate, n_tasks = _ontime(dv["id"], period)
        ontime = _clip(100 - (1 - rate) * 200, 40, 100) if rate is not None else 80
        viol = s["over10"] + s["over4"]
        compliance = _clip(100 - viol / s["n_days"] * 120, 0, 100)
        sub = {"safety": safety, "eco": eco, "ontime": ontime, "compliance": compliance}
        total = sum(sub[k] * weights[k] for k in sub) / wsum
        rows.append({
            "driver_id": dv["id"], "name": dv["name"], "nick": dv["nick"], "plate": plate, "type": t,
            "series": s["series"], "score": round(total), "sub": {k: round(v) for k, v in sub.items()},
            "metrics": {
                "km": s["km"], "n_days": s["n_days"], "drive_h": s["drive_h"], "l100": s["l100"],
                "median_l100": bm[t]["l100"], "idle_share": s["idle_share"], "harsh_100": s["harsh_100"],
                "speeding_100": s["rate"].get(8, 0), "dms_per_h": round(_dms_rate(s), 2) if s["has_dms"] else None,
                "distract_per_h": s["rate_h"].get(16, 0) if s["has_dms"] else None,
                "fatigue_per_h": s["rate_h"].get(12, 0) if s["has_dms"] else None,
                "phone_per_h": s["rate_h"].get(14, 0) if s["has_dms"] else None,
                "seatbelt": s["events"].get(13, 0) if s["has_dms"] else None,
                "ontime_rate": round(rate, 3) if rate is not None else None, "tasks": n_tasks,
                "over10": s["over10"], "over4": s["over4"], "max_cont_h": s["max_cont_h"],
            },
            "has_dms": s["has_dms"], "quality": s["quality"],
        })
    rows.sort(key=lambda r: -r["score"])
    for i, r in enumerate(rows):
        r["rank"] = i + 1
    pp = prev_period(period)
    if pp:
        prev = {r["driver_id"]: r for r in driver_scores(pp, w_param)}
        for r in rows:
            p = prev.get(r["driver_id"])
            r["prev"] = {"score": p["score"], "sub": p["sub"], "period": pp} if p else None
    return rows


def driver_trend(driver_id):
    """各月綜合分數與分項，給趨勢圖用。"""
    out = []
    for m in MONTHS:
        r = next((x for x in driver_scores(m) if x["driver_id"] == driver_id), None)
        if r:
            out.append({"month": m, "score": r["score"], "sub": r["sub"],
                        "distract_per_h": r["metrics"]["distract_per_h"], "harsh_100": r["metrics"]["harsh_100"],
                        "l100": r["metrics"]["l100"]})
    return out


def event_hours(plate, period, types):
    """事件在一天中各小時的分布。"""
    months = None if period == "all" else {period}
    hist = [0] * 24
    for t, ty, *_ in EVENTS[plate]:
        if ty in types and t[:10] < Config.TODAY and (months is None or t[:7] in months):
            hist[int(t[11:13])] += 1
    return hist


# ---------------- 車隊總覽 ----------------
def day_summary(date):
    rows = [d for d in DAYS if d["date"] == date]
    km = sum(d["km"] for d in rows)
    fuel = sum(d["fuel"] for d in rows)
    return {
        "date": date, "vehicles": len(rows), "km": round(km), "fuel": round(fuel),
        "fuel_cost": round(fuel * Config.DIESEL_PRICE), "idle_h": round(sum(d["idle_h"] for d in rows), 1),
        "idle_fuel": round(sum(d["idle_fuel"] for d in rows), 1),
        "drive_h": round(sum(d["drive_h"] for d in rows), 1),
        "events": dict(sum((Counter({int(k): v for k, v in d["events"].items()}) for d in rows), Counter())),
        "over10": [d["plate"] for d in rows if _moved(d) and d["drive_h"] > Config.DAILY_LIMIT_H],
        "over4": [{"plate": d["plate"], **s} for d in rows if _moved(d) for s in d["segments"] if s["hours"] > Config.CONT_LIMIT_H],
    }


def fleet_trend():
    """各月、各車型的 L/100km 與每百公里急加減速。"""
    out = []
    for m in MONTHS:
        st = vehicle_stats(m)
        row = {"month": m}
        for t in ("300", "500", "700"):
            g = [s for s in st.values() if s["type"] == t and not s["quality"] and s["l100"]]
            km, fuel = sum(s["km"] for s in g), sum(s["fuel"] for s in g)
            row[t] = round(fuel / km * 100, 1) if km else None
        g = list(st.values())
        row["harsh_100"] = round(sum(s["events"].get(6, 0) + s["events"].get(7, 0) for s in g)
                                 / max(sum(s["km"] for s in g), 1) * 100, 1)
        row["idle_share"] = round(sum(s["idle_h"] for s in g) / max(sum(s["idle_h"] + s["drive_h"] for s in g), 1), 3)
        out.append(row)
    return out


def hours_violations(period):
    out = []
    for d in period_days(period):
        if not _moved(d):
            continue
        dv = DRIVER_BY_PLATE[d["plate"]]
        if d["drive_h"] > Config.DAILY_LIMIT_H:
            out.append({"date": d["date"], "plate": d["plate"], "driver": dv["name"], "kind": "daily",
                        "label": f"單日駕駛 {d['drive_h']:.1f} 小時", "value": d["drive_h"]})
        for s in d["segments"]:
            if s["hours"] > Config.CONT_LIMIT_H:
                out.append({"date": d["date"], "plate": d["plate"], "driver": dv["name"], "kind": "continuous",
                            "label": f"連續駕駛 {s['hours']:.1f} 小時（{s['start']}–{s['end']}）", "value": s["hours"]})
    return sorted(out, key=lambda x: (x["date"], x["value"]), reverse=True)


# ---------------- 保養與故障碼 ----------------
def maintenance_status():
    odo = {}
    for d in DAYS:
        odo[d["plate"]] = max(odo.get(d["plate"], 0), d["odo_end"])
    dtc = defaultdict(Counter)
    dtc_last = {}
    for plate, evs in EVENTS.items():
        for t, ty, _d, _la, _lo, x in evs:
            if ty == 9 and x and t[:10] < Config.TODAY:
                dtc[plate][x] += 1
                dtc_last[(plate, x)] = max(dtc_last.get((plate, x), ""), t[:10])
    out = {}
    for plate, m in MAINTENANCE.items():
        left = round(m["next_service_km"] - odo.get(plate, 0))
        codes = [{"code": c, "count": n, "last": dtc_last[(plate, c)], "name": DTC_NAMES.get(c, "未知故障碼")}
                 for c, n in dtc[plate].most_common()]
        status = "overdue" if left < 0 else "soon" if left < 1500 else "ok"
        out[plate] = {"odo": round(odo.get(plate, 0)), "next_service_km": m["next_service_km"], "km_left": left,
                      "status": status, "dtc": codes, "last_service_date": m["last_service_date"]}
    return out


def vehicle_table(period):
    stats = vehicle_stats(period)
    bm = type_benchmarks(period)
    ms = maintenance_status()
    all_days = {d["date"] for d in period_days(period)}
    rows = []
    for plate, v in VEHICLES.items():
        s = stats.get(plate)
        dv = DRIVER_BY_PLATE[plate]
        fb = fuel_breakdown(plate, period) if s else None
        rows.append({
            "plate": plate, "type": v["type"], "series": v["series"], "driver": dv["name"], "driver_id": dv["id"],
            "active": bool(s), "n_days": s["n_days"] if s else 0, "util": round(s["n_days"] / len(all_days), 2) if s and all_days else 0,
            "km": s["km"] if s else 0, "l100": s["l100"] if s else None, "median_l100": bm[v["type"]]["l100"],
            "vs_median": round((s["l100"] / bm[v["type"]]["l100"] - 1) * 100) if s and s["l100"] and bm[v["type"]]["l100"] and not s["quality"] else None,
            "idle_share": s["idle_share"] if s else None, "drive_h_per_day": s["drive_h_per_day"] if s else None,
            "cost_per_km": s["cost_per_km"] if s else None, "fuel_cost": s["fuel_cost"] if s else 0,
            "excess_ntd": fb["excess_ntd"] if fb and fb.get("excess_l") and fb["excess_l"] > 0 else 0,
            "top_factor": fb["factors"][0]["name"] if fb and fb.get("factors") and fb["excess_l"] > 0 else None,
            "quality": s["quality"] if s else None, "maint": ms[plate],
        })
    return rows


def event_list(plate, date, types=None):
    return [{"time": t[11:16], "type": ty, "name": EVENT_NAMES.get(ty, str(ty)), "duration": d, "lat": la, "lon": lo, "extra": x}
            for t, ty, d, la, lo, x in EVENTS[plate] if t[:10] == date and (types is None or ty in types)]


def driver_by_name(q):
    q = (q or "").strip()
    for d in DRIVERS.values():
        if q and (q in d["name"] or q == d["nick"] or q == d["id"] or q == d["plate"]):
            return d
    return None
