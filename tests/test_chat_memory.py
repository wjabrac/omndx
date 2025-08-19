import json, os, sqlite3, subprocess, sys, tempfile, types

from omndx.storage.chat_memory import ChatMemory, SimpleEmbeddingFunction


def test_add_and_search_without_chromadb(monkeypatch):
    monkeypatch.setattr("omndx.storage.chat_memory.chromadb", None, raising=False)
    with tempfile.TemporaryDirectory() as tmp:
        m = ChatMemory(db_path=os.path.join(tmp, "mem.sqlite"))
        mid = m.add_message("s1", "user", "hello world")
        res = m.search_by_embedding("hello", session_id="s1", top_k=3)
        assert res and str(mid) == str(res[0]["id"])
        m.close()


def test_sessions_are_isolated(tmp_path):
    db_path = tmp_path / "mem.sqlite"
    m = ChatMemory(db_path=str(db_path))
    m.add_message("s1", "user", "hello world")
    m.add_message("s2", "user", "other")
    c1 = m.get_conversation("s1")
    c2 = m.get_conversation("s2")
    assert [r["content"] for r in c1] == ["hello world"]
    assert [r["content"] for r in c2] == ["other"]
    m.close()


def test_migration_adds_session_id(tmp_path):
    db_path = tmp_path / "mem.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, content TEXT, created_at TEXT)"
    )
    conn.commit()
    conn.close()
    m = ChatMemory(db_path=str(db_path))
    cur = m.conn.cursor()
    cur.execute("PRAGMA table_info(messages)")
    cols = [row[1] for row in cur.fetchall()]
    assert "session_id" in cols
    m.close()


def test_search_with_chromadb(monkeypatch):
    class DummyCollection:
        def __init__(self) -> None:
            self.data = []

        def add(self, ids, documents, metadatas):
            self.data.extend(zip(ids, documents, metadatas))

        def query(self, query_texts, n_results, where=None):
            ids = [i for i, _, meta in self.data if not where or meta.get("session_id") == where.get("session_id")]
            return {"ids": [ids[:n_results]]}

    class DummyClient:
        def __init__(self, settings) -> None:
            self.coll = DummyCollection()

        def get_or_create_collection(self, name):
            return self.coll

    dummy_config = types.SimpleNamespace(Settings=lambda **k: object())
    dummy_chroma = types.SimpleNamespace(Client=DummyClient, config=dummy_config)
    monkeypatch.setattr("omndx.storage.chat_memory.chromadb", dummy_chroma, raising=False)
    monkeypatch.setattr("omndx.storage.chat_memory.Settings", dummy_config.Settings, raising=False)
    with tempfile.TemporaryDirectory() as tmp:
        m = ChatMemory(db_path=os.path.join(tmp, "mem.sqlite"), persist_directory=tmp)
        mid = m.add_message("s1", "user", "hello world")
        res = m.search_by_embedding("hello", session_id="s1", top_k=3)
        assert res and str(mid) == str(res[0]["id"])
        m.close()


def test_search_topk_zero(monkeypatch):
    monkeypatch.setattr("omndx.storage.chat_memory.chromadb", None, raising=False)
    with tempfile.TemporaryDirectory() as tmp:
        m = ChatMemory(db_path=os.path.join(tmp, "mem.sqlite"))
        m.add_message("s1", "user", "hello world")
        assert m.search_by_embedding("hello", session_id="s1", top_k=0) == []
        m.close()


def test_embedding_stable():
    e1 = SimpleEmbeddingFunction()(["hello world"])[0]
    e2 = SimpleEmbeddingFunction()(["hello world"])[0]
    assert e1 == e2


def _embedding_via_subprocess(text: str):
    code = (
        "from omndx.storage.chat_memory import SimpleEmbeddingFunction; "
        "import json, sys; "
        "vec = SimpleEmbeddingFunction()([sys.argv[1]])[0]; "
        "print(json.dumps(vec))"
    )
    env = {**os.environ, "PYTHONPATH": os.getcwd()}
    out = subprocess.check_output([sys.executable, "-c", code, text], env=env)
    return json.loads(out.decode())


def test_simple_embedding_consistent_across_processes():
    emb1 = _embedding_via_subprocess("reproducible hashing")
    emb2 = _embedding_via_subprocess("reproducible hashing")
    assert emb1 == emb2

