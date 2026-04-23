from pydantic import BaseModel, Field


class CopyVariant(BaseModel):
    label: str
    headline: str
    body_copy: str


class InstagramPackage(BaseModel):
    caption: str
    hashtags: list[str] = Field(default_factory=list)
    alt_text: str
    visual_hook: str
    recommended_post_time: str


class ThreadsPackage(BaseModel):
    thread_text: str
    reply_prompt: str
    short_hook: str
    recommended_post_time: str


class BlogPackage(BaseModel):
    title: str
    intro: str
    body_outline: list[str] = Field(default_factory=list)
    seo_keywords: list[str] = Field(default_factory=list)
    cta: str
    meta_description: str


class PosterPackage(BaseModel):
    headline: str
    subcopy: str
    cta: str
    visual_direction: str


class ChannelPackages(BaseModel):
    instagram: InstagramPackage
    threads: ThreadsPackage
    blog: BlogPackage
    poster: PosterPackage


class ChannelQualityReport(BaseModel):
    instagram_score: int = Field(..., ge=0, le=100)
    threads_score: int = Field(..., ge=0, le=100)
    blog_score: int = Field(..., ge=0, le=100)
    failed_channels: list[str] = Field(default_factory=list)
    regeneration_suggestions: list[str] = Field(default_factory=list)


class QualityReport(BaseModel):
    hook_score: int = Field(..., ge=0, le=100)
    clarity_score: int = Field(..., ge=0, le=100)
    cta_score: int = Field(..., ge=0, le=100)
    channel_fit_score: int = Field(..., ge=0, le=100)
    overall_score: int = Field(..., ge=0, le=100)
    improvement_suggestions: list[str] = Field(default_factory=list)


class BackgroundAsset(BaseModel):
    prompt: str
    provider: str = "prompt_only"
    status: str = "prompt_ready"
    image_path: str | None = None
    note: str | None = None


class GenerationResult(BaseModel):
    headline: str
    body_copy: str
    cta: str
    strategy_note: str
    image_direction: str
    caption: str
    hashtags: list[str] = Field(default_factory=list)
    channel_packages: ChannelPackages
    quality_report: QualityReport
    channel_quality: ChannelQualityReport
    generation_attempts: int = 1
    auto_approved: bool = False
    pre_publish_checklist: list[str] = Field(default_factory=list)
    variants: list[CopyVariant] = Field(default_factory=list)
    background_asset: BackgroundAsset | None = None
    banner_preview_path: str | None = None
    provider_used: str = "mock"
