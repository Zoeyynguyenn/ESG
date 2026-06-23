# Commit guide — công việc 2026-06-22 (chạy trên máy thật)

Sandbox không phải git repo (bản giải nén) + không có remote/credentials, nên push phải làm
trên máy có clone gốc. Theo CLAUDE.md: lint + test trước khi commit.

## 0. Kiểm tra trước

```bash
cd <repo-root>        # vd: E:\Documents\rag-pipeline-workflow
git status
python -m pytest tests/unit/test_answerability_classification.py -q   # phải 10 passed
python scripts/run_enterprise_docs_natural_onboarding_gate.py          # regression_gate_passed = true
python scripts/eval_answerability_suite.py                            # synthetic 201, overall ~0.856
python scripts/eval_golden_530.py                                     # golden 530, answer_correct 530/530
make lint && make test   # nếu repo có
```

## 1. Commit code + test (feat)

```bash
git add src/enterprise_docs/crossdoc_case_builder.py \
        src/enterprise_docs/crossdoc_capability_benchmark.py \
        scripts/run_enterprise_docs_natural_onboarding_gate.py \
        scripts/eval_answerability_suite.py \
        scripts/eval_golden_530.py \
        tests/unit/test_answerability_classification.py
git commit -m "feat(enterprise-docs): answerability classification + evals

Classify questions as out_of_scope / no_information / answerable to separate a bad
question from missing documents (corpus_limited) and a capability gap (system_gap).
Adds answerability_probe capability + abstain_safety_rate, surfaced in the onboarding
gate artifact. Adds synthetic eval (201) and real golden eval (530) scripts. Constructed
regression gate unaffected (100%). Adds unit tests (10)."
```

## 2. Commit báo cáo + artifact + tracking (docs)

```bash
git add reports/bao-cao-23-nang-cao-chan-doan-cau-hoi-enterprise-internal-doc-20260622*.md \
        reports/enterprise_docs_answerability_classification_20260622/ \
        reports/enterprise_docs_answerability_eval_200_20260622/ \
        reports/enterprise_docs_golden_eval_530_20260622/ \
        .rag/rag-pipeline-practice/daily_report.md \
        .rag/rag-pipeline-practice/progress.md
git commit -m "docs: báo cáo 23 + golden eval 530 (answer/abstain) — 2026-06-22"
```

## 3. Push

```bash
git push origin <branch>     # vd: git push origin main
```

## Lưu ý

- File PDF (`bao-cao-23-*.pdf`, `*-ko.pdf`) và `*.xlsx`: kiểm `.gitignore`. Repo thường KHÔNG
  commit file nhị phân/derived — chia sẻ trực tiếp thay vì commit, hoặc commit riêng nếu muốn lưu.
- Gate artifact `reports/enterprise_docs_natural_onboarding_gate_*` là generated — không bắt buộc commit.
- `goldns_emni_rag_vs_gold_comparison.xlsx` là dữ liệu nguồn — KHÔNG commit (theo .gitignore data).
```
