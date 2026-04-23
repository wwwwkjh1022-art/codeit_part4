import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from openai import APIError, AuthenticationError
from starlette.responses import RedirectResponse

from app.config import Settings, get_settings
from app.schemas.form import AdGenerationForm
from app.schemas.result import GenerationResult
from app.services.banner_generator import BannerGenerator
from app.services.background_generator import BackgroundGenerator
from app.services.campaign_store import CampaignStore
from app.services.adapters.mock_copy import MockCopyGenerator
from app.services.generation_pipeline import AutoGenerationPipeline
from app.services.publishers import build_publish_adapter
from app.utils.files import save_upload_file


router = APIRouter(tags=["pages"])
logger = logging.getLogger(__name__)

TONE_OPTIONS = ["정중한", "친근한", "트렌디한", "프리미엄", "활기찬"]
PLATFORM_OPTIONS = ["인스타그램", "블로그", "전단지", "배달앱", "오프라인 포스터"]
GOAL_OPTIONS = ["신규 고객 유입", "재방문 유도", "신메뉴 홍보", "이벤트 홍보", "브랜드 인지도"]
VISUAL_STYLE_OPTIONS = ["따뜻한 감성", "미니멀", "강한 세일형", "프리미엄", "산뜻한 시즌형"]
CTA_FOCUS_OPTIONS = ["방문 유도", "예약 유도", "문의 유도", "구매 유도", "팔로우 유도"]
CAMPAIGN_TYPE_OPTIONS = ["신상품/신메뉴", "기간 한정 이벤트", "재방문 유도", "브랜드 인지도", "예약/상담 전환"]
DESIRED_ACTION_OPTIONS = ["매장 방문", "예약하기", "DM 문의", "링크 클릭", "팔로우/저장"]
POST_TIMING_OPTIONS = ["AI 추천", "평일 점심", "평일 저녁", "주말 오전", "주말 저녁"]


def _build_context(request: Request, **extra: object) -> dict[str, object]:
    return {
        "request": request,
        "tone_options": TONE_OPTIONS,
        "platform_options": PLATFORM_OPTIONS,
        "goal_options": GOAL_OPTIONS,
        "visual_style_options": VISUAL_STYLE_OPTIONS,
        "cta_focus_options": CTA_FOCUS_OPTIONS,
        "campaign_type_options": CAMPAIGN_TYPE_OPTIONS,
        "desired_action_options": DESIRED_ACTION_OPTIONS,
        "post_timing_options": POST_TIMING_OPTIONS,
        **extra,
    }


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    templates = request.app.state.templates
    initial_form = {
        "business_category": request.query_params.get("business_category", ""),
        "business_name": request.query_params.get("business_name", ""),
        "product_name": request.query_params.get("product_name", ""),
        "product_description": request.query_params.get("product_description", ""),
        "offer_details": request.query_params.get("offer_details", ""),
        "target_customer": request.query_params.get("target_customer", ""),
        "promotion_goal": request.query_params.get("promotion_goal", GOAL_OPTIONS[0]),
        "tone": request.query_params.get("tone", TONE_OPTIONS[1]),
        "platform": "Instagram, Threads, Blog",
        "visual_style": request.query_params.get("visual_style", VISUAL_STYLE_OPTIONS[0]),
        "cta_focus": request.query_params.get("cta_focus", CTA_FOCUS_OPTIONS[0]),
        "campaign_type": request.query_params.get("campaign_type", CAMPAIGN_TYPE_OPTIONS[0]),
        "desired_action": request.query_params.get("desired_action", DESIRED_ACTION_OPTIONS[0]),
        "post_timing_preference": request.query_params.get(
            "post_timing_preference", POST_TIMING_OPTIONS[0]
        ),
        "keywords": request.query_params.get("keywords", ""),
    }
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=_build_context(request, form=initial_form, result=None, warning=None, errors=[]),
    )


@router.get("/generate")
async def generate_redirect() -> RedirectResponse:
    return RedirectResponse(url="/", status_code=303)


