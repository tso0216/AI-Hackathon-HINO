"""即時配送：以 2025/11/21 的 iTRAQ 真實軌跡回放「今天」，在任一時間點算出車輛位置、工時、任務進度與延誤預測。"""
import bisect
from functools import lru_cache

from config import Config
from services import eta_model
from services.data import (
    DRIVER_BY_PLATE, EVENTS, EVENT_NAMES, TASKS, TRACKS, VEHICLES, WEATHER, hhmm_to_sec, sec_to_hhmm,
)

TODAY = Config.TODAY
WEEKDAY = 4                      # 2025/11/21 是星期五
DWELL_MIN = 20                   # 預估每站卸貨時間（分鐘）
BREAK_S = 15 * 60
URBAN = [(25.04, 121.53), (25.01, 121.30), (24.15, 120.67), (22.99, 120.21), (22.63, 120.30), (24.80, 120.97)]
SENT = {}                        # 已發送的客戶通知 task_id -> 時間字串（demo 用，重置時清空）


class Track:
    def __init__(self, pts):
        self.pts = pts
        self.secs = [p[0] for p in pts]
        self.first, self.last = pts[0][0], pts[-1][0]
        self._timeline()

    def _timeline(self):
        """預先算好每個點為止的累計駕駛秒數、目前連續駕駛秒數，以及跨過門檻的時間。"""
        self.drive_cum, self.cont = [], []
        self.cross = {"cont_35": [], "cont_4": [], "day_9": [], "day_10": []}
        total, cont, last_drive_end = 0.0, 0.0, None
        for i, p in enumerate(self.pts):
            sec, st = p[0], p[4]
            nxt = self.pts[i + 1][0] if i + 1 < len(self.pts) else sec
            dur = min(nxt - sec, 120)
            if st == 1:
                if last_drive_end is not None and sec - last_drive_end >= BREAK_S:
                    cont = 0.0          # 休息滿 15 分鐘，連續駕駛重新計算
                before_c, before_t = cont, total
                total += dur
                cont += dur
                last_drive_end = sec + dur
                for key, th, b, a in (("cont_35", 3.5, before_c, cont), ("cont_4", 4, before_c, cont),
                                      ("day_9", 9, before_t, total), ("day_10", 10, before_t, total)):
                    if b < th * 3600 <= a:
                        self.cross[key].append(sec)
            self.drive_cum.append(total)
            self.cont.append((cont, last_drive_end))

    def crossed(self, key, t):
        xs = [x for x in self.cross[key] if x <= t]
        return xs[-1] if xs else None

    def idx(self, t):
        return bisect.bisect_right(self.secs, t) - 1

    def at(self, t):
        i = self.idx(t)
        return self.pts[max(i, 0)]

    def odo_at(self, t):
        return self.at(t)[5]

    def drive_until(self, t):
        i = self.idx(t)
        if i < 0:
            return 0.0, 0.0
        cont, last_end = self.cont[i]
        if last_end is None or t - last_end >= BREAK_S:
            cont = 0.0
        return self.drive_cum[i], cont


TRACK = {p: Track(pts) for p, pts in TRACKS[TODAY].items() if len(pts) > 5}
TASKS_BY_PLATE = {}
for _t in TASKS[TODAY]:
    TASKS_BY_PLATE.setdefault(_t["plate"], []).append(_t)


def _urban(lat, lon):
    return any(((lat - a) * 111) ** 2 + ((lon - b) * 101) ** 2 < 12 ** 2 for a, b in URBAN)


def _rain(city, sec):
    for r in WEATHER["rain"]:
        if r["city"] == city and hhmm_to_sec(r["from"]) <= sec <= hhmm_to_sec(r["to"]):
            return r["desc"]
    return None


def _state(tr, t, tasks):
    if t < tr.first:
        return "待出車"
    if t > tr.last + 600:
        return "已收車"
    p = tr.at(t)
    if p[3] > 3:
        return "行駛中"
    if any(k["arrive_sec"] <= t < k["depart_sec"] for k in tasks):
        return "卸貨中"
    if p[4] == 2:
        return "怠速"
    return "停車中"


