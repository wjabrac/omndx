import importlib
import sys


def test_chat_memory_without_chroma(monkeypatch, tmp_path):
    import omndx.storage.chat_memory as cm
    orig = sys.modules.get("chromadb")
    monkeypatch.setitem(sys.modules, "chromadb", None)
    importlib.reload(cm)
    ChatMemory = cm.ChatMemory
    memory = ChatMemory(db_path=str(tmp_path / "chat.sqlite"))
    assert not memory.is_semantic_enabled
    memory.add_message("s1", "user", "cat cat dog")
    memory.add_message("s1", "user", "dog cat")
    memory.add_message("s1", "user", "cat at start")
    res = memory.search_by_embedding("cat", session_id="s1")
    assert [r["content"] for r in res][:3] == ["cat cat dog", "cat at start", "dog cat"]
    # restore
    if orig is not None:
        monkeypatch.setitem(sys.modules, "chromadb", orig)
    importlib.reload(cm)
