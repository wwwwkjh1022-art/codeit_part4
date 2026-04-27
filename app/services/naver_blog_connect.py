import asyncio
import time
from datetime import datetime
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
                    browser = await playwright.chromium.launch(
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
                context = await browser.new_context()
                page = await context.new_page()
                write_url = _build_naver_blog_write_url(blog_id, category_id)

                try:
                    self._set_session(
                        session_id,
                        status="waiting",
                        message="열린 Chromium 창에서 네이버 로그인과 블로그 진입을 완료해 주세요.",
                    )
                    await page.goto(write_url, wait_until="domcontentloaded")

                    deadline = time.monotonic() + settings.naver_blog_connect_timeout_seconds
                    while time.monotonic() < deadline:
                        current_url = page.url
                        if (
                            "blog.naver.com" in current_url
                            and "PostWriteForm.naver" in current_url
                            and "nid.naver.com" not in current_url
                        ):
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
                                message="네이버 블로그 연결이 완료되었습니다.",
                            )
                            return
                        await page.wait_for_timeout(1000)

                    self._set_session(
                        session_id,
                        status="failed",
                        message="로그인 또는 블로그 진입 확인 시간이 초과되었습니다. 다시 시도해 주세요.",
                    )
                finally:
                    await context.close()
                    await browser.close()
        except Exception as exc:
            self._set_session(session_id, status="failed", message=str(exc))


def _build_naver_blog_write_url(blog_id: str, category_id: str = "") -> str:
    query = f"blogId={blog_id.strip()}"
    if category_id.strip():
        query = f"{query}&categoryNo={category_id.strip()}"
    return f"https://blog.naver.com/PostWriteForm.naver?{query}"


naver_blog_connect_service = NaverBlogConnectService()
