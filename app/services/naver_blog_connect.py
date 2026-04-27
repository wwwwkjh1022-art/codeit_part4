import asyncio
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from app.config import Settings
from app.services.channel_connection_store import ChannelConnectionStore


class NaverBlogConnectSession(BaseModel):
    id: str
    status: str = "starting"
    blog_id: str
    category_id: str = ""
    message: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class NaverBlogConnectService:
    def __init__(self) -> None:
        self._sessions: dict[str, NaverBlogConnectSession] = {}
        self._tasks: dict[str, asyncio.Task] = {}

    def start(self, settings: Settings, blog_id: str, category_id: str = "") -> NaverBlogConnectSession:
        session = NaverBlogConnectSession(
            id=uuid4().hex,
            status="starting",
            blog_id=blog_id.strip(),
            category_id=category_id.strip(),
            message="네이버 로그인 창을 여는 중입니다.",
        )
        self._sessions[session.id] = session
        self._tasks[session.id] = asyncio.create_task(
            self._run_connect_flow(settings, session.id, session.blog_id, session.category_id)
        )
        return session

    def get(self, session_id: str) -> NaverBlogConnectSession | None:
        return self._sessions.get(session_id)

    def complete(self, settings: Settings, session_id: str) -> NaverBlogConnectSession | None:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        ChannelConnectionStore(settings).save_blog(
            platform="naver_blog",
            blog_id=session.blog_id,
            category_id=session.category_id,
            session_ready=True,
        )
        updated = session.model_copy(
            update={
                "status": "connected",
                "message": (
                    "네이버 블로그 연결이 완료되었습니다. "
                    "글쓰기 화면 도착 완료로 저장됐고, 이제 이 창은 닫아도 됩니다."
                ),
                "updated_at": datetime.now(),
            }
        )
        self._sessions[session_id] = updated
        return updated

    def _set_session(self, session_id: str, **update: str) -> None:
        session = self._sessions.get(session_id)
        if session is None:
            return
        self._sessions[session_id] = session.model_copy(
            update={**update, "updated_at": datetime.now()}
        )

    async def _run_connect_flow(self, settings: Settings, session_id: str, blog_id: str, category_id: str) -> None:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            self._set_session(
                session_id,
                status="failed",
                message="Playwright가 설치되지 않았습니다. `.venv/bin/pip install playwright`가 필요합니다.",
            )
            return

        try:
            async with async_playwright() as playwright:
                try:
                    profile_dir = _naver_blog_profile_dir(settings)
                    context = await playwright.chromium.launch_persistent_context(
                        user_data_dir=str(profile_dir),
                        headless=False,
                        slow_mo=settings.naver_blog_slowmo_ms,
                    )
                except Exception as exc:
                    message = str(exc)
                    if "libasound.so.2" in message:
                        message = (
                            "Playwright Chromium 실행에 필요한 `libasound.so.2`가 없습니다. "
                            "`sudo apt-get install libasound2`가 필요합니다."
                        )
                    self._set_session(session_id, status="failed", message=message)
                    return

                storage_state_path = settings.data_dir / "naver_blog_storage_state.json"
                context.set_default_timeout(settings.naver_blog_timeout_ms)
                page = context.pages[0] if context.pages else await context.new_page()
                write_url = _build_naver_blog_write_url(blog_id, category_id)

                try:
                    self._set_session(
                        session_id,
                        status="waiting",
                        message=(
                            "열린 Chromium 창에서 네이버 로그인 후 "
                            "`블로그 글쓰기 화면(PostWriteForm)`까지 들어가 주세요. "
                            "글쓰기 화면이 열리면 연결이 자동 완료됩니다."
                        ),
                    )
                    await page.goto(write_url, wait_until="domcontentloaded")

                    deadline = time.monotonic() + settings.naver_blog_connect_timeout_seconds
                    while time.monotonic() < deadline:
                        if await _is_naver_blog_editor_ready(page):
                            await context.storage_state(path=str(storage_state_path))
                            ChannelConnectionStore(settings).save_blog(
                                platform="naver_blog",
                                blog_id=blog_id,
                                category_id=category_id,
                                session_ready=True,
                            )
                            self._set_session(
                                session_id,
                                status="connected",
                                message=(
                                    "네이버 블로그 연결이 완료되었습니다. "
                                    "글쓰기 화면 진입이 확인됐고, 이제 이 창은 닫아도 됩니다."
                                ),
                            )
                            return
                        await page.wait_for_timeout(1000)

                    self._set_session(
                        session_id,
                        status="failed",
                        message="로그인 또는 블로그 진입 확인 시간이 초과되었습니다. 다시 시도해 주세요.",
                    )
                finally:
                    try:
                        await context.close()
                    except Exception:
                        pass
        except Exception as exc:
            message = str(exc)
            if "Target page, context or browser has been closed" in message:
                message = (
                    "네이버 로그인 창이 중간에 닫혀 연결이 완료되지 않았습니다. "
                    "다시 버튼을 누른 뒤, 글쓰기 화면이 뜰 때까지 창을 닫지 말아주세요."
                )
            self._set_session(session_id, status="failed", message=message)


def _build_naver_blog_write_url(blog_id: str, category_id: str = "") -> str:
    query = f"blogId={blog_id.strip()}"
    if category_id.strip():
        query = f"{query}&categoryNo={category_id.strip()}"
    return f"https://blog.naver.com/PostWriteForm.naver?{query}"


def _naver_blog_profile_dir(settings: Settings) -> Path:
    profile_dir = settings.data_dir / "naver_blog_profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    return profile_dir


def _looks_like_naver_blog_editor_url(url: str) -> bool:
    normalized_url = url.strip().lower()
    if "nid.naver.com" in normalized_url:
        return False
    if "blog.naver.com" not in normalized_url:
        return False
    return "postwriteform.naver" in normalized_url or "redirect=write" in normalized_url


async def _is_naver_blog_editor_ready(page) -> bool:
    if _looks_like_naver_blog_editor_url(page.url):
        return True

    frames = [frame for frame in getattr(page, "frames", []) if _is_blog_frame(frame.url)]
    if _is_blog_frame(page.url):
        frames.insert(0, page)

    if not frames:
        return False

    return await _has_visible_editor_surface(frames)


async def _has_visible_editor_surface(frames) -> bool:
    selectors = (
        "input[placeholder='제목']",
        "input[placeholder*='제목']",
        "textarea[placeholder='제목']",
        "textarea[placeholder*='제목']",
        "[contenteditable='true'][placeholder*='제목']",
        "[contenteditable='true'][data-placeholder*='제목']",
        ".se-title-text",
        ".se-placeholder.__se_placeholder.__se_title_placeholder",
        ".se-component.se-title-text",
    )
    for frame in frames:
        for selector in selectors:
            try:
                if await frame.locator(selector).count():
                    return True
            except Exception:
                continue
        try:
            if await frame.locator("text=제목").count():
                return True
        except Exception:
            continue
    return False


def _is_blog_frame(url: str) -> bool:
    normalized_url = url.strip().lower()
    return "blog.naver.com" in normalized_url and "nid.naver.com" not in normalized_url


naver_blog_connect_service = NaverBlogConnectService()
