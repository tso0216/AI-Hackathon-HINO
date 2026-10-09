"""問 AI：LLM 理解問題 → 呼叫查詢函式取得數字 → LLM 用白話回答。數字一律來自查詢結果。"""
import logging
import re

from config import Config
from services import tools
from services.ai_client import ai
from services.data import MONTHS, sec_to_hhmm

log = logging.getLogger(__name__)


def system_prompt(t):
    return f"""你是「HINO Pilot」車隊經營 AI 助理，對象是 5–50 台車的貨運車隊老闆，用繁體中文、口語、直接給結論。

現在是 {Config.TODAY}（星期五）{sec_to_hhmm(t)}，畫面以 iTRAQ 真實軌跡回放今天。
資料是每月抽樣日：有資料的月份為 {'、'.join(MONTHS)}。
- 「本月、這個月、這週、上週、最近」→ period={MONTHS[-1]}，直接用這期資料回答，不要說「沒有上週資料」
- 「上個月」→ 前一個有資料的月份 {MONTHS[-2]}
- 「今年、整體、全部、長期」→ period=all
- 「今天、現在、即時」→ 用 get_fleet_overview、get_deliveries 或 get_hours_compliance

規則：
1. 任何數字都必須來自查詢函式的結果，不可自行估算或編造；查不到就說查不到。比較時直接引用函式提供的欄位（例如 vs_median_pct、excess_pct、excess_ntd），不要自己相減或換算出新數字。需要時可以連續呼叫多個函式。
2. 先講結論（誰、多少、差多少），再用 2–3 點說明原因，最後給 1–2 個具體可執行的建議。
3. 全文 160 字以內；可用「- 」條列與 **粗體**，不要用表格與標題。
4. 司機稱呼用「X師傅」（姓氏＋師傅），提到車輛時附車牌。
5. 用到準時率、任務、客戶、天氣、保養週期時，這些是模擬資料，句末標註「（模擬）」一次即可。
6. 比較油耗與事件時，要說明是跟「同車型中位數」或「自己過去」比。
7. 問題與車隊經營無關時，簡短說明你能協助的範圍。"""


def ask(question, history, t):
    """yield 給前端的事件（SSE）。"""
    msgs = [{"role": m["role"], "content": m["content"]} for m in (history or [])[-8:] if m.get("content")]
    msgs.append({"role": "user", "content": question})
    if ai.live:
        try:
            yield {"type": "status", "text": "理解問題中…"}
            yield from ai.run_tools(system_prompt(t), msgs, tools.TOOLS, lambda n, a: tools.execute(n, a, t))
            return
        except Exception as e:  # noqa: BLE001
            log.exception("問 AI 失敗，改用模擬回答")
            yield {"type": "status", "text": f"LLM 暫時無法使用，改用規則回答（{str(e)[:60]}）"}
    yield from _mock(question, t)


# ---------------- 沒有 API key 時的規則回答 ----------------
def _mock(q, t):
    m = MONTHS[-1]
    period = "all" if re.search(r"今年|整體|全部|長期", q) else (MONTHS[-2] if "上個月" in q else m)
    plate = re.search(r"ABC-\d{4}", q.upper())
    name = next((d for d in ["王", "李", "陳", "林", "張", "黃", "吳", "劉", "蔡", "楊", "許", "鄭", "謝", "郭", "洪", "曾", "廖", "賴", "周", "徐"]
                 if d + "師傅" in q), None)

    def call(fn, **args):
        yield {"type": "tool_call", "name": fn, "args": args}
        r = tools.execute(fn, args, t)
        yield {"type": "tool_result", "name": fn, "result": r}
        return r

    if re.search(r"規定|新規|法規|罰|定義|怎麼算|手冊|故障碼|DTC", q, re.I):
        r = yield from call("search_knowledge", query=q)
        top = r["results"][0]
        text = f"{top['text']}\n（來源：{top['source']}）"
    elif re.search(r"油|耗", q) and (plate or name or "為什麼" in q):
        target = plate.group(0) if plate else (name + "師傅" if name else "ABC-1999")
        r = yield from call("get_fuel_breakdown", plate=target, period="all")
        if r.get("factors"):
            f = r["factors"][0]
            text = (f"**{r['plate']}** 油耗 {r['l100']} L/100km，比同車型中位數 {r['median_l100']} 高 {r['excess_pct']}%，"
                    f"約多花 NT${r['excess_ntd']:,}。\n- 最大原因：{f['name']}（{f['detail']}），約 {f['liters']} 公升\n"
                    "- 建議先從這一項開始改善，下個月再對照一次。")
        else:
            text = r.get("note") or r.get("error", "查不到資料")
    elif re.search(r"油|耗", q):
        r = yield from call("get_fuel_ranking", period=period, series="all")
        top = r["ranking"][0]
        text = (f"{r['資料區間']}最耗油的是 **{top['plate']}（{top['driver']}）**，{top['l100']} L/100km，"
                f"比同車型中位數高 {top['vs_median_pct']}%，約多花 NT${top['excess_ntd']:,}。主要原因：{top['top_factor'] or '待查'}。")
    elif re.search(r"關心|分數|排名|績效|誰.*(差|好)", q) or name:
        if name:
            r = yield from call("get_driver_detail", driver=name + "師傅", period=period)
            s = r.get("score") or {}
            text = (f"**{r['driver']}** {r['資料區間']}綜合 {s.get('score')} 分（安全 {s.get('sub', {}).get('safety')}、"
                    f"節能 {s.get('sub', {}).get('eco')}、準時 {s.get('sub', {}).get('ontime')}、合規 {s.get('sub', {}).get('compliance')}）。")
        else:
            r = yield from call("get_driver_ranking", period=period, sort_by="drop")
            d = r["ranking"][0]
            text = (f"最需要關心的是 **{d['driver'][0]}師傅**（{d['plate']}）：綜合分數從 {d['prev_score']} 降到 {d['score']}，"
                    f"安全分數 {d['prev_sub']['safety'] if d['prev_sub'] else '—'} → {d['sub']['safety']}。建議先了解排班與身體狀況。")
    elif re.search(r"工時|超時|連續|休息|10 ?小時", q):
        r = yield from call("get_hours_compliance", period=m)
        top = r["today"][0] if r["today"] else None
        text = (f"目前連續駕駛最久的是 **{top['driver']}**（{top['plate']}）{top['cont_h']} 小時，今日累計 {top['drive_h']} 小時。"
                if top else "目前沒有車輛在行駛。") + f"\n- {r['rule']}"
    elif re.search(r"延誤|遲到|準時|配送|到貨", q):
        r = yield from call("get_deliveries", only_risk=True)
        text = f"目前有 {len(r['tasks'])} 筆任務有延誤風險（模擬）：\n" + "\n".join(
            f"- {k['customer']}：預計 {k['eta']}，晚 {k['delay_min']} 分鐘" for k in r["tasks"][:4])
    else:
        r = yield from call("get_fleet_overview")
        k = r["today"]
        text = (f"目前 {k['vehicles_out']}/{k['vehicles_total']} 台出車，配送 {k['tasks_done']}/{k['tasks_total']} 站，"
                f"{k['risk_high']} 筆任務有延誤風險（模擬）。")
    for i in range(0, len(text), 6):
        yield {"type": "delta", "text": text[i:i + 6]}
    yield {"type": "done", "text": text}
