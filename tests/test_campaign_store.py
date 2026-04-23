from datetime import datetime
import asyncio

from app.config import Settings
from app.services.adapters.mock_copy import MockCopyGenerator
from app.services.campaign_store import CampaignStore
from evaluations.testset import GENERATION_EVAL_CASES


def _settings(tmp_path):
    return Settings(
        data_dir=tmp_path / "data",
        campaign_store_path=tmp_path / "data" / "campaigns.json",
        generated_dir=tmp_path / "generated",
        upload_dir=tmp_path / "generated" / "uploads",
        banner_dir=tmp_path / "generated" / "banners",
        static_dir=tmp_path / "static",
        templates_dir=tmp_path / "templates",
        copy_provider="mock",
    )


def _build_form_and_result():
    case = GENERATION_EVAL_CASES[0]
    result = asyncio.run(MockCopyGenerator().generate(case.form))
    return case.form, result


def test_campaign_store_schedule_publish(tmp_path):
    settings = _settings(tmp_path)
    settings.ensure_runtime_directories()
    store = CampaignStore(settings)
    form, result = _build_form_and_result()

    campaign = store.create(form, result)
    scheduled = store.schedule_publish(
        campaign.id,
        ["instagram", "threads"],
        datetime.fromisoformat("2026-04-13T12:30"),
    )

    assert scheduled is not None
    assert scheduled.status == "scheduled"
    assert len(scheduled.publish_jobs) == 1
    assert scheduled.publish_jobs[0].channels == ["instagram", "threads"]


def test_campaign_store_lists_due_publish_jobs(tmp_path):
    settings = _settings(tmp_path)
    settings.ensure_runtime_directories()
    store = CampaignStore(settings)
    form, result = _build_form_and_result()

    campaign = store.create(form, result)
    store.schedule_publish(
        campaign.id,
        ["instagram", "threads", "blog"],
        datetime.fromisoformat("2026-04-13T12:30"),
    )

    due_jobs = store.list_due_publish_jobs(datetime.fromisoformat("2026-04-13T12:31"))

    assert len(due_jobs) == 1
    due_campaign, due_job = due_jobs[0]
    assert due_campaign.id == campaign.id
    assert due_job.channels == ["instagram", "threads", "blog"]


def test_campaign_store_saves_automation_provider_and_recurrence(tmp_path):
    settings = _settings(tmp_path)
    settings.ensure_runtime_directories()
    store = CampaignStore(settings)
    form, result = _build_form_and_result()

    campaign = store.create(form, result)
    scheduled = store.schedule_publish(
        campaign.id,
        ["instagram", "threads", "blog"],
        datetime.fromisoformat("2026-04-13T12:30"),
        provider="n8n",
        recurrence="daily",
        sequence_index=2,
        sequence_total=7,
    )

    assert scheduled is not None
    job = scheduled.publish_jobs[0]
    assert job.provider == "n8n"
    assert job.recurrence == "daily"
    assert job.sequence_index == 2
    assert job.sequence_total == 7
