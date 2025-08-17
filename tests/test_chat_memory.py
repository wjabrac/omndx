import json
import os
import sqlite3
import subprocess
import sys

from omndx.storage.chat_memory import ChatMemory


def test_sessions_are_isolated(tmp_path):
    db_path = tmp_path / "chat.sqlite"
    memory = ChatMemory(db_path=str(db_path))

    memory.add_message("s1", "user", "hello world")
    memory.add_message("s1", "assistant", "hi")
    memory.add_message("s2", "user", "other session message")

    conv1 = memory.get_conversation("s1")
    conv2 = memory.get_conversation("s2")

    assert [m["content"] for m in conv1] == ["hello world", "hi"]
    assert [m["content"] for m in conv2] == ["other session message"]


def test_vector_search_with_session_filter(tmp_path):
    db_path = tmp_path / "chat.sqlite"
    memory = ChatMemory(db_path=str(db_path))

    memory.add_message("s1", "user", "cats are great pets")
    memory.add_message("s1", "assistant", "yes cats are wonderful")
    memory.add_message("s2", "user", "dogs are awesome")

    results = memory.search_by_embedding("cats", session_id="s1")
    assert results and all(r["session_id"] == "s1" for r in results)
    assert any("cats" in r["content"] for r in results)

    other = memory.search_by_embedding("cats", session_id="s2")
    assert other and all(r["session_id"] == "s2" for r in other)
    assert all("cats" not in r["content"] for r in other)


def test_migration_adds_session_column(tmp_path):
    db_path = tmp_path / "chat.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, content TEXT, created_at TEXT)"
    )
    conn.commit()
    conn.close()

    memory = ChatMemory(db_path=str(db_path))
    cur = memory.conn.cursor()
    cur.execute("PRAGMA table_info(messages)")
    cols = [row[1] for row in cur.fetchall()]
    cur.close()
    assert "session_id" in cols


def _embedding_via_subprocess(text: str):
    code = (
        "from omndx.storage.chat_memory import SimpleEmbeddingFunction; "
        "import json, sys; "
        "vec = SimpleEmbeddingFunction()([sys.argv[1]])[0]; "
        "print(json.dumps(vec.tolist() if hasattr(vec, 'tolist') else vec))"
    )
    env = {**os.environ, "PYTHONPATH": os.getcwd()}
    result = subprocess.check_output([sys.executable, "-c", code, text], env=env)
    return json.loads(result.decode())


def test_simple_embedding_consistent_across_processes():
    emb1 = _embedding_via_subprocess("reproducible hashing")
    emb2 = _embedding_via_subprocess("reproducible hashing")
    assert emb1 == emb2
