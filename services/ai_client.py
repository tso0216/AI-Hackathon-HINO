import hashlib
import json
import logging
import math
import re
from pathlib import Path

from config import Config

log = logging.getLogger(__name__)

MOCK_DIM = 256
# 有這個檔案代表使用者在畫面上把 AI 關掉了；存成檔案，debug 模式自動重啟後仍維持關閉
OFF_FLAG = Path(__file__).resolve().parent.parent / ".ai_off"


class AIClient:
    def __init__(self):
        self._client = None
        self._embed_failed = False
        self._embed_cache = {}
        self.enabled = not OFF_FLAG.exists()
        if Config.OPENAI_API_KEY and Config.AI_MODE != "mock":
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=Config.OPENAI_API_KEY, base_url=Config.OPENAI_BASE_URL, timeout=60)
            except ImportError:
                log.warning("找不到 openai 套件，改用 mock 模式")

    @property
    def configured(self):
        return self._client is not None

    @property
    def live(self):
        return self.configured and self.enabled

    def set_enabled(self, on):
        self.enabled = bool(on)
        if self.enabled:
            OFF_FLAG.unlink(missing_ok=True)
        else:
            OFF_FLAG.touch()

    def status(self):
        return {"live": self.live, "configured": self.configured, "enabled": self.enabled,
                "llm": Config.LLM_MODEL if self.configured else "mock",
                "embedding": Config.EMBEDDING_MODEL if self.live and not self._embed_failed else "mock"}

    # ---------- LLM：結構化輸出 ----------
    def chat_json(self, system, user, fallback):
        """呼叫 LLM 並解析 JSON。回傳 (dict, mode)。fallback 是產生 mock 結果的函式。"""
        if self.live:
            try:
                resp = self._client.chat.completions.create(
                    model=Config.LLM_MODEL,
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                    response_format={"type": "json_object"},
                    reasoning_effort=Config.LLM_EFFORT,
                )
                return json.loads(resp.choices[0].message.content), "live"
            except Exception as e:  # noqa: BLE001
                log.exception("LLM 呼叫失敗")
                return fallback(), f"mock（LLM 失敗：{_short(e)}）"
        return fallback(), "mock"

    # ---------- LLM：tool calling（串流） ----------
    def run_tools(self, system, messages, tools, execute, max_rounds=5):
        """以 Responses API 跑 tool calling，逐步 yield 事件：
        {"type": "tool_call", ...}、{"type": "tool_result", ...}、{"type": "delta", "text": ...}、{"type": "done"}。
        execute(name, args) 回傳 dict（會原樣交給 LLM）。"""
        items = [{"role": "system", "content": system}] + messages
        for _ in range(max_rounds):
            calls, text = [], []
            stream = self._client.responses.create(
                model=Config.LLM_MODEL, input=items, tools=tools, stream=True,
                reasoning={"effort": Config.LLM_EFFORT},
            )
            final = None
            for ev in stream:
                if ev.type == "response.output_text.delta":
                    text.append(ev.delta)
                    yield {"type": "delta", "text": ev.delta}
                elif ev.type == "response.completed":
                    final = ev.response
            if final is None:
                raise RuntimeError("串流未完成")
            for item in final.output:
                if item.type == "function_call":
                    calls.append(item)
            if not calls:
                yield {"type": "done", "text": "".join(text)}
                return
            items += [o.model_dump(exclude_none=True) for o in final.output if o.type in ("function_call", "reasoning")]
            for c in calls:
                args = json.loads(c.arguments or "{}")
                yield {"type": "tool_call", "name": c.name, "args": args}
                result = execute(c.name, args)
                yield {"type": "tool_result", "name": c.name, "result": result}
                items.append({"type": "function_call_output", "call_id": c.call_id,
                              "output": json.dumps(_for_llm(result), ensure_ascii=False)})
        yield {"type": "done", "text": ""}

    # ---------- Embedding ----------
    def embed(self, texts):
        """回傳 (list[list[float]], mode)。同一個 process 內只會用同一種向量，避免混用。"""
        if self.live and not self._embed_failed:
            missing = [t for t in texts if t not in self._embed_cache]
            try:
                for i in range(0, len(missing), 100):
                    chunk = missing[i: i + 100]
                    resp = self._client.embeddings.create(model=Config.EMBEDDING_MODEL, input=chunk)
                    for t, d in zip(chunk, resp.data):
                        self._embed_cache[t] = d.embedding
                return [self._embed_cache[t] for t in texts], "live"
            except Exception as e:  # noqa: BLE001
                log.exception("Embedding 呼叫失敗，之後一律改用 mock 向量")
                self._embed_failed = True
                return [mock_embed(t) for t in texts], f"mock（Embedding 失敗：{_short(e)}）"
        return [mock_embed(t) for t in texts], "mock"


def _for_llm(result):
    """圖表設定只給前端用，不必送進 LLM。"""
    if isinstance(result, dict):
        return {k: v for k, v in result.items() if k != "chart"}
    return result


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def mock_embed(text):
    """用字元 unigram + bigram 雜湊成固定維度向量，模擬 embedding 的語意相似度。"""
    vec = [0.0] * MOCK_DIM
    chars = [c for c in re.sub(r"\s+", "", text.lower()) if not re.match(r"[，。、？！,.?!：:「」（）()]", c)]
    grams = chars + [chars[i] + chars[i + 1] for i in range(len(chars) - 1)]
    for g in grams:
        h = int(hashlib.md5(g.encode()).hexdigest(), 16)
        vec[h % MOCK_DIM] += 2.0 if len(g) == 2 else 1.0
    n = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / n for v in vec]


def _short(e):
    s = str(e)
    return s[:80] + "…" if len(s) > 80 else s


ai = AIClient()
