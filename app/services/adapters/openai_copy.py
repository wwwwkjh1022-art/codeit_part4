import json
from json import JSONDecodeError

from openai import AsyncOpenAI

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
from app.utils.prompts import (
    build_generation_prompt,
    build_generation_response_schema,
    build_system_prompt,
)


class OpenAICopyGenerator:
    def __init__(self, api_key: str | None, model: str, reasoning_effort: str = "medium") -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for the OpenAI provider.")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.reasoning_effort = reasoning_effort

    async def generate(self, form_data: AdGenerationForm) -> GenerationResult:
        response = await self.client.responses.create(
            model=self.model,
            reasoning={"effort": self.reasoning_effort},
            text={
                "format": build_generation_response_schema(),
                "verbosity": "medium",
            },
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": build_system_prompt()}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": build_generation_prompt(form_data)}],
                },
            ],
        )
        payload = self._parse_json(response.output_text)
        normalized = self._normalize_payload(payload, form_data)
        variants = [
            CopyVariant(
                label=item["label"],
                headline=item["headline"],
                body_copy=item["body_copy"],
            )
            for item in normalized["variants"]
        ]
        return GenerationResult(
            headline=normalized["headline"],
            body_copy=normalized["body_copy"],
            cta=normalized["cta"],
            strategy_note=normalized["strategy_note"],
            image_direction=normalized["image_direction"],
            caption=normalized["caption"],
            hashtags=normalized["hashtags"],
            channel_packages=ChannelPackages(
                instagram=InstagramPackage(**normalized["channel_packages"]["instagram"]),
                threads=ThreadsPackage(**normalized["channel_packages"]["threads"]),
                blog=BlogPackage(**normalized["channel_packages"]["blog"]),
                poster=PosterPackage(**normalized["channel_packages"]["poster"]),
            ),
            quality_report=QualityReport(**normalized["quality_report"]),
            channel_quality=ChannelQualityReport(**normalized["channel_quality"]),
            generation_attempts=normalized["generation_attempts"],
            auto_approved=normalized["auto_approved"],
            pre_publish_checklist=normalized["pre_publish_checklist"],
            variants=variants,
            provider_used="openai",
        )

    def _parse_json(self, text: str) -> dict:
        try:
            return json.loads(text)
        except JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1:
                raise
            return json.loads(text[start : end + 1])

    def _normalize_payload(self, payload: dict, form_data: AdGenerationForm) -> dict:
        hashtags = payload.get("hashtags") or [
            f"#{form_data.business_name.replace(' ', '')}",
            f"#{form_data.product_name.replace(' ', '')}",
            f"#{form_data.business_category.replace(' ', '')}",
        ]
        hashtags = self._normalize_hashtags(hashtags, form_data)
        variants = payload.get("variants") or [
            {
                "label": "짧은형",
                "headline": payload.get("headline") or f"{form_data.product_name}를 지금 만나보세요",
                "body_copy": payload.get("body_copy") or form_data.product_description,
            }
        ]
        caption = payload.get("caption") or (
            f"{payload.get('headline', form_data.product_name)}\n"
            f"{payload.get('body_copy', form_data.product_description)}\n"
            f"{' '.join(hashtags)}"
        )
        channel_packages = payload.get("channel_packages") or {}
        instagram = channel_packages.get("instagram") or {}
        threads = channel_packages.get("threads") or {}
        blog = channel_packages.get("blog") or {}
        poster = channel_packages.get("poster") or {}
        quality_report = payload.get("quality_report") or {}
        channel_quality = payload.get("channel_quality") or {}
        instagram_score = self._score(channel_quality.get("instagram_score"), 82)
        threads_score = self._score(channel_quality.get("threads_score"), 80)
        blog_score = self._score(channel_quality.get("blog_score"), 82)
        failed_channels = [
            channel
            for channel, score in {
                "instagram": instagram_score,
                "threads": threads_score,
                "blog": blog_score,
            }.items()
            if score < 80
        ]
        return {
            "headline": payload.get("headline") or variants[0]["headline"],
            "body_copy": payload.get("body_copy") or variants[0]["body_copy"],
            "cta": payload.get("cta") or f"{form_data.cta_focus}해보세요",
            "strategy_note": payload.get("strategy_note")
            or f"{form_data.promotion_goal} 목적에 맞춰 {form_data.tone} 톤으로 구성했습니다.",
            "image_direction": payload.get("image_direction")
            or f"{form_data.visual_style} 스타일로 제품 또는 서비스를 돋보이게 구성하세요.",
            "caption": caption,
            "hashtags": hashtags[:3],
            "channel_packages": {
                "instagram": {
                    "caption": instagram.get("caption") or caption,
                    "hashtags": self._normalize_hashtags(instagram.get("hashtags") or hashtags, form_data),
                    "alt_text": instagram.get("alt_text")
                    or f"{form_data.product_name}를 소개하는 {form_data.visual_style} 홍보 이미지",
                    "visual_hook": instagram.get("visual_hook")
                    or f"{form_data.product_name}와 {form_data.offer_details or form_data.promotion_goal}를 첫눈에 보이게 배치",
                    "recommended_post_time": instagram.get("recommended_post_time")
                    or self._fallback_post_time(form_data),
                },
                "threads": {
                    "thread_text": threads.get("thread_text")
                    or (
                        f"{form_data.product_name} 고를 때 {form_data.target_customer}는 어떤 기준을 먼저 볼까요? "
                        f"{form_data.business_name}에서는 {form_data.offer_details or form_data.promotion_goal}도 함께 안내하고 있어요. "
                        "맛/분위기/거리 중 여러분은 뭐가 제일 중요하세요?"
                    ),
                    "reply_prompt": threads.get("reply_prompt")
                    or f"{form_data.product_name} 선택할 때 맛, 분위기, 접근성 중 무엇을 가장 먼저 보시나요?",
                    "short_hook": threads.get("short_hook") or payload.get("headline") or form_data.product_name,
                    "recommended_post_time": threads.get("recommended_post_time")
                    or self._fallback_post_time(form_data),
                },
                "blog": {
                    "title": blog.get("title")
                    or f"{form_data.business_name} {form_data.product_name} 이용 전 확인할 정보",
                    "intro": blog.get("intro")
                    or (
                        f"{form_data.business_name}의 {form_data.product_name}를 이용하기 전 확인하면 좋은 "
                        f"상품 특징, 추천 대상, {form_data.offer_details or form_data.promotion_goal} 조건, "
                        f"{form_data.desired_action} 방법을 정보 중심으로 정리했습니다."
                    ),
                    "body_outline": self._at_least_three(
                        blog.get("body_outline"),
                        [
                            f"{form_data.product_name} 기본 구성과 핵심 특징",
                            f"{form_data.target_customer}에게 추천하는 이유",
                            f"{form_data.offer_details or form_data.promotion_goal} 조건 안내",
                            f"{form_data.desired_action} 방법과 방문 전 확인사항",
                        ],
                    ),
                    "seo_keywords": self._at_least_three(
                        blog.get("seo_keywords"),
                        [
                            form_data.business_name,
                            form_data.product_name,
                            form_data.business_category,
                        ],
                    ),
                    "cta": blog.get("cta") or f"{form_data.desired_action} 전 운영 정보와 혜택 조건을 확인하세요.",
                    "meta_description": blog.get("meta_description")
                    or f"{form_data.business_name}의 {form_data.product_name}와 관련 혜택을 소개합니다.",
                },
                "poster": {
                    "headline": poster.get("headline") or payload.get("headline") or variants[0]["headline"],
                    "subcopy": poster.get("subcopy")
                    or payload.get("body_copy")
                    or form_data.product_description[:70],
                    "cta": poster.get("cta") or payload.get("cta") or f"{form_data.desired_action}하기",
                    "visual_direction": poster.get("visual_direction")
                    or f"{form_data.visual_style} 스타일로 큰 제목과 명확한 CTA를 배치",
                },
            },
            "quality_report": {
                "hook_score": self._score(quality_report.get("hook_score"), 80),
                "clarity_score": self._score(quality_report.get("clarity_score"), 82),
                "cta_score": self._score(quality_report.get("cta_score"), 78),
                "channel_fit_score": self._score(quality_report.get("channel_fit_score"), 80),
                "overall_score": self._score(quality_report.get("overall_score"), 80),
                "improvement_suggestions": self._at_least_two(
                    quality_report.get("improvement_suggestions"),
                    [
                        "혜택 조건이나 가격 정보를 더 구체화하면 전환력이 올라갑니다.",
                        "실제 이미지와 함께 게시하면 채널 적합도가 더 높아집니다.",
                    ],
                ),
            },
            "channel_quality": {
                "instagram_score": instagram_score,
                "threads_score": threads_score,
                "blog_score": blog_score,
                "failed_channels": channel_quality.get("failed_channels") or failed_channels,
                "regeneration_suggestions": self._at_least_two(
                    channel_quality.get("regeneration_suggestions"),
                    [
                        "채널별 문체 차이를 더 분명하게 조정하세요.",
                        "Blog에는 검색 키워드와 상세 설명을 더 보강하세요.",
                    ],
                ),
            },
            "generation_attempts": self._score(payload.get("generation_attempts"), 1) or 1,
            "auto_approved": bool(payload.get("auto_approved", not failed_channels)),
            "pre_publish_checklist": self._at_least_three(
                payload.get("pre_publish_checklist"),
                [
                    "혜택 기간과 조건을 다시 확인하세요.",
                    "이미지와 문구가 같은 상품을 설명하는지 확인하세요.",
                    "댓글/DM 문의 응대 문구를 준비하세요.",
                ],
            ),
            "variants": self._normalize_variants(variants, form_data),
        }

    def _normalize_hashtags(self, hashtags: list[str], form_data: AdGenerationForm) -> list[str]:
        normalized = []
        for hashtag in hashtags:
            tag = str(hashtag).strip().replace(" ", "")
            if not tag:
                continue
            normalized.append(tag if tag.startswith("#") else f"#{tag}")
        fallback = [
            f"#{form_data.business_name.replace(' ', '')}",
            f"#{form_data.product_name.replace(' ', '')}",
            f"#{form_data.business_category.replace(' ', '')}",
        ]
        return (normalized + fallback)[:8]

    def _normalize_variants(
        self, variants: list[dict[str, str]], form_data: AdGenerationForm
    ) -> list[dict[str, str]]:
        fallback = [
            {
                "label": "짧은형",
                "headline": f"{form_data.product_name}, 지금 만나보세요",
                "body_copy": form_data.product_description,
            },
            {
                "label": "설명형",
                "headline": f"{form_data.business_name}의 {form_data.product_name}",
                "body_copy": f"{form_data.target_customer}을 위한 {form_data.promotion_goal} 메시지입니다.",
            },
            {
                "label": "이벤트형",
                "headline": form_data.offer_details or f"{form_data.product_name} 이벤트",
                "body_copy": f"{form_data.desired_action}으로 이어지도록 명확하게 안내하세요.",
            },
        ]
        merged = variants + fallback
        return [
            {
                "label": item.get("label") or fallback[index]["label"],
                "headline": item.get("headline") or fallback[index]["headline"],
                "body_copy": item.get("body_copy") or fallback[index]["body_copy"],
            }
            for index, item in enumerate(merged[:3])
        ]

    def _score(self, value: object, fallback: int) -> int:
        try:
            return max(0, min(100, int(value)))
        except (TypeError, ValueError):
            return fallback

    def _at_least_two(self, values: object, fallback: list[str]) -> list[str]:
        if isinstance(values, list):
            cleaned = [str(value).strip() for value in values if str(value).strip()]
            if len(cleaned) >= 2:
                return cleaned[:5]
        return fallback

    def _at_least_three(self, values: object, fallback: list[str]) -> list[str]:
        if isinstance(values, list):
            cleaned = [str(value).strip() for value in values if str(value).strip()]
            if len(cleaned) >= 3:
                return cleaned[:5]
        return fallback

    def _fallback_post_time(self, form_data: AdGenerationForm) -> str:
        if form_data.post_timing_preference != "AI 추천":
            return form_data.post_timing_preference
        if "직장" in form_data.target_customer:
            return "평일 저녁 18:00~20:00"
        return "평일 점심 11:30~13:00"
