"""產生 demo 用的模擬資料（Mock Data），輸出到 data/mock/。

依競賽 FAQ 規範，競賽資料沒有的資訊（駕駛身分、配送任務與客戶、客訴、保養排程、天氣、延誤歷史）以模擬資料補足，
與 data/itraq/ 的真實資料分開存放，畫面上一律標示「模擬」。
配送任務的停靠點取自真實軌跡的停車位置，只有客戶名稱、預約時段等是模擬的。

用法：.venv/bin/python scripts/gen_mock.py
"""
import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ITRAQ = ROOT / "data" / "itraq"
OUT = ROOT / "data" / "mock"
TODAY, PREV_DAY = "2025-11-21", "2025-11-11"

rng = random.Random(20251121)


def load(name):
    with open(ITRAQ / name, encoding="utf-8") as f:
        return json.load(f)


def dump(name, obj):
    with open(OUT / name, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    print(f"  {name}")


# 行政區代表座標（約略位置），用來把停靠點標成「台中市西屯區」這類好讀的地名
DISTRICTS = [
    ("台北市", "內湖區", 25.083, 121.592), ("台北市", "南港區", 25.055, 121.607), ("台北市", "中山區", 25.064, 121.533),
    ("台北市", "信義區", 25.033, 121.567), ("新北市", "板橋區", 25.012, 121.462), ("新北市", "新莊區", 25.036, 121.432),
    ("新北市", "五股區", 25.083, 121.438), ("新北市", "林口區", 25.077, 121.391), ("新北市", "八里區", 25.146, 121.403),
    ("新北市", "淡水區", 25.170, 121.441), ("新北市", "三重區", 25.062, 121.488), ("新北市", "土城區", 24.972, 121.444),
    ("新北市", "樹林區", 24.991, 121.425), ("新北市", "汐止區", 25.067, 121.660), ("新北市", "三峽區", 24.934, 121.369),
    ("新北市", "鶯歌區", 24.954, 121.351), ("新北市", "中和區", 24.999, 121.499), ("基隆市", "七堵區", 25.096, 121.714),
    ("桃園市", "桃園區", 24.993, 121.301), ("桃園市", "龜山區", 25.022, 121.360), ("桃園市", "八德區", 24.946, 121.290),
    ("桃園市", "大溪區", 24.881, 121.287), ("桃園市", "中壢區", 24.965, 121.225), ("桃園市", "平鎮區", 24.946, 121.218),
    ("桃園市", "楊梅區", 24.908, 121.146), ("桃園市", "蘆竹區", 25.045, 121.292), ("桃園市", "大園區", 25.064, 121.196),
    ("桃園市", "觀音區", 25.033, 121.083), ("桃園市", "龍潭區", 24.864, 121.216), ("新竹縣", "湖口鄉", 24.903, 121.044),
    ("新竹縣", "竹北市", 24.839, 121.004), ("新竹市", "東區", 24.802, 120.972), ("新竹縣", "新豐鄉", 24.899, 120.983),
    ("苗栗縣", "竹南鎮", 24.686, 120.873), ("苗栗縣", "頭份市", 24.688, 120.903), ("苗栗縣", "苗栗市", 24.560, 120.821),
    ("台中市", "西屯區", 24.181, 120.638), ("台中市", "北屯區", 24.182, 120.686), ("台中市", "南屯區", 24.138, 120.645),
    ("台中市", "豐原區", 24.252, 120.722), ("台中市", "潭子區", 24.209, 120.705), ("台中市", "大雅區", 24.229, 120.648),
    ("台中市", "神岡區", 24.258, 120.662), ("台中市", "后里區", 24.309, 120.711), ("台中市", "太平區", 24.126, 120.718),
    ("台中市", "大里區", 24.099, 120.678), ("台中市", "烏日區", 24.105, 120.624), ("台中市", "梧棲區", 24.255, 120.532),
    ("台中市", "沙鹿區", 24.233, 120.566), ("台中市", "清水區", 24.268, 120.560), ("台中市", "大甲區", 24.344, 120.623),
    ("台中市", "龍井區", 24.193, 120.546), ("台中市", "大肚區", 24.154, 120.541), ("彰化縣", "彰化市", 24.081, 120.538),
    ("彰化縣", "和美鎮", 24.111, 120.500), ("彰化縣", "鹿港鎮", 24.057, 120.434), ("彰化縣", "福興鄉", 24.047, 120.444),
    ("彰化縣", "秀水鄉", 24.035, 120.503), ("彰化縣", "花壇鄉", 24.029, 120.538), ("彰化縣", "員林市", 23.959, 120.574),
    ("彰化縣", "大村鄉", 23.993, 120.540), ("彰化縣", "溪湖鎮", 23.962, 120.479), ("彰化縣", "埔心鄉", 23.953, 120.543),
    ("彰化縣", "芬園鄉", 23.997, 120.629), ("彰化縣", "北斗鎮", 23.871, 120.521), ("南投縣", "南投市", 23.916, 120.664),
    ("南投縣", "草屯鎮", 23.974, 120.680), ("雲林縣", "斗六市", 23.711, 120.543), ("雲林縣", "虎尾鎮", 23.708, 120.432),
    ("嘉義縣", "民雄鄉", 23.552, 120.429), ("嘉義市", "西區", 23.480, 120.437), ("台南市", "新營區", 23.310, 120.317),
    ("台南市", "麻豆區", 23.181, 120.248), ("台南市", "佳里區", 23.165, 120.177), ("台南市", "善化區", 23.132, 120.297),
    ("台南市", "官田區", 23.194, 120.315), ("台南市", "新市區", 23.079, 120.295), ("台南市", "永康區", 23.026, 120.257),
    ("台南市", "安南區", 23.047, 120.185), ("台南市", "北區", 23.005, 120.208), ("台南市", "仁德區", 22.972, 120.252),
    ("台南市", "歸仁區", 22.967, 120.293), ("台南市", "安定區", 23.121, 120.237), ("高雄市", "路竹區", 22.857, 120.262),
    ("高雄市", "岡山區", 22.797, 120.296), ("高雄市", "阿蓮區", 22.884, 120.327), ("高雄市", "燕巢區", 22.794, 120.361),
    ("高雄市", "大社區", 22.730, 120.348), ("高雄市", "仁武區", 22.701, 120.348), ("高雄市", "楠梓區", 22.728, 120.307),
    ("高雄市", "三民區", 22.648, 120.302), ("高雄市", "前鎮區", 22.595, 120.315), ("高雄市", "小港區", 22.565, 120.354),
    ("高雄市", "鳳山區", 22.627, 120.357), ("高雄市", "大寮區", 22.605, 120.395), ("屏東縣", "屏東市", 22.670, 120.488),
    ("宜蘭縣", "宜蘭市", 24.752, 121.754), ("宜蘭縣", "礁溪鄉", 24.827, 121.771), ("宜蘭縣", "羅東鎮", 24.677, 121.767),
    ("宜蘭縣", "五結鄉", 24.685, 121.799), ("宜蘭縣", "冬山鄉", 24.637, 121.792), ("宜蘭縣", "蘇澳鎮", 24.595, 121.851),
    ("宜蘭縣", "頭城鎮", 24.858, 121.823), ("花蓮縣", "花蓮市", 23.988, 121.601), ("花蓮縣", "吉安鄉", 23.962, 121.568),
    ("花蓮縣", "壽豐鄉", 23.870, 121.509), ("花蓮縣", "鳳林鎮", 23.745, 121.452), ("花蓮縣", "光復鄉", 23.669, 121.423),
    ("花蓮縣", "瑞穗鄉", 23.497, 121.376), ("花蓮縣", "玉里鎮", 23.336, 121.312), ("台東縣", "池上鄉", 23.125, 121.219),
    ("台東縣", "台東市", 22.756, 121.144), ("新竹縣", "關西鎮", 24.789, 121.177), ("桃園市", "復興區", 24.820, 121.352),
]

DRIVER_NAMES = ["陳俊宏", "林國榮", "張家豪", "黃信義", "吳建興", "劉育成", "蔡明峰", "楊宗翰", "許文彬",
                "鄭志偉", "謝坤霖", "郭振源", "洪世昌", "曾國峰", "廖俊傑", "賴政達", "周永福", "徐志強"]

CUSTOMER_PREFIX = ["全聯", "家樂福", "大潤發", "好市多", "統一超商", "全家", "萊爾富", "美廉社", "楓康超市", "愛買",
                   "三商家購", "台灣菸酒", "義美食品", "光泉牧場", "桂冠實業", "味全食品", "黑松", "台灣中油",
                   "興農", "台塑生醫", "寶雅", "屈臣氏", "康是美", "大買家", "振宇五金", "特力屋", "燦坤", "全國電子"]
CUSTOMER_SUFFIX = ["物流中心", "配送中心", "門市", "倉庫", "分店", "營業所"]
CARGO = ["常溫食品 6 板", "冷藏乳品 4 板", "日用品 8 板", "飲料 10 板", "建材 3.2 噸", "五金零件 1.8 噸",
         "電子零組件 24 箱", "生鮮蔬果 5 板", "冷凍食品 4 板", "紙箱包材 2 噸", "化工原料 1.5 噸", "家電 12 件"]


def district(lat, lon):
    best = min(DISTRICTS, key=lambda d: (d[2] - lat) ** 2 + ((d[3] - lon) * 0.91) ** 2)
    return best[0], best[1]


def km_between(a, b):
    return math.hypot((a[0] - b[0]) * 111, (a[1] - b[1]) * 101)


def hhmm(sec):
    sec = int(sec) % 86400
    return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}"


