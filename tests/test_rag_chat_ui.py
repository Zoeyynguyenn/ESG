# -*- coding: utf-8 -*-
"""
Tests cho UI functions và stream_response trong rag_chat.py.
Dùng mock để tránh phụ thuộc vào Ollama và terminal thật.
"""
import os
import io
import pytest
from unittest.mock import MagicMock, patch, call


# ── Redirect HISTORY_DIR về tmp_path ─────────────────────────────────────────
@pytest.fixture(autouse=True)
def patch_history_dir(history_dir, monkeypatch):
    import rag_chat
    monkeypatch.setattr(rag_chat, "HISTORY_DIR", history_dir)


# ── Console capture helper ────────────────────────────────────────────────────
@pytest.fixture
def capture_console(monkeypatch):
    """
    Thay thế console trong rag_chat bằng Console ghi vào StringIO.
    Trả về buffer để kiểm tra output.
    """
    from rich.console import Console
    buf = io.StringIO()
    fake_console = Console(file=buf, highlight=False, force_terminal=False, width=120)
    import rag_chat
    monkeypatch.setattr(rag_chat, "console", fake_console)
    return buf


# ════════════════════════════════════════════════════════════════════════════════
# print_banner
# ════════════════════════════════════════════════════════════════════════════════

class TestPrintBanner:

    def test_banner_contains_model(self, capture_console):
        from rag_chat import print_banner
        print_banner("llama3.2:3b", rag_on=True, n_docs=2)
        out = capture_console.getvalue()
        assert "llama3.2:3b" in out

    def test_banner_shows_rag_on(self, capture_console):
        from rag_chat import print_banner
        print_banner("model", rag_on=True, n_docs=0)
        out = capture_console.getvalue()
        assert "ON" in out

    def test_banner_shows_rag_off(self, capture_console):
        from rag_chat import print_banner
        print_banner("model", rag_on=False, n_docs=0)
        out = capture_console.getvalue()
        assert "OFF" in out

    def test_banner_shows_doc_count(self, capture_console):
        from rag_chat import print_banner
        print_banner("model", rag_on=True, n_docs=5)
        out = capture_console.getvalue()
        assert "5" in out


# ════════════════════════════════════════════════════════════════════════════════
# print_help
# ════════════════════════════════════════════════════════════════════════════════

class TestPrintHelp:

    def test_help_contains_all_commands(self, capture_console):
        from rag_chat import print_help
        print_help()
        out = capture_console.getvalue()
        for cmd in ["/ingest", "/docs", "/deldoc", "/rag", "/save", "/load",
                    "/sessions", "/clear", "/history", "/model", "/help", "/exit"]:
            assert cmd in out, f"Thieu lenh {cmd} trong help"

    def test_help_does_not_raise(self, capture_console):
        from rag_chat import print_help
        print_help()  # Không raise là pass


# ════════════════════════════════════════════════════════════════════════════════
# print_history
# ════════════════════════════════════════════════════════════════════════════════

class TestPrintHistory:

    def test_empty_history_shows_notice(self, capture_console):
        from rag_chat import print_history
        print_history([{"role": "system", "content": "sys"}])
        out = capture_console.getvalue()
        assert "Chua co tin nhan" in out

    def test_history_shows_user_messages(self, capture_console):
        from rag_chat import print_history
        history = [
            {"role": "system",    "content": "sys"},
            {"role": "user",      "content": "Xin chao AI"},
            {"role": "assistant", "content": "Xin chao ban"},
        ]
        print_history(history)
        out = capture_console.getvalue()
        assert "Xin chao AI" in out

    def test_history_truncates_long_messages(self, capture_console):
        from rag_chat import print_history
        long_msg = "A" * 200
        history = [{"role": "user", "content": long_msg}]
        print_history(history)
        out = capture_console.getvalue()
        # Output không nên dài hơn 120 ký tự cho snippet
        assert "..." in out or len([l for l in out.split("\n") if "A" * 121 in l]) == 0


# ════════════════════════════════════════════════════════════════════════════════
# print_docs
# ════════════════════════════════════════════════════════════════════════════════

