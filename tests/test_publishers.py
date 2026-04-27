from datetime import datetime

import pytest

from app.config import Settings
from app.services.adapters.mock_copy import MockCopyGenerator
from app.services.campaign_store import CampaignStore
from app.services.channel_connection_store import ChannelConnectionStore
from app.services.publishers import DirectApiPublishAdapter
from evaluations.testset import GENERATION_EVAL_CASES


def _settings(tmp_path):
    return Settings(
        public_base_url="https://demo.example.com",
        data_dir=tmp_path / "data",
        campaign_store_path=tmp_path / "data" / "campaigns.json",
        generated_dir=tmp_path / "generated",
        upload_dir=tmp_path / "generated" / "uploads",
        banner_dir=tmp_path / "generated" / "banners",
        background_dir=tmp_path / "generated" / "backgrounds",
        static_dir=tmp_path / "static",
        templates_dir=tmp_path / "templates",
        copy_provider="mock",
    )


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


@pytest.mark.asyncio
async def test_direct_api_publish_adapter_publishes_all_channels(monkeypatch, tmp_path):
    settings = _settings(tmp_path)
    settings.ensure_runtime_directories()
    result = await MockCopyGenerator().generate(GENERATION_EVAL_CASES[0].form)
    result = result.model_copy(update={"banner_preview_path": "/static/generated/banners/banner-test.png"})
    banner_path = settings.banner_dir / "banner-test.png"
    banner_path.write_bytes(b"fake-image")

    campaign = CampaignStore(settings).create(GENERATION_EVAL_CASES[0].form, result)
    job = CampaignStore(settings).schedule_publish(
        campaign.id,
        ["instagram", "threads", "blog"],
        datetime.now(),
        provider="direct_api",
    ).publish_jobs[0]

    ChannelConnectionStore(settings).save_instagram("ig-token", "1789")
    ChannelConnectionStore(settings).save_threads("threads-token", "thr-1")
    ChannelConnectionStore(settings).save_blog(
        api_base_url="https://example.com/wp-json/wp/v2",
        username="writer",
        application_password="app-pass",
    )

    calls: list[tuple[str, dict | None, dict | None, bytes | None]] = []

    async def fake_post(self, url, headers=None, data=None, json=None, content=None):
        calls.append((url, data, json, content))
        if url.endswith("/media"):
            return _Response({"id": "ig-container"})
        if url.endswith("/media_publish"):
            return _Response({"id": "ig-post"})
        if url.endswith("/threads"):
            return _Response({"id": "threads-container"})
        if url.endswith("/threads_publish"):
            return _Response({"id": "threads-post"})
        if url.endswith("/wp-json/wp/v2/media"):
            return _Response({"id": 17})
        if url.endswith("/wp-json/wp/v2/posts"):
            return _Response({"id": 99, "link": "https://example.com/post/99"})
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr("httpx.AsyncClient.post", fake_post)

    published = await DirectApiPublishAdapter(settings).publish(campaign, job)

    assert published.status == "published"
    assert published.provider == "direct_api"
    assert published.external_ids["instagram"] == "ig-post"
    assert published.external_ids["threads"] == "threads-post"
    assert published.external_ids["blog"] == "https://example.com/post/99"
    assert any(url.endswith("/media_publish") for url, *_ in calls)
    assert any(url.endswith("/threads_publish") for url, *_ in calls)
    assert any(url.endswith("/wp-json/wp/v2/posts") for url, *_ in calls)


@pytest.mark.asyncio
async def test_direct_api_publish_adapter_fails_on_local_public_url(tmp_path):
    settings = Settings(
        public_base_url="http://127.0.0.1:8000",
        data_dir=tmp_path / "data",
        campaign_store_path=tmp_path / "data" / "campaigns.json",
        generated_dir=tmp_path / "generated",
        upload_dir=tmp_path / "generated" / "uploads",
        banner_dir=tmp_path / "generated" / "banners",
        background_dir=tmp_path / "generated" / "backgrounds",
        static_dir=tmp_path / "static",
        templates_dir=tmp_path / "templates",
        copy_provider="mock",
    )
    settings.ensure_runtime_directories()
    result = await MockCopyGenerator().generate(GENERATION_EVAL_CASES[0].form)
    result = result.model_copy(update={"banner_preview_path": "/static/generated/banners/banner-test.png"})
    campaign = CampaignStore(settings).create(GENERATION_EVAL_CASES[0].form, result)
    job = CampaignStore(settings).schedule_publish(
        campaign.id,
        ["instagram"],
        datetime.now(),
        provider="direct_api",
    ).publish_jobs[0]
    ChannelConnectionStore(settings).save_instagram("ig-token", "1789")

    published = await DirectApiPublishAdapter(settings).publish(campaign, job)

    assert published.status == "failed"
    assert "PUBLIC_BASE_URL" in (published.error_message or "")


@pytest.mark.asyncio
async def test_direct_api_publish_adapter_uses_playwright_for_naver_blog(monkeypatch, tmp_path):
    settings = _settings(tmp_path)
    settings.ensure_runtime_directories()
    result = await MockCopyGenerator().generate(GENERATION_EVAL_CASES[0].form)
    result = result.model_copy(update={"banner_preview_path": "/static/generated/banners/banner-test.png"})
    campaign = CampaignStore(settings).create(GENERATION_EVAL_CASES[0].form, result)
    job = CampaignStore(settings).schedule_publish(
        campaign.id,
        ["blog"],
        datetime.now(),
        provider="direct_api",
    ).publish_jobs[0]
    ChannelConnectionStore(settings).save_blog(
        platform="naver_blog",
        blog_id="my-naver-blog",
        username="naver-user",
        login_password="naver-pass",
    )

    async def fake_publish_naver_blog(self, campaign_arg, job_arg, connection):
        assert campaign_arg.id == campaign.id
        assert job_arg.id == job.id
        assert connection.blog_id == "my-naver-blog"
        return "https://blog.naver.com/my-naver-blog/223123456789"

    monkeypatch.setattr(
        DirectApiPublishAdapter,
        "_publish_naver_blog",
        fake_publish_naver_blog,
    )

    published = await DirectApiPublishAdapter(settings).publish(campaign, job)

    assert published.status == "published"
    assert published.external_ids["blog"] == "https://blog.naver.com/my-naver-blog/223123456789"
