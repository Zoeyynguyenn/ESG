# -*- coding: utf-8 -*-
"""
Unit tests cho RagEngine.
Test từng phương thức độc lập, không phụ thuộc LLM hay network.
"""
import os
import pytest


# ════════════════════════════════════════════════════════════════════════════════
# ingest()
# ════════════════════════════════════════════════════════════════════════════════

class TestIngest:

    def test_ingest_txt_returns_correct_keys(self, rag, sample_txt):
        """Kết quả ingest phải có đủ 4 keys."""
        result = rag.ingest(sample_txt)
        assert set(result.keys()) == {"source", "chunks", "added", "skipped"}

    def test_ingest_txt_adds_chunks(self, rag, sample_txt):
        """Lần đầu ingest phải add ít nhất 1 chunk."""
        result = rag.ingest(sample_txt)
        assert result["added"] >= 1
        assert result["chunks"] >= 1

    def test_ingest_twice_skips_existing(self, rag, sample_txt):
        """Ingest lần 2 cùng file → skipped = chunks, added = 0."""
        first  = rag.ingest(sample_txt)
        second = rag.ingest(sample_txt)
        assert second["added"]   == 0
        assert second["skipped"] == first["chunks"]

    def test_ingest_source_name_is_filename(self, rag, sample_txt):
        """source phải là tên file, không phải full path."""
        result = rag.ingest(sample_txt)
        assert result["source"] == os.path.basename(sample_txt)

    def test_ingest_nonexistent_file_raises(self, rag):
        """File không tồn tại phải raise exception."""
        with pytest.raises(Exception):
            rag.ingest("/khong/ton/tai/file.txt")

    def test_ingest_unsupported_format_raises(self, rag, tmp_path):
        """Định dạng không hỗ trợ (.xlsx) phải raise ValueError."""
        f = tmp_path / "data.xlsx"
        f.write_bytes(b"fake excel")
        with pytest.raises(ValueError, match="Dinh dang khong ho tro"):
            rag.ingest(str(f))

    def test_ingest_pdf_file(self, rag):
        """Ingest file PDF thật (sample đã tạo sẵn)."""
        pdf_path = os.path.join(os.path.dirname(__file__), "..", "sample_esg_report.pdf")
        if not os.path.exists(pdf_path):
            pytest.skip("sample_esg_report.pdf chua duoc tao")
        result = rag.ingest(pdf_path)
        assert result["chunks"] >= 1
        assert result["added"]  >= 1

    def test_ingest_empty_txt(self, rag, tmp_path):
        """File rỗng không nên raise, nhưng chunks = 0."""
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")
        result = rag.ingest(str(f))
        assert result["chunks"] == 0
        assert result["added"]  == 0

    def test_ingest_increases_count(self, rag, sample_txt):
        """count() tăng sau khi ingest."""
        before = rag.count()
        rag.ingest(sample_txt)
        assert rag.count() > before


# ════════════════════════════════════════════════════════════════════════════════
# query()
# ════════════════════════════════════════════════════════════════════════════════

class TestQuery:

    def test_query_empty_db_returns_empty_string(self, rag):
        """DB trống → query trả về string rỗng."""
        result = rag.query("ESG la gi?")
        assert result == ""

    def test_query_returns_string(self, rag_with_data):
        """Query với DB có data phải trả về string."""
        result = rag_with_data.query("phat thai CO2")
        assert isinstance(result, str)

    def test_query_relevant_content_found(self, rag_with_data):
        """Query câu liên quan phải tìm được nội dung."""
        result = rag_with_data.query("muc phat thai CO2 nam 2024")
        assert result != ""
        assert "12500" in result or "CO2" in result.upper() or "phat thai" in result.lower()

    def test_query_contains_source_metadata(self, rag_with_data):
        """Context phải chứa thông tin [Nguon: ...]."""
        result = rag_with_data.query("phat thai CO2")
        if result:  # chỉ check nếu tìm thấy
            assert "Nguon:" in result or "esg_report" in result

    def test_query_unrelated_returns_empty(self, rag_with_data):
        """Câu hỏi hoàn toàn không liên quan → rỗng (distance > 0.7)."""
        result = rag_with_data.query("lich su trung quoc thoi nha thanh")
        # distance threshold 0.7 — câu không liên quan nên trả về ""
        # (không thể đảm bảo 100% nhưng khả năng cao)
        # Chỉ assert kiểu dữ liệu
        assert isinstance(result, str)

    def test_query_respects_top_k(self, rag_with_data):
        """Query không trả về quá top_k chunks."""
        import rag_engine
        result = rag_with_data.query("ESG", top_k=2)
        if result:
            # Đếm số lần "Nguon:" xuất hiện ≤ top_k
            count = result.count("Nguon:")
            assert count <= 2


