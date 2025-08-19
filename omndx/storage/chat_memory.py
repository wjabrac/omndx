from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:  # optional dependency
    import chromadb  # type: ignore
    from chromadb.config import Settings  # type: ignore
except Exception:  # pragma: no cover - chromadb not installed
    chromadb = None
    Settings = None  # type: ignore


class SimpleEmbeddingFunction:
    def __call__(self, texts: List[str]) -> List[List[float]]:
        out: List[List[float]] = []
        for text in texts:
            vec = [0.0] * 16
            for token in text.lower().split():
                idx = int.from_bytes(hashlib.sha1(token.encode()).digest(), "big") % 16
                vec[idx] += 1.0
            out.append(vec)
        return out


class ChatMemory:
    def __init__(
        self, db_path: str = "chat_memory.sqlite", persist_directory: Optional[str] = None
    ) -> None:
        self.db_path = db_path
        self.persist_directory = persist_directory
        self.conn = sqlite3.connect(self.db_path)
        self._migrate()
        self._emb = SimpleEmbeddingFunction()
        try:
            if chromadb is None:
                raise ImportError
            settings = Settings(
                anonymized_telemetry=False, persist_directory=self.persist_directory
            )
            self._client = chromadb.Client(settings)
            self._collection = self._client.get_or_create_collection(
                name="messages", embedding_function=self._emb
            )
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._store: List[Tuple[str, List[float], Dict[str, Any], str]] = []

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass

    def __enter__(self) -> ChatMemory:  # pragma: no cover - simple passthrough
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - simple passthrough
        self.close()

    # ------------------------------------------------------------------
    def _migrate(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              session_id TEXT NOT NULL,
              role TEXT NOT NULL,
              content TEXT NOT NULL,
              created_at TEXT NOT NULL
            )
            """
        )
        cur.execute("PRAGMA table_info(messages)")
        cols = [row[1] for row in cur.fetchall()]
        if "session_id" not in cols:
            cur.execute("ALTER TABLE messages ADD COLUMN session_id TEXT")
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, id)"
        )
        self.conn.commit()
        cur.close()

    # ------------------------------------------------------------------
    def add_message(self, session_id: str, role: str, content: str) -> int:
        created_at = datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO messages(session_id, role, content, created_at) VALUES (?,?,?,?)",
            (session_id, role, content, created_at),
        )
        msg_id = cur.lastrowid
        self.conn.commit()
        cur.close()
        if self._use_chroma:
            self._collection.add(ids=[str(msg_id)], documents=[content], metadatas=[{"session_id": session_id}])
        else:
            emb = self._emb([content])[0]
            self._store.append((str(msg_id), emb, {"session_id": session_id}, content))
        return int(msg_id)

    # ------------------------------------------------------------------
    def get_conversation(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        sql = "SELECT role, content, created_at FROM messages WHERE session_id=? ORDER BY id"
        params: List[Any] = [session_id]
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return [{"role": r, "content": c, "created_at": t} for r, c, t in rows]

    # ------------------------------------------------------------------
    def search_by_embedding(self, query: str, session_id: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        if top_k <= 0:
            return []
        if self._use_chroma:
            where = {"session_id": session_id} if session_id else None
            res = self._collection.query(query_texts=[query], n_results=top_k, where=where)
            ids = res["ids"][0] if res and res.get("ids") else []
        else:
            q = self._emb([query])[0]
            cands: List[Tuple[float, str]] = []
            for _id, emb, meta, _doc in self._store:
                if session_id and meta.get("session_id") != session_id:
                    continue
                cands.append((sum(a * b for a, b in zip(q, emb)), _id))
            cands.sort(reverse=True)
            ids = [i for _, i in cands[:top_k]]
        if not ids:
            return []
        placeholders = ",".join(["?"] * len(ids))
        cur = self.conn.cursor()
        cur.execute(
            f"SELECT id, session_id, role, content, created_at FROM messages WHERE id IN ({placeholders})",
            ids,
        )
        rows = cur.fetchall()
        cur.close()
        mapping = {str(r[0]): r for r in rows}
        ordered = [mapping[i] for i in ids if i in mapping]
        return [
            {"id": r[0], "session_id": r[1], "role": r[2], "content": r[3], "created_at": r[4]}
            for r in ordered
        ]

    # ------------------------------------------------------------------
    def get_recent_context(self, session_id: str, limit: int = 5) -> str:
        msgs = self.get_conversation(session_id, limit)
        return "\n".join(f"{m['role']}: {m['content']}" for m in msgs)


__all__ = ["ChatMemory", "SimpleEmbeddingFunction"]