# ---------------- 駕駛 ----------------
def make_drivers(vehicles, days):
    """一車一位主要駕駛（FAQ 建議的假設）。王師傅、李師傅綁到資料中有對應故事的車。"""
    prev = [d for d in days if d["date"] == PREV_DAY]
    wang = max(prev, key=lambda d: d["max_cont_h"])["plate"]           # 上一營運日連續駕駛最久

    rate = defaultdict(lambda: defaultdict(Counter))
    for d in days:
        r = rate[d["plate"]][d["date"][:7]]
        r["km"] += d["km"]
        r["distract"] += d["events"].get("16", 0)
    def dr(p, m):
        r = rate[p][m]
        return r["distract"] / r["km"] * 100 if r["km"] > 50 else 0
    li = max(rate, key=lambda p: dr(p, "2025-11") - dr(p, "2025-09"))  # 分心事件增加最多

    names = DRIVER_NAMES[:]
    rng.shuffle(names)
    drivers = []
    for i, v in enumerate(sorted(vehicles, key=lambda v: v["plate"])):
        if v["plate"] == wang:
            name = "王志明"
        elif v["plate"] == li:
            name = "李文雄"
        else:
            name = names.pop()
        drivers.append({
            "id": f"D{i + 1:02d}", "name": name, "nick": name[0] + "師傅", "plate": v["plate"],
            "years": rng.choice([2, 3, 4, 5, 6, 8, 10, 12, 15]), "phone": f"09{rng.randint(10, 99)}-***-{rng.randint(100, 999)}",
            "line": rng.random() > 0.1,
        })
    return drivers


