import base64
import ipaddress
import json
import mimetypes
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import httpx

from app.config import Settings
from app.schemas.campaign import CampaignRecord, PublishJob
from app.services.channel_connection_store import ChannelConnectionStore


class PublishAdapter:
    async def publish(self, campaign: CampaignRecord, job: PublishJob) -> PublishJob:
        raise NotImplementedError


class MockPublishAdapter(PublishAdapter):
    async def publish(self, campaign: CampaignRecord, job: PublishJob) -> PublishJob:
        external_ids = {
            channel: f"mock-{channel}-{campaign.id[:8]}-{uuid4().hex[:8]}"
            for channel in job.channels
        }
        return job.model_copy(
            update={
                "status": "published",
                "published_at": datetime.now(),
                "updated_at": datetime.now(),
                "provider": "mock",
                "external_ids": external_ids,
                "error_message": None,
            }
        )


class DirectApiPublishAdapter(PublishAdapter):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.connection_store = ChannelConnectionStore(settings)

    async def publish(self, campaign: CampaignRecord, job: PublishJob) -> PublishJob:
        connections = self.connection_store.get()
        external_ids: dict[str, str] = {}
        errors: list[str] = []

        async with httpx.AsyncClient(timeout=120) as client:
            for channel in job.channels:
                try:
                    if channel == "instagram":
                        external_ids[channel] = await self._publish_instagram(
                            client, campaign, connections.instagram
                        )
                    elif channel == "threads":
                        external_ids[channel] = await self._publish_threads(
                            client, campaign, connections.threads
                        )
                    elif channel == "blog":
                        if connections.blog.platform.strip().lower() == "naver_blog":
                            external_ids[channel] = await self._publish_naver_blog(
                                campaign, job, connections.blog
                            )
                        else:
                            external_ids[channel] = await self._publish_wordpress(
                                client, campaign, job, connections.blog
                            )
                except Exception as exc:
                    errors.append(f"{channel}: {exc}")

        status = "published" if not errors else "failed"
        return job.model_copy(
            update={
                "status": status,
                "published_at": datetime.now() if status == "published" else None,
                "updated_at": datetime.now(),
                "provider": "direct_api",
                "external_ids": external_ids,
                "error_message": " | ".join(errors) if errors else None,
            }
        )

    async def _publish_instagram(self, client: httpx.AsyncClient, campaign: CampaignRecord, connection) -> str:
        if not connection.is_configured:
            raise ValueError("Instagram API 값이 저장되지 않았습니다.")

        image_url = _require_public_media_url(self.settings, campaign.result.banner_preview_path)
        instagram = campaign.result.channel_packages.instagram
        caption = instagram.caption
        if instagram.hashtags:
            caption = f"{caption}\n\n{' '.join(instagram.hashtags)}"

        headers = {"Authorization": f"Bearer {connection.access_token.strip()}"}
        base_url = f"https://graph.instagram.com/v23.0/{connection.instagram_user_id.strip()}"
        container = await client.post(
            f"{base_url}/media",
            headers=headers,
            data={"image_url": image_url, "caption": caption},
        )
        container.raise_for_status()
        creation_id = container.json().get("id")
        if not creation_id:
            raise RuntimeError("Instagram media container id를 받지 못했습니다.")

        published = await client.post(
            f"{base_url}/media_publish",
            headers=headers,
            data={"creation_id": creation_id},
        )
        published.raise_for_status()
        return str(published.json().get("id") or creation_id)

    async def _publish_threads(self, client: httpx.AsyncClient, campaign: CampaignRecord, connection) -> str:
        if not connection.is_configured:
            raise ValueError("Threads API 값이 저장되지 않았습니다.")

        threads = campaign.result.channel_packages.threads
        image_url = _absolute_url(self.settings, campaign.result.banner_preview_path)
        headers = {"Authorization": f"Bearer {connection.access_token.strip()}"}
        base_url = f"https://graph.threads.net/v1.0/{connection.threads_user_id.strip()}"
        data = {"text": threads.thread_text}

        if image_url and _is_public_https_url(image_url):
            data["media_type"] = "IMAGE"
            data["image_url"] = image_url
        else:
            data["media_type"] = "TEXT"

        container = await client.post(
            f"{base_url}/threads",
            headers=headers,
            data=data,
        )
        container.raise_for_status()
        creation_id = container.json().get("id")
        if not creation_id:
            raise RuntimeError("Threads container id를 받지 못했습니다.")

        published = await client.post(
            f"{base_url}/threads_publish",
            headers=headers,
            data={"creation_id": creation_id},
        )
        published.raise_for_status()
        return str(published.json().get("id") or creation_id)

    async def _publish_wordpress(
        self,
        client: httpx.AsyncClient,
        campaign: CampaignRecord,
        job: PublishJob,
        connection,
    ) -> str:
        if not connection.is_configured:
            raise ValueError("Blog API 값이 저장되지 않았습니다.")
        if connection.platform.strip().lower() != "wordpress":
            raise ValueError("현재 Blog 실제 게시 지원은 WordPress만 가능합니다.")

        api_base = connection.api_base_url.strip().rstrip("/")
        auth_value = base64.b64encode(
            f"{connection.username.strip()}:{connection.application_password.strip()}".encode("utf-8")
        ).decode("ascii")
        headers = {"Authorization": f"Basic {auth_value}"}

        featured_media_id: int | None = None
        banner_path = _local_static_path(self.settings, campaign.result.banner_preview_path)
        if banner_path and banner_path.exists():
            media_headers = {
                **headers,
                "Content-Disposition": f'attachment; filename="{banner_path.name}"',
                "Content-Type": mimetypes.guess_type(banner_path.name)[0] or "image/png",
            }
            media_response = await client.post(
                f"{api_base}/media",
                headers=media_headers,
                content=banner_path.read_bytes(),
            )
            media_response.raise_for_status()
            featured_media_id = media_response.json().get("id")

        blog = campaign.result.channel_packages.blog
        payload: dict[str, object] = {
            "title": blog.title,
            "content": _build_blog_html(campaign),
            "status": "publish" if job.scheduled_at <= datetime.now() else "future",
        }
        if featured_media_id is not None:
            payload["featured_media"] = featured_media_id
        if payload["status"] == "future":
            payload["date"] = job.scheduled_at.isoformat()

        post_response = await client.post(
            f"{api_base}/posts",
            headers={**headers, "Content-Type": "application/json"},
            json=payload,
        )
        post_response.raise_for_status()
        data = post_response.json()
        return str(data.get("link") or data.get("id"))

    async def _publish_naver_blog(self, campaign: CampaignRecord, job: PublishJob, connection) -> str:
        if not connection.is_configured:
            raise ValueError("네이버 블로그 로그인 정보가 저장되지 않았습니다.")

        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Playwright가 설치되지 않았습니다. `.venv/bin/pip install playwright` 후 "
                "`.venv/bin/playwright install chromium`를 실행하세요."
            ) from exc

        storage_state_path = self.settings.data_dir / "naver_blog_storage_state.json"
        write_url = _build_naver_blog_write_url(connection)
        profile_dir = self.settings.data_dir / "naver_blog_profile"
        profile_dir.mkdir(parents=True, exist_ok=True)

        async with async_playwright() as playwright:
            try:
                context = await playwright.chromium.launch_persistent_context(
                    user_data_dir=str(profile_dir),
                    headless=self.settings.naver_blog_headless,
                    slow_mo=self.settings.naver_blog_slowmo_ms,
                )
            except Exception as exc:
                message = str(exc)
                if "libasound.so.2" in message:
                    raise RuntimeError(
                        "Playwright Chromium 실행에 필요한 시스템 라이브러리 `libasound.so.2`가 없습니다. "
                        "Ubuntu/WSL에서는 `sudo apt-get install libasound2` 또는 "
                        "`.venv/bin/playwright install-deps chromium`가 필요합니다."
                    ) from exc
                raise
            context.set_default_timeout(self.settings.naver_blog_timeout_ms)
            if storage_state_path.exists():
                try:
                    await context.add_cookies(_storage_state_cookies(storage_state_path))
                except Exception:
                    pass
            page = context.pages[0] if context.pages else await context.new_page()

            try:
                await page.goto(write_url, wait_until="domcontentloaded")
                await self._login_naver_if_needed(page, connection)
                await page.goto(write_url, wait_until="domcontentloaded")
                await page.wait_for_load_state("networkidle")
                await self._dismiss_naver_blog_popups(page)
                await self._fill_naver_blog_editor(page, campaign)

                banner_path = _local_static_path(self.settings, campaign.result.banner_preview_path)
                if banner_path and banner_path.exists():
                    await self._attach_naver_blog_image(page, banner_path)

                published_url = await self._publish_naver_blog_post(page)
                await context.storage_state(path=str(storage_state_path))
                return published_url
            finally:
                await context.close()

    async def _login_naver_if_needed(self, page, connection) -> None:
        if "nid.naver.com" not in page.url and not await self._selector_exists(page, "#id"):
            return
        if not connection.username.strip() or not connection.login_password.strip():
            raise RuntimeError(
                "저장된 네이버 로그인 세션이 없거나 만료되었습니다. 결과 페이지에서 "
                "`네이버 로그인 창 열기` 버튼으로 다시 연결해 주세요."
            )

        await page.wait_for_selector("#id")
        await page.fill("#id", connection.username.strip())
        await page.fill("#pw", connection.login_password.strip())
        await page.click("#log\\.login")
        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(1500)

        if "captcha" in page.url.lower():
            raise RuntimeError(
                "네이버 로그인에 CAPTCHA 또는 추가 인증이 필요합니다. "
                "브라우저에서 한 번 로그인해 세션을 만든 뒤 다시 시도해 주세요."
            )
        if "nid.naver.com" in page.url and await self._selector_exists(page, "#id"):
            raise RuntimeError("네이버 로그인에 실패했습니다. 계정 정보 또는 추가 인증 상태를 확인해 주세요.")

    async def _dismiss_naver_blog_popups(self, page) -> None:
        dismiss_selectors = [
            "button:has-text('닫기')",
            "button:has-text('취소')",
            "button:has-text('나중에')",
            "[role='button']:has-text('닫기')",
            "[role='button']:has-text('취소')",
        ]
        for selector in dismiss_selectors:
            locator = await self._find_first_locator(page, [selector], timeout_ms=1200)
            if locator is None:
                continue
            try:
                await locator.click()
                await page.wait_for_timeout(300)
            except Exception:
                continue
        try:
            await page.keyboard.press("Escape")
        except Exception:
            pass

    async def _fill_naver_blog_editor(self, page, campaign: CampaignRecord) -> None:
        blog = campaign.result.channel_packages.blog
        title_text = blog.title or campaign.result.headline
        body_text = _build_naver_blog_text(campaign)

        title_locator = await self._find_first_locator(
            page,
            [
                "textarea[placeholder*='제목']",
                "[contenteditable='true'][placeholder*='제목']",
                "[contenteditable='true'][data-placeholder*='제목']",
                "span[contenteditable='true']",
                "h3[contenteditable='true']",
            ],
            timeout_ms=20000,
        )
        if title_locator is None:
            raise RuntimeError("네이버 블로그 제목 입력 영역을 찾지 못했습니다.")
        await self._replace_editor_text(title_locator, title_text)

        body_locator = await self._find_first_locator(
            page,
            [
                "[contenteditable='true'][data-placeholder*='본문']",
                "[contenteditable='true'][aria-label*='본문']",
                "div.se-component-content [contenteditable='true']",
                "div[contenteditable='true'].se-text-paragraph",
                "p[contenteditable='true']",
            ],
            timeout_ms=20000,
        )
        if body_locator is None:
            editable_locators = await self._collect_visible_locators(
                page,
                ["div[contenteditable='true']", "p[contenteditable='true']"],
            )
            if len(editable_locators) >= 2:
                body_locator = editable_locators[1]
        if body_locator is None:
            raise RuntimeError("네이버 블로그 본문 입력 영역을 찾지 못했습니다.")
        await self._replace_editor_text(body_locator, body_text)

    async def _attach_naver_blog_image(self, page, image_path: Path) -> None:
        file_input = await self._find_first_locator(
            page,
            ["input[type='file'][accept*='image']", "input[type='file']"],
            timeout_ms=1500,
        )
        if file_input is not None:
            try:
                await file_input.set_input_files(str(image_path))
                await page.wait_for_timeout(1500)
                return
            except Exception:
                pass

        trigger_selectors = [
            "button:has-text('사진')",
            "[role='button']:has-text('사진')",
            "button:has-text('이미지')",
            "[aria-label*='사진']",
        ]
        for selector in trigger_selectors:
            trigger = await self._find_first_locator(page, [selector], timeout_ms=1200)
            if trigger is None:
                continue
            try:
                async with page.expect_file_chooser(timeout=3000) as chooser_info:
                    await trigger.click()
                chooser = await chooser_info.value
                await chooser.set_files(str(image_path))
                await page.wait_for_timeout(1800)
                return
            except Exception:
                continue

    async def _publish_naver_blog_post(self, page) -> str:
        publish_selectors = [
            "button:has-text('발행')",
            "[role='button']:has-text('발행')",
            "a:has-text('발행')",
        ]
        current_url = page.url
        publish_button = await self._find_first_locator(page, publish_selectors, timeout_ms=12000)
        if publish_button is None:
            raise RuntimeError("네이버 블로그 발행 버튼을 찾지 못했습니다.")
        await publish_button.click()
        await page.wait_for_timeout(1800)

        confirm_button = await self._find_first_locator(page, publish_selectors, timeout_ms=3000)
        if confirm_button is not None:
            try:
                await confirm_button.click()
                await page.wait_for_timeout(2200)
            except Exception:
                pass

        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(1800)
        return page.url or current_url

    async def _replace_editor_text(self, locator, text: str) -> None:
        await locator.click()
        try:
            await locator.press("Control+A")
            await locator.press("Backspace")
        except Exception:
            pass

        is_contenteditable = False
        try:
            is_contenteditable = bool(await locator.evaluate("node => node.isContentEditable"))
        except Exception:
            is_contenteditable = False

        if not is_contenteditable:
            try:
                await locator.fill(text)
                return
            except Exception:
                pass

        lines = text.splitlines() or [text]
        for index, line in enumerate(lines):
            if line:
                await locator.type(line, delay=12)
            if index < len(lines) - 1:
                await locator.press("Enter")

    async def _collect_visible_locators(self, page, selectors: list[str]) -> list:
        matches = []
        for frame in [page, *page.frames]:
            for selector in selectors:
                locator = frame.locator(selector)
                try:
                    count = await locator.count()
                except Exception:
                    continue
                for index in range(count):
                    candidate = locator.nth(index)
                    try:
                        if await candidate.is_visible():
                            matches.append(candidate)
                    except Exception:
                        continue
        return matches

    async def _find_first_locator(self, page, selectors: list[str], timeout_ms: int | None = None):
        deadline = time.monotonic() + ((timeout_ms or self.settings.naver_blog_timeout_ms) / 1000)
        while time.monotonic() < deadline:
            matches = await self._collect_visible_locators(page, selectors)
            if matches:
                return matches[0]
            await page.wait_for_timeout(250)
        return None

    async def _selector_exists(self, page, selector: str) -> bool:
        for frame in [page, *page.frames]:
            locator = frame.locator(selector)
            try:
                if await locator.count():
                    return True
            except Exception:
                continue
        return False