class TestPrintDocs:

    def test_empty_docs_shows_notice(self, capture_console, rag):
        from rag_chat import print_docs
        print_docs(rag)
        out = capture_console.getvalue()
        assert "Chua co tai lieu" in out

    def test_docs_shows_filename(self, capture_console, rag_with_data):
        from rag_chat import print_docs
        print_docs(rag_with_data)
        out = capture_console.getvalue()
        assert "esg_report.txt" in out

    def test_docs_shows_chunk_count(self, capture_console, rag_with_data):
        from rag_chat import print_docs
        print_docs(rag_with_data)
        out = capture_console.getvalue()
        # Phải có số chunks hiển thị
        assert any(c.isdigit() for c in out)


# ════════════════════════════════════════════════════════════════════════════════
# stream_response (mock ollama.chat)
# ════════════════════════════════════════════════════════════════════════════════

def make_fake_stream(*tokens):
    """Tạo generator giả lập ollama stream từ danh sách token."""
    for token in tokens:
        chunk = MagicMock()
        chunk.message.content = token
        yield chunk


class TestStreamResponse:

    def test_returns_full_text(self, capture_console, monkeypatch):
        """stream_response ghép đúng các token thành câu hoàn chỉnh."""
        import rag_chat
        fake_stream = make_fake_stream("Xin ", "chao ", "ban!")
        monkeypatch.setattr(
            rag_chat.ollama, "chat",
            lambda **kw: (c for c in fake_stream)
        )
        result = rag_chat.stream_response("model", [{"role":"user","content":"hi"}], used_rag=False)
        assert result == "Xin chao ban!"

    def test_rag_badge_shown_when_used(self, capture_console, monkeypatch):
        """Khi used_rag=True, output phải chứa [RAG]."""
        import rag_chat
        monkeypatch.setattr(
            rag_chat.ollama, "chat",
            lambda **kw: make_fake_stream("OK")
        )
        rag_chat.stream_response("model", [{"role":"user","content":"q"}], used_rag=True)
        out = capture_console.getvalue()
        assert "RAG" in out

    def test_no_rag_badge_when_not_used(self, capture_console, monkeypatch):
        """Khi used_rag=False, không có [RAG] badge."""
        import rag_chat
        monkeypatch.setattr(
            rag_chat.ollama, "chat",
            lambda **kw: make_fake_stream("OK")
        )
        rag_chat.stream_response("model", [{"role":"user","content":"q"}], used_rag=False)
        out = capture_console.getvalue()
        assert "RAG" not in out

    def test_returns_empty_on_stop_iteration(self, capture_console, monkeypatch):
        """Stream rỗng (StopIteration) → trả về string rỗng."""
        import rag_chat
        monkeypatch.setattr(
            rag_chat.ollama, "chat",
            lambda **kw: make_fake_stream()   # generator rỗng
        )
        result = rag_chat.stream_response("model", [{"role":"user","content":"q"}], used_rag=False)
        assert result == ""

    def test_returns_empty_on_ollama_error(self, capture_console, monkeypatch):
        """Khi ollama raise ResponseError → trả về string rỗng."""
        import rag_chat
        def raise_error(**kw):
            raise rag_chat.ollama.ResponseError("model not found")
        monkeypatch.setattr(rag_chat.ollama, "chat", raise_error)
        result = rag_chat.stream_response("model", [], used_rag=False)
        assert result == ""

    def test_output_contains_response_text(self, capture_console, monkeypatch):
        """Token từ stream phải xuất hiện trong console output."""
        import rag_chat
        monkeypatch.setattr(
            rag_chat.ollama, "chat",
            lambda **kw: make_fake_stream("Hello", " World")
        )
        rag_chat.stream_response("model", [{"role":"user","content":"hi"}], used_rag=False)
        out = capture_console.getvalue()
        assert "Hello" in out
        assert "World" in out

    def test_multiple_chunks_concatenated(self, capture_console, monkeypatch):
        """Nhiều chunks phải được nối đúng thứ tự."""
        import rag_chat
        tokens = ["ESG ", "la ", "viet ", "tat ", "cua ", "3 ", "tu."]
        monkeypatch.setattr(
            rag_chat.ollama, "chat",
            lambda **kw: make_fake_stream(*tokens)
        )
        result = rag_chat.stream_response("model", [{"role":"user","content":"?"}], used_rag=False)
        assert result == "ESG la viet tat cua 3 tu."

    def test_returns_empty_on_generic_exception(self, capture_console, monkeypatch):
        """Exception không phải ResponseError khi gọi ollama → trả về rỗng."""
        import rag_chat
        def raise_generic(**kw):
            raise ConnectionError("timeout")
        monkeypatch.setattr(rag_chat.ollama, "chat", raise_generic)
        result = rag_chat.stream_response("model", [], used_rag=False)
        assert result == ""

    def test_stream_exception_mid_stream_partial_result(self, capture_console, monkeypatch):
        """Exception xảy ra giữa stream → trả về phần đã nhận được."""
        import rag_chat

        def bad_stream(**kw):
            chunk = MagicMock()
            chunk.message.content = "Partial "
            yield chunk
            raise RuntimeError("network dropped")

        monkeypatch.setattr(rag_chat.ollama, "chat", bad_stream)
        result = rag_chat.stream_response("model", [{"role":"user","content":"q"}], used_rag=False)
        assert "Partial" in result


