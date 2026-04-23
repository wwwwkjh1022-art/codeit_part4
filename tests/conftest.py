import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.main import create_app
from app.services.background_generator import BackgroundGenerator


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    async def fake_openai_background(self: BackgroundGenerator, prompt: str) -> str:
        self.settings.background_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.settings.background_dir / "test-openai-background.png"
        Image.new("RGB", (1536, 1024), "#f2c7a6").save(output_path)
        return "/static/generated/backgrounds/test-openai-background.png"

    monkeypatch.setenv("COPY_PROVIDER", "mock")
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("CAMPAIGN_STORE_PATH", str(tmp_path / "data" / "campaigns.json"))
    monkeypatch.setattr(BackgroundGenerator, "_generate_with_openai", fake_openai_background)
    get_settings.cache_clear()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()
