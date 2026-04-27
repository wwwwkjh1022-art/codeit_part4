from io import BytesIO

from app.schemas.result import BackgroundAsset
from app.services.background_generator import BackgroundGenerator
from app.services.banner_generator import BannerGenerator
from app.services.generation_pipeline import AutoGenerationPipeline
from app.services.naver_blog_connect import NaverBlogConnectSession, naver_blog_connect_service
from PIL import Image


def _build_form_data() -> dict[str, str]:
    return {
        "business_category": "카페",
        "business_name": "오늘의카페",
        "product_name": "딸기 라떼",
        "product_description": "생딸기를 갈아 넣은 시즌 한정 메뉴로 상큼하고 부드러운 맛이 특징입니다.",
        "offer_details": "첫 방문 고객 10% 할인",
        "target_customer": "20대 직장인",
        "promotion_goal": "신메뉴 홍보",
        "tone": "친근한",
        "platform": "인스타그램",
        "visual_style": "따뜻한 감성",
        "cta_focus": "방문 유도",
        "campaign_type": "신상품/신메뉴",
        "desired_action": "매장 방문",
        "post_timing_preference": "AI 추천",
        "keywords": "시즌메뉴, 생딸기, 사진맛집",
    }


def _build_test_image() -> bytes:
    image = Image.new("RGB", (50, 50), "#ffb199")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_index_page_renders(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "광고 문구 스튜디오" in response.text
    assert 'type="file"' not in response.text
    assert "다음 화면에서 참고 이미지를 넣고" in response.text


def test_generate_page_renders_result(client):
    response = client.post("/generate", data=_build_form_data())

    assert response.status_code == 200
    assert "생성 결과" in response.text
    assert "오늘의카페" in response.text
    assert 'data-active-workbench-tab="content"' in response.text
    assert "이미지 생성 먼저 진행하기" in response.text
    assert "참고 이미지 업로드" in response.text
    assert "경과 시간" in response.text
    assert "Instagram" in response.text
    assert "Threads" in response.text
    assert "Blog" in response.text
    assert "이미지 우선 워크플로" in response.text
    assert "3채널 미리보기와 문구 수정" in response.text
    assert "Instagram 업로드 이미지 예상 초안" in response.text
    assert "Threads 첨부 이미지 예상 초안" in response.text
    assert "블로그 대표 이미지 예상 초안" in response.text
    assert "/static/generated/banners/" in response.text
    assert "Campaign ID" in response.text
    assert "CHANNEL API SETUP" in response.text
    assert "Threads API 저장" in response.text
    assert "이미지 생성" in response.text
    assert "Gemini / Nano Banana" in response.text
    assert "네이버 로그인 창 열기" in response.text
    assert "글쓰기 화면" in response.text
    assert "전략 메모" not in response.text
    assert "권장 비주얼 방향" not in response.text
    assert "자동 생성 판정" not in response.text
    assert "보조 포스터 문구 보기" not in response.text
    assert "자동예약 전 체크리스트" not in response.text
    assert "호환용 통합 캡션" not in response.text


def test_generate_page_falls_back_when_ai_times_out(client, monkeypatch):
    async def fake_generate_until_pass(self, form_data):
        raise TimeoutError("simulated timeout")

    monkeypatch.setattr(
        AutoGenerationPipeline,
        "generate_until_pass",
        fake_generate_until_pass,
    )

    response = client.post("/generate", data=_build_form_data())

    assert response.status_code == 200
    assert "AI 응답이 지연돼 기본 생성 로직으로 결과를 만들었습니다." in response.text
    assert "생성 결과" in response.text
    assert "오늘의카페" in response.text


def test_generate_without_product_description_uses_auto_description(client):
    data = _build_form_data()
    data["product_description"] = ""

    response = client.post("/generate", data=data)

    assert response.status_code == 200
    assert "생성 결과" in response.text
    assert "딸기 라떼" in response.text


def test_campaign_history_lists_generated_campaign(client):
    client.post("/generate", data=_build_form_data())

    response = client.get("/campaigns")

    assert response.status_code == 200
    assert "생성 이력" in response.text
    assert "오늘의카페" in response.text
    assert "딸기 라떼" in response.text


def test_campaign_detail_ready_and_regenerate_flow(client):
    client.post("/generate", data=_build_form_data())
    history = client.get("/campaigns")
    marker = '/campaigns/'
    start = history.text.index(marker) + len(marker)
    campaign_id = history.text[start : history.text.index('"', start)]

    detail = client.get(f"/campaigns/{campaign_id}")
    assert detail.status_code == 200
    assert "초안" in detail.text

    ready = client.post(f"/campaigns/{campaign_id}/ready", follow_redirects=True)
    assert ready.status_code == 200
    assert "예약 준비 완료" in ready.text

    regenerated = client.post(f"/campaigns/{campaign_id}/regenerate")
    assert regenerated.status_code == 200
    assert "같은 브리프로 재생성" in regenerated.text
    assert "오늘의카페" in regenerated.text


def test_campaign_schedule_and_mock_publish_flow(client):
    client.post("/generate", data=_build_form_data())
    history = client.get("/campaigns")
    marker = '/campaigns/'
    start = history.text.index(marker) + len(marker)
    campaign_id = history.text[start : history.text.index('"', start)]

    scheduled = client.post(
        f"/campaigns/{campaign_id}/schedule",
        data={
            "instagram": "1",
            "threads": "1",
            "scheduled_at": "2026-04-13T12:30",
            "automation_provider": "mock",
        },
        follow_redirects=True,
    )
    assert scheduled.status_code == 200
    assert "예약됨" in scheduled.text
    assert "예약 대기" in scheduled.text

    published = client.post(f"/campaigns/{campaign_id}/publish-now", follow_redirects=True)
    assert published.status_code == 200
    assert "게시 완료" in published.text
    assert "mock-instagram" in published.text
    assert "mock-threads" in published.text


def test_channel_api_values_can_be_saved_from_result_page(client):
    client.post("/generate", data=_build_form_data())
    history = client.get("/campaigns")
    marker = '/campaigns/'
    start = history.text.index(marker) + len(marker)
    campaign_id = history.text[start : history.text.index('"', start)]

    response = client.post(
        "/channels/connect/instagram",
        data={
            "instagram_user_id": "1789000001",
            "access_token": "ig-test-token",
            "redirect_to": f"/campaigns/{campaign_id}",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "연결 완료 · IG User ID 1789000001" in response.text

    response = client.post(
        "/channels/connect/threads",
        data={
            "threads_user_id": "thr-7788",
            "access_token": "threads-test-token",
            "redirect_to": f"/campaigns/{campaign_id}",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "연결 완료 · Threads User ID thr-7788" in response.text

    response = client.post(
        "/channels/connect/blog",
        data={
            "platform": "naver_blog",
            "blog_id": "my-naver-blog",
            "naver_username": "naver-user",
            "login_password": "naver-pass",
            "redirect_to": f"/campaigns/{campaign_id}",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "연결 완료 · naver_blog · my-naver-blog" in response.text


def test_naver_blog_connect_start_and_status_routes(client, monkeypatch):
    session = NaverBlogConnectSession(
        id="naver-session-1",
        status="waiting",
        blog_id="my-naver-blog",
        category_id="12",
        message="열린 Chromium 창에서 로그인해 주세요.",
    )

    def fake_start(settings, blog_id, category_id=""):
        assert blog_id == "my-naver-blog"
        assert category_id == "12"
        return session

    def fake_get(session_id):
        assert session_id == "naver-session-1"
        return session.model_copy(update={"status": "connected", "message": "연결 완료"})

    monkeypatch.setattr(naver_blog_connect_service, "start", fake_start)
    monkeypatch.setattr(naver_blog_connect_service, "get", fake_get)

    start_response = client.post(
        "/channels/connect/blog/naver/start",
        data={"blog_id": "my-naver-blog", "category_id": "12"},
    )
    assert start_response.status_code == 200
    assert start_response.json()["session_id"] == "naver-session-1"

    status_response = client.get("/channels/connect/blog/naver/status/naver-session-1")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "connected"


def test_naver_blog_connect_complete_route(client, monkeypatch):
    session = NaverBlogConnectSession(
        id="naver-session-2",
        status="waiting",
        blog_id="my-naver-blog",
        category_id="3",
        message="대기 중",
    )

    def fake_complete(settings, session_id):
        assert session_id == "naver-session-2"
        return session.model_copy(update={"status": "connected", "message": "수동 완료"})

    monkeypatch.setattr(naver_blog_connect_service, "complete", fake_complete)

    response = client.post(
        "/channels/connect/blog/naver/complete",
        data={"session_id": "naver-session-2"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "connected"
    assert response.json()["message"] == "수동 완료"


def test_campaign_image_can_be_regenerated_from_image_tab(client, monkeypatch):
    preview_calls: list[dict[str, str | None]] = []

    async def fake_prepare(self, form_data, result, prompt_override=None):
        return BackgroundAsset(
            prompt=prompt_override or "new image prompt",
            provider="sd35",
            status="generated",
            image_path="/static/generated/backgrounds/regenerated.png",
            note="regenerated",
        )

    def fake_create_preview(self, form_data, result, uploaded_image_path=None, background_image_path=None):
        preview_calls.append(
            {
                "uploaded_image_path": uploaded_image_path,
                "background_image_path": background_image_path,
            }
        )
        return "/static/generated/banners/regenerated-banner.png"

    monkeypatch.setattr(BackgroundGenerator, "prepare", fake_prepare)
    monkeypatch.setattr(BannerGenerator, "create_preview", fake_create_preview)

    client.post("/generate", data=_build_form_data())
    history = client.get("/campaigns")
    marker = '/campaigns/'
    start = history.text.index(marker) + len(marker)
    campaign_id = history.text[start : history.text.index('"', start)]

    response = client.post(
        f"/campaigns/{campaign_id}/image-regenerate",
        data={"image_prompt": "clean dessert hero shot with left-side negative space"},
        files={"image": ("reference.png", _build_test_image(), "image/png")},
    )

    assert response.status_code == 200
    assert "이미지 프롬프트를 기준으로 배경과 배너를 다시 생성했습니다." in response.text
    assert "현재 참고 이미지: /static/generated/uploads/" in response.text
    assert "clean dessert hero shot with left-side negative space" in response.text
    assert "/static/generated/banners/regenerated-banner.png" in response.text
    assert preview_calls[-1]["background_image_path"] == "/static/generated/backgrounds/regenerated.png"
    assert preview_calls[-1]["uploaded_image_path"] is not None
    assert str(preview_calls[-1]["uploaded_image_path"]).startswith("/static/generated/uploads/")


def test_campaign_image_can_use_gemini_tab(client, monkeypatch):
    captured = {}

    async def fake_prepare(self, form_data, result, prompt_override=None):
        captured["provider"] = self.settings.resolved_image_provider
        captured["gemini_api_key"] = self.settings.gemini_api_key
        captured["allow_paid"] = self.settings.allow_paid_image_generation
        return BackgroundAsset(
            prompt=prompt_override or "gemini prompt",
            provider="gemini",
            status="generated",
            image_path="/static/generated/backgrounds/gemini-regenerated.png",
            note="gemini",
        )

    def fake_create_preview(self, form_data, result, uploaded_image_path=None, background_image_path=None):
        captured["uploaded_image_path"] = uploaded_image_path
        captured["background_image_path"] = background_image_path
        return "/static/generated/banners/gemini-banner.png"

    monkeypatch.setattr(BackgroundGenerator, "prepare", fake_prepare)
    monkeypatch.setattr(BannerGenerator, "create_preview", fake_create_preview)

    client.post("/generate", data=_build_form_data())
    history = client.get("/campaigns")
    marker = '/campaigns/'
    start = history.text.index(marker) + len(marker)
    campaign_id = history.text[start : history.text.index('"', start)]

    response = client.post(
        f"/campaigns/{campaign_id}/image-regenerate",
        data={
            "image_mode": "gemini",
            "gemini_api_key": "gemini-test-key",
            "image_prompt": "premium cafe dessert photo, soft daylight, no text",
        },
    )

    assert response.status_code == 200
    assert "Gemini / Nano Banana" in response.text
    assert captured["provider"] == "gemini"
    assert captured["gemini_api_key"] == "gemini-test-key"
    assert captured["allow_paid"] is True
    assert captured["uploaded_image_path"] is None
    assert captured["background_image_path"] == "/static/generated/backgrounds/gemini-regenerated.png"