# ════════════════════════════════════════════════════════════════════════════════
# print_sessions
# ════════════════════════════════════════════════════════════════════════════════

class TestPrintSessions:

    def test_empty_shows_notice(self, capture_console, history_dir):
        from rag_chat import print_sessions
        sessions = print_sessions()
        out = capture_console.getvalue()
        assert "Chua co session" in out
        assert sessions == []

    def test_shows_saved_sessions(self, capture_console, history_dir):
        from rag_chat import save_session, print_sessions
        save_session([{"role": "user", "content": "hi"}], "llama3.2:3b", name="demo_ui")
        sessions = print_sessions()
        out = capture_console.getvalue()
        assert "demo_ui" in out
        assert len(sessions) >= 1

    def test_returns_list(self, capture_console, history_dir):
        from rag_chat import save_session, print_sessions
        save_session([{"role": "user", "content": "q"}], "model", name="ret_test")
        result = print_sessions()
        assert isinstance(result, list)
        assert result[0]["name"] == "ret_test"


# ════════════════════════════════════════════════════════════════════════════════
# main() — test từng command path qua mock Prompt.ask
# ════════════════════════════════════════════════════════════════════════════════

class TestMainCommands:
    """
    Test main() bằng cách inject sequence lệnh qua mock Prompt.ask.
    Dùng side_effect=[] để simulate từng lần user gõ.
    """

    def _run_main_with_inputs(self, inputs, monkeypatch, tmp_path):
        """
        Chạy main() với danh sách input giả.
        inputs: list[str] — mỗi phần tử là một lần Prompt.ask trả về.
        """
        import rag_chat
        import rag_engine as re_mod

        # Isolate ChromaDB
        monkeypatch.setattr(re_mod, "DB_DIR", str(tmp_path / "vdb"))

        # Mock Prompt.ask để inject inputs tuần tự
        call_iter = iter(inputs)
        monkeypatch.setattr(
            rag_chat, "Prompt",
            MagicMock(ask=MagicMock(side_effect=lambda *a, **kw: next(call_iter)))
        )
        # Confirm.ask luôn trả về False (không lưu khi thoát)
        monkeypatch.setattr(rag_chat, "Confirm", MagicMock(ask=MagicMock(return_value=False)))

        rag_chat.main()

    def test_main_exit_immediately(self, capture_console, monkeypatch, tmp_path):
        """/exit ngay → main() thoát sạch."""
        self._run_main_with_inputs(["/exit"], monkeypatch, tmp_path)
        assert True  # không raise là pass

    def test_main_help_then_exit(self, capture_console, monkeypatch, tmp_path):
        """/help in bảng lệnh, /exit thoát."""
        self._run_main_with_inputs(["/help", "/exit"], monkeypatch, tmp_path)
        out = capture_console.getvalue()
        assert "/ingest" in out

    def test_main_clear_then_exit(self, capture_console, monkeypatch, tmp_path):
        """/clear reset history."""
        self._run_main_with_inputs(["/clear", "/exit"], monkeypatch, tmp_path)
        out = capture_console.getvalue()
        assert "Da xoa lich su" in out

    def test_main_rag_toggle(self, capture_console, monkeypatch, tmp_path):
        """/rag off rồi /rag on → cả hai message xuất hiện."""
        self._run_main_with_inputs(["/rag off", "/rag on", "/exit"], monkeypatch, tmp_path)
        out = capture_console.getvalue()
        assert "TAT" in out
        assert "BAT" in out

    def test_main_rag_status(self, capture_console, monkeypatch, tmp_path):
        """/rag (không có on/off) → hiện trạng thái hiện tại."""
        self._run_main_with_inputs(["/rag", "/exit"], monkeypatch, tmp_path)
        out = capture_console.getvalue()
        assert "ON" in out or "OFF" in out

    def test_main_unknown_command(self, capture_console, monkeypatch, tmp_path):
        """Lệnh không hợp lệ → báo lỗi, không crash."""
        self._run_main_with_inputs(["/foobar", "/exit"], monkeypatch, tmp_path)
        out = capture_console.getvalue()
        assert "khong hop le" in out.lower() or "foobar" in out

    def test_main_empty_input_ignored(self, capture_console, monkeypatch, tmp_path):
        """Input rỗng bị bỏ qua, không crash."""
        self._run_main_with_inputs(["", "   ", "/exit"], monkeypatch, tmp_path)
        assert True

    def test_main_save_without_content(self, capture_console, monkeypatch, tmp_path):
        """/save khi chưa có tin nhắn → thông báo chưa có nội dung."""
        self._run_main_with_inputs(["/save", "/exit"], monkeypatch, tmp_path)
        out = capture_console.getvalue()
        assert "Chua co noi dung" in out

    def test_main_sessions_empty(self, capture_console, monkeypatch, tmp_path):
        """/sessions khi chưa có file → hiện thông báo."""
        self._run_main_with_inputs(["/sessions", "/exit"], monkeypatch, tmp_path)
        out = capture_console.getvalue()
        assert "Chua co session" in out

    def test_main_ingest_missing_arg(self, capture_console, monkeypatch, tmp_path):
        """/ingest không có đường dẫn → thông báo thiếu arg."""
        self._run_main_with_inputs(["/ingest", "/exit"], monkeypatch, tmp_path)
        out = capture_console.getvalue()
        assert "Thieu duong dan" in out

    def test_main_ingest_nonexistent_file(self, capture_console, monkeypatch, tmp_path):
        """/ingest file không tồn tại → thông báo lỗi."""
        self._run_main_with_inputs(["/ingest /khong/co/file.pdf", "/exit"], monkeypatch, tmp_path)
        out = capture_console.getvalue()
        assert "Khong tim thay" in out

    def test_main_deldoc_missing_arg(self, capture_console, monkeypatch, tmp_path):
        """/deldoc không có tên → thông báo thiếu arg."""
        self._run_main_with_inputs(["/deldoc", "/exit"], monkeypatch, tmp_path)
        out = capture_console.getvalue()
        assert "Thieu ten file" in out

    def test_main_history_empty(self, capture_console, monkeypatch, tmp_path):
        """/history khi chưa chat → hiện 'Chua co tin nhan'."""
        self._run_main_with_inputs(["/history", "/exit"], monkeypatch, tmp_path)
        out = capture_console.getvalue()
        assert "Chua co tin nhan" in out

    def test_main_chat_calls_ollama(self, capture_console, monkeypatch, tmp_path):
        """Gõ câu hỏi → ollama.chat được gọi."""
        import rag_chat
        import rag_engine as re_mod
        monkeypatch.setattr(re_mod, "DB_DIR", str(tmp_path / "vdb"))

        call_count = {"n": 0}

        def fake_chat(**kw):
            call_count["n"] += 1
            return make_fake_stream("Xin chao!")

        monkeypatch.setattr(rag_chat.ollama, "chat", fake_chat)
        monkeypatch.setattr(rag_chat, "Confirm", MagicMock(ask=MagicMock(return_value=False)))

        inputs = iter(["ESG la gi?", "/exit"])
        monkeypatch.setattr(rag_chat, "Prompt",
            MagicMock(ask=MagicMock(side_effect=lambda *a, **kw: next(inputs))))

        rag_chat.main()
        assert call_count["n"] >= 1

    # ── Các nhánh chưa cover ─────────────────────────────────────────────────

    def test_main_keyboard_interrupt_exits(self, capture_console, monkeypatch, tmp_path):
        """Ctrl+C (KeyboardInterrupt) → thoát như /exit."""
        import rag_chat
        import rag_engine as re_mod
        monkeypatch.setattr(re_mod, "DB_DIR", str(tmp_path / "vdb"))
        monkeypatch.setattr(rag_chat, "Confirm", MagicMock(ask=MagicMock(return_value=False)))
        # Lần đầu raise KeyboardInterrupt, simulate Ctrl+C
        monkeypatch.setattr(rag_chat, "Prompt",
            MagicMock(ask=MagicMock(side_effect=KeyboardInterrupt)))
        rag_chat.main()   # không raise = pass
        out = capture_console.getvalue()
        assert "Tam biet" in out

    def test_main_exit_with_autosave_yes(self, capture_console, monkeypatch, tmp_path):
        """Chat rồi /exit + chọn Yes lưu → file JSON được tạo."""
        import rag_chat
        import rag_engine as re_mod
        monkeypatch.setattr(re_mod, "DB_DIR", str(tmp_path / "vdb"))
        monkeypatch.setattr(rag_chat, "HISTORY_DIR", str(tmp_path / "hist"))
        (tmp_path / "hist").mkdir()

        monkeypatch.setattr(rag_chat.ollama, "chat",
                            lambda **kw: make_fake_stream("OK reply"))
        # Confirm = True (muốn lưu khi thoát)
        monkeypatch.setattr(rag_chat, "Confirm", MagicMock(ask=MagicMock(return_value=True)))

        inputs = iter(["Xin chao", "/exit"])
        monkeypatch.setattr(rag_chat, "Prompt",
            MagicMock(ask=MagicMock(side_effect=lambda *a, **kw: next(inputs))))

        rag_chat.main()
        # Phải có ít nhất 1 file JSON được tạo
        import glob
        saved = glob.glob(str(tmp_path / "hist" / "*.json"))
        assert len(saved) >= 1

    def test_main_save_with_content(self, capture_console, monkeypatch, tmp_path):
        """/save sau khi đã chat → lưu thành công."""
        import rag_chat
        import rag_engine as re_mod
        monkeypatch.setattr(re_mod, "DB_DIR", str(tmp_path / "vdb"))
        monkeypatch.setattr(rag_chat.ollama, "chat",
                            lambda **kw: make_fake_stream("reply"))
        monkeypatch.setattr(rag_chat, "Confirm", MagicMock(ask=MagicMock(return_value=False)))
        inputs = iter(["Hello AI", "/save mysession", "/exit"])
        monkeypatch.setattr(rag_chat, "Prompt",
            MagicMock(ask=MagicMock(side_effect=lambda *a, **kw: next(inputs))))
        rag_chat.main()
        out = capture_console.getvalue()
        assert "Da luu" in out

    def test_main_docs_command(self, capture_console, monkeypatch, tmp_path):
        """/docs trong main() → gọi print_docs."""
        self._run_main_with_inputs(["/docs", "/exit"], monkeypatch, tmp_path)
        out = capture_console.getvalue()
        # Có docs hoặc không, đều phải in ra gì đó
        assert "Chua co tai lieu" in out or "File" in out

    def test_main_deldoc_found(self, capture_console, monkeypatch, tmp_path, sample_txt):
        """/deldoc source tồn tại → xóa và hiện banner."""
        import rag_chat
        import rag_engine as re_mod
        monkeypatch.setattr(re_mod, "DB_DIR", str(tmp_path / "vdb"))
        monkeypatch.setattr(rag_chat, "Confirm", MagicMock(ask=MagicMock(return_value=False)))

        # Pre-ingest sample_txt trước khi chạy main
        engine = re_mod.RagEngine()
        engine.ingest(sample_txt)
        src_name = os.path.basename(sample_txt)

        inputs = iter([f"/deldoc {src_name}", "/exit"])
        monkeypatch.setattr(rag_chat, "Prompt",
            MagicMock(ask=MagicMock(side_effect=lambda *a, **kw: next(inputs))))
        rag_chat.main()
        out = capture_console.getvalue()
        assert "Da xoa" in out or src_name in out

    def test_main_deldoc_not_found(self, capture_console, monkeypatch, tmp_path):
        """/deldoc source không tồn tại → thông báo không tìm thấy."""
        self._run_main_with_inputs(["/deldoc khong_ton_tai.pdf", "/exit"],
                                   monkeypatch, tmp_path)
        out = capture_console.getvalue()
        assert "Khong tim thay" in out

    def test_main_load_valid_session(self, capture_console, monkeypatch, tmp_path):
        """/load + chọn số hợp lệ → tải session thành công."""
        import rag_chat
        import rag_engine as re_mod
        monkeypatch.setattr(re_mod, "DB_DIR", str(tmp_path / "vdb"))
        monkeypatch.setattr(rag_chat, "HISTORY_DIR", str(tmp_path / "hist"))
        (tmp_path / "hist").mkdir()

        # Tạo sẵn session để load
        rag_chat.save_session(
            [{"role": "system", "content": "sys"},
             {"role": "user", "content": "old question"}],
            "llama3.2:3b", name="old_session"
        )

        monkeypatch.setattr(rag_chat, "Confirm", MagicMock(ask=MagicMock(return_value=False)))
        # Prompt.ask: lần 1 = "/load", lần 2 = chọn session "1", lần 3 = /exit
        call_n = {"i": 0}
        answers = ["/load", "1", "/exit"]
        def side_effect(*a, **kw):
            v = answers[call_n["i"]]
            call_n["i"] = min(call_n["i"] + 1, len(answers) - 1)
            return v
        monkeypatch.setattr(rag_chat, "Prompt",
            MagicMock(ask=MagicMock(side_effect=side_effect)))

        rag_chat.main()
        out = capture_console.getvalue()
        assert "old_session" in out or "Tai thanh cong" in out

    def test_main_load_cancel(self, capture_console, monkeypatch, tmp_path):
        """/load + nhấn Enter (hủy) → không crash."""
        import rag_chat
        import rag_engine as re_mod
        monkeypatch.setattr(re_mod, "DB_DIR", str(tmp_path / "vdb"))
        monkeypatch.setattr(rag_chat, "HISTORY_DIR", str(tmp_path / "hist"))
        (tmp_path / "hist").mkdir()
        rag_chat.save_session(
            [{"role": "user", "content": "q"}], "model", name="sess_cancel"
        )
        monkeypatch.setattr(rag_chat, "Confirm", MagicMock(ask=MagicMock(return_value=False)))
        call_n = {"i": 0}
        answers = ["/load", "", "/exit"]  # /load → "" hủy chọn → /exit
        def side_effect(*a, **kw):
            v = answers[call_n["i"]]
            call_n["i"] = min(call_n["i"] + 1, len(answers) - 1)
            return v
        monkeypatch.setattr(rag_chat, "Prompt",
            MagicMock(ask=MagicMock(side_effect=side_effect)))
        rag_chat.main()
        out = capture_console.getvalue()
        assert "Huy" in out

    def test_main_model_command(self, capture_console, monkeypatch, tmp_path):
        """/model → gọi pick_model và in banner mới."""
        import rag_chat
        import rag_engine as re_mod
        monkeypatch.setattr(re_mod, "DB_DIR", str(tmp_path / "vdb"))
        monkeypatch.setattr(rag_chat, "Confirm", MagicMock(ask=MagicMock(return_value=False)))

        fake_model = MagicMock()
        fake_model.model = "mistral:7b"
        fake_model.size  = 4_000_000_000
        monkeypatch.setattr(rag_chat.ollama, "list",
                            lambda: MagicMock(models=[fake_model]))

        # /model → pick_model hỏi chọn số → /exit
        call_n = {"i": 0}
        answers = ["/model", "1", "/exit"]
        def side_effect(*a, **kw):
            v = answers[call_n["i"]]
            call_n["i"] = min(call_n["i"] + 1, len(answers) - 1)
            return v
        monkeypatch.setattr(rag_chat, "Prompt",
            MagicMock(ask=MagicMock(side_effect=side_effect)))

        rag_chat.main()
        out = capture_console.getvalue()
        assert "mistral:7b" in out

    def test_main_chat_with_rag_shows_badge(self, capture_console, monkeypatch,
                                             tmp_path, sample_txt):
        """Chat khi RAG on + có docs liên quan → in thông báo RAG inject."""
        import rag_chat
        import rag_engine as re_mod
        monkeypatch.setattr(re_mod, "DB_DIR", str(tmp_path / "vdb"))

        # Pre-ingest trước khi main chạy
        engine = re_mod.RagEngine()
        engine.ingest(sample_txt)

        monkeypatch.setattr(rag_chat.ollama, "chat",
                            lambda **kw: make_fake_stream("Phat thai 12500 tan."))
        monkeypatch.setattr(rag_chat, "Confirm", MagicMock(ask=MagicMock(return_value=False)))

        inputs = iter(["phat thai CO2 nam 2024", "/exit"])
        monkeypatch.setattr(rag_chat, "Prompt",
            MagicMock(ask=MagicMock(side_effect=lambda *a, **kw: next(inputs))))

        rag_chat.main()
        out = capture_console.getvalue()
        # Dòng 449: RAG inject message hoặc badge trong stream
        assert "RAG" in out or "inject" in out or "tai lieu" in out.lower()


