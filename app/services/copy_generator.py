from abc import ABC, abstractmethod

from app.config import Settings
from app.schemas.form import AdGenerationForm
from app.schemas.result import GenerationResult
from app.services.adapters.huggingface_copy import HuggingFaceCopyGenerator
from app.services.adapters.mock_copy import MockCopyGenerator
from app.services.adapters.openai_copy import OpenAICopyGenerator


class CopyGenerator(ABC):
    @abstractmethod
    async def generate(self, form_data: AdGenerationForm) -> GenerationResult:
        raise NotImplementedError


def build_copy_generator(settings: Settings) -> CopyGenerator:
    provider = settings.resolved_copy_provider

    if provider == "openai":
        return OpenAICopyGenerator(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            reasoning_effort=settings.openai_reasoning_effort,
        )

    if provider == "huggingface":
        return HuggingFaceCopyGenerator()

    return MockCopyGenerator()

