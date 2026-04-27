from pathlib import Path
from textwrap import wrap
from uuid import uuid4

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from app.config import Settings
from app.schemas.form import AdGenerationForm
from app.schemas.result import GenerationResult


class BannerGenerator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create_preview(
        self,
        form_data: AdGenerationForm,
        result: GenerationResult,
        uploaded_image_path: str | None = None,
        background_image_path: str | None = None,
    ) -> str:
        theme = self._select_theme(form_data.visual_style)
        width, height = 1200, 628
        has_uploaded_reference = self._has_uploaded_reference(uploaded_image_path)
        image = self._create_base_image(
            width=width,
            height=height,
            theme=theme,
            background_image_path=background_image_path,
            uploaded_image_path=uploaded_image_path,
        )

        if has_uploaded_reference:
            self._apply_photo_showcase_finish(image)
        else:
            draw = ImageDraw.Draw(image)
            self._apply_readability_layers(
                image,
                theme,
                has_photo=bool(background_image_path or uploaded_image_path),
            )
            self._draw_campaign_copy(draw, form_data, result, theme)
            self._draw_brand_marks(draw, form_data, result, theme, width, height)

        output_path = self.settings.banner_dir / f"banner-{uuid4().hex}.png"
        image.convert("RGB").save(output_path, quality=94)
        return f"/static/generated/banners/{output_path.name}"

    def _create_base_image(
        self,
        width: int,
        height: int,
        theme: dict[str, str],
        background_image_path: str | None,
        uploaded_image_path: str | None,
    ) -> Image.Image:
        uploaded_path = self._resolve_static_path(uploaded_image_path)
        background_path = self._resolve_static_path(background_image_path)

        if uploaded_path and uploaded_path.exists():
            with Image.open(uploaded_path).convert("RGBA") as source:
                return ImageOps.fit(source, (width, height), method=Image.Resampling.LANCZOS)

        if background_path and background_path.exists():
            with Image.open(background_path).convert("RGBA") as source:
                return ImageOps.fit(source, (width, height), method=Image.Resampling.LANCZOS)

        return self._draw_modern_fallback_background(width, height, theme)

    def _draw_modern_fallback_background(
        self,
        width: int,
        height: int,
        theme: dict[str, str],
    ) -> Image.Image:
        image = Image.new("RGBA", (width, height), theme["canvas"])
        draw = ImageDraw.Draw(image)

        for y in range(height):
            ratio = y / height
            color = self._blend_hex(theme["canvas"], theme["wash"], ratio)
            draw.line((0, y, width, y), fill=color)

        draw.ellipse((-160, -110, 420, 470), fill=self._hex_to_rgba(theme["orb_a"], 150))
        draw.ellipse((780, -180, 1380, 360), fill=self._hex_to_rgba(theme["orb_b"], 170))
        draw.ellipse((640, 330, 1320, 860), fill=self._hex_to_rgba(theme["orb_c"], 145))

        for index, box in enumerate(
            [
                (710, 86, 1080, 244),
                (820, 260, 1148, 442),
                (650, 422, 980, 570),
            ]
        ):
            draw.rounded_rectangle(
                box,
                radius=36,
                fill=self._hex_to_rgba(theme["glass"], 108 - index * 15),
                outline=self._hex_to_rgba("#FFFFFF", 80),
                width=2,
            )

        return image

    def _apply_readability_layers(
        self,
        image: Image.Image,
        theme: dict[str, str],
        has_photo: bool,
    ) -> None:
        width, height = image.size
        overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)

        for x in range(width):
            ratio = x / width
            alpha = int((215 if has_photo else 120) * (1 - ratio) ** 1.7)
            draw.line((x, 0, x, height), fill=self._hex_to_rgba(theme["veil"], alpha))

        for y in range(height):
            ratio = y / height
            alpha = int(90 * ratio**2)
            draw.line((0, y, width, y), fill=(25, 18, 14, alpha))

        draw.rounded_rectangle(
            (38, 34, width - 38, height - 34),
            radius=34,
            outline=self._hex_to_rgba("#FFFFFF", 80),
            width=2,
        )
        image.alpha_composite(overlay)

    def _apply_photo_showcase_finish(self, image: Image.Image) -> None:
        width, height = image.size
        overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)

        # Keep uploaded photos crisp and clean, with only a subtle edge treatment.
        for y in range(height):
            ratio = y / height
            alpha = int(24 + ratio * 36)
            draw.line((0, y, width, y), fill=(20, 16, 14, alpha))

        draw.rounded_rectangle(
            (18, 18, width - 18, height - 18),
            radius=34,
            outline=(255, 255, 255, 165),
            width=2,
        )
        draw.rounded_rectangle(
            (32, 32, width - 32, height - 32),
            radius=30,
            outline=(255, 255, 255, 88),
            width=1,
        )
        image.alpha_composite(overlay)

    def _draw_campaign_copy(
        self,
        draw: ImageDraw.ImageDraw,
        form_data: AdGenerationForm,
        result: GenerationResult,
        theme: dict[str, str],
    ) -> None:
        poster = result.channel_packages.poster
        label_font = self._load_font(23)
        headline_font = self._load_font(64)
        body_font = self._load_font(29)
        cta_font = self._load_font(27)

        left, top = 82, 76
        badge = f"{form_data.business_name}  /  {form_data.business_category}"
        self._draw_pill(draw, (left, top, left + min(440, 42 + len(badge) * 14), top + 42), badge, label_font, theme)

        headline = poster.headline or result.headline
        headline_lines = self._wrap_korean(headline, 13)
        draw.multiline_text(
            (left, top + 76),
            headline_lines,
            fill=theme["headline"],
            font=headline_font,
            spacing=10,
        )

        body = poster.subcopy or result.body_copy
        body_lines = self._wrap_korean(body, 26)
        draw.multiline_text(
            (left, top + 250),
            body_lines,
            fill=theme["body"],
            font=body_font,
            spacing=11,
        )

        cta_text = poster.cta or result.cta
        cta_width = min(390, 70 + len(cta_text) * 19)
        cta_box = (left, 512, left + cta_width, 574)
        draw.rounded_rectangle(cta_box, radius=22, fill=theme["accent"])
        draw.text((left + 25, 527), cta_text, fill="white", font=cta_font)

    def _draw_brand_marks(
        self,
        draw: ImageDraw.ImageDraw,
        form_data: AdGenerationForm,
        result: GenerationResult,
        theme: dict[str, str],
        width: int,
        height: int,
    ) -> None:
        small_font = self._load_font(22)
        meta_font = self._load_font(24)
        product = form_data.product_name[:18]
        goal = form_data.promotion_goal[:16]
        time = result.channel_packages.instagram.recommended_post_time[:18]

        card = (780, 96, 1094, 292)
        draw.rounded_rectangle(
            card,
            radius=30,
            fill=self._hex_to_rgba(theme["card"], 224),
            outline=self._hex_to_rgba("#FFFFFF", 130),
            width=2,
        )
        draw.text((814, 132), product, fill=theme["card_text"], font=meta_font)
        draw.text((814, 178), goal, fill=theme["card_muted"], font=small_font)
        draw.line((814, 224, 1058, 224), fill=self._hex_to_rgba(theme["card_muted"], 70), width=2)
        draw.text((814, 242), time, fill=theme["card_muted"], font=small_font)

        draw.rounded_rectangle(
            (874, 330, width - 78, height - 78),
            radius=34,
            fill=self._hex_to_rgba(theme["accent"], 210),
        )
        initial_font = self._load_font(72)
        initial = form_data.business_name[:1] if form_data.business_name else "A"
        draw.text((982, 383), initial, fill="white", font=initial_font)

    def _draw_pill(
        self,
        draw: ImageDraw.ImageDraw,
        box: tuple[int, int, int, int],
        text: str,
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
        theme: dict[str, str],
    ) -> None:
        draw.rounded_rectangle(
            box,
            radius=18,
            fill=self._hex_to_rgba(theme["pill"], 208),
            outline=self._hex_to_rgba("#FFFFFF", 125),
            width=1,
        )
        draw.text((box[0] + 18, box[1] + 9), text, fill=theme["pill_text"], font=font)

    def _wrap_korean(self, text: str, width: int) -> str:
        return "\n".join(wrap(text, width=width, break_long_words=False, break_on_hyphens=False))

    def _resolve_static_path(self, path: str | None) -> Path | None:
        if not path:
            return None
        return self.settings.static_dir / path.removeprefix("/static/")

    def _has_uploaded_reference(self, uploaded_image_path: str | None) -> bool:
        path = self._resolve_static_path(uploaded_image_path)
        return bool(path and path.exists())

    def _load_font(self, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        if self.settings.default_font_path.exists():
            return ImageFont.truetype(str(self.settings.default_font_path), size=size)
        return ImageFont.load_default()

    def _hex_to_rgba(self, value: str, alpha: int) -> tuple[int, int, int, int]:
        value = value.lstrip("#")
        return (
            int(value[0:2], 16),
            int(value[2:4], 16),
            int(value[4:6], 16),
            alpha,
        )

    def _blend_hex(self, start: str, end: str, ratio: float) -> tuple[int, int, int, int]:
        start = start.lstrip("#")
        end = end.lstrip("#")
        channels = []
        for index in (0, 2, 4):
            channels.append(
                round(int(start[index : index + 2], 16) * (1 - ratio) + int(end[index : index + 2], 16) * ratio)
            )
        return channels[0], channels[1], channels[2], 255

    def _select_theme(self, visual_style: str) -> dict[str, str]:
        themes = {
            "따뜻한 감성": {
                "canvas": "#F4E7DA",
                "wash": "#FFE7D6",
                "orb_a": "#F6B99B",
                "orb_b": "#D86445",
                "orb_c": "#F1BE78",
                "glass": "#FFFFFF",
                "veil": "#FFF4EA",
                "headline": "#231713",
                "body": "#4B352E",
                "accent": "#D86445",
                "pill": "#FFFFFF",
                "pill_text": "#7A4936",
                "card": "#FFF8F0",
                "card_text": "#2C1D17",
                "card_muted": "#76564A",
            },
            "미니멀": {
                "canvas": "#E8ECEB",
                "wash": "#F7F8F5",
                "orb_a": "#BACBC8",
                "orb_b": "#8AA3A0",
                "orb_c": "#D5D0C5",
                "glass": "#FFFFFF",
                "veil": "#F7F8F5",
                "headline": "#162221",
                "body": "#405453",
                "accent": "#345F5A",
                "pill": "#FFFFFF",
                "pill_text": "#345F5A",
                "card": "#F8FAF8",
                "card_text": "#162221",
                "card_muted": "#526664",
            },
            "강한 세일형": {
                "canvas": "#FFE9DE",
                "wash": "#FFF4EA",
                "orb_a": "#FF9E70",
                "orb_b": "#D9432A",
                "orb_c": "#FFC05D",
                "glass": "#FFFFFF",
                "veil": "#FFF1E9",
                "headline": "#2D1109",
                "body": "#663126",
                "accent": "#D9432A",
                "pill": "#FFFFFF",
                "pill_text": "#A13A25",
                "card": "#FFF6EF",
                "card_text": "#2D1109",
                "card_muted": "#7A3A2D",
            },
            "프리미엄": {
                "canvas": "#EAE2D7",
                "wash": "#FBF7EF",
                "orb_a": "#C9B48D",
                "orb_b": "#8C6942",
                "orb_c": "#DDD0BA",
                "glass": "#FFFFFF",
                "veil": "#FBF7EF",
                "headline": "#1F1A15",
                "body": "#4A3B2E",
                "accent": "#7A5A35",
                "pill": "#FFFFFF",
                "pill_text": "#6C5134",
                "card": "#F7F0E5",
                "card_text": "#1F1A15",
                "card_muted": "#6E5B47",
            },
            "산뜻한 시즌형": {
                "canvas": "#EAF4E2",
                "wash": "#FFF6D8",
                "orb_a": "#CDEEA6",
                "orb_b": "#7CB45B",
                "orb_c": "#F4C96A",
                "glass": "#FFFFFF",
                "veil": "#F9FFF2",
                "headline": "#1D2A19",
                "body": "#405C36",
                "accent": "#5F9E43",
                "pill": "#FFFFFF",
                "pill_text": "#4F813A",
                "card": "#FAFFF3",
                "card_text": "#1D2A19",
                "card_muted": "#607952",
            },
        }
        return themes.get(visual_style, themes["따뜻한 감성"])
