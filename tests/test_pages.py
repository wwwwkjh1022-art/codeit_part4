from io import BytesIO

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


def test_generate_page_renders_result(client):
    response = client.post("/generate", data=_build_form_data())

    assert response.status_code == 200
    assert "생성 결과" in response.text
    assert "짧은형" in response.text
    assert "오늘의카페" in response.text
    assert "전략 메모" in response.text
    assert "Instagram" in response.text
    assert "Threads" in response.text
    assert "Blog" in response.text
    assert "품질 기준 통과" in response.text
    assert "업로드 예상 초안" in response.text
    assert "게시 전 화면 검수" in response.text
    assert "Instagram 업로드 이미지 예상 초안" in response.text
    assert "Threads 첨부 이미지 예상 초안" in response.text
    assert "블로그 대표 이미지 예상 초안" in response.text
    assert "자동예약 전 체크리스트" in response.text
    assert "AI 배경 이미지 프롬프트" in response.text
    assert "GPT Image 또는 Nano Banana" in response.text
    assert "Campaign ID" in response.text


def test_generate_with_image_upload(client):
    files = {"image": ("reference.png", _build_test_image(), "image/png")}
    response = client.post("/generate", data=_build_form_data(), files=files)

    assert response.status_code == 200
    assert "/static/generated/banners/" in response.text


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
        },
        follow_redirects=True,
    )
    assert scheduled.status_code == 200
    assert "예약됨" in scheduled.text
    assert "queued" in scheduled.text

    published = client.post(f"/campaigns/{campaign_id}/publish-now", follow_redirects=True)
    assert published.status_code == 200
    assert "게시 완료" in published.text
    assert "mock-instagram" in published.text
    assert "mock-threads" in published.text
