"""Golden Set v2 pipeline CLI — Silver → Gold (6 steps)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _load_dotenv() -> None:
    for name in (".env.local", ".env"):
        p = ROOT / name
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if v:
                os.environ.setdefault(k, v)


def _paths(cfg: dict) -> dict:
    out = ROOT / cfg["output_root"]
    return {
        "root": out,
        "step1": out / "step1_corpus_units" / "corpus_units.jsonl",
        "step2": out / "step2_silver" / "silver_distilled.jsonl",
        "step3": out / "step3_silver_evolved" / "silver_evolved.jsonl",
        "step4_pass": out / "step4_silver_qc" / "silver_qc_pass.jsonl",
        "step4_reject": out / "step4_silver_qc" / "silver_qc_reject.jsonl",
        "step5_csv": out / "step5_sme_review" / "sme_review.csv",
        "step5_xlsx": out / "step5_sme_review" / "sme_review.xlsx",
        "step6_gold": out / "step6_gold" / "golden_set.jsonl",
        "step6_eval": ROOT / cfg["gold"]["eval_set_out"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Golden Set v2 Silver→Gold pipeline")
    parser.add_argument("--config", default="configs/golden_set_pipeline.yaml")
    parser.add_argument(
        "--step",
        type=int,
        choices=[0, 1, 2, 3, 4, 5, 6],
        required=True,
        help="0=prefilter only; 1..6=pipeline steps",
    )
    parser.add_argument(
        "--prefilter-r2-2",
        action="store_true",
        help="Step 0: use pre-filter R2.2 (does not overwrite R2.1 artifacts)",
    )
    parser.add_argument(
        "--pilot-selector-r2-3",
        action="store_true",
        help="Step 0: run pilot selector R2.3 after R2.2 eligible pool exists",
    )
    parser.add_argument("--limit", type=int, default=0, help="Limit units for step 2 or AI SME (0=all)")
    parser.add_argument("--input-jsonl", default=None, help="Override input JSONL for step 2")
    parser.add_argument("--output-jsonl", default=None, help="Override output JSONL for step 2")
    parser.add_argument(
        "--distill-r2-1",
        action="store_true",
        help="Step 2: use Distillation R2.1 prompt (keep/drop + evidence_span)",
    )
    parser.add_argument(
        "--ai-sme",
        action="store_true",
        help="Step 5: LLM-as-judge auto-fill sme_decision (no human SME)",
    )
    args = parser.parse_args(argv)

    _load_dotenv()
    cfg_path = ROOT / args.config
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    paths = _paths(cfg)
    gen = cfg.get("generation") or {}
    qc = cfg.get("qc") or {}
    ai_sme = cfg.get("ai_sme") or {}

    if args.step == 0:
        step1_dir = paths["root"] / "step1_corpus_units"
        input_path = step1_dir / "corpus_units.jsonl"
        if args.prefilter_r2_2:
            from golden_set.prefilter_corpus_units_r2_2 import run_prefilter_r22, write_report_r22

            summary = run_prefilter_r22(
                input_path=input_path,
                output_dir=step1_dir,
                pilot_path=step1_dir / "pilot_hanssem_15_eligible_r2_2.jsonl",
                pilot_size=15,
                r21_eligible_path=step1_dir / "corpus_units_eligible.jsonl",
                old_pilot_path=step1_dir / "pilot_hanssem_15_eligible.jsonl",
            )
            write_report_r22(summary, ROOT / "reports/golden_set_prefilter_round2_2.md")
            (ROOT / "reports/_prefilter_r2_2_summary.json").write_text(
                __import__("json").dumps(summary, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        else:
            from golden_set.prefilter_corpus_units_r2_1 import run_prefilter, write_report

            summary = run_prefilter(
                input_path=input_path,
                output_dir=step1_dir,
                pilot_path=step1_dir / "pilot_hanssem_15_eligible.jsonl",
                pilot_size=15,
            )
            write_report(summary, ROOT / "reports/golden_set_prefilter_round2_1.md")
        if args.pilot_selector_r2_3:
            from golden_set.pilot_selector_r2_3 import run_selector_r23, write_report_r23

            step1_dir = paths["root"] / "step1_corpus_units"
            sel_summary = run_selector_r23(
                eligible_path=step1_dir / "corpus_units_eligible_r2_2.jsonl",
                conditional_path=step1_dir / "corpus_units_conditional_r2_2.jsonl",
                corpus_path=step1_dir / "corpus_units.jsonl",
                output_path=step1_dir / "pilot_hanssem_15_eligible_r2_3.jsonl",
                old_pilot_path=step1_dir / "pilot_hanssem_15_eligible_r2_2.jsonl",
                distill_summary_path=ROOT / "reports/_distill_pilot_hanssem_round2_2_summary.json",
            )
            write_report_r23(sel_summary, ROOT / "reports/golden_set_selector_round2_3.md")
            (ROOT / "reports/_selector_r2_3_summary.json").write_text(
                __import__("json").dumps(sel_summary, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(sel_summary)
        else:
            print(summary)
        return 0

    if args.step == 1:
        from golden_set.step1_prepare import run_step1

        stats = run_step1(
            dataset_root=ROOT / cfg["dataset_root"],
            output_path=paths["step1"],
            companies=cfg["companies"],
            max_units_per_company=int(gen.get("max_units_per_company", 40)),
        )
        print(stats)
        return 0

    if args.step == 2:
        in_path = Path(args.input_jsonl) if args.input_jsonl else paths["step1"]
        if args.input_jsonl and not in_path.is_absolute():
            in_path = ROOT / in_path
        out_path = Path(args.output_jsonl) if args.output_jsonl else paths["step2"]
        if args.output_jsonl and not out_path.is_absolute():
            out_path = ROOT / out_path

        if args.distill_r2_1:
            from golden_set.step2_distill_r2_1 import run_distill_r2_1

            stats = run_distill_r2_1(
                input_path=in_path,
                output_path=out_path,
                model=str(gen.get("llm_model", "gpt-4o-mini")),
                max_chars=int(gen.get("text_max_chars", 4000)),
                limit=args.limit,
            )
        else:
            from golden_set.step2_distill import run_step2

            stats = run_step2(
                input_path=in_path,
                output_path=out_path,
                model=str(gen.get("llm_model", "gpt-4o-mini")),
                max_chars=int(gen.get("text_max_chars", 1200)),
                limit=args.limit,
            )
        print(stats)
        return 0

    if args.step == 3:
        from golden_set.step3_evolve import run_step3

        stats = run_step3(
            input_path=paths["step2"],
            output_path=paths["step3"],
            model=str(gen.get("llm_model", "gpt-4o-mini")),
            evolve_ratio=float(gen.get("evolve_ratio", 0.25)),
            modes=list(gen.get("evolve_modes") or ["reasoning", "multi_context"]),
        )
        print(stats)
        return 0

    if args.step == 4:
        from golden_set.step4_qc import run_step4

        stats = run_step4(
            input_path=paths["step3"],
            pass_path=paths["step4_pass"],
            reject_path=paths["step4_reject"],
            min_question_chars=int(qc.get("min_question_chars", 12)),
            min_answer_chars=int(qc.get("min_answer_chars", 8)),
            min_context_overlap=float(qc.get("min_context_overlap", 0.15)),
            drop_if_answer_not_in_context=bool(qc.get("drop_if_answer_not_in_context", True)),
        )
        print(stats)
        return 0

    if args.step == 5:
        if args.ai_sme:
            from golden_set.step5_ai_judge import run_step5_ai_judge

            stats = run_step5_ai_judge(
                input_path=paths["step4_pass"],
                csv_path=paths["step5_csv"],
                xlsx_path=paths["step5_xlsx"],
                model=str(ai_sme.get("judge_model") or gen.get("llm_model", "gpt-4o-mini")),
                min_confidence=float(ai_sme.get("min_confidence", 0.75)),
                limit=args.limit,
            )
        else:
            from golden_set.step5_sme import run_step5

            stats = run_step5(
                input_path=paths["step4_pass"],
                csv_path=paths["step5_csv"],
                xlsx_path=paths["step5_xlsx"],
            )
        print(stats)
        return 0

    if args.step == 6:
        from golden_set.step6_promote import run_step6

        if not paths["step5_csv"].exists():
            print("ERROR: sme_review.csv missing — run step 5 and complete SME review first", file=sys.stderr)
            return 1
        stats = run_step6(
            sme_csv_path=paths["step5_csv"],
            gold_jsonl_path=paths["step6_gold"],
            eval_md_path=paths["step6_eval"],
            gold_version=str(cfg.get("version", "2.0.0")),
        )
        print(stats)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