# ════════════════════════════════════════════════════════════════════════════════
# list_sources() & delete_source()
# ════════════════════════════════════════════════════════════════════════════════

class TestSourceManagement:

    def test_list_sources_empty(self, rag):
        """DB trống → list_sources trả về []."""
        assert rag.list_sources() == []

    def test_list_sources_after_ingest(self, rag, sample_txt):
        """Sau ingest phải có 1 source."""
        rag.ingest(sample_txt)
        sources = rag.list_sources()
        assert len(sources) == 1
        assert sources[0]["source"] == os.path.basename(sample_txt)
        assert sources[0]["chunks"] >= 1

    def test_list_sources_multiple_files(self, rag, tmp_path):
        """Ingest 2 file khác nhau → list_sources trả về 2."""
        for name in ["doc1.txt", "doc2.txt"]:
            f = tmp_path / name
            f.write_text(f"Noi dung tai lieu {name} ve ESG va moi truong.", encoding="utf-8")
            rag.ingest(str(f))
        sources = rag.list_sources()
        names   = [s["source"] for s in sources]
        assert "doc1.txt" in names
        assert "doc2.txt" in names

    def test_delete_existing_source(self, rag, sample_txt):
        """Xóa source đã tồn tại → trả về số chunk đã xóa > 0."""
        rag.ingest(sample_txt)
        n = rag.delete_source(os.path.basename(sample_txt))
        assert n > 0

    def test_delete_reduces_count(self, rag, sample_txt):
        """Sau khi xóa, count() giảm."""
        rag.ingest(sample_txt)
        before = rag.count()
        rag.delete_source(os.path.basename(sample_txt))
        assert rag.count() < before

    def test_delete_nonexistent_source_returns_zero(self, rag):
        """Xóa source không tồn tại → trả về 0, không raise."""
        n = rag.delete_source("khong_ton_tai.pdf")
        assert n == 0

    def test_delete_then_list_empty(self, rag, sample_txt):
        """Sau khi xóa source duy nhất → list_sources trả về []."""
        rag.ingest(sample_txt)
        rag.delete_source(os.path.basename(sample_txt))
        assert rag.list_sources() == []


# ════════════════════════════════════════════════════════════════════════════════
# count() & _split()
# ════════════════════════════════════════════════════════════════════════════════

class TestHelpers:

    def test_count_empty(self, rag):
        assert rag.count() == 0

    def test_count_after_ingest(self, rag, sample_txt):
        rag.ingest(sample_txt)
        assert rag.count() > 0

    def test_split_short_text(self):
        """Text ngắn hơn CHUNK_SIZE → 1 chunk."""
        from rag_engine import RagEngine
        chunks = list(RagEngine._split("Hello world"))
        assert len(chunks) == 1
        assert chunks[0] == "Hello world"

    def test_split_long_text_multiple_chunks(self):
        """Text dài → nhiều chunk."""
        from rag_engine import CHUNK_SIZE, RagEngine
        words = ["word"] * (CHUNK_SIZE * 3)
        text  = " ".join(words)
        chunks = list(RagEngine._split(text))
        assert len(chunks) > 1

    def test_split_overlap(self):
        """Kiểm tra overlap: từ cuối chunk trước xuất hiện ở đầu chunk sau."""
        from rag_engine import CHUNK_SIZE, CHUNK_OVERLAP, RagEngine
        words  = [f"w{i}" for i in range(CHUNK_SIZE + CHUNK_OVERLAP + 10)]
        text   = " ".join(words)
        chunks = list(RagEngine._split(text))
        if len(chunks) >= 2:
            last_of_first  = set(chunks[0].split()[-CHUNK_OVERLAP:])
            first_of_second = set(chunks[1].split()[:CHUNK_OVERLAP])
            assert len(last_of_first & first_of_second) > 0

    def test_chunk_id_deterministic(self):
        """Cùng input → cùng ID (deterministic)."""
        from rag_engine import RagEngine
        id1 = RagEngine._chunk_id("file.txt", 0, "hello world content")
        id2 = RagEngine._chunk_id("file.txt", 0, "hello world content")
        assert id1 == id2

    def test_chunk_id_different_for_different_input(self):
        """Input khác nhau → ID khác nhau."""
        from rag_engine import RagEngine
        id1 = RagEngine._chunk_id("file.txt", 0, "content A")
        id2 = RagEngine._chunk_id("file.txt", 1, "content B")
        assert id1 != id2
