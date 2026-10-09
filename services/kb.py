"""RAG：檢索法規、iTRAQ 事件定義與操作手冊。"""
import threading

from services.ai_client import ai, cosine
from services.data import KB

_lock = threading.Lock()
_index = {"vecs": None, "mode": None}


def _doc_text(d):
    return f"{d['title']}\n{d['text']}"


def search(query, k=3):
    (q,), mode = ai.embed([query])
    with _lock:
        # 文件與問題必須是同一種向量（live 或 mock），embedding 中途失敗時重建索引
        if _index["mode"] != mode:
            _index["vecs"], _index["mode"] = ai.embed([_doc_text(d) for d in KB])
            if _index["mode"] != mode:
                (q,), mode = ai.embed([query])
    scored = sorted(((cosine(q, v), d) for v, d in zip(_index["vecs"], KB)), key=lambda x: -x[0])[:k]
    return {
        "query": query, "mode": mode,
        "results": [{"title": d["title"], "source": d["source"], "text": d["text"], "score": round(s, 3)} for s, d in scored],
    }
