# -*- coding: utf-8 -*-
"""
Integration tests — chạy toàn bộ pipeline RAG end-to-end.
Không mock LLM, chỉ test phần retrieve + context building.
Cần Ollama đang chạy để chạy test có marker @pytest.mark.ollama.
"""
import os
import pytest


# ════════════════════════════════════════════════════════════════════════════════
# Pipeline: ingest → query → build_messages
# ════════════════════════════════════════════════════════════════════════════════

class TestRagPipeline:

    def test_full_ingest_query_cycle(self, rag, sample_txt):
        """Ingest → query → context không rỗng."""
        rag.ingest(sample_txt)
        context = rag.query("muc phat thai CO2 nam 2024")
        assert context != ""
        assert "12500" in context or "phat thai" in context.lower()

    def test_multiple_docs_query_returns_best_match(self, rag, tmp_path):
        """Với 2 tài liệu khác chủ đề → query trả về đúng doc liên quan."""
        # Doc 1: về ESG
        esg_doc = tmp_path / "esg.txt"
        esg_doc.write_text(
            "Cong ty XYZ giam 30% phat thai CO2. Dat chung chi ISO 14001.",
            encoding="utf-8"
        )
        # Doc 2: về ẩm thực
        food_doc = tmp_path / "food.txt"
        food_doc.write_text(
            "Pho bo Ha Noi la mon an truyen thong. Bun bo Hue rat ngon.",
            encoding="utf-8"
        )
        rag.ingest(str(esg_doc))
        rag.ingest(str(food_doc))

        # Query về ESG → phải lấy từ esg.txt
        context = rag.query("phat thai CO2 ISO")
        assert "esg.txt" in context or "ISO 14001" in context or "CO2" in context

    def test_delete_then_query_returns_empty(self, rag, sample_txt):
        """Sau khi xóa doc → query không còn tìm thấy."""
        rag.ingest(sample_txt)
        # Có context trước khi xóa
        before = rag.query("phat thai CO2 nam 2024")
        assert before != ""

        # Xóa → query lại
        rag.delete_source(os.path.basename(sample_txt))
        after = rag.query("phat thai CO2 nam 2024")
        assert after == ""

    def test_build_messages_end_to_end(self, rag, sample_txt):
        """build_messages inject đúng context từ tài liệu thật."""
        from rag_chat import build_messages, BASE_SYSTEM
        rag.ingest(sample_txt)

        history  = [{"role": "system", "content": BASE_SYSTEM}]
        question = "phat thai CO2 bao nhieu tan"
        msgs, used = build_messages(history, question, rag, rag_on=True)

        assert used is True
        system_content = msgs[0]["content"]
        assert "TAI LIEU THAM KHAO" in system_content
        # Context chứa số liệu từ doc
        assert "12500" in system_content or "phat thai" in system_content.lower()

    def test_rag_off_ignores_documents(self, rag, sample_txt):
        """Khi RAG tắt, phần context tài liệu không được inject dù đã ingest."""
        from rag_chat import build_messages, BASE_SYSTEM
        rag.ingest(sample_txt)

        history  = [{"role": "system", "content": BASE_SYSTEM}]
        msgs, used = build_messages(history, "phat thai CO2", rag, rag_on=False)

        assert used is False
        # Khi RAG off, không có section === TAI LIEU THAM KHAO === (dấu === là marker inject)
        assert "=== TAI LIEU THAM KHAO ===" not in msgs[0]["content"]
        # System prompt gốc được giữ nguyên
        assert msgs[0]["content"] == BASE_SYSTEM

    def test_ingest_pdf_and_query(self, rag):
        """End-to-end với file PDF thật."""
        pdf_path = os.path.join(os.path.dirname(__file__), "..", "sample_esg_report.pdf")
        if not os.path.exists(pdf_path):
            pytest.skip("sample_esg_report.pdf chua duoc tao")

        rag.ingest(pdf_path)
        context = rag.query("phat thai CO2 12500")
        assert isinstance(context, str)
        # Có thể rỗng nếu PDF extract không tốt, nhưng không raise


# ════════════════════════════════════════════════════════════════════════════════
# Persistence — ChromaDB lưu qua phiên
# ════════════════════════════════════════════════════════════════════════════════

class TestPersistence:

    def test_data_persists_across_engine_instances(self, tmp_path, monkeypatch, sample_txt):
        """Ingest ở instance 1, query ở instance 2 vẫn tìm được."""
        import rag_engine as re_mod
        monkeypatch.setattr(re_mod, "DB_DIR", str(tmp_path / "vector_db"))

        # Instance 1: ingest
        engine1 = re_mod.RagEngine()
        engine1.ingest(sample_txt)
        count1 = engine1.count()
        assert count1 > 0

        # Instance 2: query (cùng DB path)
        engine2 = re_mod.RagEngine()
        assert engine2.count() == count1
        context = engine2.query("phat thai CO2")
        assert context != ""


# ════════════════════════════════════════════════════════════════════════════════
# Ollama integration (cần Ollama chạy, đánh dấu skip nếu không có)
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.ollama
class TestOllamaIntegration:
    """
    Test gọi thật Ollama. Chạy với:
        pytest -m ollama tests/test_integration.py -v
    Bỏ qua nếu Ollama không chạy.
    """

    @pytest.fixture(autouse=True)
    def check_ollama(self):
        """Bỏ qua test nếu Ollama không phản hồi."""
        import ollama
        try:
            ollama.list()
        except Exception:
            pytest.skip("Ollama khong chay hoac khong co model")

    def test_ollama_list_returns_models(self):
        """Ollama list() trả về danh sách model."""
        import ollama
        result = ollama.list()
        assert hasattr(result, "models")

    def test_ollama_chat_basic(self):
        """Chat đơn giản với model."""
        import ollama
        models = ollama.list().models
        if not models:
            pytest.skip("Khong co model nao")
        model = models[0].model
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": "Say 'OK' only."}],
        )
        assert response.message.content.strip() != ""
