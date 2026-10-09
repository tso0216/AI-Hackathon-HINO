"""把 iTRAQ 競賽原始資料（約 49 萬筆）彙整成 demo 用的 JSON，輸出到 data/itraq/。

這支程式只處理主辦單位提供的真實資料，不加入任何模擬數字；模擬資料由 gen_mock.py 另外產生。

用法：
    .venv/bin/python scripts/build_dataset.py                # 預設讀競賽資料夾內的 xlsx
    .venv/bin/python scripts/build_dataset.py path/to.csv    # 也可讀先轉好的 csv（較快）
"""
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "HINO 競賽數據" / "HINO x GenAI：運用商用車車聯網大數據，發展商用車頭家的智慧夥伴"
DEFAULT_SRC = SRC_DIR / "output data_Hotai_20260511.xlsx"
OUT = ROOT / "data" / "itraq"

TRACK_DAYS = ["2025-11-11", "2025-11-21"]   # 即時配送回放與客訴佐證需要的完整軌跡
GAP_MAX = 120                               # 相鄰兩筆超過 2 分鐘視為資料中斷，不計入油耗、里程與時數
BREAK_MIN = 15 * 60                         # 停車滿 15 分鐘才算一次休息（連續駕駛重新計算）
HIGH_RPM = {"300": 2300, "500": 2050, "700": 1840}   # 約為各車型行駛中轉速第 90 百分位
EVENT_KEEP = {2, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20}
URBAN = [(25.04, 121.53), (25.01, 121.30), (24.15, 120.67), (22.99, 120.21), (22.63, 120.30), (24.80, 120.97)]

NUM = {
    "gps.longitude": "lon", "gps.latitude": "lat", "gps.speed": "spd", "gps.speedLimit": "limit",
    "can.totalMileage": "odo", "can.engine.totalFuelUsed": "fuel_total", "can.engine.rpm": "rpm",
    "can.engine.engineLoad": "load", "line.fuelLevel": "fuel_level",
}


def load(src):
    t0 = time.time()
    if src.suffix == ".csv":
        df = pd.read_csv(src, dtype=str, low_memory=False)
    else:
        import openpyxl

        ws = openpyxl.load_workbook(src, read_only=True)["output"]
        rows = ws.iter_rows(values_only=True)
        header = next(rows)
        df = pd.DataFrame([["" if v is None else str(v) for v in r] for r in rows], columns=header)
        df = df.replace("", np.nan)
    print(f"讀入 {len(df):,} 筆（{time.time() - t0:.0f}s）")
    return df


def prepare(df):
    df = df.rename(columns={**NUM, "enabledCode": "code", "carNum": "plate", "Type": "type", "carStatus": "status"})
    for c in NUM.values():
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["t"] = pd.to_datetime(df["time"])
    df["type"] = df["type"].astype(str).str.replace(r"\.0$", "", regex=True)
    df["status"] = pd.to_numeric(df["status"], errors="coerce").fillna(-1).astype(int)
    df["date"] = df.t.dt.strftime("%Y-%m-%d")
    df = df.sort_values(["code", "t"]).reset_index(drop=True)

    same = (df.code == df.code.shift(-1)) & (df.date == df.date.shift(-1))
    gap = (df.t.shift(-1) - df.t).dt.total_seconds()
    ok = same & (gap <= GAP_MAX)
    # 每一筆代表「到下一筆為止」的區間：時長、里程、油耗都歸給這一筆的狀態
    df["dur"] = np.where(ok, gap, 0.0)
    dkm = df.odo.shift(-1) - df.odo
    dfuel = df.fuel_total.shift(-1) - df.fuel_total
    good = ok & (dkm >= 0) & (dkm < 10) & (dfuel >= 0) & (dfuel < 10)
    df["dkm"] = np.where(good, dkm, 0.0)
    df["dfuel"] = np.where(good, dfuel, 0.0)
    df["gap_next"] = np.where(same, gap, np.inf)
    df["high_rpm"] = df.rpm > df.type.map(HIGH_RPM)
    return df


