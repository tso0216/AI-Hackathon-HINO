"""延誤預測：以 LightGBM 預估剩餘路段所需時間，並用 SHAP 貢獻值說明影響因素。
訓練資料 data/mock/delivery_history.csv 為模擬的歷史配送紀錄（車速參考 iTRAQ 真實資料各時段平均車速）。"""
import csv
from pathlib import Path

import lightgbm as lgb
import numpy as np

DATA = Path(__file__).resolve().parent.parent / "data" / "mock" / "delivery_history.csv"

FEATURES = ["vehicle_type", "urban", "hour", "remaining_km", "hist_speed", "rain", "weekday"]
LABELS = {"vehicle_type": "車型", "urban": "市區路段", "hour": "出發時段", "remaining_km": "剩餘距離",
          "hist_speed": "路段歷史車速", "rain": "降雨（模擬天氣）", "weekday": "星期"}
TYPE_CODE = {"300": 0, "500": 1, "700": 2}


def _encode(row):
    return [TYPE_CODE.get(str(row["vehicle_type"]), 0), int(row["urban"]), int(row["hour"]), float(row["remaining_km"]),
            float(row["hist_speed"]), int(row["rain"]), int(row["weekday"])]


def _train():
    with DATA.open() as f:
        rows = list(csv.DictReader(f))
    X = np.array([_encode(r) for r in rows], dtype=float)
    y = np.array([float(r["minutes"]) for r in rows])
    ds = lgb.Dataset(X, y, feature_name=FEATURES, categorical_feature=["vehicle_type"])
    params = {"objective": "regression", "learning_rate": 0.05, "num_leaves": 31, "min_data_in_leaf": 20,
              "verbose": -1, "seed": 42}
    return lgb.train(params, ds, num_boost_round=400), len(rows)


MODEL, N_TRAIN = _train()


def predict(row):
    """回傳 (預估分鐘數, [{特徵, 貢獻分鐘}], 基準分鐘)。"""
    x = np.array([_encode(row)], dtype=float)
    contrib = MODEL.predict(x, pred_contrib=True)[0]
    factors = [{"key": f, "name": LABELS[f], "minutes": round(float(c), 1)} for f, c in zip(FEATURES, contrib[:-1])]
    factors.sort(key=lambda f: -abs(f["minutes"]))
    return max(1.0, float(contrib.sum())), factors, float(contrib[-1])
