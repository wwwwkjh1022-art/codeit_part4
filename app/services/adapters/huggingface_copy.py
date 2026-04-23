from app.schemas.form import AdGenerationForm
from app.schemas.result import GenerationResult


class HuggingFaceCopyGenerator:
    async def generate(self, form_data: AdGenerationForm) -> GenerationResult:
        raise NotImplementedError(
            "Hugging Face adapter is reserved for the next iteration. "
            "Use COPY_PROVIDER=mock or OPENAI_API_KEY for now."
        )
