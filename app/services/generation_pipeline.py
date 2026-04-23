from app.config import Settings
from app.schemas.form import AdGenerationForm
from app.schemas.result import GenerationResult
from app.services.copy_generator import build_copy_generator


MIN_CHANNEL_SCORE = 80
MIN_OVERALL_SCORE = 82

class AutoGenerationPipeline:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def generate_until_pass(self, form_data: AdGenerationForm) -> GenerationResult:
        generator = build_copy_generator(self.settings)
        best_result: GenerationResult | None = None

        max_attempts = max(1, self.settings.max_generation_attempts)
        for attempt in range(1, max_attempts + 1):
            result = await generator.generate(form_data)
            result = self._with_decision(result, attempt)
            if best_result is None or self._score(result) > self._score(best_result):
                best_result = result
            if result.auto_approved:
                return result

        if best_result is None:
            raise RuntimeError("generation failed without a result")
        return self._with_decision(best_result, max_attempts)

    def _with_decision(self, result: GenerationResult, attempt: int) -> GenerationResult:
        failed_channels = self._failed_channels(result)
        auto_approved = (
            not failed_channels
            and result.quality_report.overall_score >= MIN_OVERALL_SCORE
        )
        channel_quality = result.channel_quality.model_copy(
            update={"failed_channels": failed_channels}
        )
        suggestions = list(channel_quality.regeneration_suggestions)
        if failed_channels and len(suggestions) < 2:
            suggestions.extend(
                [
                    "점수가 낮은 채널의 문체와 CTA를 더 분명하게 조정하세요.",
                    "채널별 목적에 맞게 길이와 정보량을 다시 조정하세요.",
                ]
            )
            channel_quality = channel_quality.model_copy(
                update={"regeneration_suggestions": suggestions[:5]}
            )
        return result.model_copy(
            update={
                "channel_quality": channel_quality,
                "generation_attempts": attempt,
                "auto_approved": auto_approved,
            }
        )

    def _failed_channels(self, result: GenerationResult) -> list[str]:
        scores = {
            "instagram": result.channel_quality.instagram_score,
            "threads": result.channel_quality.threads_score,
            "blog": result.channel_quality.blog_score,
        }
        return [
            channel
            for channel, score in scores.items()
            if score < MIN_CHANNEL_SCORE
        ]

    def _score(self, result: GenerationResult) -> int:
        return round(
            (
                result.channel_quality.instagram_score
                + result.channel_quality.threads_score
                + result.channel_quality.blog_score
                + result.quality_report.overall_score
            )
            / 4
        )
