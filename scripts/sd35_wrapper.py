import base64
import logging
import os
from functools import lru_cache
from io import BytesIO

from fastapi import FastAPI
from pydantic import BaseModel, Field
from PIL import Image, ImageDraw, ImageFilter
from dotenv import load_dotenv


load_dotenv()
logger = logging.getLogger(__name__)


class SD35GenerateRequest(BaseModel):
    model: str | None = None
    prompt: str
    negative_prompt: str = ""
    width: int = Field(default=1536, ge=256, le=2048)
    height: int = Field(default=1024, ge=256, le=2048)
    num_inference_steps: int = Field(default=28, ge=1, le=80)
    guidance_scale: float = Field(default=3.5, ge=0.0, le=20.0)
    response_format: str = "b64_json"


app = FastAPI(title="Local SD3.5 Wrapper")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {
        "status": "ok",
        "backend": _backend(),
        "model": _model_id(),
    }


@app.post("/sd35/generate")
def generate_image(payload: SD35GenerateRequest) -> dict[str, object]:
    if _backend() == "diffusers":
        image = _generate_with_diffusers(payload)
        provider = "sd35-diffusers"
    else:
        image = _generate_fallback_image(payload)
        provider = "sd35-wrapper-fallback"

    buffer = BytesIO()
    image.convert("RGB").save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return {
        "provider": provider,
        "model": _resolve_diffusers_model_id(payload.model),
        "data": [{"b64_json": encoded}],
    }


def _backend() -> str:
    return os.getenv("SD35_WRAPPER_BACKEND", "fallback").strip().lower()


def _model_id() -> str:
    return os.getenv("SD35_DIFFUSERS_MODEL_ID", "stabilityai/sdxl-turbo")


def _fallback_model_id() -> str:
    return os.getenv("SD35_FALLBACK_DIFFUSERS_MODEL_ID", "stabilityai/sdxl-turbo")


def _resolve_diffusers_model_id(requested_model_id: str | None) -> str:
    configured_model_id = _model_id().strip()
    model_id = (requested_model_id or "").strip()
    if not model_id:
        return configured_model_id
    if "tensorrt" in model_id.lower():
        return _model_id()
    return model_id


def _generate_with_diffusers(payload: SD35GenerateRequest) -> Image.Image:
    model_id = _resolve_diffusers_model_id(payload.model)
    pipe = _load_pipeline(model_id)
    width, height = _normalize_dimensions(payload.width, payload.height, model_id)
    num_inference_steps, guidance_scale = _normalize_inference_config(
        payload.num_inference_steps,
        payload.guidance_scale,
        model_id,
    )
    image = pipe(
        prompt=payload.prompt,
        negative_prompt=payload.negative_prompt,
        width=width,
        height=height,
        num_inference_steps=num_inference_steps,
        guidance_scale=guidance_scale,
    ).images[0]
    return image