def build_publish_adapter(settings: Settings, provider: str = "direct_api") -> PublishAdapter:
    if provider == "mock":
        return MockPublishAdapter()
    return DirectApiPublishAdapter(settings)


def _build_blog_html(campaign: CampaignRecord) -> str:
    blog = campaign.result.channel_packages.blog
    outline = "\n".join(f"<li>{item}</li>" for item in blog.body_outline)
    keywords = ", ".join(blog.seo_keywords)
    return (
        f"<p>{blog.intro}</p>\n"
        f"<ul>{outline}</ul>\n"
        f"<p><strong>{blog.cta}</strong></p>\n"
        f"<p>추천 키워드: {keywords}</p>"
    )


def _build_naver_blog_text(campaign: CampaignRecord) -> str:
    blog = campaign.result.channel_packages.blog
    lines = [blog.intro, ""]
    lines.extend(f"- {item}" for item in blog.body_outline)
    lines.extend(
        [
            "",
            blog.cta,
            "",
            f"추천 키워드: {', '.join(blog.seo_keywords)}",
        ]
    )
    return "\n".join(line for line in lines if line is not None)


def _build_naver_blog_write_url(connection) -> str:
    blog_id = connection.blog_id.strip()
    category_id = connection.category_id.strip()
    query = f"blogId={blog_id}"
    if category_id:
        query = f"{query}&categoryNo={category_id}"
    return f"https://blog.naver.com/PostWriteForm.naver?{query}"


