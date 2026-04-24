import base64
from io import BytesIO

import httpx
import pytest
from PIL import Image

from app.config import Settings
from app.services.adapters.mock_copy import MockCopyGenerator
from app.services.background_generator import BackgroundGenerator
from evaluations.testset import GENERATION_EVAL_CASES


@pytest.mark.asyncio
async def test_background_generator_prompt_only_is_default(tmp_path):
    settings = Settings(
        copy_provider="mock",
        image_provider="auto",
        sd35_endpoint_url=None,
        gemini_api_key="test-key",
        allow_paid_image_generation=False,
        data_dir=tmp_path / "data",
        generated_dir=tmp_path / "generated",
        upload_dir=tmp_path / "generated" / "uploads",
        banner_dir=tmp_path / "generated" / "banners",
        background_dir=tmp_path / "generated" / "backgrounds",
        static_dir=tmp_path / "static",
        templates_dir=tmp_path / "templates",
    )
    settings.ensure_runtime_directories()
    form = GENERATION_EVAL_CASES[0].form
    result = await MockCopyGenerator().generate(form)

    asset = await BackgroundGenerator(settings).prepare(form, result)

    assert asset.provider == "prompt_only"
    assert asset.status == "prompt_ready"
    assert asset.image_path is None
    assert "No readable text" in asset.prompt
    assert form.product_name in asset.prompt


@pytest.mark.asyncio
async def test_background_generator_gemini_requires_explicit_paid_opt_in(tmp_path):
    settings = Settings(
        copy_provider="mock",
        image_provider="gemini",
        gemini_api_key="test-key",
        allow_paid_image_generation=False,
        data_dir=tmp_path / "data",
        generated_dir=tmp_path / "generated",
        upload_dir=tmp_path / "generated" / "uploads",
        banner_dir=tmp_path / "generated" / "banners",
        background_dir=tmp_path / "generated" / "backgrounds",
        static_dir=tmp_path / "static",
        templates_dir=tmp_path / "templates",
    )
    settings.ensure_runtime_directories()
    form = GENERATION_EVAL_CASES[0].form
    result = await MockCopyGenerator().generate(form)

    asset = await BackgroundGenerator(settings).prepare(form, result)

    assert asset.provider == "gemini"
    assert asset.status == "skipped"
    assert asset.image_path is None
    assert "비용 방지" in (asset.note or "")


