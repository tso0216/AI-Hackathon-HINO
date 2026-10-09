import json
import logging
import os
import threading

from flask import Flask, Response, jsonify, render_template, request, stream_with_context

from config import Config
from services import assistant, briefing, coach, complaints, engine, eta_model, live
from services.ai_client import ai
from services.data import (
    DRIVERS, DRIVER_BY_PLATE, EVENT_NAMES, META, MONTHS, VEHICLES, period_days, period_label, periods,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
app = Flask(__name__)
app.json.ensure_ascii = False
app.json.sort_keys = False


def _t():
    try:
        return int(float(request.args.get("t", 14 * 3600)))
    except ValueError:
        return 14 * 3600


def _period(default=None):
    p = request.args.get("period") or default or MONTHS[-1]
    return p if p in MONTHS or p == "all" else MONTHS[-1]


def _weights():
    w = request.args.get("w")
    if not w:
        return None
    vals = [max(0, int(x)) for x in w.split(",")][:4]
    return tuple(zip(("safety", "eco", "ontime", "compliance"), vals))


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/bootstrap")
def bootstrap():
    return jsonify({
        "today": Config.TODAY, "prev_day": Config.PREV_DAY, "company": Config.COMPANY, "ai": ai.status(),
        "periods": periods(), "months": MONTHS, "weights": Config.WEIGHTS, "diesel_price": Config.DIESEL_PRICE,
        "limits": {"daily": Config.DAILY_LIMIT_H, "cont": Config.CONT_LIMIT_H},
        "meta": META, "eta_model": {"n_train": eta_model.N_TRAIN, "features": eta_model.FEATURES},
        "drivers": list(DRIVERS.values()),
        "vehicles": [{**v, "driver": DRIVER_BY_PLATE[p]["name"]} for p, v in VEHICLES.items()],
    })


# ---------- 首頁總覽 ----------
@app.get("/api/overview")
def overview():
    t = _t()
    snap = live.snapshot(t)
    month = MONTHS[-1]
    scores = engine.driver_scores(month)
    attention = sorted([r for r in scores if r.get("prev")], key=lambda r: r["score"] - r["prev"]["score"])[:3]
    return jsonify({
        "kpi": snap["kpi"], "time": snap["time"], "alerts": snap["alerts"][:30],
        "prev_day": engine.day_summary(Config.PREV_DAY),
        "prev_prev_day": engine.day_summary(_prev_data_day(Config.PREV_DAY)),
        "fleet_trend": engine.fleet_trend(),
        "attention": [{"driver_id": r["driver_id"], "name": r["name"], "plate": r["plate"], "score": r["score"],
                       "prev": r["prev"]["score"], "sub": r["sub"], "prev_sub": r["prev"]["sub"]} for r in attention],
        "month_label": period_label(month),
    })


def _prev_data_day(date):
    dates = sorted({d["date"] for d in period_days("all") if d["date"] < date})
    counts = {x: sum(1 for d in period_days("all") if d["date"] == x) for x in dates}
    return next(x for x in reversed(dates) if counts[x] >= 8)


@app.get("/api/briefing")
def morning():
    return jsonify(briefing.morning())


# ---------- 即時配送 ----------
@app.get("/api/live")
def live_snapshot():
    return jsonify(live.snapshot(_t()))


@app.get("/api/tasks/<task_id>")
def task(task_id):
    k = live.task_detail(task_id, _t())
    return (jsonify(k), 200) if k else (jsonify({"error": "not found"}), 404)


@app.get("/api/route/<plate>")
def route(plate):
    r = live.vehicle_route(plate, _t())
    return (jsonify(r), 200) if r else (jsonify({"error": "not found"}), 404)


@app.post("/api/notice")
def notice():
    body = request.json or {}
    out = coach.customer_notice(body["task_id"], int(body.get("t", 14 * 3600)))
    return (jsonify(out), 200) if out else (jsonify({"error": "not found"}), 404)


@app.post("/api/notice/send")
def notice_send():
    body = request.json or {}
    coach.mark_sent(body["task_id"], int(body.get("t", 14 * 3600)))
    return jsonify({"ok": True})


# ---------- 司機績效 ----------
@app.get("/api/drivers")
def drivers():
    period = _period()
    rows = engine.driver_scores(period, _weights())
    return jsonify({"period": period, "period_label": period_label(period), "rows": rows})


@app.get("/api/drivers/<driver_id>")
def driver(driver_id):
    period = _period()
    d = DRIVERS.get(driver_id)
    if not d:
        return jsonify({"error": "not found"}), 404
    row = next((r for r in engine.driver_scores(period, _weights()) if r["driver_id"] == driver_id), None)
    return jsonify({
        "driver": d, "period_label": period_label(period), "row": row, "trend": engine.driver_trend(driver_id),
        "dms_hours": engine.event_hours(d["plate"], period, {12, 14, 16}),
        "fuel": engine.fuel_breakdown(d["plate"], period),
    })


@app.get("/api/drivers/<driver_id>/advice")
def driver_advice(driver_id):
    return jsonify(coach.driver_advice(driver_id, _period()))


@app.get("/api/monthly")
def monthly():
    return jsonify(briefing.monthly(_period()))


# ---------- 車隊績效 ----------
@app.get("/api/vehicles")
def vehicles():
    period = _period()
    return jsonify({"period": period, "period_label": period_label(period), "rows": engine.vehicle_table(period),
                    "benchmarks": engine.type_benchmarks(period)})


@app.get("/api/vehicles/<plate>")
def vehicle(plate):
    period = _period()
    if plate not in VEHICLES:
        return jsonify({"error": "not found"}), 404
    days = [{"date": d["date"], "l100": round(d["fuel"] / d["km"] * 100, 1) if d["km"] >= 15 else None,
             "km": d["km"], "idle_h": d["idle_h"], "drive_h": d["drive_h"]}
            for d in period_days("all") if d["plate"] == plate]
    return jsonify({"plate": plate, "vehicle": VEHICLES[plate], "driver": DRIVER_BY_PLATE[plate],
                    "period_label": period_label(period), "fuel": engine.fuel_breakdown(plate, period),
                    "stats": engine.vehicle_stats(period).get(plate), "maint": engine.maintenance_status()[plate],
                    "days": days, "median_all": engine.type_benchmarks("all")[VEHICLES[plate]["type"]]["l100"]})


@app.get("/api/vehicles/<plate>/explain")
def vehicle_explain(plate):
    return jsonify(coach.vehicle_explain(plate, _period()))


# ---------- 安全與合規 ----------
@app.get("/api/safety")
def safety():
    period = _period()
    t = _t()
    snap = live.snapshot(t)
    stats = engine.vehicle_stats(period)
    hours = [0] * 24
    for p, s in stats.items():
        if s["has_dms"]:
            for h, n in enumerate(engine.event_hours(p, period, {12, 14, 16})):
                hours[h] += n
    rows = []
    for p, s in sorted(stats.items()):
        rows.append({"plate": p, "driver": DRIVER_BY_PLATE[p]["name"], "driver_id": DRIVER_BY_PLATE[p]["id"],
                     "series": s["series"], "has_dms": s["has_dms"], "drive_h": s["drive_h"], "km": s["km"],
                     "fatigue": s["rate_h"].get(12, 0), "distract": s["rate_h"].get(16, 0), "phone": s["rate_h"].get(14, 0),
                     "seatbelt": s["events"].get(13, 0), "pcs": s["events"].get(19, 0), "ldws": s["rate_h"].get(20, 0),
                     "harsh_100": s["harsh_100"], "speeding_100": s["rate"].get(8, 0)})
    today = [{k: v.get(k) for k in ("plate", "driver", "driver_id", "state", "depart", "drive_h", "cont_h", "type")}
             for v in snap["vehicles"] if v["state"] != "今日未排班"]
    return jsonify({"period": period, "period_label": period_label(period), "time": snap["time"],
                    "today": sorted(today, key=lambda v: -(v["cont_h"] or 0)),
                    "violations": engine.hours_violations(period), "dms_hours": hours, "rows": rows,
                    "complaints": complaints.listing(), "event_names": EVENT_NAMES})


@app.get("/api/complaints/<cid>")
def complaint(cid):
    return jsonify(complaints.analyze(cid))


@app.post("/api/complaints/<cid>/status")
def complaint_status(cid):
    complaints.set_status(cid, (request.json or {}).get("status", "處理中"))
    return jsonify({"ok": True, "complaints": complaints.listing()})


# ---------- 問 AI（SSE 串流） ----------
@app.post("/api/ask")
def ask():
    body = request.json or {}
    q = (body.get("question") or "").strip()
    t = int(body.get("t", 14 * 3600))

    def gen():
        for ev in assistant.ask(q, body.get("history"), t):
            yield f"data: {json.dumps(ev, ensure_ascii=False, default=str)}\n\n"

    return Response(stream_with_context(gen()), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/ai")
def ai_switch():
    """畫面上的 AI 開關。關閉後一律走規則模擬，不呼叫 LLM／Embedding。"""
    ai.set_enabled((request.get_json(silent=True) or {}).get("enabled"))
    if ai.live:
        # 重新開啟時丟掉關閉期間產生的模擬結果，之後打開才會改由 LLM 產生
        for mod in (briefing, coach, complaints):
            with mod._lock:
                for k in [k for k, v in mod._cache.items() if not (isinstance(v, dict) and v.get("mode") == "live")]:
                    del mod._cache[k]
    return jsonify(ai.status())


@app.post("/api/reset")
def reset():
    live.SENT.clear()
    live.snapshot.cache_clear()
    complaints.clear()
    return jsonify({"ok": True})


def _warm_up():
    """預先產生晨報與月報，demo 時打開就有內容。"""
    try:
        briefing.morning()
        briefing.monthly()
    except Exception:  # noqa: BLE001
        logging.exception("預熱失敗")


if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Thread(target=_warm_up, daemon=True).start()
    print(f"AI 模式：{'LIVE（' + Config.LLM_MODEL + '）' if ai.live else 'MOCK（已在畫面上關閉 AI）' if ai.configured else 'MOCK（未設定 OPENAI_API_KEY）'}")
    print(f"開啟 http://localhost:{Config.PORT}")
    app.run(debug=True, port=Config.PORT, threaded=True)
