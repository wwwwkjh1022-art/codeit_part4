import asyncio
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.adapters.mock_copy import MockCopyGenerator
from evaluations.scorer import EvaluationScore, score_generation
from evaluations.testset import GENERATION_EVAL_CASES, GenerationEvalCase


REPORT_DIR = PROJECT_ROOT / "eval_resources"


async def run_eval() -> list[tuple[GenerationEvalCase, EvaluationScore]]:
    generator = MockCopyGenerator(provider_name="mock-eval")
    rows: list[tuple[GenerationEvalCase, EvaluationScore]] = []
    for case in GENERATION_EVAL_CASES:
        result = await generator.generate(case.form)
        rows.append((case, score_generation(case, result)))
    return rows


def build_report(rows: list[tuple[GenerationEvalCase, EvaluationScore]]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    passed = sum(1 for _, score in rows if score.passed)
    total = len(rows)
    lines = [
        "# Generation Evaluation Report",
        "",
        f"- generated_at: {now}",
        "- provider: mock-eval",
        f"- passed: {passed}/{total}",
        "",
        "## Summary",
        "",
        "| Case | Overall | Channel | Hook | Specificity | Difference | CTA | Compliance | Structure | Quality | Status |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for case, score in rows:
        status = "PASS" if score.passed else "FAIL"
        lines.append(
            f"| {case.id} | {score.overall_score} | {score.channel_score} | "
            f"{score.hook_score} | {score.specificity_score} | "
            f"{score.differentiation_score} | {score.cta_score} | "
            f"{score.compliance_score} | {score.structure_score} | "
            f"{score.quality_report_score} | {status} |"
        )

    lines.extend(["", "## Details", ""])
    for case, score in rows:
        lines.extend(
            [
                f"### {case.id}: {case.title}",
                "",
                f"- min_overall_score: {case.min_overall_score}",
                f"- min_channel_score: {case.min_channel_score}",
                f"- expected_terms: {', '.join(case.expected_terms)}",
                f"- overall_score: {score.overall_score}",
                f"- channel_score: {score.channel_score}",
                f"- keyword_score: {score.keyword_score}",
                f"- hook_score: {score.hook_score}",
                f"- specificity_score: {score.specificity_score}",
                f"- differentiation_score: {score.differentiation_score}",
                f"- cta_score: {score.cta_score}",
                f"- compliance_score: {score.compliance_score}",
                f"- structure_score: {score.structure_score}",
                f"- quality_report_score: {score.quality_report_score}",
                f"- status: {'PASS' if score.passed else 'FAIL'}",
            ]
        )
        if score.reasons:
            lines.append(f"- reasons: {'; '.join(score.reasons)}")
        lines.append("")

    return "\n".join(lines)


async def main() -> None:
    rows = await run_eval()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = build_report(rows)
    output_path = REPORT_DIR / "eval_report_latest.md"
    output_path.write_text(report, encoding="utf-8")
    print(output_path)
    print(report)


if __name__ == "__main__":
    asyncio.run(main())