# ════════════════════════════════════════════════════════════════════════════════
# _setup_utf8 — test an toàn: mock io.TextIOWrapper để không phá pytest stdout
# ════════════════════════════════════════════════════════════════════════════════

class TestSetupUtf8:

    def test_setup_utf8_sets_env(self, monkeypatch):
        """_setup_utf8 phải set PYTHONIOENCODING."""
        monkeypatch.delenv("PYTHONIOENCODING", raising=False)
        # Mock TextIOWrapper để không thật sự thay sys.stdout
        monkeypatch.setattr("rag_chat.io.TextIOWrapper", lambda buf, **kw: buf)
        import rag_chat
        rag_chat._setup_utf8()
        assert os.environ.get("PYTHONIOENCODING") == "utf-8"

    def test_setup_utf8_does_not_raise(self, monkeypatch):
        """_setup_utf8 không được raise exception."""
        monkeypatch.setattr("rag_chat.io.TextIOWrapper", lambda buf, **kw: buf)
        import rag_chat
        rag_chat._setup_utf8()  # không raise = pass


# ════════════════════════════════════════════════════════════════════════════════
# pick_model
# ════════════════════════════════════════════════════════════════════════════════

class TestPickModel:

    def _make_model(self, name, size_bytes=2_000_000_000):
        m = MagicMock()
        m.model = name
        m.size  = size_bytes
        return m

    def test_pick_valid_choice(self, capture_console, monkeypatch):
        """Chọn số hợp lệ → trả về model tương ứng."""
        import rag_chat
        models = [self._make_model("llama3.2:3b"), self._make_model("mistral:7b")]
        monkeypatch.setattr(rag_chat.ollama, "list", lambda: MagicMock(models=models))
        monkeypatch.setattr(rag_chat, "Prompt", MagicMock(
            ask=MagicMock(return_value="2")
        ))
        result = rag_chat.pick_model("llama3.2:3b")
        assert result == "mistral:7b"

    def test_pick_empty_choice_keeps_current(self, capture_console, monkeypatch):
        """Nhấn Enter (choice rỗng) → giữ nguyên model hiện tại."""
        import rag_chat
        models = [self._make_model("llama3.2:3b")]
        monkeypatch.setattr(rag_chat.ollama, "list", lambda: MagicMock(models=models))
        monkeypatch.setattr(rag_chat, "Prompt", MagicMock(
            ask=MagicMock(return_value="")
        ))
        result = rag_chat.pick_model("llama3.2:3b")
        assert result == "llama3.2:3b"

    def test_pick_invalid_number_keeps_current(self, capture_console, monkeypatch):
        """Chọn số ngoài range → giữ nguyên."""
        import rag_chat
        models = [self._make_model("llama3.2:3b")]
        monkeypatch.setattr(rag_chat.ollama, "list", lambda: MagicMock(models=models))
        monkeypatch.setattr(rag_chat, "Prompt", MagicMock(
            ask=MagicMock(return_value="99")
        ))
        result = rag_chat.pick_model("llama3.2:3b")
        assert result == "llama3.2:3b"

    def test_pick_ollama_error_keeps_current(self, capture_console, monkeypatch):
        """Ollama không kết nối → giữ nguyên model."""
        import rag_chat
        def raise_conn_error():
            raise Exception("connection refused")
        monkeypatch.setattr(rag_chat.ollama, "list", raise_conn_error)
        result = rag_chat.pick_model("llama3.2:3b")
        assert result == "llama3.2:3b"
