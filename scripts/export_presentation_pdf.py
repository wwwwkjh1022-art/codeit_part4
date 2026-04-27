from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "docs" / "PRESENTATION_SLIDES.html"
PDF_PATH = ROOT / "docs" / "PRESENTATION_SLIDES.pdf"


def main() -> None:
    image_pages: list[Image.Image] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=1)
        page.goto(HTML_PATH.resolve().as_uri(), wait_until="networkidle")
        slide_count = page.locator(".slide").count()

        for idx in range(slide_count):
            page.evaluate(f"window.location.hash = '#'+document.querySelectorAll('.slide')[{idx}].id")
            page.wait_for_timeout(120)
            deck = page.locator("#deck")
            png_bytes = deck.screenshot(type="png")
            image = Image.open(BytesIO(png_bytes)).convert("RGB")
            image_pages.append(image)

        browser.close()

    if not image_pages:
        raise RuntimeError("No slides captured")

    first, rest = image_pages[0], image_pages[1:]
    first.save(PDF_PATH, save_all=True, append_images=rest, resolution=150.0)
    print(f"saved {PDF_PATH} ({len(image_pages)} pages)")


if __name__ == "__main__":
    main()
