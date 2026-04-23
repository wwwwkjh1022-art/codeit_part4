import pytest

from app.config import Settings
from app.services.generation_pipeline import AutoGenerationPipeline
from evaluations.testset import GENERATION_EVAL_CASES


@pytest.mark.asyncio
async def test_pipeline_auto_approves_mock_generation(tmp_path):
    settings = Settings(
        copy_provider="mock",
        data_dir=tmp_path / "data",
        campaign_store_path=tmp_path / "data" / "campaigns.json",
        generated_dir=tmp_path / "generated",
        upload_dir=tmp_path / "generated" / "uploads",
        banner_dir=tmp_path / "generated" / "banners",
        static_dir=tmp_path / "static",
        templates_dir=tmp_path / "templates",
    )
    pipeline = AutoGenerationPipeline(settings)

    result = await pipeline.generate_until_pass(GENERATION_EVAL_CASES[0].form)

    assert result.auto_approved is True
    assert result.generation_attempts == 1
    assert result.channel_quality.failed_channels == []
    assert result.channel_quality.instagram_score >= 80
    assert result.channel_quality.threads_score >= 80
    assert result.channel_quality.blog_score >= 80