def events(df):
    """事件在原始資料會出現「開始」與「結束」兩筆，以（車、類型、開始時間）去重，保留有持續時間的那筆。"""
    parts = []
    for i in range(3):
        p = f"event[{i}]."
        e = df[["plate_fix", "code", "t", "lat", "lon"]].copy()
        e["etype"] = pd.to_numeric(df[p + "type"], errors="coerce")
        e["start"] = df[p + "startTime"]
        e["end"] = df[p + "endTime"]
        e["duration"] = pd.to_numeric(df[p + "info.duration"], errors="coerce")
        e["diff"] = pd.to_numeric(df[p + "info.speedDifference"], errors="coerce")
        e["speed"] = pd.to_numeric(df[p + "info.speed"], errors="coerce")
        e["limit"] = pd.to_numeric(df[p + "info.speedLimit"], errors="coerce")
        e["eload"] = pd.to_numeric(df[p + "info.engineLoad"], errors="coerce")
        e["dtc"] = df.get(p + "info.dtcCodes[0]")
        parts.append(e[e.etype.notna()])
    ev = pd.concat(parts)
    ev = ev[ev.etype.isin(EVENT_KEEP)]
    ev["has_end"] = ev.end.notna()
    ev = ev.sort_values(["has_end", "t"]).drop_duplicates(["code", "etype", "start"], keep="last")
    ev["start_t"] = pd.to_datetime(ev.start)
    return ev.sort_values(["code", "start_t"]).reset_index(drop=True)


def continuous_segments(day):
    """回傳當日每段連續駕駛（中間沒有 ≥15 分鐘停車）的 [開始, 結束, 駕駛秒數]。"""
    segs, cur = [], None
    for t, st, dur, gap in zip(day.t, day.status, day.dur, day.gap_next):
        if st == 1:
            if cur and (t - cur["last"]).total_seconds() >= BREAK_MIN:
                segs.append(cur)
                cur = None
            if not cur:
                cur = {"start": t, "drive": 0.0}
            cur["drive"] += dur
            cur["last"] = t + pd.Timedelta(seconds=min(gap, GAP_MAX) if np.isfinite(gap) else 0)
    if cur:
        segs.append(cur)
    return [{"start": s["start"].strftime("%H:%M"), "end": s["last"].strftime("%H:%M"), "hours": round(s["drive"] / 3600, 2)}
            for s in segs]


def vehicle_days(df, ev):
    ev_day = ev.assign(date=ev.start_t.dt.strftime("%Y-%m-%d"))
    counts = ev_day.groupby(["code", "date", "etype"]).size()
    dur_sum = ev_day.groupby(["code", "date", "etype"]).duration.sum()
    out = []
    for (code, date), d in df.groupby(["code", "date"], sort=True):
        drive = d.status == 1
        idle = d.status == 2
        segs = continuous_segments(d)
        ev_counts = {str(int(k)): int(v) for k, v in counts.get((code, date), pd.Series(dtype=int)).items()}
        ev_secs = dur_sum.get((code, date), pd.Series(dtype=float))
        moving = d[drive & (d.spd > 5)]
        out.append({
            "plate": d.plate_fix.iloc[0], "type": d.type.iloc[0], "date": date,
            "first": d.t.min().strftime("%H:%M"), "last": d.t.max().strftime("%H:%M"),
            "km": round(float(d.dkm.sum()), 1), "fuel": round(float(d.dfuel.sum()), 1),
            "idle_fuel": round(float(d.dfuel[idle].sum()), 1),
            "drive_h": round(float(d.dur[drive].sum()) / 3600, 2), "idle_h": round(float(d.dur[idle].sum()) / 3600, 2),
            "high_rpm_min": round(float(d.dur[drive & d.high_rpm].sum()) / 60, 1),
            "high_rpm_fuel": round(float(d.dfuel[drive & d.high_rpm].sum()), 1),
            "speeding_min": round(float(ev_secs.get(8.0, 0) or 0) / 60, 1),
            "overload_min": round(float(ev_secs.get(11.0, 0) or 0) / 60, 1),
            "avg_speed": round(float(moving.spd.mean()), 1) if len(moving) else None,
            "max_cont_h": max((s["hours"] for s in segs), default=0),
            "segments": [s for s in segs if s["hours"] >= 3.5],
            "events": ev_counts,
            "odo_end": float(d.odo.max()),
        })
    return out