@pytest.mark.asyncio
async def test_background_generator_openai_provider_uses_explicit_opt_in(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    async def fake_generate(self, prompt: str) -> str:
        assert "Pinterest-worthy" in prompt
        return "/static/generated/backgrounds/openai-test.png"

    monkeypatch.setattr(BackgroundGenerator, "_generate_with_openai", fake_generate)
    settings = Settings(
        copy_provider="mock",
        image_provider="openai",
        openai_api_key="test-key",
        allow_paid_image_generation=True,
        data_dir=tmp_path / "data",
        generated_dir=tmp_path / "generated",
        upload_dir=tmp_path / "generated" / "uploads",
        banner_dir=tmp_path / "generated" / "banners",
        background_dir=tmp_path / "generated" / "backgrounds",
        static_dir=tmp_path / "static",
        templates_dir=tmp_path / "templates",
    )
    settings.ensure_runtime_directories()
    form = GENERATION_EVAL_CASES[0].form
    result = await MockCopyGenerator().generate(form)

    asset = await BackgroundGenerator(settings).prepare(form, result)

    assert asset.provider == "openai"
    assert asset.status == "generated"
    assert asset.image_path == "/static/generated/backgrounds/openai-test.png"


@pytest.mark.asyncio
async def test_background_generator_sd35_requires_endpoint(tmp_path):
    settings = Settings(
        copy_provider="mock",
        image_provider="sd35",
        sd35_endpoint_url=None,
        allow_paid_image_generation=True,
        data_dir=tmp_path / "data",
        generated_dir=tmp_path / "generated",
        upload_dir=tmp_path / "generated" / "uploads",
        banner_dir=tmp_path / "generated" / "banners",
        background_dir=tmp_path / "generated" / "backgrounds",
        static_dir=tmp_path / "static",
        templates_dir=tmp_path / "templates",
    )
    settings.ensure_runtime_directories()
    form = GENERATION_EVAL_CASES[0].form
    result = await MockCopyGenerator().generate(form)

    asset = await BackgroundGenerator(settings).prepare(form, result)

    assert asset.provider == "sd35"
    assert asset.status == "skipped"
    assert "SD35_ENDPOINT_URL" in (asset.note or "")


@pytest.mark.asyncio
async def test_background_generator_sd35_provider_uses_explicit_opt_in(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    async def fake_generate(self, prompt: str) -> str:
        assert "Stable Diffusion 3.5 Large FP8" in prompt
        return "/static/generated/backgrounds/sd35-test.png"

    monkeypatch.setattr(BackgroundGenerator, "_generate_with_sd35", fake_generate)
    settings = Settings(
        copy_provider="mock",
        image_provider="sd35",
        sd35_endpoint_url="http://127.0.0.1:8188/sd35",
        allow_paid_image_generation=True,
        data_dir=tmp_path / "data",
        generated_dir=tmp_path / "generated",
        upload_dir=tmp_path / "generated" / "uploads",
        banner_dir=tmp_path / "generated" / "banners",
        background_dir=tmp_path / "generated" / "backgrounds",
        static_dir=tmp_path / "static",
        templates_dir=tmp_path / "templates",
    )
    settings.ensure_runtime_directories()
    form = GENERATION_EVAL_CASES[0].form
    result = await MockCopyGenerator().generate(form)

    asset = await BackgroundGenerator(settings).prepare(form, result)

    assert asset.provider == "sd35"
    assert asset.status == "generated"
    assert asset.image_path == "/static/generated/backgrounds/sd35-test.png"


@pytest.mark.asyncio
async def test_background_generator_sd35_does_not_require_paid_opt_in(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    async def fake_generate(self, prompt: str) -> str:
        return "/static/generated/backgrounds/local-sd35-test.png"

    monkeypatch.setattr(BackgroundGenerator, "_generate_with_sd35", fake_generate)
    settings = Settings(
        copy_provider="mock",
        image_provider="sd35",
        sd35_endpoint_url="http://127.0.0.1:8188/sd35",
        allow_paid_image_generation=False,
        data_dir=tmp_path / "data",
        generated_dir=tmp_path / "generated",
        upload_dir=tmp_path / "generated" / "uploads",
        banner_dir=tmp_path / "generated" / "banners",
        background_dir=tmp_path / "generated" / "backgrounds",
        static_dir=tmp_path / "static",
        templates_dir=tmp_path / "templates",
    )
    settings.ensure_runtime_directories()
    form = GENERATION_EVAL_CASES[0].form
    result = await MockCopyGenerator().generate(form)

    asset = await BackgroundGenerator(settings).prepare(form, result)

    assert asset.provider == "sd35"
    assert asset.status == "generated"
    assert asset.image_path == "/static/generated/backgrounds/local-sd35-test.png"


@pytest.mark.asyncio
async def test_background_generator_sd35_uses_embedded_wrapper_when_local_endpoint_is_down(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    async def fake_post(self, *args, **kwargs):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    def fake_embedded(self, payload: dict[str, object]) -> bytes:
        buffer = BytesIO()
        Image.new("RGB", (32, 32), "#d07a5c").save(buffer, format="PNG")
        return buffer.getvalue()

    monkeypatch.setattr(
        BackgroundGenerator,
        "_generate_with_embedded_sd35_wrapper",
        fake_embedded,
    )
    settings = Settings(
        copy_provider="mock",
        image_provider="sd35",
        sd35_endpoint_url="http://127.0.0.1:8188/sd35/generate",
        sd35_fallback_to_local=True,
        allow_paid_image_generation=False,
        data_dir=tmp_path / "data",
        generated_dir=tmp_path / "generated",
        upload_dir=tmp_path / "generated" / "uploads",
        banner_dir=tmp_path / "generated" / "banners",
        background_dir=tmp_path / "generated" / "backgrounds",
        static_dir=tmp_path / "static",
        templates_dir=tmp_path / "templates",
    )
    settings.ensure_runtime_directories()
    form = GENERATION_EVAL_CASES[0].form
    result = await MockCopyGenerator().generate(form)

    asset = await BackgroundGenerator(settings).prepare(form, result)

    assert asset.provider == "sd35"
    assert asset.status == "generated"
    assert asset.image_path is not None
    output_path = settings.background_dir / asset.image_path.rsplit("/", 1)[-1]
    assert output_path.exists()


@pytest.mark.asyncio
async def test_background_generator_sd35_falls_back_to_local_image(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    async def fake_generate(self, prompt: str) -> str:
        raise RuntimeError("local sd35 server is not running")

    monkeypatch.setattr(BackgroundGenerator, "_generate_with_sd35", fake_generate)
    settings = Settings(
        copy_provider="mock",
        image_provider="sd35",
        sd35_endpoint_url="http://127.0.0.1:8188/sd35",
        sd35_fallback_to_local=True,
        allow_paid_image_generation=False,
        data_dir=tmp_path / "data",
        generated_dir=tmp_path / "generated",
        upload_dir=tmp_path / "generated" / "uploads",
        banner_dir=tmp_path / "generated" / "banners",
        background_dir=tmp_path / "generated" / "backgrounds",
        static_dir=tmp_path / "static",
        templates_dir=tmp_path / "templates",
    )
    settings.ensure_runtime_directories()
    form = GENERATION_EVAL_CASES[0].form
    result = await MockCopyGenerator().generate(form)

    asset = await BackgroundGenerator(settings).prepare(form, result)

    assert asset.provider == "sd35-local-fallback"
    assert asset.status == "generated_fallback"
    assert asset.image_path is not None
    output_path = settings.background_dir / asset.image_path.rsplit("/", 1)[-1]
    assert output_path.exists()


@pytest.mark.asyncio
async def test_background_generator_sd35_extracts_base64_image(tmp_path):
    settings = Settings(
        copy_provider="mock",
        image_provider="sd35",
        sd35_endpoint_url="http://127.0.0.1:8188/sd35",
        allow_paid_image_generation=True,
        data_dir=tmp_path / "data",
        generated_dir=tmp_path / "generated",
        upload_dir=tmp_path / "generated" / "uploads",
        banner_dir=tmp_path / "generated" / "banners",
        background_dir=tmp_path / "generated" / "backgrounds",
        static_dir=tmp_path / "static",
        templates_dir=tmp_path / "templates",
    )
    settings.ensure_runtime_directories()
    generator = BackgroundGenerator(settings)
    buffer = BytesIO()
    Image.new("RGB", (16, 16), "#c85f3f").save(buffer, format="PNG")

    image_bytes = await generator._extract_sd35_image_bytes(
        {"data": [{"b64_json": base64.b64encode(buffer.getvalue()).decode("utf-8")}]},
        client=None,
    )

    assert image_bytes.startswith(b"\x89PNG")


@pytest.mark.asyncio
async def test_background_generator_sd35_omits_tensorrt_model_for_local_wrapper(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    captured_json: dict[str, object] = {}

    class FakeResponse:
        headers = {"content-type": "application/json"}

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            buffer = BytesIO()
            Image.new("RGB", (16, 16), "#c85f3f").save(buffer, format="PNG")
            return {"data": [{"b64_json": base64.b64encode(buffer.getvalue()).decode("utf-8")}]}

    async def fake_post(self, url, json, headers):
        captured_json.update(json)
        return FakeResponse()

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    settings = Settings(
        copy_provider="mock",
        image_provider="sd35",
        sd35_endpoint_url="http://127.0.0.1:8188/sd35/generate",
        sd35_model="stabilityai/stable-diffusion-3.5-large-tensorrt",
        allow_paid_image_generation=False,
        data_dir=tmp_path / "data",
        generated_dir=tmp_path / "generated",
        upload_dir=tmp_path / "generated" / "uploads",
        banner_dir=tmp_path / "generated" / "banners",
        background_dir=tmp_path / "generated" / "backgrounds",
        static_dir=tmp_path / "static",
        templates_dir=tmp_path / "templates",
    )
    settings.ensure_runtime_directories()
    generator = BackgroundGenerator(settings)

    image_path = await generator._generate_with_sd35("warm bakery hero image")

    assert image_path.startswith("/static/generated/backgrounds/background-")
    assert "model" not in captured_json


def test_background_generator_sd35_request_model_keeps_non_tensorrt_value(tmp_path):
    settings = Settings(
        sd35_endpoint_url="http://127.0.0.1:8188/sd35/generate",
        sd35_model="stabilityai/stable-diffusion-3.5-medium",
        data_dir=tmp_path / "data",
        generated_dir=tmp_path / "generated",
        upload_dir=tmp_path / "generated" / "uploads",
        banner_dir=tmp_path / "generated" / "banners",
        background_dir=tmp_path / "generated" / "backgrounds",
        static_dir=tmp_path / "static",
        templates_dir=tmp_path / "templates",
    )

    assert BackgroundGenerator(settings)._resolve_sd35_request_model() == (
        "stabilityai/stable-diffusion-3.5-medium"
    )
