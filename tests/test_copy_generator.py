import asyncio

import pytest

from app.schemas.form import AdGenerationForm
from app.services.adapters.openai_copy import OpenAICopyGenerator
from app.services.adapters.mock_copy import MockCopyGenerator


def _build_form() -> AdGenerationForm:
    return AdGenerationForm(
        business_category="꽃집",
        business_name="라일락플라워",
        product_name="봄꽃다발",
        product_description="기념일과 집들이에 어울리는 화사한 색감의 꽃다발입니다.",
        offer_details="주말 예약 고객 무료 포장",
        target_customer="동네 주민",
        promotion_goal="신규 고객 유입",
        tone="정중한",
        platform="블로그",
        visual_style="프리미엄",
        cta_focus="문의 유도",
        campaign_type="기간 한정 이벤트",
        desired_action="DM 문의",
        post_timing_preference="AI 추천",
        keywords="당일 제작, 예약 가능",
    )


def test_form_auto_fills_missing_product_description():
    form = AdGenerationForm(
        business_category="카페",
        business_name="오카페",
        product_name="딸기 라떼",
        product_description="",
        offer_details="",
        target_customer="동네 주민",
        promotion_goal="신메뉴 홍보",
        tone="친근한",
        platform="인스타그램",
        visual_style="따뜻한 감성",
        cta_focus="방문 유도",
        campaign_type="신상품/신메뉴",
        desired_action="매장 방문",
        post_timing_preference="AI 추천",
        keywords="",
    )

    assert "딸기 라떼" in form.product_description
    assert "카페" in form.product_description
    assert len(form.product_description) >= 10


@pytest.mark.asyncio
async def test_mock_generator_returns_three_variants():
    generator = MockCopyGenerator()
    form = _build_form()

    result = await generator.generate(form)

    assert len(result.variants) == 3
    assert result.cta
    assert result.provider_used == "mock"
    assert result.strategy_note
    assert result.caption
    assert result.channel_packages.instagram.caption
    assert result.channel_packages.threads.thread_text
    assert result.channel_packages.blog.title
    assert len(result.channel_packages.blog.body_outline) >= 3
    assert result.channel_packages.poster.headline
    assert 0 <= result.quality_report.overall_score <= 100
    assert result.auto_approved is True
    assert len(result.quality_report.improvement_suggestions) >= 2


def test_openai_normalize_payload_fills_missing_channel_fields():
    generator = OpenAICopyGenerator(api_key="test-key", model="gpt-5-mini")
    form = _build_form()

    normalized = generator._normalize_payload(
        {
            "headline": "봄꽃다발 예약 시작",
            "body_copy": "주말 예약 고객에게 무료 포장을 제공합니다.",
            "cta": "DM으로 문의하기",
            "hashtags": ["꽃집", "#봄꽃"],
            "variants": [
                {
                    "label": "짧은형",
                    "headline": "봄꽃다발 예약",
                    "body_copy": "주말 무료 포장 혜택을 확인하세요.",
                }
            ],
        },
        form,
    )

    assert normalized["channel_packages"]["instagram"]["caption"]
    assert normalized["channel_packages"]["threads"]["reply_prompt"]
    assert normalized["channel_packages"]["blog"]["title"]
    assert len(normalized["channel_packages"]["blog"]["body_outline"]) >= 3
    assert normalized["channel_packages"]["poster"]["cta"]
    assert normalized["channel_quality"]["blog_score"] >= 0
    assert len(normalized["quality_report"]["improvement_suggestions"]) >= 2
    assert len(normalized["pre_publish_checklist"]) >= 3


@pytest.mark.asyncio
async def test_openai_generator_times_out_safely():
    class SlowResponses:
        async def create(self, **kwargs):
            await asyncio.sleep(0.05)
            return None

    class SlowClient:
        responses = SlowResponses()

    generator = OpenAICopyGenerator(
        api_key="test-key",
        model="gpt-5-mini",
        timeout_seconds=0.01,
    )
    generator.client = SlowClient()

    with pytest.raises(TimeoutError, match="timed out"):
        await generator.generate(_build_form())
