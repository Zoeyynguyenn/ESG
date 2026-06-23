# Chay benchmark qua dem — khong can bam Run tung lenh trong chat

## Vi sao chat Cursor van hoi "Run"?

Agent moi lan goi terminal la **mot lenh rieng**. Mac dinh Cursor hoi phe duyet (bao mat).

**Cach 1 — Chi bam Run 1 lan (khuyen dung):** chay script nay ngoai chat hoac paste vao terminal:

```powershell
cd e:\Documents\rag-pipeline-workflow
.\scripts\run_overnight_model_benchmark.ps1
```

RAGAS (tu dong sau phase 1 neu co `OPENAI_API_KEY` trong `.env`):

```powershell
.\scripts\run_overnight_model_benchmark.ps1
```

Neu phase 1 da chay tu truoc, chi can doi RAGAS:

```powershell
.\scripts\wait_then_ragas.ps1
```

Hoac thu cong sau khi co CSV:

```powershell
python -u src/run_model_candidate_benchmark.py --ragas-only --enable-ragas true --ragas-top-n 3 --ragas-max-questions 10
```

**Cach 2 — Agent tu chay het trong chat:** Cursor Settings → **Agents** → **Terminal** → **Auto-Run Mode** = **Run Everything** (hoac them `python` vao Command Allowlist neu dung Allowlist).

**Cach 3 — May dong / khong can mo Cursor:** Task Scheduler chay `powershell -File scripts\run_overnight_model_benchmark.ps1` luc 23:00.

## OpenAI (tuy chon, chi phase 2)

```powershell
Copy-Item .env.local.example .env
# Sua .env: dien OPENAI_API_KEY=
```

Khong commit file `.env`.

## Log

Output ghi tren terminal; ket qua: `reports/model_candidate_results.csv`, `model_candidate_benchmark_summary.md`.
