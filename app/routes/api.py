import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query
from openai import APIError, AuthenticationError
from pydantic import BaseModel, Field

from app.config import get_settings
from app.schemas.campaign import CampaignRecord, PublishChannel, PublishJob, PublishStatus
from app.schemas.form import AdGenerationForm
from app.services.adapters.mock_copy import MockCopyGenerator
from app.services.background_generator import BackgroundGenerator
from app.services.banner_generator import BannerGenerator
from app.services.campaign_store import CampaignStore
from app.services.generation_pipeline import AutoGenerationPipeline
from app.services.publishers import build_publish_adapter


router = APIRouter(prefix="/api", tags=["automation"])
logger = logging.getLogger(__name__)


class GenerateCampaignResponse(BaseModel):
    campaign: CampaignRecord
    warning: str | None = None
    n8n_next_step: str


class ScheduleCampaignRequest(BaseModel):
    channels: list[PublishChannel] = Field(
        default_factory=lambda: ["instagram", "threads", "blog"]
    )
    scheduled_at: datetime | None = None
    automation_provider: str = "n8n"
    repeat_interval: str = "none"
    repeat_count: int = 1


class PublishJobCompletionRequest(BaseModel):
    status: PublishStatus = "published"
    provider: str = "n8n"
    external_ids: dict[str, str] = Field(default_factory=dict)
    error_message: str | None = None
    published_at: datetime | None = None


class ChannelPublishPayload(BaseModel):
    channel: PublishChannel
    text: str
    title: str | None = None
    hashtags: list[str] = Field(default_factory=list)
    image_url: str | None = None
    alt_text: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class PublishJobPayload(BaseModel):
    campaign_id: str
    job_id: str
    scheduled_at: datetime
    channels: list[PublishChannel]
    public_result_url: str
    payloads: dict[PublishChannel, ChannelPublishPayload]


class DuePublishJobResponse(BaseModel):
    due_jobs: list[PublishJobPayload]


@router.post("/campaigns/generate", response_model=GenerateCampaignResponse)
async def generate_campaign_for_automation(
    form_data: AdGenerationForm,
) -> GenerateCampaignResponse:
    settings = get_settings()
    warning: str | None = None

    try:
        result = await AutoGenerationPipeline(settings).generate_until_pass(form_data)
    except AuthenticationError:
        result = await MockCopyGenerator(provider_name="mock-fallback").generate(form_data)
        warning = "OPENAI_API_KEY 인증 실패로 mock fallback 결과를 생성했습니다."
        logger.exception("OpenAI authentication failed during API generation.")
    except APIError:
        result = await MockCopyGenerator(provider_name="mock-fallback").generate(form_data)
        warning = "OpenAI API 호출 실패로 mock fallback 결과를 생성했습니다."
        logger.exception("OpenAI API request failed during API generation.")
    except Exception:
        result = await MockCopyGenerator(provider_name="mock-fallback").generate(form_data)
        warning = "생성 중 예외가 발생해 mock fallback 결과를 생성했습니다."
        logger.exception("Unexpected generation error during API generation.")

    background_asset = await BackgroundGenerator(settings).prepare(form_data, result)
    result = result.model_copy(update={"background_asset": background_asset})
    banner_preview_path = BannerGenerator(settings).create_preview(
        form_data=form_data,
        result=result,
        uploaded_image_path=None,
        background_image_path=background_asset.image_path,
    )
    result = result.model_copy(update={"banner_preview_path": banner_preview_path})
    campaign = CampaignStore(settings).create(form=form_data, result=result)
    next_step = "schedule_or_publish" if result.auto_approved else "manual_review_or_regenerate"

    return GenerateCampaignResponse(
        campaign=campaign,
        warning=warning,
        n8n_next_step=next_step,
    )


@router.get("/campaigns/{campaign_id}", response_model=CampaignRecord)
async def get_campaign_for_automation(campaign_id: str) -> CampaignRecord:
    campaign = CampaignStore(get_settings()).get(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="캠페인을 찾을 수 없습니다.")
    return campaign


@router.post("/campaigns/{campaign_id}/ready", response_model=CampaignRecord)
async def mark_campaign_ready_for_automation(campaign_id: str) -> CampaignRecord:
    campaign = CampaignStore(get_settings()).update_status(campaign_id, "ready_for_schedule")
    if campaign is None:
        raise HTTPException(status_code=404, detail="캠페인을 찾을 수 없습니다.")
    return campaign


@router.post("/campaigns/{campaign_id}/schedule", response_model=CampaignRecord)
async def schedule_campaign_for_automation(
    campaign_id: str,
    payload: ScheduleCampaignRequest,
) -> CampaignRecord:
    scheduled_at = payload.scheduled_at or datetime.now() + timedelta(hours=1)
    channels = payload.channels or ["instagram", "threads", "blog"]
    repeat_total = _normalize_repeat_count(payload.repeat_interval, payload.repeat_count)
    recurrence = "once" if repeat_total == 1 else payload.repeat_interval
    store = CampaignStore(get_settings())
    campaign = None
    for index in range(repeat_total):
        campaign = store.schedule_publish(
            campaign_id,
            channels,
            _next_schedule_time(scheduled_at, payload.repeat_interval, index),
            provider=payload.automation_provider,
            recurrence=recurrence,
            sequence_index=index + 1,
            sequence_total=repeat_total,
        )
    if campaign is None:
        raise HTTPException(status_code=404, detail="캠페인을 찾을 수 없습니다.")
    return campaign