def _storage_state_cookies(storage_state_path: Path) -> list[dict]:
    raw = storage_state_path.read_text(encoding="utf-8").strip()
    if not raw:
        return []
    payload = json.loads(raw)
    cookies = payload.get("cookies", [])
    return cookies if isinstance(cookies, list) else []


def _absolute_url(settings: Settings, path: str | None) -> str | None:
    if not path:
        return None
    if path.startswith(("http://", "https://")):
        return path
    return f"{settings.public_base_url.rstrip('/')}/{path.lstrip('/')}"


def _local_static_path(settings: Settings, path: str | None) -> Path | None:
    if not path:
        return None
    return settings.static_dir / path.removeprefix("/static/")


def _require_public_media_url(settings: Settings, path: str | None) -> str:
    image_url = _absolute_url(settings, path)
    if not image_url or not _is_public_https_url(image_url):
        raise ValueError(
            "Instagram/Threads는 외부에서 접근 가능한 public HTTPS 이미지 URL이 필요합니다. "
            "PUBLIC_BASE_URL을 ngrok, Cloudflare Tunnel, 실제 도메인 같은 공개 주소로 설정하세요."
        )
    return image_url


def _is_public_https_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    hostname = parsed.hostname.lower()
    if hostname in {"localhost", "127.0.0.1", "0.0.0.0"}:
        return False
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return True
    return not (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_unspecified
    )
