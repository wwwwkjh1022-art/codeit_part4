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


class MockCopyGenerator:
    def __init__(self, provider_name: str = "mock") -> None:
        self.provider_name = provider_name

    async def generate(self, form_data: AdGenerationForm) -> GenerationResult:
        keyword_text = ", ".join(form_data.keyword_list[:3]) if form_data.keyword_list else "가성비, 신뢰"
        offer_text = form_data.offer_details or "지금 가장 눈에 띄는 시즌 포인트"
        action_text = form_data.desired_action
        cta_text = self._cta_text(form_data)
        primary_hashtag = form_data.product_name.replace(" ", "")
        variants = [
            CopyVariant(
                label="짧은형",
                headline=f"{form_data.product_name}, {offer_text}",
                body_copy=(
                    f"{form_data.business_name}에서 {form_data.target_customer}에게 맞춘 "
                    f"{form_data.product_name}를 준비했습니다. {action_text} 전에 혜택 조건을 살펴보세요."
                ),
            ),
            CopyVariant(
                label="설명형",
                headline=f"{form_data.business_name}의 {form_data.product_name}, 이런 분께 좋아요",
                body_copy=(
                    f"{form_data.product_description[:95]} "
                    f"{keyword_text} 포인트를 찾는 {form_data.target_customer}에게 특히 어울립니다."
                ),
            ),
            CopyVariant(
                label="이벤트형",
                headline=f"{offer_text} 놓치기 전에 확인하세요",
                body_copy=(
                    f"{form_data.business_name}의 {form_data.product_name} 혜택을 "
                    f"{form_data.platform}에서 먼저 살펴보고 {action_text}로 이어가세요."
                ),
            ),
        ]
        hashtags = [
            f"#{form_data.business_name.replace(' ', '')}",
            f"#{primary_hashtag}",
            f"#{form_data.business_category.replace(' ', '')}",
            *[f"#{keyword.replace(' ', '')}" for keyword in form_data.keyword_list[:3]],
        ]
        instagram = InstagramPackage(
            caption=(
                f"{form_data.product_name} | {offer_text}\n"
                f"{form_data.business_name}에서 {form_data.target_customer}에게 안내하는 {form_data.business_category} 메뉴입니다.\n"
                f"{action_text} 전 구성과 혜택 조건을 확인해 주세요.\n"
                f"{' '.join(hashtags)}"
            ),
            hashtags=hashtags,
            alt_text=(
                f"{form_data.visual_style} 분위기에서 {form_data.product_name}와 "
                f"{offer_text} 안내가 보이는 {form_data.business_name} 홍보 이미지"
            ),
            visual_hook=(
                f"첫 컷에 {form_data.product_name}를 크게 보여주고, "
                f"{offer_text}와 {action_text} 메시지를 여백 위에 배치"
            ),
            recommended_post_time=self._recommend_time(form_data),
        )
        threads = ThreadsPackage(
            thread_text=(
                f"{form_data.product_name} 고를 때 은근 고민되는 포인트가 있더라고요. "
                f"{keyword_text}를 보는 분이라면 {form_data.business_name}의 {offer_text}도 참고해보면 좋아요. "
                f"여러분은 {form_data.business_category} 고를 때 맛/분위기/거리 중 뭐를 제일 먼저 보세요?"
            ),
            reply_prompt=f"{form_data.product_name} 선택할 때 가장 중요한 기준은 맛, 분위기, 접근성 중 무엇인가요?",
            short_hook=f"{form_data.product_name} 고를 때 기준",
            recommended_post_time=self._recommend_time(form_data),
        )
        blog = BlogPackage(
            title=f"{form_data.business_name} {form_data.product_name} 이용 전 확인할 정보",
            intro=(
                f"{form_data.business_name}의 {form_data.product_name}는 {form_data.target_customer}가 "
                f"{form_data.promotion_goal} 상황에서 비교해보기 좋은 {form_data.business_category} 상품입니다. "
                f"방문 전 확인할 수 있도록 상품 특징, 추천 대상, {offer_text} 조건, "
                f"{action_text} 방법을 정보 중심으로 정리했습니다."
            ),
            body_outline=[
                f"{form_data.product_name} 기본 구성과 주요 특징",
                f"{form_data.target_customer}에게 추천하는 이유",
                f"{offer_text} 조건과 이용 전 확인할 점",
                f"{action_text} 방법과 문의 전 준비사항",
                f"방문 전 위치, 운영시간, 재고/예약 가능 여부 확인",
            ],
            seo_keywords=[
                form_data.business_name,
                form_data.product_name,
                form_data.business_category,
                *form_data.keyword_list[:3],
            ],
            cta=cta_text,
            meta_description=(
                f"{form_data.business_name}의 {form_data.product_name} 소개와 "
                f"{form_data.offer_details or form_data.promotion_goal} 정보를 확인하세요."
            ),
        )
        poster = PosterPackage(
            headline=f"{form_data.product_name} 혜택",
            subcopy=f"{offer_text} | {form_data.product_description[:42]}",
            cta=cta_text,
            visual_direction=(
                f"{form_data.visual_style} 스타일로 {form_data.product_name}를 주인공처럼 배치하고 "
                f"{offer_text}, {action_text} 메시지는 짧고 선명하게 보여주세요."
            ),
        )
        return GenerationResult(
            headline=variants[0].headline,
            body_copy=variants[0].body_copy,
            cta=cta_text,
            strategy_note=(
                f"{form_data.target_customer}에게 바로 닿도록 {form_data.tone} 톤과 "
                f"{form_data.promotion_goal} 메시지를 중심으로 구성했습니다."
            ),
            image_direction=(
                f"{form_data.visual_style} 무드의 배경에 {form_data.product_name}를 중심 오브제로 두고, "
                f"{offer_text}를 보조 카피로 강조하세요."
            ),
            caption=(
                f"{form_data.business_name}의 {form_data.product_name}를 소개합니다. "
                f"{form_data.product_description[:80]} {offer_text} 조건을 확인하고 "
                f"{action_text}으로 이어가보세요.\n"
                f"{' '.join(hashtags)}"
            ),
            hashtags=hashtags,
            channel_packages=ChannelPackages(
                instagram=instagram,
                threads=threads,
                blog=blog,
                poster=poster,
            ),
            quality_report=QualityReport(
                hook_score=88,
                clarity_score=90,
                cta_score=87,
                channel_fit_score=89,
                overall_score=89,
                improvement_suggestions=[
                    f"{form_data.product_name}의 실제 가격이나 {offer_text} 기간을 추가하면 전환력이 더 높아집니다.",
                    f"{form_data.business_name}의 대표 상품 이미지와 {action_text} 동선을 함께 쓰면 문의 가능성이 올라갑니다.",
                ],
            ),
            channel_quality=ChannelQualityReport(
                instagram_score=88,
                threads_score=86,
                blog_score=90,
                failed_channels=[],
                regeneration_suggestions=[
                    f"Instagram에는 {form_data.product_name} 대표 이미지와 {offer_text}를 첫 컷에 함께 배치하세요.",
                    f"Blog에는 {form_data.business_name} 위치, 운영시간, {action_text} 방법을 추가하면 검색 유입이 좋아집니다.",
                ],
            ),
            generation_attempts=1,
            auto_approved=True,
            pre_publish_checklist=[
                "혜택 기간과 조건이 실제 운영 내용과 일치하는지 확인하세요.",
                "이미지에 상호명과 핵심 상품명이 잘 보이는지 확인하세요.",
                "댓글이나 DM 문의가 왔을 때 응대할 문구를 미리 준비하세요.",
            ],
            variants=variants,
            provider_used=self.provider_name,
        )

    def _recommend_time(self, form_data: AdGenerationForm) -> str:
        if form_data.post_timing_preference != "AI 추천":
            return form_data.post_timing_preference
        if "직장" in form_data.target_customer:
            return "평일 저녁 18:00~20:00"
        if "주말" in form_data.offer_details:
            return "주말 오전 10:00~12:00"
        return "평일 점심 11:30~13:00"

    def _cta_text(self, form_data: AdGenerationForm) -> str:
        cta_by_action = {
            "매장 방문": f"{form_data.business_name} 매장 방문 전 혜택 살펴보기",
            "예약하기": f"{form_data.business_name} 예약 가능 시간 문의하기",
            "DM 문의": f"{form_data.business_name}에 DM으로 문의하기",
            "링크 클릭": "프로필 링크에서 자세히 보기",
            "팔로우/저장": "저장하고 다음 방문 때 다시 보기",
        }
        return cta_by_action.get(form_data.desired_action, f"{form_data.desired_action}로 이어가기")