# ---------------- 配送任務（停靠點來自真實軌跡） ----------------
def find_stops(track):
    """找出停車 ≥ 6 分鐘、離出發點 1 公里以上的位置，作為配送停靠點。"""
    if len(track) < 10:
        return []
    depot = (track[0][1], track[0][2])
    stops, cur = [], None
    for sec, lat, lon, spd, st, odo in track:
        stopped = spd == 0 or st in (0, 2)
        if stopped:
            if cur is None:
                cur = {"start": sec, "end": sec, "lat": lat, "lon": lon, "odo": odo}
            cur["end"] = sec
        else:
            if cur and cur["end"] - cur["start"] >= 360 and km_between((cur["lat"], cur["lon"]), depot) > 1:
                stops.append(cur)
            cur = None
    merged = []
    for s in stops:
        if merged and km_between((s["lat"], s["lon"]), (merged[-1]["lat"], merged[-1]["lon"])) < 0.6:
            merged[-1]["end"] = s["end"]
        else:
            merged.append(s)
    # 最後一站若是收車地點（之後沒再移動）不算配送
    last_move = max((p[0] for p in track if p[3] > 5), default=0)
    merged = [s for s in merged if s["start"] < last_move]
    if len(merged) > 7:
        merged = sorted(sorted(merged, key=lambda s: s["end"] - s["start"], reverse=True)[:7], key=lambda s: s["start"])
    return merged


