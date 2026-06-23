# Baseline V1 Guide (Evidence-based)

## Muc tieu

Chay mini RAG end-to-end tren `data/rag_dataset` voi output:

- answer
- evidence source
- citation
- confidence (low/medium/high)
- insufficient: tra ve ro "Khong du du lieu trong context"

## Stack uu tien

LangChain + Chroma + `sentence-transformers/all-MiniLM-L6-v2` + Ollama (`qwen2.5:7b-instruct`).

## Fallback (neu Chroma/Ollama khong san sang)

Lexical retrieval + rule-based answer (`src/evidence_rag.py`), index tai `artifacts/lexical_index.json`.

Ly do thuong gap tren Windows/Python 3.13:

- `chroma-hnswlib` can Microsoft C++ Build Tools
- Ollama chua co trong PATH

## Cai dat

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Tuy chon PDF ingest: `pip install pypdf` (file `ESG-X02_*.pdf` can co trong dataset).

## Chuan bi LLM local (stack chinh)

```powershell
ollama pull qwen2.5:7b-instruct
```

## Ingest

```powershell
python .\src\ingest.py
```

## Hoi don le

```powershell
python .\src\ask.py --question "Muc tieu giam cuong do phat thai Scope 1+2 den 2028 la gi?"
```

## Chay eval 10 cau + bao cao

```powershell
python .\src\run_v1_eval.py
```

Artifact: `reports/v1-baseline-eval-<timestamp>.md`