@router.post("/generate", response_class=HTMLResponse)
async def generate(
    request: Request,
    form_data: AdGenerationForm = Depends(AdGenerationForm.as_form),
    image: UploadFile | None = File(default=None),
) -> HTMLResponse:
    settings = get_settings()
    templates = request.app.state.templates
    uploaded_image_path = save_upload_file(image, settings)

    pipeline = AutoGenerationPipeline(settings)
    warning: str | None = None

    try:
        result = await pipeline.generate_until_pass(form_data)
    except AuthenticationError:
        fallback = MockCopyGenerator(provider_name="mock-fallback")
        result = await fallback.generate(form_data)
        warning = (
            "OPENAI_API_KEY 인증에 실패해 기본 생성 로직으로 결과를 만들었습니다. "
            ".env의 API 키를 다시 확인해주세요."
        )
        logger.exception("OpenAI authentication failed during generation.")
    except APIError:
        fallback = MockCopyGenerator(provider_name="mock-fallback")
        result = await fallback.generate(form_data)
        warning = "OpenAI 호출에 실패해 기본 생성 로직으로 결과를 만들었습니다. 잠시 후 다시 시도해주세요."
        logger.exception("OpenAI API request failed during generation.")
    except Exception:
        fallback = MockCopyGenerator(provider_name="mock-fallback")
        result = await fallback.generate(form_data)
        warning = "AI 호출에 문제가 있어 기본 생성 로직으로 결과를 만들었습니다."

    result = await _attach_visual_assets(settings, form_data, result, uploaded_image_path)
    campaign = CampaignStore(settings).create(
        form=form_data,
        result=result,
        uploaded_image_path=uploaded_image_path,
    )

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context=_build_context(
            request,
            form=form_data.model_dump(),
            result=result,
            campaign=campaign,
            warning=warning,
            uploaded_image_path=uploaded_image_path,
        ),
    )


@router.get("/campaigns", response_class=HTMLResponse)
async def campaign_history(request: Request) -> HTMLResponse:
    settings = get_settings()
    templates = request.app.state.templates
    campaigns = CampaignStore(settings).list_recent()
    return templates.TemplateResponse(
        request=request,
        name="campaigns.html",
        context=_build_context(request, campaigns=campaigns),
    )


@router.get("/campaigns/{campaign_id}", response_class=HTMLResponse)
async def campaign_detail(request: Request, campaign_id: str) -> HTMLResponse:
    settings = get_settings()
    templates = request.app.state.templates
    campaign = CampaignStore(settings).get(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="캠페인을 찾을 수 없습니다.")
    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context=_build_context(
            request,
            form=campaign.form.model_dump(),
            result=campaign.result,
            campaign=campaign,
            warning=None,
            uploaded_image_path=campaign.uploaded_image_path,
        ),
    )


@router.post("/campaigns/{campaign_id}/ready")
async def mark_campaign_ready(campaign_id: str) -> RedirectResponse:
    settings = get_settings()
    campaign = CampaignStore(settings).update_status(campaign_id, "ready_for_schedule")
    if campaign is None:
        raise HTTPException(status_code=404, detail="캠페인을 찾을 수 없습니다.")
    return RedirectResponse(url=f"/campaigns/{campaign_id}", status_code=303)


@router.post("/campaigns/{campaign_id}/schedule")
async def schedule_campaign(
    campaign_id: str,
    scheduled_at: str = Form(""),
    instagram: str | None = Form(default=None),
    threads: str | None = Form(default=None),
    blog: str | None = Form(default=None),
    automation_provider: str = Form("n8n"),
    repeat_interval: str = Form("none"),
    repeat_count: int = Form(1),
) -> RedirectResponse:
    settings = get_settings()
    channels = []
    if instagram:
        channels.append("instagram")
    if threads:
        channels.append("threads")
    if blog:
        channels.append("blog")
    if not channels:
        channels = ["instagram", "threads", "blog"]

    schedule_time = _parse_schedule_time(scheduled_at)
    repeat_total = _normalize_repeat_count(repeat_interval, repeat_count)
    recurrence = "once" if repeat_total == 1 else repeat_interval
    store = CampaignStore(settings)
    campaign = None
    for index in range(repeat_total):
        campaign = store.schedule_publish(
            campaign_id,
            channels,
            _next_schedule_time(schedule_time, repeat_interval, index),
            provider=automation_provider,
            recurrence=recurrence,
            sequence_index=index + 1,
            sequence_total=repeat_total,
        )
    if campaign is None:
        raise HTTPException(status_code=404, detail="캠페인을 찾을 수 없습니다.")
    return RedirectResponse(url=f"/campaigns/{campaign_id}", status_code=303)


