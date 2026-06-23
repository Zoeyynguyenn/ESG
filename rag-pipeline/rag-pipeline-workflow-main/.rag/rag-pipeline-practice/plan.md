# Plan: Evidence-based RAG Pipeline Practice

## Goal

Xay dung nang luc thuc hanh Evidence-based RAG Pipeline theo tung version, tu baseline retrieval+answer den extraction co cau truc va workflow gan product. Toan bo tien do, quyet dinh, eval va bao cao duoc luu file-backed de khong phu thuoc vao chat memory.

## Current Version

Version 6: Advanced RAG

## Version Roadmap

| Version | Name | Status | Main Tools | Exit Criteria |
|---|---|---|---|---|
| 1 | Mini RAG Baseline | completed | Python, LangChain, Chroma, sentence-transformers, Ollama | Co pipeline end-to-end va output co answer + evidence source + citation + confidence don gian |
| 2 | Evaluated Evidence RAG | completed | Eval set co dinh, RAGAS hoac rubric thu cong | Co metric retrieval hit rate, citation correctness, groundedness, answer correctness, insufficient-information handling |
| 3 | Improved Evidence Retrieval | completed | MMR, BM25, hybrid retrieval, reranking, metadata filtering | Co bang chung cai thien kha nang tim dung evidence (khong chi semantic similarity) |
| 4 | Structured Extraction RAG | completed | Schema extraction, parser/validator, evidence binding | Co output co cau truc: field, value, evidence_text, source, confidence, status |
| 5 | Workflow / Product-Oriented RAG | completed | Workflow orchestration, logging, gap analysis, report export | Co workflow intake->retrieve->extract->gap->report; artifact v5_runs/<run_id> |
| 6 | Advanced RAG | completed | Python orchestrator, router, verification loop, conflict resolver | Co route/verify/resolve; metric V6 vs V5; trace + verification log |

## Version 1: Mini RAG Baseline

### Muc tieu

Chay RAG co ban end-to-end va hinh thanh tu duy evidence-based answer ngay tu dau.

### Output can co

1. Cau tra loi.
2. Evidence source/chunk.
3. Citation.
4. Confidence don gian (low/medium/high).

### Tieu chi hoan thanh

1. Co implementation hoac experiment artifact.
2. Co evaluation result baseline.
3. Co report summary.
4. Co decision: continue / improve / advance.

## Version 2: Evaluated Evidence RAG

### Muc tieu

Danh gia khong chi answer ma ca kha nang tim dung evidence.

### Metrics can do

1. Retrieval hit rate.
2. Citation correctness.
3. Groundedness.
4. Answer correctness.
5. Insufficient-information handling.

### Tieu chi hoan thanh

1. Co implementation hoac experiment artifact.
2. Co evaluation result theo metric tren.
3. Co report summary.
4. Co decision: continue / improve / advance.

## Version 3: Improved Evidence Retrieval

### Muc tieu

Cai thien retrieval theo huong tim dung bang chung.

### Ky thuat

1. MMR
2. BM25
3. Hybrid retrieval
4. Reranking
5. Metadata filtering

### Tieu chi hoan thanh

1. Co implementation hoac experiment artifact.
2. Co evaluation result so sanh voi Version 2.
3. Co report summary.
4. Co decision: continue / improve / advance.

## Version 4: Structured Extraction RAG

### Muc tieu

Trich xuat du lieu co cau truc tu tai lieu va gan voi evidence.

### Output mau

```json
{
  "field": "has_environment_policy",
  "value": true,
  "evidence_text": "...",
  "source": "...",
  "confidence": "medium",
  "status": "verified"
}
```

### Tieu chi hoan thanh

1. Co implementation hoac experiment artifact.
2. Co evaluation result extraction + evidence quality.
3. Co report summary.
4. Co decision: continue / improve / advance.

## Version 5: Workflow / Product-Oriented RAG

### Muc tieu

Dong goi thanh workflow gan product, khong chi Q&A.

### Workflow can co

1. Intake input.
2. Collect/load documents.
3. Process documents.
4. Retrieve evidence.
5. Extract structured data.
6. Gap analysis.
7. Generate report/export.

### Toi uu van hanh

1. Metadata filtering.
2. Contextual compression.
3. Cache.
4. Logging.
5. Observability.
6. Token/latency optimization.

### Tieu chi hoan thanh

1. Co implementation hoac experiment artifact.
2. Co evaluation result workflow-level.
3. Co report summary.
4. Co decision: continue / improve / advance.

## Version 6: Advanced RAG

### Muc tieu

Thu nghiem huong nang cao khi baseline da co so lieu ro.

### Huong ap dung

1. LangGraph cho workflow nhieu buoc, query routing, fallback, verification loop.
2. GraphRAG/LightRAG cho multi-hop hoac quan he thuc the.
3. Agentic RAG khi can lap ke hoach/goi nhieu tool.

### Tieu chi hoan thanh

1. Co implementation hoac experiment artifact.
2. Co evaluation result so voi workflow hien tai.
3. Co report summary.
4. Co decision: continue / improve / advance.

## Current Next Step

Post-V6 **Hardening** da chay (4 configs + public_only rerun). Roadmap V1–V6 **dong practice**. Tiep theo ngoai roadmap: PDF/table parser cho public buckets, pilot ESG thuc te.

## Blockers

1. Public-only corpus: coverage ~11% — schema field gan synthetic, khong map truc tiep PDF public.
2. Mixed corpus metric cao do synthetic + policy_boost — khong phan anh pilot public.
3. Chua tich hop LangGraph / token observability day du.
