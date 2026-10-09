# demo app

## 快速使用

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env        # 填入 OPENAI_API_KEY
.venv/bin/python app.py
```

開啟 http://localhost:5080

註：不填 API key 也能完整操作（AI 改用規則模擬）。

## 體驗流程

左下角「Demo 模擬」可切換一天中的時間點，或按 ▶ 讓車輛依真實軌跡移動。

| # | 時間點 | 試試看 |
|---|---|---|
| 1 | 07:30 LINE 晨報 | 首頁看 AI 晨報與「今天先處理這 3 件事」，按「LINE 預覽」看推播畫面 |
| 2 | 14:00 即時提醒 | 即時配送：台中兩筆任務預計延誤，點任務看 LightGBM 預測依據 → 「AI 擬客戶通知」→ 以 LINE 發送 |
| 3 | 17:30 工時預警 | 安全與合規：連續駕駛超過 4 小時、單日接近 10 小時的司機 |
| 4 | 隨時 問 AI | 右上「問 AI」：問「這個月誰最需要關心？」「ABC-1999 為什麼這麼耗油？」，看 AI 呼叫哪些查詢函式 |
| 5 | 月底 績效月報 | 司機績效：綜合分數排名、AI 教練分析、LINE 週回饋；「AI 月報與獎金建議」 |
| 6 | 車隊績效 | 同車型油耗比較，點車輛看「多耗的油花在哪裡」與 AI 節能建議 |
| 7 | 客訴追蹤 | 安全與合規 → 客訴追蹤：AI 分類、調出當天真實軌跡與事件、擬回覆 |



重新產生資料：

```bash
.venv/bin/python scripts/build_dataset.py     # 讀「HINO 競賽數據」資料夾內的 xlsx（約 1 分鐘）
.venv/bin/python scripts/gen_mock.py
```


地圖底圖使用內政部國土測繪中心「臺灣通用電子地圖」。