@router.post("/campaigns/{campaign_id}/publish-now")
async def publish_campaign_now(campaign_id: str) -> RedirectResponse:
    settings = get_settings()
    store = CampaignStore(settings)
    campaign = store.get(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="캠페인을 찾을 수 없습니다.")

    if campaign.publish_jobs:
        job = campaign.publish_jobs[-1]
    else:
        scheduled = store.schedule_publish(
            campaign_id,
            ["instagram", "threads"],
            datetime.now(),
        )
        if scheduled is None:
            raise HTTPException(status_code=404, detail="캠페인을 찾을 수 없습니다.")
        campaign = scheduled
        job = campaign.publish_jobs[-1]

    adapter = build_publish_adapter()
    published_job = await adapter.publish(campaign, job)
    store.update_publish_job(campaign_id, published_job)
    return RedirectResponse(url=f"/campaigns/{campaign_id}", status_code=303)


@router.post("/campaigns/{campaign_id}/regenerate")
async def regenerate_campaign(request: Request, campaign_id: str) -> HTMLResponse:
    settings = get_settings()
    templates = request.app.state.templates
    store = CampaignStore(settings)
    campaign = store.get(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="캠페인을 찾을 수 없습니다.")

    form_data = campaign.form
    pipeline = AutoGenerationPipeline(settings)
    warning: str | None = None
    try:
        result = await pipeline.generate_until_pass(form_data)
    except AuthenticationError:
        fallback = MockCopyGenerator(provider_name="mock-fallback")
        result = await fallback.generate(form_data)
        warning = (
            "OPENAI_API_KEY 인증에 실패해 기본 생성 로직으로 결과를 만들었습니다. "
            ".env의 API 키를 다시 확인해주세요."
        )
        logger.exception("OpenAI authentication failed during regeneration.")
    except APIError:
        fallback = MockCopyGenerator(provider_name="mock-fallback")
        result = await fallback.generate(form_data)
        warning = "OpenAI 호출에 실패해 기본 생성 로직으로 결과를 만들었습니다. 잠시 후 다시 시도해주세요."
        logger.exception("OpenAI API request failed during regeneration.")
    except Exception:
        fallback = MockCopyGenerator(provider_name="mock-fallback")
        result = await fallback.generate(form_data)
        warning = "AI 호출에 문제가 있어 기본 생성 로직으로 결과를 만들었습니다."

    result = await _attach_visual_assets(settings, form_data, result, campaign.uploaded_image_path)
    new_campaign = store.create(
        form=form_data,
        result=result,
        uploaded_image_path=campaign.uploaded_image_path,
        source_campaign_id=campaign.id,
    )

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context=_build_context(
            request,
            form=form_data.model_dump(),
            result=result,
            campaign=new_campaign,
            warning=warning,
            uploaded_image_path=campaign.uploaded_image_path,
        ),
    )


def _parse_schedule_time(value: str) -> datetime:
    if not value:
        return datetime.now() + timedelta(hours=1)
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.now() + timedelta(hours=1)


def _normalize_repeat_count(repeat_interval: str, repeat_count: int) -> int:
    if repeat_interval not in {"daily", "weekly"}:
        return 1
    return min(max(repeat_count, 1), 30)


def _next_schedule_time(base_time: datetime, repeat_interval: str, index: int) -> datetime:
    if repeat_interval == "daily":
        return base_time + timedelta(days=index)
    if repeat_interval == "weekly":
        return base_time + timedelta(weeks=index)
    return base_time


async def _attach_visual_assets(
    settings: Settings,
    form_data: AdGenerationForm,
    result: GenerationResult,
    uploaded_image_path: str | None,
) -> GenerationResult:
    background_asset = await BackgroundGenerator(settings).prepare(form_data, result)
    result = result.model_copy(update={"background_asset": background_asset})
    banner_preview_path = BannerGenerator(settings).create_preview(
        form_data=form_data,
        result=result,
        uploaded_image_path=uploaded_image_path,
        background_image_path=background_asset.image_path,
    )
    return result.model_copy(update={"banner_preview_path": banner_preview_path})
