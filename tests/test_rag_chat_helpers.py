# -*- coding: utf-8 -*-
"""
Unit tests cho các helper function trong rag_chat.py:
  - save_session / load_session / list_sessions
  - build_messages (RAG context injection)
"""
import os
import json
import datetime
import pytest


# ════════════════════════════════════════════════════════════════════════════════
# Patch HISTORY_DIR để dùng thư mục tạm
# ════════════════════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def patch_history_dir(history_dir, monkeypatch):
    """Redirect HISTORY_DIR về tmp_path cho mọi test trong file này."""
    import rag_chat
    monkeypatch.setattr(rag_chat, "HISTORY_DIR", history_dir)


# ════════════════════════════════════════════════════════════════════════════════
# save_session
# ════════════════════════════════════════════════════════════════════════════════

class TestSaveSession:

    def test_save_creates_json_file(self, history_dir):
        from rag_chat import save_session
        history = [{"role": "user", "content": "Hello"}]
        name    = save_session(history, "llama3.2:3b", name="test_save")
        assert os.path.exists(os.path.join(history_dir, "test_save.json"))

    def test_save_returns_name(self, history_dir):
        from rag_chat import save_session
        name = save_session([{"role": "user", "content": "Hi"}], "llama3.2:3b", name="mysession")
        assert name == "mysession"

    def test_save_auto_name_when_none(self, history_dir):
        from rag_chat import save_session
        name = save_session([{"role": "user", "content": "Hi"}], "llama3.2:3b")
        assert name.startswith("rag_")
        assert os.path.exists(os.path.join(history_dir, f"{name}.json"))

    def test_save_json_structure(self, history_dir):
        from rag_chat import save_session
        history = [
            {"role": "system",    "content": "You are AI"},
            {"role": "user",      "content": "ESG?"},
            {"role": "assistant", "content": "ESG means..."},
        ]
        name = save_session(history, "llama3.2:3b", name="struct_test")
        path = os.path.join(history_dir, "struct_test.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        assert "saved_at"  in data
        assert "model"     in data
        assert "messages"  in data
        assert data["model"]    == "llama3.2:3b"
        assert len(data["messages"]) == 3

    def test_save_preserves_unicode(self, history_dir):
        from rag_chat import save_session
        content = "Phát thải CO2 là 12.500 tấn năm 2024"
        save_session([{"role": "user", "content": content}], "model", name="unicode_test")
        path = os.path.join(history_dir, "unicode_test.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert data["messages"][0]["content"] == content

    def test_save_name_with_spaces_normalized(self, history_dir):
        from rag_chat import save_session, _spath
        name = save_session([{"role": "user", "content": "test"}], "model", name="my session")
        # Tên có space được replace bằng _
        assert os.path.exists(_spath("my session"))


# ════════════════════════════════════════════════════════════════════════════════
# load_session
# ════════════════════════════════════════════════════════════════════════════════

class TestLoadSession:

    def test_load_existing_session(self, history_dir):
        from rag_chat import save_session, load_session
        history = [{"role": "user", "content": "test"}]
        save_session(history, "llama3.2:3b", name="to_load")
        result = load_session("to_load")
        assert result is not None
        loaded_history, loaded_model = result
        assert loaded_model   == "llama3.2:3b"
        assert len(loaded_history) == 1

    def test_load_nonexistent_returns_none(self):
        from rag_chat import load_session
        result = load_session("khong_ton_tai_session")
        assert result is None

    def test_load_preserves_all_messages(self, history_dir):
        from rag_chat import save_session, load_session
        history = [
            {"role": "system",    "content": "System"},
            {"role": "user",      "content": "User msg 1"},
            {"role": "assistant", "content": "AI reply 1"},
            {"role": "user",      "content": "User msg 2"},
        ]
        save_session(history, "model_x", name="full_history")
        loaded_history, model = load_session("full_history")
        assert len(loaded_history) == 4
        assert loaded_history[1]["content"] == "User msg 1"
        assert model == "model_x"

    def test_load_corrupted_file_returns_none(self, history_dir):
        from rag_chat import load_session
        # Tạo file JSON hỏng
        path = os.path.join(history_dir, "broken.json")
        with open(path, "w") as f:
            f.write("{ not valid json >>>")
        result = load_session("broken")
        assert result is None


# ════════════════════════════════════════════════════════════════════════════════
# list_sessions
# ════════════════════════════════════════════════════════════════════════════════

class TestListSessions:

    def test_list_empty_dir(self, history_dir):
        from rag_chat import list_sessions
        sessions = list_sessions()
        assert sessions == []

    def test_list_returns_all_sessions(self, history_dir):
        from rag_chat import save_session, list_sessions
        save_session([{"role": "user", "content": "a"}], "model", name="sess1")
        save_session([{"role": "user", "content": "b"}], "model", name="sess2")
        sessions = list_sessions()
        names = [s["name"] for s in sessions]
        assert "sess1" in names
        assert "sess2" in names

    def test_list_sorted_newest_first(self, history_dir):
        from rag_chat import save_session, list_sessions
        import time
        save_session([{"role": "user", "content": "old"}], "model", name="old_session")
        time.sleep(0.05)
        save_session([{"role": "user", "content": "new"}], "model", name="new_session")
        sessions = list_sessions()
        assert sessions[0]["name"] == "new_session"

    def test_list_session_has_correct_turn_count(self, history_dir):
        from rag_chat import save_session, list_sessions
        history = [
            {"role": "system",    "content": "sys"},
            {"role": "user",      "content": "q1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user",      "content": "q2"},
        ]
        save_session(history, "model", name="count_test")
        sessions = list_sessions()
        sess = next(s for s in sessions if s["name"] == "count_test")
        assert sess["turns"] == 2  # 2 user messages

    def test_list_ignores_non_json_files(self, history_dir):
        from rag_chat import list_sessions
        # Tạo file không phải JSON
        open(os.path.join(history_dir, "notes.txt"), "w").close()
        sessions = list_sessions()
        assert all(s["name"] != "notes" for s in sessions)


# ════════════════════════════════════════════════════════════════════════════════
# build_messages (RAG injection)
# ════════════════════════════════════════════════════════════════════════════════

class TestBuildMessages:

    BASE_HISTORY = [
        {"role": "system", "content": "Base system prompt."},
        {"role": "user",   "content": "Câu hỏi trước"},
        {"role": "assistant", "content": "Trả lời trước"},
    ]

    def test_rag_off_no_context_injection(self, rag):
        """RAG tắt → messages giữ nguyên system prompt gốc."""
        from rag_chat import build_messages
        msgs, used = build_messages(self.BASE_HISTORY, "câu hỏi mới", rag, rag_on=False)
        assert used is False
        # System prompt không bị thay đổi
        assert msgs[0]["content"] == "Base system prompt."
        # Câu hỏi mới được thêm vào cuối
        assert msgs[-1]["role"]    == "user"
        assert msgs[-1]["content"] == "câu hỏi mới"

    def test_rag_on_no_relevant_docs_no_injection(self, rag):
        """RAG bật nhưng DB trống → không inject, used=False."""
        from rag_chat import build_messages
        msgs, used = build_messages(self.BASE_HISTORY, "câu hỏi", rag, rag_on=True)
        assert used is False

    def test_rag_on_with_docs_injects_context(self, rag_with_data):
        """RAG bật + có tài liệu liên quan → inject context, used=True."""
        from rag_chat import build_messages
        msgs, used = build_messages(
            self.BASE_HISTORY,
            "muc phat thai CO2 nam 2024",
            rag_with_data,
            rag_on=True,
        )
        assert used is True
        # System prompt phải chứa TAI LIEU THAM KHAO
        assert "TAI LIEU THAM KHAO" in msgs[0]["content"]

    def test_rag_injection_preserves_chat_history(self, rag_with_data):
        """Sau khi inject RAG, lịch sử chat cũ vẫn còn."""
        from rag_chat import build_messages
        msgs, _ = build_messages(
            self.BASE_HISTORY,
            "phat thai CO2",
            rag_with_data,
            rag_on=True,
        )
        roles = [m["role"] for m in msgs]
        assert "assistant" in roles
        assert msgs[-1]["content"] == "phat thai CO2"

    def test_question_always_appended_last(self, rag):
        """Câu hỏi mới luôn là message cuối cùng."""
        from rag_chat import build_messages
        question = "Câu hỏi test cuối"
        msgs, _ = build_messages(self.BASE_HISTORY, question, rag, rag_on=False)
        assert msgs[-1]["role"]    == "user"
        assert msgs[-1]["content"] == question

    def test_original_history_not_mutated(self, rag):
        """build_messages không được sửa history gốc."""
        from rag_chat import build_messages
        original = [{"role": "system", "content": "sys"},
                    {"role": "user",   "content": "old"}]
        import copy
        before = copy.deepcopy(original)
        build_messages(original, "new question", rag, rag_on=False)
        assert original == before
