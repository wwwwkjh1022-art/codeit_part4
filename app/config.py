from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # For this local MVP, .env is the source of truth. This prevents an old
        # exported shell variable from overriding a newly issued API key.
        return init_settings, dotenv_settings, env_settings, file_secret_settings

    app_name: str = "Ad Copy Studio"
    environment: str = "development"
    public_base_url: str = "http://127.0.0.1:8000"
    copy_provider: str = "auto"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5-mini"
    openai_reasoning_effort: str = "medium"
    max_generation_attempts: int = 1
    huggingface_api_key: str | None = None
    image_provider: str = "prompt_only"
    gemini_api_key: str | None = None
    gemini_image_model: str = "gemini-2.5-flash-image"
    openai_image_model: str = "gpt-image-1-mini"
    openai_image_quality: str = "low"
    sd35_api_key: str | None = None
    sd35_endpoint_url: str | None = None
    sd35_model: str = "stabilityai/stable-diffusion-3.5-large-tensorrt"
    sd35_width: int = 1536
    sd35_height: int = 1024
    sd35_steps: int = 28
    sd35_guidance_scale: float = 3.5
    sd35_request_timeout_seconds: int = 1800
    sd35_fallback_to_local: bool = True
    allow_paid_image_generation: bool = False
    max_upload_size_mb: int = 10
    allowed_image_extensions: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".webp")
    base_dir: Path = Field(default=BASE_DIR)
    static_dir: Path = Field(default=BASE_DIR / "app" / "static")
    templates_dir: Path = Field(default=BASE_DIR / "app" / "templates")
    generated_dir: Path = Field(default=BASE_DIR / "app" / "static" / "generated")
    upload_dir: Path = Field(default=BASE_DIR / "app" / "static" / "generated" / "uploads")
    banner_dir: Path = Field(default=BASE_DIR / "app" / "static" / "generated" / "banners")
    background_dir: Path = Field(
        default=BASE_DIR / "app" / "static" / "generated" / "backgrounds"
    )
    data_dir: Path = Field(default=BASE_DIR / "data")
    campaign_store_path: Path = Field(default=BASE_DIR / "data" / "campaigns.json")
    default_font_path: Path = Field(
        default=Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf")
    )

    @property
    def resolved_copy_provider(self) -> str:
        if self.copy_provider != "auto":
            return self.copy_provider
        if self.openai_api_key:
            return "openai"
        return "mock"

    @property
    def resolved_image_provider(self) -> str:
        if self.image_provider == "auto":
            if self.sd35_endpoint_url:
                return "sd35"
            if self.openai_api_key and self.allow_paid_image_generation:
                return "openai"
            if self.gemini_api_key and self.allow_paid_image_generation:
                return "gemini"
            return "prompt_only"
        return self.image_provider

    def ensure_runtime_directories(self) -> None:
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.banner_dir.mkdir(parents=True, exist_ok=True)
        self.background_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_runtime_directories()
    return settings