@router.get("/campaigns/{campaign_id}/publish-payload", response_model=PublishJobPayload)
async def get_publish_payload_for_automation(campaign_id: str) -> PublishJobPayload:
    campaign = CampaignStore(get_settings()).get(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="캠페인을 찾을 수 없습니다.")
    if not campaign.publish_jobs:
        raise HTTPException(status_code=404, detail="예약 작업이 없습니다.")
    return _build_publish_job_payload(campaign, campaign.publish_jobs[-1])


@router.get("/publish-jobs/due", response_model=DuePublishJobResponse)
async def list_due_publish_jobs_for_automation(
    due_at: datetime | None = None,
    limit: int = Query(default=20, ge=1, le=100),
) -> DuePublishJobResponse:
    store = CampaignStore(get_settings())
    due_jobs = store.list_due_publish_jobs(due_at or datetime.now(), limit=limit)
    return DuePublishJobResponse(
        due_jobs=[
            _build_publish_job_payload(campaign, job)
            for campaign, job in due_jobs
        ]
    )


@router.post(
    "/campaigns/{campaign_id}/publish-jobs/{job_id}/complete",
    response_model=CampaignRecord,
)
async def complete_publish_job_from_automation(
    campaign_id: str,
    job_id: str,
    payload: PublishJobCompletionRequest,
) -> CampaignRecord:
    store = CampaignStore(get_settings())
    campaign = store.get(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="캠페인을 찾을 수 없습니다.")

    job = next((item for item in campaign.publish_jobs if item.id == job_id), None)
    if job is None:
        raise HTTPException(status_code=404, detail="게시 작업을 찾을 수 없습니다.")

    updated_job = job.model_copy(
        update={
            "status": payload.status,
            "provider": payload.provider,
            "external_ids": payload.external_ids,
            "error_message": payload.error_message,
            "published_at": payload.published_at or (
                datetime.now() if payload.status == "published" else None
            ),
            "updated_at": datetime.now(),
        }
    )
    updated = store.update_publish_job(campaign_id, updated_job)
    if updated is None:
        raise HTTPException(status_code=404, detail="캠페인을 찾을 수 없습니다.")
    return updated


@router.post("/campaigns/{campaign_id}/publish-now", response_model=CampaignRecord)
async def publish_campaign_now_for_automation(campaign_id: str) -> CampaignRecord:
    settings = get_settings()
    store = CampaignStore(settings)
    campaign = store.get(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="캠페인을 찾을 수 없습니다.")

    if campaign.publish_jobs:
        job = campaign.publish_jobs[-1]
    else:
        campaign = store.schedule_publish(
            campaign_id,
            ["instagram", "threads", "blog"],
            datetime.now(),
        )
        if campaign is None:
            raise HTTPException(status_code=404, detail="캠페인을 찾을 수 없습니다.")
        job = campaign.publish_jobs[-1]

    published_job = await build_publish_adapter().publish(campaign, job)
    updated = store.update_publish_job(campaign_id, published_job)
    if updated is None:
        raise HTTPException(status_code=404, detail="캠페인을 찾을 수 없습니다.")
    return updated


def _build_publish_job_payload(
    campaign: CampaignRecord,
    job: PublishJob,
) -> PublishJobPayload:
    result = campaign.result
    image_url = _absolute_url(result.banner_preview_path)
    instagram = result.channel_packages.instagram
    threads = result.channel_packages.threads
    blog = result.channel_packages.blog
    payloads: dict[PublishChannel, ChannelPublishPayload] = {
        "instagram": ChannelPublishPayload(
            channel="instagram",
            text=instagram.caption,
            hashtags=instagram.hashtags,
            image_url=image_url,
            alt_text=instagram.alt_text,
            metadata={
                "visual_hook": instagram.visual_hook,
                "recommended_post_time": instagram.recommended_post_time,
            },
        ),
        "threads": ChannelPublishPayload(
            channel="threads",
            text=threads.thread_text,
            image_url=image_url,
            metadata={
                "reply_prompt": threads.reply_prompt,
                "short_hook": threads.short_hook,
                "recommended_post_time": threads.recommended_post_time,
            },
        ),
        "blog": ChannelPublishPayload(
            channel="blog",
            title=blog.title,
            text=_build_blog_html(campaign),
            hashtags=blog.seo_keywords,
            image_url=image_url,
            metadata={
                "intro": blog.intro,
                "body_outline": blog.body_outline,
                "cta": blog.cta,
                "meta_description": blog.meta_description,
            },
        ),
    }
    return PublishJobPayload(
        campaign_id=campaign.id,
        job_id=job.id,
        scheduled_at=job.scheduled_at,
        channels=job.channels,
        public_result_url=f"{_public_base_url()}/campaigns/{campaign.id}",
        payloads={channel: payloads[channel] for channel in job.channels},
    )


def _build_blog_html(campaign: CampaignRecord) -> str:
    blog = campaign.result.channel_packages.blog
    outline = "\n".join(f"<li>{item}</li>" for item in blog.body_outline)
    keywords = ", ".join(blog.seo_keywords)
    return (
        f"<p>{blog.intro}</p>\n"
        f"<ul>{outline}</ul>\n"
        f"<p><strong>{blog.cta}</strong></p>\n"
        f"<p>추천 키워드: {keywords}</p>"
    )


def _absolute_url(path: str | None) -> str | None:
    if not path:
        return None
    if path.startswith(("http://", "https://")):
        return path
    return f"{_public_base_url()}/{path.lstrip('/')}"


def _public_base_url() -> str:
    return get_settings().public_base_url.rstrip("/")


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
