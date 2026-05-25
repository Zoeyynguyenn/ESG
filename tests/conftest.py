# -*- coding: utf-8 -*-
"""
Shared fixtures cho toàn bộ test suite.
"""
import os
import sys
import pytest

# Đảm bảo import được từ thư mục gốc D:/ESG/AI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def sample_txt(tmp_path_factory):
    """
    Tạo file TXT mẫu về ESG để dùng trong toàn bộ test session.
    scope=session → chỉ tạo 1 lần, tái dùng cho tất cả test.
    """
    d = tmp_path_factory.mktemp("data")
    p = d / "esg_report.txt"
    p.write_text(
        "BAO CAO ESG 2024 - CONG TY XANH VIET NAM\n\n"
        "Muc phat thai CO2 nam 2024 la 12500 tan, giam 18% so voi 2023.\n"
        "Ti le phu nu trong nhan su la 42 phan tram.\n"
        "Tong so nhan vien la 2134 nguoi.\n"
        "Muc luong trung binh cao hon 35% muc toi thieu vung.\n"
        "Muc tieu 2030: Giam 50% phat thai CO2 so voi nam 2020.\n"
        "Muc tieu 2030: Dat 100% nang luong tai tao trong san xuat.\n"
        "Dau tu 50 ty dong vao du an phat trien cong dong.\n"
        "Mo rong sang 5 nuoc ASEAN voi tieu chuan ESG dong nhat.\n"
        "Chi so hai long khach hang CSAT dat 94 diem nam 2024.\n"
        "He thong ISO 27001 duoc cap chung chi nam 2024.\n",
        encoding="utf-8",
    )
    return str(p)


@pytest.fixture
def rag(tmp_path, monkeypatch):
    """
    RagEngine với ChromaDB isolated trong tmp_path.
    Mỗi test nhận một DB sạch, không ảnh hưởng nhau.
    """
    import rag_engine as re_mod
    monkeypatch.setattr(re_mod, "DB_DIR", str(tmp_path / "vector_db"))
    engine = re_mod.RagEngine()
    return engine


@pytest.fixture
def rag_with_data(rag, sample_txt):
    """RagEngine đã được ingest sẵn sample_txt."""
    rag.ingest(sample_txt)
    return rag


@pytest.fixture
def history_dir(tmp_path):
    """Thư mục tạm để lưu session JSON."""
    d = tmp_path / "chat_history"
    d.mkdir()
    return str(d)
