# Execution Plan: Benchmark RAG Stage-wise

## Muc tieu chung

Tim cau hinh tot nhat nhanh va co can cu bang benchmark co kiem soat, khong chay full 36 case ngay.

Nguyen tac:
1. Giu backbone V6.
2. Uu tien retrieval gate truoc.
3. Dung lane de tiet kiem thoi gian.
4. Reuse cache/index toi da.

## Pha A: Stagewise + Dev + Retrieval-only

### Muc tieu
1. Quet nhanh ung vien va loai config yeu.
2. Tao shortlist cho Pha B.

### Lenh can chay
```powershell
python src/run_benchmark.py --mode stagewise --lane dev --benchmark-kind retrieval_only --reuse-index true
```

### Dieu kien pass/fail
Pass:
1. Runner ket thuc khong crash.
2. Co run success trong CSV.
3. Co top config theo lane trong summary.

Fail:
1. Tat ca run fail.
2. CSV khong co metric retrieval/citation hop le.
3. error_reason lap lai do cung mot nguyen nhan he thong.

### Output mong doi
1. `reports/benchmark_results.csv`
2. `reports/benchmark_summary.md`
3. `reports/benchmark_dashboard.html`
4. `reports/notebooklm-brief-latest.md`

### Xu ly khi fail
1. Neu model embedding chua cache local: loai config do, ghi ro fail reason.
2. Neu re-index loi: kiem tra `--reuse-index true` va cache dir.
3. Neu lane dev qua nho dan den metric dao dong: tang `eval_questions` dev lane trong matrix.

### Dau ra can chot sau Pha A
1. Top-2 chunking.
2. Top-2 embedding.
3. Top retrieval mode.
4. Top reranker choice.

## Pha B: Focused + Validation

### Muc tieu
1. Xac nhan shortlist trong dieu kien kho hon.
2. Danh gia trade-off quality vs latency on dinh hon Pha A.

### Lenh can chay
```powershell
python src/run_benchmark.py --mode focused --lane validation --benchmark-kind retrieval_only --reuse-index true
```

Neu can full-pipeline cho shortlist:
```powershell
python src/run_benchmark.py --mode focused --lane validation --benchmark-kind full_pipeline --reuse-index true
```

### RAGAS trong Pha B
1. Neu runtime/API co san: bat RAGAS.
2. Neu khong co: tiep tuc metric noi bo, bat buoc ghi `ragas_status` + ly do.

### Dieu kien pass/fail
Pass:
1. Co top 3 config on dinh (khong chi 1 run dot bien).
2. Metric retrieval/citation tot hon hoac it nhat on dinh so voi Pha A.
3. Latency nam trong nguong chap nhan.

Fail:
1. Ket qua dao dong lon, khong chot duoc shortlist.
2. quality cao nhung latency qua cao cho pilot.

### Output mong doi
1. `reports/benchmark_results.csv` (lane=validation)
2. `reports/benchmark_summary.md`
3. `reports/benchmark_dashboard.html`
4. `reports/notebooklm-brief-latest.md`

### Dau ra can chot sau Pha B
1. Top 2-3 config vao Pha C.
2. 1 config du phong neu top-1 fail o full lane.

## Pha C: Final + Full pipeline + Top-3

### Muc tieu
1. Confirm config cuoi tren lane full.
2. Chot de xuat config pilot.

### Lenh can chay
```powershell
python src/run_benchmark.py --mode final --lane full --top-n 3 --benchmark-kind full_pipeline --reuse-index true
```

### Dieu kien chot config
1. Config top dat composite score cao va on dinh.
2. Citation_correctness, retrieval_hit_rate, verified_rate dat muc chap nhan noi bo.
3. Insufficient/conflict nam trong nguong chap nhan.
4. Latency khong vuot nguong van hanh pilot.

### Output mong doi
1. `reports/benchmark_results.csv`
2. `reports/benchmark_summary.md`
3. `reports/benchmark_dashboard.html`
4. `reports/notebooklm-brief-latest.md`

### Tieu chi dung vong benchmark
1. Co config final de xuat ro rang.
2. Co 1 config backup.
3. Workflow state cap nhat day du.

## RAGAS Strategy

1. Pha A: khong bat buoc RAGAS.
2. Pha B: uu tien bat neu runtime san sang.
3. Pha C: neu co the thi bat de co lop danh gia bo sung.
4. Neu khong co runtime/API:
   - Van benchmark bang metric noi bo.
   - Bat buoc ghi `ragas_status` va `ragas_reason` trong CSV/report.

## NotebookLM Strategy

NotebookLM chi dung de tong hop va trinh bay ket qua, khong thay the benchmark runner.

File dau vao uu tien:
1. `reports/notebooklm-brief-latest.md`
2. `reports/benchmark_summary.md`
3. (Tuy chon) `reports/benchmark_dashboard.html` hoac ban PDF export.