def _legs(plate):
    """每筆任務的路段：從上一站（或出發點）離開的時間、路段里程、路段歷史車速。
    路段歷史車速以該路段實際行駛中的平均車速代表（同路段過去的車速），加上 ±8% 的差異。"""
    tr = TRACK[plate]
    prev_dep, prev_odo = tr.first, tr.pts[0][5]
    out = {}
    for k in TASKS_BY_PLATE.get(plate, []):
        km = max(0.5, tr.odo_at(k["arrive_sec"]) - prev_odo)
        moving = sum(min(tr.pts[i + 1][0] - p[0], 120) for i, p in enumerate(tr.pts[:-1])
                     if prev_dep <= p[0] < k["arrive_sec"] and p[3] > 3)
        speed = km / max(moving / 3600, 0.05)
        jitter = 0.92 + (sum(map(ord, k["id"])) % 17) / 100
        out[k["id"]] = {"from": prev_dep, "km": round(km, 1), "hist_speed": round(min(85, max(12, speed * jitter)), 1)}
        prev_dep, prev_odo = k["depart_sec"], tr.odo_at(k["depart_sec"])
    return out


LEGS = {p: _legs(p) for p in TRACK}


def _predict_chain(plate, t):
    """預測尚未送達任務的到達時間。
    下一站：從目前位置出發，以 LightGBM 依剩餘里程、路段歷史車速、時段、天氣預估；
    之後各站：以排程離站時間加上前一站延誤的遞延，再加上該路段的預估時間。"""
    tr = TRACK[plate]
    vtype = VEHICLES[plate]["type"]
    out, carry, first = {}, 0.0, True
    for k in TASKS_BY_PLATE.get(plate, []):
        if t >= k["depart_sec"]:
            continue
        if k["arrive_sec"] <= t:              # 卸貨中
            first = False
            continue
        leg = LEGS[plate][k["id"]]
        if first:
            if t < tr.first:
                start, km = tr.first, leg["km"]
            else:
                start = max(t, leg["from"])
                km = max(0.3, tr.odo_at(k["arrive_sec"]) - tr.odo_at(start))
            first = False
        else:
            start, km = leg["from"] + carry, leg["km"]
        rain = _rain(k["city"], start)
        row = {"vehicle_type": vtype, "urban": int(_urban(k["lat"], k["lon"])), "hour": int(start // 3600),
               "remaining_km": round(km, 1), "hist_speed": leg["hist_speed"], "rain": int(bool(rain)), "weekday": WEEKDAY}
        minutes, factors, base = eta_model.predict(row)
        eta = start + minutes * 60
        carry = max(0.0, eta - k["arrive_sec"])
        out[k["id"]] = {"eta_sec": eta, "leg_km": round(km, 1), "leg_minutes": round(minutes), "depart_from": sec_to_hhmm(start),
                        "factors": factors, "base": round(base, 1), "features": row, "rain": rain}
    return out


@lru_cache(maxsize=512)
def snapshot(t):
    t = int(t)
    vehicles, tasks_out, alerts = [], [], []
    for plate in sorted(VEHICLES):
        dv = DRIVER_BY_PLATE[plate]
        tr = TRACK.get(plate)
        tasks = TASKS_BY_PLATE.get(plate, [])
        if not tr:
            vehicles.append({"plate": plate, "driver": dv["name"], "driver_id": dv["id"], "type": VEHICLES[plate]["type"],
                             "state": "今日未排班", "lat": None, "lon": None})
            continue
        p = tr.at(max(t, tr.first))
        drive_s, cont_s = tr.drive_until(t)
        preds = _predict_chain(plate, t)
        state = _state(tr, t, tasks)
        km_today = round(tr.odo_at(t) - tr.pts[0][5], 1) if t >= tr.first else 0
        done = 0
        for k in tasks:
            pr = preds.get(k["id"])
            win_end = hhmm_to_sec(k["window_end"])
            if t >= k["arrive_sec"]:
                status = "已送達" if t >= k["depart_sec"] else "卸貨中"
                late = (k["arrive_sec"] - win_end) / 60
                eta, delay = k["arrive_sec"], late
                done += t >= k["depart_sec"]
            else:
                status = "配送中" if t >= tr.first and k is next((x for x in tasks if x["arrive_sec"] > t), None) else "待配送"
                eta = pr["eta_sec"]
                delay = (eta - win_end) / 60
            risk = "high" if delay >= 15 else "medium" if delay > 0 else "ok"
            tasks_out.append({
                **{x: k[x] for x in ("id", "plate", "seq", "customer", "city", "district", "lat", "lon", "cargo",
                                     "window_start", "window_end", "contact")},
                "driver": dv["name"], "driver_id": dv["id"], "status": status,
                "eta": sec_to_hhmm(eta), "delay_min": round(delay), "risk": risk if status in ("配送中", "待配送") else
                ("late" if delay > 0 else "ok"),
                "arrived": sec_to_hhmm(k["arrive_sec"]) if t >= k["arrive_sec"] else None,
                "pred": {kk: vv for kk, vv in pr.items() if kk != "eta_sec"} if pr else None,
                "notified": SENT.get(k["id"]),
            })
        ev_today = [e for e in EVENTS[plate] if e[0][:10] == TODAY and hhmm_to_sec(e[0][11:16]) <= t]
        vehicles.append({
            "plate": plate, "driver": dv["name"], "nick": dv["nick"], "driver_id": dv["id"], "type": VEHICLES[plate]["type"],
            "state": state, "lat": p[1], "lon": p[2], "speed": p[3] if state == "行駛中" else 0,
            "depart": sec_to_hhmm(tr.first), "drive_h": round(drive_s / 3600, 2), "cont_h": round(cont_s / 3600, 2),
            "km_today": km_today, "tasks_total": len(tasks), "tasks_done": done,
            "events_today": len([e for e in ev_today if e[1] not in (2,)]),
        })
        alerts += _alerts(plate, dv, tr, t, ev_today)

    pending = [k for k in tasks_out if k["status"] in ("配送中", "待配送")]
    for k in pending:
        if k["risk"] == "high":
            alerts.append({"at": t, "kind": "delay", "level": "high", "plate": k["plate"], "task_id": k["id"],
                           "title": f"延誤風險：{k['customer']}",
                           "body": f"{k['driver']}（{k['plate']}）預計 {k['eta']} 到達，晚於預約 {k['window_end']} 約 {k['delay_min']} 分鐘。"
                                   + ("已通知客戶。" if k["notified"] else "")})
    alerts.sort(key=lambda a: (-a["at"], a["level"] != "high"))
    for a in alerts:
        a["time"] = sec_to_hhmm(a["at"])

    done_tasks = [k for k in tasks_out if k["status"] == "已送達"]
    started = [v for v in vehicles if v["state"] not in ("待出車", "今日未排班")]
    return {
        "t": t, "time": sec_to_hhmm(t), "date": TODAY,
        "kpi": {
            "vehicles_total": len(VEHICLES), "vehicles_planned": len(TRACK), "vehicles_out": len(started),
            "tasks_total": len(tasks_out), "tasks_done": len(done_tasks),
            "on_time_rate": round(sum(1 for k in done_tasks if k["delay_min"] <= 0) / len(done_tasks), 3) if done_tasks else None,
            "risk_high": sum(1 for k in pending if k["risk"] == "high"),
            "risk_medium": sum(1 for k in pending if k["risk"] == "medium"),
            "km": round(sum(v.get("km_today", 0) for v in vehicles)),
        },
        "vehicles": vehicles, "tasks": tasks_out, "alerts": alerts,
    }


def _alerts(plate, dv, tr, t, ev_today):
    out = []
    who = f"{dv['name']}（{plate}）"
    drive_s, cont_s = tr.drive_until(t)
    c35, c4 = tr.crossed("cont_35", t), tr.crossed("cont_4", t)
    if c4 is not None and cont_s >= 4 * 3600:
        out.append({"at": c4, "kind": "hours", "level": "high", "plate": plate,
                    "title": f"連續駕駛已超過 4 小時：{dv['name']}",
                    "body": f"{who}已連續駕駛 {cont_s / 3600:.1f} 小時未休息，依 2026 新規須休息 30 分鐘。"})
    elif c35 is not None and cont_s >= 3.5 * 3600:
        out.append({"at": c35, "kind": "hours", "level": "medium", "plate": plate,
                    "title": f"連續駕駛將滿 4 小時：{dv['name']}",
                    "body": f"{who}已連續駕駛 {cont_s / 3600:.1f} 小時，建議 {sec_to_hhmm(t + max(0, 4 * 3600 - cont_s))} 前安排休息 30 分鐘。"})
    for key, th, level in (("day_10", 10, "high"), ("day_9", 9, "medium")):
        at = tr.crossed(key, t)
        if at is not None:
            out.append({"at": at, "kind": "hours", "level": level, "plate": plate,
                        "title": f"單日駕駛{'已超過' if th == 10 else '接近'} 10 小時：{dv['name']}",
                        "body": f"{who}今日已駕駛 {drive_s / 3600:.1f} 小時。" + ("請立即安排換手或收車。" if th == 10 else "剩餘工時有限，請調整後續任務。")})
            break
    # 疲勞、分心、手機事件密集：任一 60 分鐘內 ≥ 6 次
    dms = [hhmm_to_sec(e[0][11:16]) for e in ev_today if e[1] in (12, 14, 16)]
    last_alert = -10 ** 9
    for i, s in enumerate(dms):
        n = sum(1 for x in dms[: i + 1] if s - 3600 <= x <= s)
        if n >= 6 and s - last_alert > 3 * 3600:
            kinds = {EVENT_NAMES[e[1]] for e in ev_today if e[1] in (12, 14, 16) and s - 3600 <= hhmm_to_sec(e[0][11:16]) <= s}
            out.append({"at": s, "kind": "dms", "level": "medium", "plate": plate,
                        "title": f"疲勞／分心事件密集：{dv['name']}",
                        "body": f"{who}過去 1 小時內有 {n} 次{'、'.join(sorted(kinds))}事件，建議電話關心並提醒休息。"})
            last_alert = s
    seen = set()
    for e in ev_today:
        if e[1] == 9 and e[5] not in seen:
            seen.add(e[5])
            out.append({"at": hhmm_to_sec(e[0][11:16]), "kind": "dtc", "level": "medium", "plate": plate,
                        "title": f"故障碼 {e[5] or ''}：{plate}", "body": f"{who}回報故障碼 {e[5] or '（未知）'}，建議收車後檢查。"})
    return out


def task_detail(task_id, t):
    snap = snapshot(int(t))
    k = next((x for x in snap["tasks"] if x["id"] == task_id), None)
    if not k:
        return None
    tr = TRACK[k["plate"]]
    route = [[p[1], p[2]] for p in tr.pts if p[0] <= t]
    ahead = [[p[1], p[2]] for p in tr.pts if p[0] >= t]
    return {**k, "route_done": route[::3], "route_ahead": ahead[::3]}


def vehicle_route(plate, t):
    tr = TRACK.get(plate)
    if not tr:
        return None
    return {"plate": plate, "done": [[p[1], p[2]] for p in tr.pts if p[0] <= t][::2],
            "ahead": [[p[1], p[2]] for p in tr.pts if p[0] > t][::2],
            "tasks": [k["id"] for k in TASKS_BY_PLATE.get(plate, [])]}
