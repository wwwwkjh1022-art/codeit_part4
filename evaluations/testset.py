from dataclasses import dataclass

from app.schemas.form import AdGenerationForm


@dataclass(frozen=True)
class GenerationEvalCase:
    id: str
    title: str
    form: AdGenerationForm
    expected_terms: tuple[str, ...]
    min_overall_score: int = 88
    min_channel_score: int = 86


GENERATION_EVAL_CASES: tuple[GenerationEvalCase, ...] = (
    GenerationEvalCase(
        id="cafe-season-menu",
        title="카페 신메뉴 인스타/스레드 홍보",
        form=AdGenerationForm(
            business_category="카페",
            business_name="오늘의카페",
            product_name="딸기 라떼",
            product_description="생딸기를 갈아 넣은 시즌 한정 메뉴로 상큼하고 부드러운 맛이 특징입니다.",
            offer_details="첫 방문 고객 10% 할인",
            target_customer="20대 직장인",
            promotion_goal="신메뉴 홍보",
            tone="친근한",
            platform="인스타그램",
            visual_style="따뜻한 감성",
            cta_focus="방문 유도",
            campaign_type="신상품/신메뉴",
            desired_action="매장 방문",
            post_timing_preference="AI 추천",
            keywords="시즌메뉴, 생딸기, 사진맛집",
        ),
        expected_terms=("딸기", "라떼", "오늘의카페", "방문"),
    ),
    GenerationEvalCase(
        id="flower-event",
        title="꽃집 기간 한정 예약 이벤트",
        form=AdGenerationForm(
            business_category="꽃집",
            business_name="라일락플라워",
            product_name="봄꽃다발",
            product_description="기념일과 집들이에 어울리는 화사한 색감의 꽃다발입니다.",
            offer_details="주말 예약 고객 무료 포장",
            target_customer="동네 주민",
            promotion_goal="신규 고객 유입",
            tone="정중한",
            platform="인스타그램",
            visual_style="프리미엄",
            cta_focus="문의 유도",
            campaign_type="기간 한정 이벤트",
            desired_action="DM 문의",
            post_timing_preference="주말 오전",
            keywords="당일 제작, 예약 가능, 무료 포장",
        ),
        expected_terms=("봄꽃", "예약", "포장", "라일락플라워"),
    ),
    GenerationEvalCase(
        id="nail-reservation",
        title="네일샵 예약 전환 캠페인",
        form=AdGenerationForm(
            business_category="네일샵",
            business_name="오후네일",
            product_name="봄 젤네일",
            product_description="파스텔 컬러와 진주 포인트가 들어간 시즌 디자인입니다.",
            offer_details="주중 예약 시 오프 할인",
            target_customer="20대 직장인",
            promotion_goal="예약 전환",
            tone="트렌디한",
            platform="인스타그램",
            visual_style="산뜻한 시즌형",
            cta_focus="예약 유도",
            campaign_type="예약/상담 전환",
            desired_action="예약하기",
            post_timing_preference="평일 저녁",
            keywords="예약 할인, 봄 디자인, 파스텔",
        ),
        expected_terms=("네일", "예약", "봄", "오후네일"),
    ),
    GenerationEvalCase(
        id="restaurant-revisit",
        title="식당 재방문 유도 이벤트",
        form=AdGenerationForm(
            business_category="식당",
            business_name="한그릇식당",
            product_name="점심 정식",
            product_description="직장인을 위한 빠르고 든든한 점심 정식으로 매일 다른 반찬을 제공합니다.",
            offer_details="재방문 쿠폰 지참 시 음료 제공",
            target_customer="근처 직장인",
            promotion_goal="재방문 유도",
            tone="활기찬",
            platform="Threads",
            visual_style="강한 세일형",
            cta_focus="방문 유도",
            campaign_type="재방문 유도",
            desired_action="매장 방문",
            post_timing_preference="평일 점심",
            keywords="점심, 빠른 식사, 재방문 쿠폰",
        ),
        expected_terms=("점심", "직장인", "재방문", "한그릇식당"),
    ),
)
