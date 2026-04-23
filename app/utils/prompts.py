from app.schemas.form import AdGenerationForm


def build_system_prompt() -> str:
    return (
        "당신은 한국 소상공인의 SNS 홍보 자동화를 돕는 마케팅 전략가입니다. "
        "하나의 캠페인 브리프를 Instagram, Threads, Blog에 맞게 재가공하세요. "
        "모든 결과는 한국어로 작성하고, 과장광고나 보장성 표현을 피하세요. "
        "Instagram은 간단하고 정보 중심으로 작성하세요. 감성적인 긴 문장보다 상품명, 혜택, 이용 조건, "
        "방문/예약 행동을 바로 알 수 있는 짧은 문장을 우선합니다. "
        "Threads는 광고문처럼 밀어붙이지 말고 친구에게 말하듯 친근하고 자연스럽게 작성하세요. "
        "가벼운 관찰, 공감, 구체적인 질문으로 댓글과 대화를 유도하되 의미 없는 참여 유도 bait는 피하세요. "
        "Blog는 완전히 정보 중심으로 작성하세요. 검색자가 알고 싶은 메뉴 구성, 이용 조건, 추천 대상, "
        "방문 전 확인사항, 예약/문의 방법을 빠짐없이 정리합니다. "
        "최신 SNS 광고처럼 상호명, 상품명, 혜택 조건, 대상 고객, 다음 행동을 구체적으로 넣되 "
        "근거 없는 1위, 최고, 보장, 마감 임박 표현은 피하세요. "
        "품질 리포트는 실제 게시 전 검수자가 참고할 수 있게 냉정하게 작성하세요."
    )


def build_generation_prompt(form_data: AdGenerationForm) -> str:
    keyword_text = ", ".join(form_data.keyword_list) if form_data.keyword_list else "없음"
    return f"""
다음 브리프를 바탕으로 광고 문구를 생성하세요.

- 업종: {form_data.business_category}
- 상호명: {form_data.business_name}
- 상품/서비스명: {form_data.product_name}
- 설명: {form_data.product_description}
- 프로모션 상세: {form_data.offer_details or "없음"}
- 타깃 고객: {form_data.target_customer}
- 홍보 목적: {form_data.promotion_goal}
- 톤: {form_data.tone}
- 게시 채널: {form_data.platform}
- 비주얼 스타일: {form_data.visual_style}
- CTA 목표: {form_data.cta_focus}
- 캠페인 유형: {form_data.campaign_type}
- 최종 행동: {form_data.desired_action}
- 게시 타이밍 선호: {form_data.post_timing_preference}
- 강조 키워드: {keyword_text}

반드시 아래 규칙을 지키세요.
1. variants에는 짧은형, 설명형, 이벤트형 3개를 넣으세요.
2. Instagram caption은 2~4개의 짧은 줄로 작성하세요. 각 줄은 정보가 바로 보이게 하며 과한 감성어를 줄이세요.
3. Instagram 첫 줄에는 상품명과 핵심 혜택/특징을 넣으세요. 마지막 줄에는 방문, 예약, 문의, 저장 중 하나의 행동을 명확히 넣으세요.
4. Instagram에는 실제 브리프에 없는 가격, 기간, 운영시간을 만들지 말고, 정보가 없으면 "방문 전 확인"처럼 안전하게 표현하세요.
5. Threads thread_text는 120~260자 정도로 작성하세요. 친구에게 말하듯 친근하게 시작하고, 마지막에는 사용자가 자기 경험을 댓글로 남기고 싶어지는 구체적인 질문을 넣으세요.
6. Threads reply_prompt는 "어떤 게 좋아요?" 같은 뻔한 질문이 아니라 취향, 상황, 선택 기준을 묻는 구체적인 질문으로 작성하세요.
7. Blog title에는 상호명 또는 상품명과 검색 의도가 드러나게 작성하세요. 제목은 정보형 검색어처럼 자연스럽게 작성하세요.
8. Blog intro는 120자 이상으로 작성하고, 누가, 왜, 어떤 조건에서 이용하면 좋은지 구체적으로 설명하세요.
9. Blog body_outline은 4~6개 섹션을 권장하며 메뉴/서비스 구성, 혜택 조건, 추천 대상, 이용 팁, 방문 전 확인사항, 위치/예약 확인 중 필요한 항목을 포함하세요.
10. Blog는 광고성 감탄문보다 설명문으로 작성하고, 독자가 방문 전에 필요한 정보를 한 번에 얻도록 구성하세요.
11. CTA는 사용자의 다음 행동이 즉시 이해되도록 작성하세요.
12. 과장광고, 보장성 표현, 근거 없는 최상급 표현, 실제 브리프에 없는 마감/가격을 만들지 마세요.
13. visual_hook과 image_direction은 배경 이미지 생성 프롬프트로도 쓸 수 있게 구체적인 장면/구도/여백을 포함하세요.
14. Poster headline은 18자 이내를 목표로 강하게 작성하세요.
15. quality_report 점수는 0~100 정수로 작성하세요.
16. improvement_suggestions는 최소 2개 이상 작성하세요.
17. quality_report와 channel_quality는 실제 자동 승인 판단에 쓸 수 있게 냉정하게 작성하세요.
18. pre_publish_checklist는 실제 예약 게시 전에 확인할 사항 3개를 작성하세요.
""".strip()


