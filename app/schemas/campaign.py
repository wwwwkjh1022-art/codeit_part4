from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.form import AdGenerationForm
from app.schemas.result import GenerationResult


CampaignStatus = Literal["draft", "ready_for_schedule", "scheduled", "published"]
PublishChannel = Literal["instagram", "threads", "blog"]
PublishStatus = Literal["queued", "published", "failed"]


class PublishJob(BaseModel):
    id: str
    campaign_id: str
    channels: list[PublishChannel] = Field(default_factory=list)
    scheduled_at: datetime
    status: PublishStatus = "queued"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    published_at: datetime | None = None
    provider: str = "mock"
    recurrence: str = "once"
    sequence_index: int = 1
    sequence_total: int = 1
    external_ids: dict[str, str] = Field(default_factory=dict)
    error_message: str | None = None


class CampaignRecord(BaseModel):
    id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: CampaignStatus = "draft"
    form: AdGenerationForm
    result: GenerationResult
    uploaded_image_path: str | None = None
    source_campaign_id: str | None = None
    publish_jobs: list[PublishJob] = Field(default_factory=list)