def make_tasks(date, tracks, drivers, story=False):
    used = set()
    by_plate = {d["plate"]: d for d in drivers}
    tasks = []
    for plate, tr in sorted(tracks.items()):
        for i, s in enumerate(find_stops(tr)):
            city, dist = district(s["lat"], s["lon"])
            while True:
                short = dist[:-1] if len(dist) > 2 else city[:2] + dist[:-1]
                cust = rng.choice(CUSTOMER_PREFIX) + " " + short + rng.choice(CUSTOMER_SUFFIX)
                if cust not in used:
                    used.add(cust)
                    break
            arrive = s["start"]
            # 預約時段：大多數準時（實際到達落在時段內），少數會遲到
            slack = rng.choice([10, 15, 20, 25, 30, 40]) * 60
            win_end = math.ceil((arrive + slack) / 1800) * 1800
            if rng.random() < 0.03:
                win_end = math.floor((arrive - rng.choice([20, 25, 35]) * 60) / 600) * 600
            tasks.append({
                "id": f"T{date[5:7]}{date[8:]}-{len(tasks) + 1:03d}", "date": date, "plate": plate,
                "driver": by_plate[plate]["id"], "seq": i + 1, "customer": cust, "city": city, "district": dist,
                "lat": s["lat"], "lon": s["lon"], "cargo": rng.choice(CARGO),
                "window_start": hhmm(win_end - 3600), "window_end": hhmm(win_end),
                "arrive_actual": hhmm(arrive), "depart_actual": hhmm(s["end"]),
                "arrive_sec": arrive, "depart_sec": s["end"], "contact": f"{rng.choice('王林陳張黃吳劉蔡楊許')}先生/小姐",
            })
    if story:
        # 簡報範例「下午台中線有 2 筆任務可能延誤 30 分鐘」：挑兩筆下午在台中的任務，預約時段設得比實際到達早
        tc = [t for t in tasks if t["city"] == "台中市" and 14.6 * 3600 <= t["arrive_sec"] <= 17 * 3600]
        tc = sorted(tc, key=lambda t: t["arrive_sec"])[:2]
        for t in tc:
            end = math.floor((t["arrive_sec"] - 38 * 60) / 600) * 600
            t["window_start"], t["window_end"] = hhmm(end - 3600), hhmm(end)
            t["story"] = "taichung_delay"
    return tasks


# ---------------- 準時率歷史（每位駕駛每月） ----------------
def make_ontime(drivers, days):
    months = sorted({d["date"][:7] for d in days})
    out = []
    for dv in drivers:
        base = rng.uniform(0.86, 0.98)
        for m in months:
            n_days = sum(1 for d in days if d["plate"] == dv["plate"] and d["date"][:7] == m)
            if not n_days:
                continue
            n = n_days * rng.randint(4, 7)
            rate = min(1, max(0.7, base + rng.uniform(-0.05, 0.04)))
            out.append({"driver": dv["id"], "month": m, "tasks": n, "on_time": round(n * rate)})
    return out