@lru_cache(maxsize=1)
def _load_pipeline(model_id: str):
    try:
        import torch
        from diffusers import AutoPipelineForText2Image
        from huggingface_hub.errors import GatedRepoError
    except ImportError as exc:
        raise RuntimeError(
            "diffusers backend requires torch and diffusers. "
            "Install optional SD3.5 dependencies first."
        ) from exc

    device = os.getenv("SD35_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
    dtype_name = os.getenv("SD35_TORCH_DTYPE", "float16")
    dtype = {
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "float32": torch.float32,
    }.get(dtype_name, torch.bfloat16)

    try:
        pipe = AutoPipelineForText2Image.from_pretrained(model_id, torch_dtype=dtype)
    except GatedRepoError:
        fallback_model_id = _fallback_model_id()
        if fallback_model_id == model_id:
            raise
        logger.warning(
            "Requested model %s is gated. Falling back to %s.",
            model_id,
            fallback_model_id,
        )
        pipe = AutoPipelineForText2Image.from_pretrained(
            fallback_model_id,
            torch_dtype=dtype,
        )

    if hasattr(pipe, "enable_attention_slicing"):
        pipe.enable_attention_slicing()
    if hasattr(pipe, "enable_vae_slicing"):
        pipe.enable_vae_slicing()

    cpu_offload = os.getenv("SD35_ENABLE_CPU_OFFLOAD", "true").lower() == "true"
    if cpu_offload:
        pipe.enable_model_cpu_offload()
    elif device == "cuda":
        pipe = pipe.to("cuda")
    else:
        pipe = pipe.to(device)
    return pipe


def _normalize_dimensions(
    width: int,
    height: int,
    model_id: str,
) -> tuple[int, int]:
    model_name = model_id.lower()
    max_edge = 1024 if "sdxl-turbo" in model_name else 1536
    longest = max(width, height)
    if longest <= max_edge:
        return _round_to_64(width), _round_to_64(height)

    ratio = max_edge / longest
    scaled_width = max(512, int(width * ratio))
    scaled_height = max(512, int(height * ratio))
    return _round_to_64(scaled_width), _round_to_64(scaled_height)


def _normalize_inference_config(
    num_inference_steps: int,
    guidance_scale: float,
    model_id: str,
) -> tuple[int, float]:
    model_name = model_id.lower()
    if "sdxl-turbo" in model_name:
        return min(num_inference_steps, 4), min(guidance_scale, 2.0)
    return num_inference_steps, guidance_scale


def _round_to_64(value: int) -> int:
    return max(512, int(round(value / 64)) * 64)


def _generate_fallback_image(payload: SD35GenerateRequest) -> Image.Image:
    width, height = payload.width, payload.height
    base = (247, 238, 225)
    wash = (238, 205, 170)
    accent = (211, 98, 64)
    warm = (248, 186, 119)
    cool = (141, 160, 151)

    image = Image.new("RGB", (width, height), base)
    draw = ImageDraw.Draw(image, "RGBA")

    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = tuple(round(base[i] * (1 - ratio) + wash[i] * ratio) for i in range(3))
        draw.line([(0, y), (width, y)], fill=color)

    draw.ellipse(
        [int(width * 0.58), -int(height * 0.22), int(width * 1.10), int(height * 0.58)],
        fill=(*accent, 82),
    )
    draw.ellipse(
        [int(width * 0.54), int(height * 0.50), int(width * 1.05), int(height * 1.14)],
        fill=(*warm, 112),
    )
    draw.ellipse(
        [-int(width * 0.14), int(height * 0.58), int(width * 0.34), int(height * 1.06)],
        fill=(*cool, 74),
    )
    draw.rounded_rectangle(
        [int(width * 0.58), int(height * 0.24), int(width * 0.86), int(height * 0.66)],
        radius=max(26, int(width * 0.035)),
        fill=(255, 249, 242, 188),
    )

    plate = [int(width * 0.14), int(height * 0.22), int(width * 0.52), int(height * 0.64)]
    draw.ellipse(plate, fill=(255, 255, 251, 225))
    inset = int(width * 0.028)
    draw.ellipse(
        [plate[0] + inset, plate[1] + inset, plate[2] - inset, plate[3] - inset],
        outline=(*accent, 115),
        width=max(4, int(width * 0.004)),
    )

    for index in range(7):
        x = int(width * (0.23 + 0.045 * index))
        y = int(height * (0.34 + 0.045 * (index % 2)))
        radius = int(width * 0.022)
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=(*accent, 184))

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay, "RGBA")
    overlay_draw.rectangle([0, 0, int(width * 0.54), height], fill=(255, 250, 244, 140))
    return Image.alpha_composite(image.convert("RGBA"), overlay).filter(
        ImageFilter.GaussianBlur(radius=0.25)
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "scripts.sd35_wrapper:app",
        host=os.getenv("SD35_WRAPPER_HOST", "127.0.0.1"),
        port=int(os.getenv("SD35_WRAPPER_PORT", "8188")),
        reload=False,
    )
