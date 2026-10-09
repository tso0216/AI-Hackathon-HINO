"""載入資料。data/itraq/ 是由競賽原始資料彙整的真實數據；data/mock/ 是模擬資料（畫面上一律標示）。"""
import json
from collections import defaultdict
from pathlib import Path

from config import Config

DATA = Path(__file__).resolve().parent.parent / "data"


def _load(*parts):
    with open(DATA.joinpath(*parts), encoding="utf-8") as f:
        return json.load(f)


# ---------- 真實資料（iTRAQ 競賽資料） ----------
META = _load("itraq", "meta.json")
VEHICLES = {v["plate"]: v for v in _load("itraq", "vehicles.json")}
DAYS = [d for d in _load("itraq", "vehicle_days.json") if d["date"] < Config.TODAY]
TODAY_DAYS = {d["plate"]: d for d in _load("itraq", "vehicle_days.json") if d["date"] == Config.TODAY}
TRACKS = {Config.TODAY: _load("itraq", f"tracks_{Config.TODAY}.json"),
          Config.PREV_DAY: _load("itraq", f"tracks_{Config.PREV_DAY}.json")}
SPEED_PROFILE = _load("itraq", "speed_profile.json")

EVENTS = defaultdict(list)       # plate -> [(datetime 字串, type, duration_s, lat, lon, extra)]
for _p, _t, _ty, _dur, _lat, _lon, _x in _load("itraq", "events.json"):
    EVENTS[_p].append((_t, _ty, _dur, _lat, _lon, _x))

# ---------- 模擬資料 ----------
DRIVERS = {d["id"]: d for d in _load("mock", "drivers.json")}
DRIVER_BY_PLATE = {d["plate"]: d for d in DRIVERS.values()}
TASKS = {Config.TODAY: _load("mock", f"tasks_{Config.TODAY}.json"),
         Config.PREV_DAY: _load("mock", f"tasks_{Config.PREV_DAY}.json")}
ONTIME = _load("mock", "ontime.json")
COMPLAINTS = _load("mock", "complaints.json")
MAINTENANCE = {m["plate"]: m for m in _load("mock", "maintenance.json")}
WEATHER = _load("mock", "weather.json")
KB = _load("kb", "kb.json")

EVENT_NAMES = {
    2: "怠速", 6: "急加速", 7: "急減速", 8: "超速", 9: "DTC 故障碼", 11: "引擎過載", 12: "疲勞駕駛",
    13: "未繫安全帶", 14: "使用手機", 15: "抽菸", 16: "分心", 17: "鏡頭遮蔽", 18: "駕駛離座",
    19: "PCS 預警式防護", 20: "LDWS 車道偏離",
}
DMS_TYPES = {12, 13, 14, 15, 16, 17, 18}
DTC_NAMES = {
    "P2002": "柴油微粒濾清器（DPF）效率低於門檻",
    "P244B": "DPF 壓差過高（可能堵塞）",
    "P20EE": "SCR 觸媒效率低於門檻",
    "P2280": "進氣系統漏氣或阻塞",
    "U3FFF": "通訊類故障碼（需原廠診斷判讀）",
}

# 有資料的月份（競賽資料為每隔一個月的抽樣日）
MONTHS = sorted({d["date"][:7] for d in DAYS if sum(1 for x in DAYS if x["date"][:7] == d["date"][:7]) > 20})


def period_days(period):
    """period：'2025-11' 這類月份，或 'all'。只含「今天」以前的資料日。"""
    if period == "all":
        return DAYS
    return [d for d in DAYS if d["date"][:7] == period]


def prev_period(period):
    if period == "all" or period not in MONTHS:
        return None
    i = MONTHS.index(period)
    return MONTHS[i - 1] if i > 0 else None


def period_label(period):
    if period == "all":
        return f"全期間（{MONTHS[0].replace('-', '/')}–{MONTHS[-1][5:]}）"
    dates = sorted({d["date"][5:].replace("-", "/") for d in period_days(period)})
    return f"{period.replace('-', '/')}（資料日 {'、'.join(dates)}）"


def periods():
    out = [{"id": m, "label": f"{int(m[5:])} 月", "full": period_label(m)} for m in reversed(MONTHS)]
    out.append({"id": "all", "label": "全期間", "full": period_label("all")})
    return out


def sec_to_hhmm(sec):
    sec = int(sec)
    return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}"


def hhmm_to_sec(s):
    h, m = map(int, s.split(":")[:2])
    return h * 3600 + m * 60
