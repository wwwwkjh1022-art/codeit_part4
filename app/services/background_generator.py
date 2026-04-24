import base64
from io import BytesIO
from urllib.parse import urlparse
from uuid import uuid4

import httpx
from PIL import Image, ImageDraw, ImageFilter

from app.config import Settings
from app.schemas.form import AdGenerationForm
from app.schemas.result import BackgroundAsset, GenerationResult


class BackgroundGenerator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def prepare(
        self,
        form_data: AdGenerationForm,
        result: GenerationResult,
    ) -> BackgroundAsset:
        prompt = self._build_prompt(form_data, result)
        provider = self.settings.resolved_image_provider

        if provider not in {"gemini", "openai", "sd35"}:
            return BackgroundAsset(
                prompt=prompt,
                provider="prompt_only",
                status="prompt_ready",
                note="이미지 생성 API를 끄면 이 프롬프트를 복사해 외부 이미지 도구에서 배경을 만들 수 있습니다.",
            )

        if provider == "openai" and not self.settings.openai_api_key:
            return BackgroundAsset(
                prompt=prompt,
                provider="openai",
                status="skipped",
                note="OPENAI_API_KEY가 없어 프롬프트만 준비했습니다.",
            )

        if provider == "gemini" and not self.settings.gemini_api_key:
            return BackgroundAsset(
                prompt=prompt,
                provider="gemini",
                status="skipped",
                note="GEMINI_API_KEY가 없어 프롬프트만 준비했습니다.",
            )

        if provider == "sd35" and not self.settings.sd35_endpoint_url:
            return BackgroundAsset(
                prompt=prompt,
                provider="sd35",
                status="skipped",
                note="SD35_ENDPOINT_URL이 없어 프롬프트만 준비했습니다.",
            )

        if provider in {"openai", "gemini"} and not self.settings.allow_paid_image_generation:
            return BackgroundAsset(
                prompt=prompt,
                provider=provider,
                status="skipped",
                note=(
                    "비용 방지를 위해 이미지 API 호출을 막았습니다. "
                    "나중에 ALLOW_PAID_IMAGE_GENERATION=true로 켜면 자동 생성됩니다."
                ),
            )

        try:
            if provider == "openai":
                image_path = await self._generate_with_openai(prompt)
            elif provider == "sd35":
                image_path = await self._generate_with_sd35(prompt)
            else:
                image_path = await self._generate_with_gemini(prompt)
        except Exception as exc:
            if provider == "sd35" and self.settings.sd35_fallback_to_local:
                image_path = self._generate_local_fallback(form_data, result)
                return BackgroundAsset(
                    prompt=prompt,
                    provider="sd35-local-fallback",
                    status="generated_fallback",
                    image_path=image_path,
                    note=(
                        "SD3.5 로컬 엔드포인트 연결에 실패해 앱 내부 로컬 배경 생성기로 대체했습니다. "
                        f"원인: {exc}"
                    ),
                )
            return BackgroundAsset(
                prompt=prompt,
                provider=provider,
                status="failed",
                note=f"{provider} 이미지 생성에 실패해 프롬프트만 유지했습니다: {exc}",
            )

        return BackgroundAsset(
            prompt=prompt,
            provider=provider,
            status="generated",
            image_path=image_path,
            note=f"{provider} API로 생성한 배경 이미지를 배너 합성에 사용했습니다.",
        )

    async def _generate_with_openai(self, prompt: str) -> str:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise RuntimeError("openai 패키지가 설치되어 있지 않습니다.") from exc

        client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        response = await client.images.generate(
            model=self.settings.openai_image_model,
            prompt=prompt,
            size="1536x1024",
            quality=self.settings.openai_image_quality,
            n=1,
        )
        image_base64 = response.data[0].b64_json
        if not image_base64:
            raise RuntimeError("OpenAI 응답에서 이미지 데이터를 찾지 못했습니다.")

        image = Image.open(BytesIO(base64.b64decode(image_base64))).convert("RGB")
        output_path = self.settings.background_dir / f"background-{uuid4().hex}.png"
        image.save(output_path)
        return f"/static/generated/backgrounds/{output_path.name}"

    def _generate_local_fallback(
        self,
        form_data: AdGenerationForm,
        result: GenerationResult,
    ) -> str:
        width = self.settings.sd35_width
        height = self.settings.sd35_height
        palette = self._fallback_palette(form_data.visual_style)
        image = Image.new("RGB", (width, height), palette["base"])
        draw = ImageDraw.Draw(image, "RGBA")

        for y in range(height):
            ratio = y / max(height - 1, 1)
            color = tuple(
                round(palette["base"][index] * (1 - ratio) + palette["wash"][index] * ratio)
                for index in range(3)
            )
            draw.line([(0, y), (width, y)], fill=color)

        # Soft editorial blobs create a product-photography-like composition without text.
        draw.ellipse(
            [int(width * 0.58), -int(height * 0.18), int(width * 1.08), int(height * 0.58)],
            fill=(*palette["accent"], 86),
        )
        draw.ellipse(
            [int(width * 0.55), int(height * 0.50), int(width * 1.05), int(height * 1.14)],
            fill=(*palette["warm"], 110),
        )
        draw.ellipse(
            [-int(width * 0.16), int(height * 0.54), int(width * 0.32), int(height * 1.08)],
            fill=(*palette["cool"], 72),
        )

        card = [
            int(width * 0.58),
            int(height * 0.22),
            int(width * 0.86),
            int(height * 0.66),
        ]
        draw.rounded_rectangle(card, radius=int(width * 0.035), fill=(255, 248, 240, 190))

        plate_box = [
            int(width * 0.16),
            int(height * 0.24),
            int(width * 0.51),
            int(height * 0.64),
        ]
        draw.ellipse(plate_box, fill=(255, 255, 252, 225))
        inset = int(width * 0.025)
        draw.ellipse(
            [plate_box[0] + inset, plate_box[1] + inset, plate_box[2] - inset, plate_box[3] - inset],
            outline=(*palette["accent"], 115),
            width=max(4, int(width * 0.004)),
        )

        for index, keyword in enumerate(form_data.keyword_list[:5] or [form_data.product_name]):
            x = int(width * (0.22 + 0.055 * index))
            y = int(height * (0.35 + 0.035 * (index % 2)))
            radius = int(width * 0.025)
            draw.ellipse(
                [x - radius, y - radius, x + radius, y + radius],
                fill=(*palette["accent"], 190),
            )

        for index in range(18):
            x = int(width * (0.08 + 0.045 * index))
            y = int(height * (0.78 + 0.025 * (index % 3)))
            draw.line(
                [(x, y), (x + int(width * 0.08), y - int(height * 0.04))],
                fill=(255, 255, 255, 34),
                width=max(2, int(width * 0.002)),
            )

        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay, "RGBA")
        overlay_draw.rectangle([0, 0, int(width * 0.54), height], fill=(255, 250, 244, 142))
        image = Image.alpha_composite(image.convert("RGBA"), overlay).filter(
            ImageFilter.GaussianBlur(radius=0.25)
        )

        output_path = self.settings.background_dir / f"background-local-{uuid4().hex}.png"
        image.convert("RGB").save(output_path)
        return f"/static/generated/backgrounds/{output_path.name}"

    def _fallback_palette(self, visual_style: str) -> dict[str, tuple[int, int, int]]:
        if "프리미엄" in visual_style:
            return {
                "base": (35, 31, 28),
                "wash": (219, 200, 176),
                "accent": (194, 145, 86),
                "warm": (236, 200, 145),
                "cool": (98, 119, 120),
            }
        if "미니멀" in visual_style:
            return {
                "base": (238, 237, 231),
                "wash": (203, 213, 210),
                "accent": (129, 153, 147),
                "warm": (230, 205, 176),
                "cool": (173, 190, 187),
            }
        if "강한" in visual_style or "세일" in visual_style:
            return {
                "base": (255, 239, 219),
                "wash": (255, 178, 118),
                "accent": (219, 83, 54),
                "warm": (255, 199, 119),
                "cool": (88, 121, 151),
            }
        return {
            "base": (250, 241, 229),
            "wash": (246, 213, 181),
            "accent": (211, 102, 67),
            "warm": (245, 190, 127),
            "cool": (151, 169, 153),
        }

    async def _generate_with_gemini(self, prompt: str) -> str:
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError(
                "google-genai가 설치되어 있지 않습니다. requirements.txt 설치 후 다시 시도하세요."
            ) from exc

        client = genai.Client(api_key=self.settings.gemini_api_key)
        response = client.models.generate_content(
            model=self.settings.gemini_image_model,
            contents=[prompt],
        )

        for part in response.candidates[0].content.parts:
            if getattr(part, "inline_data", None) is None:
                continue
            image = Image.open(BytesIO(part.inline_data.data)).convert("RGB")
            output_path = self.settings.background_dir / f"background-{uuid4().hex}.png"
            image.save(output_path)
            return f"/static/generated/backgrounds/{output_path.name}"

        raise RuntimeError("Gemini 응답에서 이미지 데이터를 찾지 못했습니다.")

    async def _generate_with_sd35(self, prompt: str) -> str:
        if not self.settings.sd35_endpoint_url:
            raise RuntimeError("SD35_ENDPOINT_URL이 설정되어 있지 않습니다.")

        payload: dict[str, object] = {
            "prompt": prompt,
            "negative_prompt": (
                "readable text, logo, watermark, fake interface, distorted typography, "
                "extra fingers, deformed objects, low quality, blurry, noisy"
            ),
            "width": self.settings.sd35_width,
            "height": self.settings.sd35_height,
            "num_inference_steps": self.settings.sd35_steps,
            "guidance_scale": self.settings.sd35_guidance_scale,
            "response_format": "b64_json",
        }
        request_model = self._resolve_sd35_request_model()
        if request_model:
            payload["model"] = request_model
        headers = {"Accept": "application/json, image/png, image/jpeg"}
        if self.settings.sd35_api_key:
            headers["Authorization"] = f"Bearer {self.settings.sd35_api_key}"

        async with httpx.AsyncClient(timeout=self.settings.sd35_request_timeout_seconds) as client:
            try:
                response = await client.post(
                    self.settings.sd35_endpoint_url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()

                content_type = response.headers.get("content-type", "")
                if content_type.startswith("image/"):
                    image_bytes = response.content
                else:
                    image_bytes = await self._extract_sd35_image_bytes(response.json(), client)
            except httpx.HTTPError:
                if not self._is_local_sd35_endpoint():
                    raise
                image_bytes = self._generate_with_embedded_sd35_wrapper(payload)

        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        output_path = self.settings.background_dir / f"background-{uuid4().hex}.png"
        image.save(output_path)
        return f"/static/generated/backgrounds/{output_path.name}"

    def _resolve_sd35_request_model(self) -> str | None:
        model = (self.settings.sd35_model or "").strip()
        if not model:
            return None
        if self._is_local_sd35_endpoint() and "tensorrt" in model.lower():
            return None
        return model

    def _is_local_sd35_endpoint(self) -> bool:
        if not self.settings.sd35_endpoint_url:
            return False
        parsed = urlparse(self.settings.sd35_endpoint_url)
        return parsed.hostname in {"127.0.0.1", "localhost", "0.0.0.0"}

    def _generate_with_embedded_sd35_wrapper(self, payload: dict[str, object]) -> bytes:
        try:
            from scripts.sd35_wrapper import SD35GenerateRequest, generate_image
        except ImportError as exc:
            raise RuntimeError(
                "로컬 SD3.5 wrapper를 불러오지 못했습니다. scripts/sd35_wrapper.py를 확인하세요."
            ) from exc

        response_payload = generate_image(SD35GenerateRequest(**payload))
        image_base64 = None
        data = response_payload.get("data")
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict):
                image_base64 = first.get("b64_json") or first.get("base64")

        if not image_base64:
            raise RuntimeError(
                "내장 SD3.5 wrapper 응답에서 이미지 데이터를 찾지 못했습니다."
            )

        return base64.b64decode(image_base64)

    async def _extract_sd35_image_bytes(
        self,
        payload: dict,
        client: httpx.AsyncClient,
    ) -> bytes:
        image_base64 = (
            payload.get("image_base64")
            or payload.get("b64_json")
            or payload.get("image")
            or payload.get("base64")
        )

        data = payload.get("data")
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict):
                image_base64 = image_base64 or first.get("b64_json") or first.get("base64")
                image_url = first.get("url") or first.get("image_url")
            else:
                image_url = None
        else:
            image_url = payload.get("image_url") or payload.get("url")

        if image_base64:
            if "," in image_base64 and image_base64.startswith("data:"):
                image_base64 = image_base64.split(",", 1)[1]
            return base64.b64decode(image_base64)

        if image_url:
            response = await client.get(image_url)
            response.raise_for_status()
            return response.content

        raise RuntimeError(
            "SD3.5 응답에서 이미지 데이터를 찾지 못했습니다. "
            "image_base64, b64_json, data[0].b64_json, image_url 중 하나가 필요합니다."
        )

    def _build_prompt(
        self,
        form_data: AdGenerationForm,
        result: GenerationResult,
    ) -> str:
        keywords = ", ".join(form_data.keyword_list[:5]) if form_data.keyword_list else "local business"
        poster = result.channel_packages.poster
        visual_hook = result.channel_packages.instagram.visual_hook
        return (
            "Create a premium Pinterest-worthy social ad background for a Korean small business. "
            "Stable Diffusion 3.5 Large FP8 / TensorRT friendly prompt. "
            "Modern 2026 Instagram campaign aesthetic: editorial product photography, refined composition, "
            "soft natural light, tactile materials, layered depth, tasteful negative space, brand campaign mood. "
            "No readable text, no logos, no watermark, no fake UI, no people with identifiable faces. "
            "Leave clean negative space for Korean headline and CTA overlays. "
            f"Business category: {form_data.business_category}. "
            f"Brand mood: {form_data.visual_style}, {form_data.tone}. "
            f"Product or service: {form_data.product_name}. "
            f"Campaign goal: {form_data.promotion_goal}, desired action: {form_data.desired_action}. "
            f"Visual hook: {visual_hook}. "
            f"Poster direction: {poster.visual_direction}. "
            f"Keywords: {keywords}. "
            "Aspect ratio 3:2 or 1.91:1, high-end commercial still life, polished but realistic, "
            "not a flat template, not clipart, not generic stock."
        )
