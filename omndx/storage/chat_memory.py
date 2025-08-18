import sqlite3
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:  # optional dependency
    import chromadb  # type: ignore
    from chromadb.config import Settings  # type: ignore
    from chromadb.utils import embedding_functions  # type: ignore
except Exception:  # exercised in tests
    chromadb = None  # type: ignore
    class Settings:  # type: ignore
        def __init__(self, **_: Any) -> None: ...
    class _EFBase:  # minimal stand-in
        pass
    class embedding_functions:  # type: ignore
        EmbeddingFunction = _EFBase


class SimpleEmbeddingFunction(embedding_functions.EmbeddingFunction):
    """Deterministic bag-of-words embedding."""

    def __call__(self, texts: List[str]) -> List[List[float]]:
        vectors: List[List[float]] = []
        for text in texts:
            vec = [0.0] * 16
            for token in text.lower().split():
                digest = hashlib.sha1(token.encode()).digest()
                index = int.from_bytes(digest, "big") % len(vec)
                vec[index] += 1.0
            vectors.append(vec)
        return vectors


class ChatMemory:
    """Stores chat messages in SQLite with optional Chroma vector search.

    When ``chromadb`` is unavailable the class still functions but
    ``search_by_embedding`` falls back to a ranked substring match.
    """

    def __init__(self, db_path: str = "chat_memory.sqlite", persist_directory: Optional[str] = None) -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self._migrate()

        self._collection = None
        if chromadb is not None:
            if persist_directory:
                settings = Settings(anonymized_telemetry=False, persist_directory=persist_directory)
            else:
                settings = Settings(anonymized_telemetry=False)
            try:
                client = chromadb.Client(settings)
                self._collection = client.get_or_create_collection(
                    "messages", embedding_function=SimpleEmbeddingFunction()
                )
            except Exception:  # pragma: no cover - defensive
                self._collection = None

    # ------------------------------------------------------------------
    def _migrate(self) -> None:
        """Create tables and migrate old schemas."""
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
        columns = [row[1] for row in cur.fetchall()]
        if "session_id" not in columns:
            cur.execute("ALTER TABLE messages ADD COLUMN session_id TEXT")
            self.conn.commit()
        cur.close()

    # ------------------------------------------------------------------
    def add_message(self, session_id: str, role: str, content: str) -> int:
        """Add a message to the store and return its ID."""
        created_at = datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, created_at),
        )
        msg_id = cur.lastrowid
        self.conn.commit()
        cur.close()
        if self._collection is not None:
            self._collection.add(
                ids=[str(msg_id)],
                documents=[content],
                metadatas=[{"session_id": session_id}],
            )
        return msg_id

    # ------------------------------------------------------------------
    def get_conversation(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return messages for a session ordered by insertion."""
        cur = self.conn.cursor()
        sql = "SELECT role, content, created_at FROM messages WHERE session_id = ? ORDER BY id"
        params: List[Any] = [session_id]
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return [
            {"role": role, "content": content, "created_at": created_at}
            for role, content, created_at in rows
        ]

    @property
    def is_semantic_enabled(self) -> bool:
        """Return ``True`` if Chroma vector search is available."""
        return self._collection is not None

    # ------------------------------------------------------------------
    def search_by_embedding(self, query: str, session_id: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search messages similar to the query."""
        if self._collection is not None:
            where = {"session_id": session_id} if session_id else None
            results = self._collection.query(query_texts=[query], n_results=top_k, where=where)
            ids = results["ids"][0]
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
            index = {str(r[0]): r for r in rows}
            ordered = [index[i] for i in ids if i in index]
            return [
                {
                    "id": r[0],
                    "session_id": r[1],
                    "role": r[2],
                    "content": r[3],
                    "created_at": r[4],
                }
                for r in ordered
            ]

        # ranked substring fallback
        cur = self.conn.cursor()
        sql = "SELECT id, session_id, role, content, created_at FROM messages"
        params: List[Any] = []
        if session_id:
            sql += " WHERE session_id = ?"
            params.append(session_id)
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        q = query.lower()
        scored: List[Tuple[int, int, Tuple[int, str, str, str, str]]] = []
        for r in rows:
            text = r[3].lower()
            if q in text:
                scored.append((-text.count(q), text.index(q), r))
        scored.sort()
        top = [r for _, _, r in scored[:top_k]]
        return [
            {
                "id": r[0],
                "session_id": r[1],
                "role": r[2],
                "content": r[3],
                "created_at": r[4],
            }
            for r in top
        ]


__all__ = ["ChatMemory"]