# ---------------- 客訴（關聯到真實事件） ----------------
def make_complaints(drivers, tasks_prev, events):
    by_plate = {d["plate"]: d for d in drivers}
    ev_prev = defaultdict(list)
    for e in events:
        if e[1].startswith(PREV_DAY):
            h, m, s = map(int, e[1][11:].split(":"))
            ev_prev[e[0]].append((h * 3600 + m * 60 + s, e[2]))

    def count_before(t, types, window=3600):
        return sum(1 for sec, ty in ev_prev[t["plate"]] if ty in types and t["arrive_sec"] - window <= sec <= t["arrive_sec"])

    used, out = set(), []

    def pick(key):
        cands = [t for t in tasks_prev if t["plate"] not in used]
        t = max(cands, key=key)
        used.add(t["plate"])
        return t

    t = pick(lambda t: count_before(t, {7}))
    out.append({"task": t, "channel": "客戶來電", "received": "2025-11-11 " + hhmm(t["depart_sec"] + 2400),
                "text": f"今天送到{t['customer']}的貨，有兩箱外箱凹陷、裡面瓶子破了，司機說路上沒怎樣，但我們懷疑是路上急煞造成的，希望給個說法。",
                "status": "待處理"})
    t = pick(lambda t: (lambda late: late if late > 0 else -1)(t["arrive_sec"] - _sec(t["window_end"])))
    out.append({"task": t, "channel": "LINE 官方帳號", "received": "2025-11-11 " + hhmm(t["arrive_sec"] + 1200),
                "text": f"約好 {t['window_end']} 前到，結果拖到 {t['arrive_actual']} 才到，中間也沒人通知，害我們倉庫人員一直等。",
                "status": "處理中"})
    t = pick(lambda t: t["depart_sec"] - t["arrive_sec"])
    out.append({"task": t, "channel": "客戶來電", "received": "2025-11-11 " + hhmm(t["depart_sec"] + 1800),
                "text": "你們的貨車在我們門口卸貨時引擎一直沒熄火，排氣直接吹進店裡，客人都在抱怨，可以請司機注意一下嗎？",
                "status": "待處理"})
    phone = max((p for p in ev_prev if p not in used), key=lambda p: sum(1 for _, ty in ev_prev[p] if ty in (14, 16)))
    cands = [t for t in tasks_prev if t["plate"] == phone] or [t for t in tasks_prev if t["plate"] not in used]
    t = cands[len(cands) // 2]
    out.append({"task": t, "channel": "民眾來電", "received": "2025-11-11 " + hhmm(t["arrive_sec"] - 600),
                "text": f"車牌 {t['plate']} 的貨車司機邊開車邊低頭看手機，在路口差點撞到機車，很危險。",
                "status": "待處理"})
    res = []
    for i, c in enumerate(out):
        t = c.pop("task")
        res.append({"id": f"C11{i + 1:02d}", **c, "plate": t["plate"], "driver": by_plate[t["plate"]]["id"],
                    "task_id": t["id"], "customer": t["customer"] if i < 3 else "路人（未具名）"})
    return res


def _sec(hm):
    h, m = map(int, hm.split(":"))
    return h * 3600 + m * 60


# ---------------- 保養設定 ----------------
def make_maintenance(vehicles, days):
    interval = {"300": 10000, "500": 15000, "700": 20000}
    odo = {}
    for d in days:
        if d["date"] <= TODAY:
            odo[d["plate"]] = max(odo.get(d["plate"], 0), d["odo_end"])
    out = []
    for v in vehicles:
        iv = interval[v["type"]]
        cur = odo.get(v["plate"], 0)
        # 讓幾台車接近或超過保養里程，畫面上才看得到「到期」的狀態
        offset = rng.choice([-800, -300, 600, 1500, 2500, 4000, 5500, 7000])
        next_km = max(iv, math.ceil(cur / iv) * iv + (offset if offset < 0 else 0))
        out.append({"plate": v["plate"], "interval_km": iv, "next_service_km": next_km,
                    "last_service_date": rng.choice(["2025-08-12", "2025-09-03", "2025-09-25", "2025-10-08", "2025-10-21"])})
    return out


# ---------------- 延誤預測的歷史資料（給 LightGBM 訓練） ----------------
def make_delivery_history(profile, n=6000):
    """每筆是一段配送路程：路段歷史車速（同路段過去的平均車速）是主要依據，再受時段、市區、降雨影響。
    時段效果取自 iTRAQ 真實資料各小時平均車速相對全日平均的比例。"""
    sp = defaultdict(dict)
    for p in profile:
        sp[(p["type"], p["urban"])][p["hour"]] = p["speed"]
    hour_factor = {}
    for key, hours in sp.items():
        day = [v for h, v in hours.items() if 7 <= h <= 19]
        mean = sum(day) / len(day)
        for h in range(5, 23):
            v = hours.get(h) or mean
            hour_factor[key + (h,)] = min(1.25, max(0.8, v / mean))

    rows = []
    for _ in range(n):
        tp = rng.choice(["300", "300", "500", "700"])
        urban = rng.random() < 0.55
        hour = rng.randint(6, 20)
        dist = round(rng.uniform(0.5, 40) if rng.random() < 0.8 else rng.uniform(40, 150), 1)
        hist = round(rng.uniform(15, 45) if urban else rng.uniform(25, 75), 1)
        rain = int(rng.random() < 0.18)
        weekday = rng.randint(0, 6)
        speed = hist * hour_factor[(tp, urban, hour)]
        peak = 1.25 if urban and hour in (7, 8, 17, 18) else 1.0
        minutes = dist / speed * 60 * peak * (1.18 if rain else 1) * (1.04 if weekday < 5 else 0.95)
        minutes = minutes * rng.lognormvariate(0, 0.1) + rng.uniform(0, 3)
        rows.append({"vehicle_type": tp, "urban": int(urban), "hour": hour, "remaining_km": dist, "hist_speed": hist,
                     "rain": rain, "weekday": weekday, "minutes": round(minutes, 1)})
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    vehicles, days, events = load("vehicles.json"), load("vehicle_days.json"), load("events.json")
    drivers = make_drivers(vehicles, days)
    dump("drivers.json", drivers)
    tasks_today = make_tasks(TODAY, load(f"tracks_{TODAY}.json"), drivers, story=True)
    tasks_prev = make_tasks(PREV_DAY, load(f"tracks_{PREV_DAY}.json"), drivers)
    dump(f"tasks_{TODAY}.json", tasks_today)
    dump(f"tasks_{PREV_DAY}.json", tasks_prev)
    dump("ontime.json", make_ontime(drivers, days))
    dump("complaints.json", make_complaints(drivers, tasks_prev, events))
    dump("maintenance.json", make_maintenance(vehicles, days))
    dump("weather.json", {"date": TODAY, "note": "模擬天氣", "rain": [{"city": "台中市", "from": "14:00", "to": "17:30", "desc": "午後雷陣雨"}]})
    hist = make_delivery_history(load("speed_profile.json"))
    with open(OUT / "delivery_history.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(hist[0]))
        w.writeheader()
        w.writerows(hist)
    print(f"  delivery_history.csv（{len(hist)} 筆）")
    print(f"今日任務 {len(tasks_today)} 筆、上一營運日 {len(tasks_prev)} 筆")


if __name__ == "__main__":
    main()
