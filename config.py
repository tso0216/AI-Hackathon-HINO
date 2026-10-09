import os

from dotenv import load_dotenv

load_dotenv()

# .env 裡留空的 OPENAI_BASE_URL= 會被 OpenAI SDK 當成空網址，留空時直接移除
if not os.getenv("OPENAI_BASE_URL", "").strip():
    os.environ.pop("OPENAI_BASE_URL", None)


class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "").strip() or None
    AI_MODE = os.getenv("AI_MODE", "auto").strip().lower()

    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-6-luna")
    LLM_EFFORT = os.getenv("LLM_EFFORT", "low")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    PORT = int(os.getenv("PORT", "5080"))

    # Demo 設定：以 iTRAQ 競賽資料 2025/11/21 的真實軌跡回放「今天」
    TODAY = "2025-11-21"
    PREV_DAY = "2025-11-11"
    COMPANY = "順達物流"        # 模擬的車隊公司名稱
    DIESEL_PRICE = 28          # 柴油每公升 NT$（假設值，與簡報一致）
    WEIGHTS = {"safety": 40, "eco": 30, "ontime": 20, "compliance": 10}   # 司機綜合分數初版權重
    DAILY_LIMIT_H = 10         # 2026/5/8 起營業大貨車每日駕駛上限
    CONT_LIMIT_H = 4           # 連續駕駛上限
