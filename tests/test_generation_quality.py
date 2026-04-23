import pytest

from app.services.adapters.mock_copy import MockCopyGenerator
from evaluations.scorer import score_generation
from evaluations.testset import GENERATION_EVAL_CASES


@pytest.mark.asyncio
@pytest.mark.parametrize("case", GENERATION_EVAL_CASES, ids=[case.id for case in GENERATION_EVAL_CASES])
async def test_mock_generation_quality_gate(case):
    generator = MockCopyGenerator()

    result = await generator.generate(case.form)
    score = score_generation(case, result)

    assert score.passed, (
        f"{case.id} failed quality gate: {score.reasons}. "
        f"overall={score.overall_score}, channel={score.channel_score}, "
        f"keyword={score.keyword_score}, structure={score.structure_score}, "
        f"quality_report={score.quality_report_score}"
    )


@pytest.mark.asyncio
async def test_quality_gate_rejects_generic_ad_copy():
    case = GENERATION_EVAL_CASES[0]
    result = await MockCopyGenerator().generate(case.form)
    degraded = result.model_copy(deep=True)
    degraded.headline = "좋은 상품을 소개합니다"
    degraded.body_copy = "지금 확인해보세요."
    degraded.caption = "좋은 상품입니다. 확인해보세요."
    degraded.channel_packages.instagram.caption = "좋은 상품입니다.\n확인해보세요."
    degraded.channel_packages.instagram.hashtags = ["#홍보"]
    degraded.channel_packages.instagram.visual_hook = "상품 이미지"
    degraded.channel_packages.instagram.alt_text = "상품 이미지"
    degraded.channel_packages.threads.thread_text = "좋은 상품입니다. 많은 관심 부탁드립니다."
    degraded.channel_packages.threads.reply_prompt = "관심 있으신가요"
    degraded.channel_packages.threads.short_hook = "좋은 상품"
    degraded.channel_packages.blog.title = "상품 소개"
    degraded.channel_packages.blog.intro = "좋은 상품을 소개합니다."
    degraded.channel_packages.blog.body_outline = ["소개"]
    degraded.channel_packages.blog.seo_keywords = ["상품"]
    degraded.channel_packages.blog.cta = "확인해보세요"
    degraded.channel_packages.blog.meta_description = "좋은 상품 소개"
    degraded.channel_packages.poster.headline = "좋은 상품"
    degraded.channel_packages.poster.subcopy = "확인해보세요"
    degraded.channel_packages.poster.cta = "확인"

    score = score_generation(case, degraded)

    assert score.passed is False
    assert score.overall_score < case.min_overall_score
    assert score.channel_score < case.min_channel_score


@pytest.mark.asyncio
async def test_quality_gate_rejects_copy_pasted_channel_versions():
    case = GENERATION_EVAL_CASES[0]
    result = await MockCopyGenerator().generate(case.form)
    duplicated = result.model_copy(deep=True)
    same_text = (
        "딸기 라떼 찾고 있었다면 오늘의카페에서 첫 방문 고객 10% 할인으로 만나보세요. "
        "생딸기 시즌메뉴를 저장해두고 매장 방문 전에 조건을 살펴보세요."
    )
    duplicated.channel_packages.instagram.caption = same_text
    duplicated.channel_packages.threads.thread_text = same_text
    duplicated.channel_packages.threads.short_hook = "딸기 라떼 할인"
    duplicated.channel_packages.blog.title = "딸기 라떼 할인"
    duplicated.channel_packages.blog.intro = same_text
    duplicated.channel_packages.blog.body_outline = [same_text, same_text, same_text]

    score = score_generation(case, duplicated)

    assert score.passed is False
    assert score.differentiation_score < 80


@pytest.mark.asyncio
async def test_quality_report_score_rewards_brief_specific_suggestions():
    case = GENERATION_EVAL_CASES[0]
    result = await MockCopyGenerator().generate(case.form)

    score = score_generation(case, result)

    assert score.quality_report_score >= 85
    assert case.form.product_name in " ".join(result.quality_report.improvement_suggestions)
    assert case.form.business_name in " ".join(result.channel_quality.regeneration_suggestions)
