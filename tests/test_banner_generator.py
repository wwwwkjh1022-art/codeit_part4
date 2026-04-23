from pathlib import Path

from app.config import Settings
from app.schemas.form import AdGenerationForm
from app.schemas.result import (
    BlogPackage,
    ChannelQualityReport,
    ChannelPackages,
    CopyVariant,
    GenerationResult,
    InstagramPackage,
    PosterPackage,
    QualityReport,
    ThreadsPackage,
)
from app.services.banner_generator import BannerGenerator


def test_banner_generator_creates_preview(tmp_path: Path):
    settings = Settings(
        generated_dir=tmp_path / "generated",
        upload_dir=tmp_path / "generated" / "uploads",
        banner_dir=tmp_path / "generated" / "banners",
        static_dir=tmp_path / "static",
        templates_dir=tmp_path / "templates",
        copy_provider="mock",
    )
    settings.ensure_runtime_directories()
    generator = BannerGenerator(settings)

    form = AdGenerationForm(
        business_category="네일샵",
        business_name="오후네일",
        product_name="봄 젤네일",
        product_description="파스텔 컬러와 진주 포인트가 들어간 시즌 디자인입니다.",
        offer_details="주중 예약 시 오프 할인",
        target_customer="20대 직장인",
        promotion_goal="이벤트 홍보",
        tone="트렌디한",
        platform="인스타그램",
        visual_style="산뜻한 시즌형",
        cta_focus="예약 유도",
        campaign_type="기간 한정 이벤트",
        desired_action="예약하기",
        post_timing_preference="평일 저녁",
        keywords="예약 할인, 봄 디자인",
    )
    result = GenerationResult(
        headline="봄을 닮은 네일 디자인",
        body_copy="지금 예약하면 더 가볍게 봄 기분을 즐길 수 있어요.",
        cta="예약 링크 확인하기",
        strategy_note="예약 전환을 높이기 위해 시즌성과 혜택을 함께 강조했습니다.",
        image_direction="산뜻한 민트와 옐로우 톤으로 봄 무드를 강조하세요.",
        caption="봄 젤네일 예약을 오픈했습니다.\n#오후네일 #봄젤네일 #예약이벤트",
        hashtags=["#오후네일", "#봄젤네일", "#예약이벤트"],
        channel_packages=ChannelPackages(
            instagram=InstagramPackage(
                caption="봄 젤네일 예약을 오픈했습니다.\n#오후네일 #봄젤네일 #예약이벤트",
                hashtags=["#오후네일", "#봄젤네일", "#예약이벤트"],
                alt_text="봄 젤네일 홍보 이미지",
                visual_hook="파스텔 컬러와 진주 포인트",
                recommended_post_time="평일 저녁 18:00~20:00",
            ),
            threads=ThreadsPackage(
                thread_text="봄 젤네일 예약 오픈했어요. 이번 시즌 디자인 어떠세요?",
                reply_prompt="가장 좋아하는 봄 네일 컬러는 무엇인가요?",
                short_hook="봄 네일 예약 오픈",
                recommended_post_time="평일 저녁 18:00~20:00",
            ),
            blog=BlogPackage(
                title="오후네일 봄 젤네일 예약 안내",
                intro="오후네일의 봄 젤네일 디자인과 주중 예약 할인 정보를 소개합니다.",
                body_outline=["봄 젤네일 특징", "예약 할인 안내", "예약 방법"],
                seo_keywords=["오후네일", "봄 젤네일", "예약 할인"],
                cta="예약 링크에서 원하는 시간을 확인하세요.",
                meta_description="오후네일 봄 젤네일 예약 할인과 시즌 디자인을 확인하세요.",
            ),
            poster=PosterPackage(
                headline="봄 젤네일 예약",
                subcopy="주중 예약 시 오프 할인",
                cta="예약 링크 확인",
                visual_direction="산뜻한 민트와 옐로우 톤으로 봄 무드를 강조하세요.",
            ),
        ),
        quality_report=QualityReport(
            hook_score=85,
            clarity_score=88,
            cta_score=82,
            channel_fit_score=84,
            overall_score=85,
            improvement_suggestions=["예약 마감일을 추가하세요.", "대표 디자인 사진을 함께 쓰세요."],
        ),
        channel_quality=ChannelQualityReport(
            instagram_score=86,
            threads_score=84,
            blog_score=88,
            failed_channels=[],
            regeneration_suggestions=["블로그에 예약 방법을 추가하세요.", "인스타 대표 이미지를 준비하세요."],
        ),
        generation_attempts=1,
        auto_approved=True,
        pre_publish_checklist=["혜택 기간 확인", "이미지 확인", "댓글 응대 문구 준비"],
        variants=[
            CopyVariant(
                label="짧은형",
                headline="봄을 닮은 네일 디자인",
                body_copy="지금 예약하면 더 가볍게 봄 기분을 즐길 수 있어요.",
            )
        ],
    )

    output = generator.create_preview(form, result)

    assert output.startswith("/static/generated/banners/")
    output_path = settings.banner_dir / output.split("/")[-1]
    assert output_path.exists()