def build_generation_response_schema() -> dict[str, object]:
    score_schema = {"type": "integer", "minimum": 0, "maximum": 100}
    return {
        "name": "ad_campaign_generation",
        "type": "json_schema",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "headline",
                "body_copy",
                "cta",
                "strategy_note",
                "image_direction",
                "caption",
                "hashtags",
                "channel_packages",
                "quality_report",
                "channel_quality",
                "generation_attempts",
                "auto_approved",
                "pre_publish_checklist",
                "variants",
            ],
            "properties": {
                "headline": {"type": "string"},
                "body_copy": {"type": "string"},
                "cta": {"type": "string"},
                "strategy_note": {"type": "string"},
                "image_direction": {"type": "string"},
                "caption": {"type": "string"},
                "hashtags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 3,
                    "maxItems": 5,
                },
                "channel_packages": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["instagram", "threads", "blog", "poster"],
                    "properties": {
                        "instagram": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "caption",
                                "hashtags",
                                "alt_text",
                                "visual_hook",
                                "recommended_post_time",
                            ],
                            "properties": {
                                "caption": {"type": "string"},
                                "hashtags": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "minItems": 3,
                                    "maxItems": 8,
                                },
                                "alt_text": {"type": "string"},
                                "visual_hook": {"type": "string"},
                                "recommended_post_time": {"type": "string"},
                            },
                        },
                        "threads": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "thread_text",
                                "reply_prompt",
                                "short_hook",
                                "recommended_post_time",
                            ],
                            "properties": {
                                "thread_text": {"type": "string"},
                                "reply_prompt": {"type": "string"},
                                "short_hook": {"type": "string"},
                                "recommended_post_time": {"type": "string"},
                            },
                        },
                        "blog": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "title",
                                "intro",
                                "body_outline",
                                "seo_keywords",
                                "cta",
                                "meta_description",
                            ],
                            "properties": {
                                "title": {"type": "string"},
                                "intro": {"type": "string"},
                                "body_outline": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "minItems": 4,
                                    "maxItems": 6,
                                },
                                "seo_keywords": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "minItems": 3,
                                    "maxItems": 8,
                                },
                                "cta": {"type": "string"},
                                "meta_description": {"type": "string"},
                            },
                        },
                        "poster": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["headline", "subcopy", "cta", "visual_direction"],
                            "properties": {
                                "headline": {"type": "string"},
                                "subcopy": {"type": "string"},
                                "cta": {"type": "string"},
                                "visual_direction": {"type": "string"},
                            },
                        },
                    },
                },
                "quality_report": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "hook_score",
                        "clarity_score",
                        "cta_score",
                        "channel_fit_score",
                        "overall_score",
                        "improvement_suggestions",
                    ],
                    "properties": {
                        "hook_score": score_schema,
                        "clarity_score": score_schema,
                        "cta_score": score_schema,
                        "channel_fit_score": score_schema,
                        "overall_score": score_schema,
                        "improvement_suggestions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 2,
                            "maxItems": 5,
                        },
                    },
                },
                "channel_quality": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "instagram_score",
                        "threads_score",
                        "blog_score",
                        "failed_channels",
                        "regeneration_suggestions",
                    ],
                    "properties": {
                        "instagram_score": score_schema,
                        "threads_score": score_schema,
                        "blog_score": score_schema,
                        "failed_channels": {
                            "type": "array",
                            "items": {"type": "string"},
                            "maxItems": 3,
                        },
                        "regeneration_suggestions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 2,
                            "maxItems": 5,
                        },
                    },
                },
                "generation_attempts": {"type": "integer", "minimum": 1, "maximum": 5},
                "auto_approved": {"type": "boolean"},
                "pre_publish_checklist": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 3,
                    "maxItems": 5,
                },
                "variants": {
                    "type": "array",
                    "minItems": 3,
                    "maxItems": 3,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["label", "headline", "body_copy"],
                        "properties": {
                            "label": {"type": "string"},
                            "headline": {"type": "string"},
                            "body_copy": {"type": "string"},
                        },
                    },
                },
            },
        },
    }