def tracks(df, date):
    """完整軌跡降頻到約 30 秒一點（狀態改變的點一定保留），給即時配送地圖回放用。"""
    res = {}
    for code, d in df[df.date == date].groupby("code"):
        keep, last_t, last_st = [], None, None
        for r in d.itertuples():
            sec = r.t.hour * 3600 + r.t.minute * 60 + r.t.second
            if last_t is None or sec - last_t >= 30 or r.status != last_st:
                keep.append([sec, round(r.lat, 5), round(r.lon, 5), int(r.spd if r.spd == r.spd else 0), r.status, round(r.odo, 1)])
                last_t, last_st = sec, r.status
        res[d.plate_fix.iloc[0]] = keep
    return res


def speed_profile(df):
    """各小時、車型、市區/郊區的行駛中平均車速，給延誤預測的模擬歷史資料參考。"""
    d = df[(df.status == 1) & df.lat.notna()].copy()
    lat, lon = d.lat.to_numpy(), d.lon.to_numpy()
    near = np.zeros(len(d), bool)
    for clat, clon in URBAN:
        near |= ((lat - clat) * 111) ** 2 + ((lon - clon) * 101) ** 2 < 12 ** 2
    d["urban"] = near
    d["hour"] = d.t.dt.hour
    prof = d.groupby(["type", "urban", "hour"]).spd.mean().round(1)
    return [{"type": t, "urban": bool(u), "hour": int(h), "speed": float(v)} for (t, u, h), v in prof.items() if not math.isnan(v)]


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SRC
    df = prepare(load(src))
    plate = df.dropna(subset=["plate"]).groupby("code").plate.first()
    df["plate_fix"] = df.code.map(plate)

    ev = events(df)
    days = vehicle_days(df, ev)

    vehicles = []
    for code, d in df.groupby("code"):
        vehicles.append({"plate": plate[code], "code": code, "type": d.type.iloc[0], "series": f"HINO {d.type.iloc[0]}",
                         "first_date": d.date.min(), "last_date": d.date.max()})

    ev_out = []
    for r in ev.itertuples():
        extra = None
        if r.etype in (6, 7):
            extra = None if pd.isna(r.diff) else int(r.diff)
        elif r.etype == 8:
            extra = [None if pd.isna(r.speed) else int(r.speed), None if pd.isna(r.limit) else int(r.limit)]
        elif r.etype == 11:
            extra = None if pd.isna(r.eload) else int(r.eload)
        elif r.etype == 9:
            extra = r.dtc if isinstance(r.dtc, str) else None
        ev_out.append([r.plate_fix, r.start_t.strftime("%Y-%m-%d %H:%M:%S"), int(r.etype),
                       None if pd.isna(r.duration) else int(r.duration),
                       None if pd.isna(r.lat) else round(r.lat, 5), None if pd.isna(r.lon) else round(r.lon, 5), extra])

    OUT.mkdir(parents=True, exist_ok=True)

    def dump(name, obj):
        with open(OUT / name, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        print(f"  {name}: {(OUT / name).stat().st_size / 1024:,.0f} KB")

    dump("meta.json", {
        "source": src.name, "rows": int(len(df)), "vehicles": len(vehicles),
        "vehicle_days": len(days), "date_min": df.date.min(), "date_max": df.date.max(),
        "gap_max_s": GAP_MAX, "break_min_s": BREAK_MIN, "high_rpm": HIGH_RPM,
        "built_at": time.strftime("%Y-%m-%d %H:%M"),
    })
    dump("vehicles.json", vehicles)
    dump("vehicle_days.json", days)
    dump("events.json", ev_out)
    dump("speed_profile.json", speed_profile(df))
    for date in TRACK_DAYS:
        dump(f"tracks_{date}.json", tracks(df, date))


if __name__ == "__main__":
    main()
