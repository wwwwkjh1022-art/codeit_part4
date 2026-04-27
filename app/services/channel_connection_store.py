import json

from app.config import Settings
from app.schemas.channel_connection import (
    BlogConnection,
    ChannelConnections,
    InstagramConnection,
    ThreadsConnection,
)


class ChannelConnectionStore:
    def __init__(self, settings: Settings) -> None:
        self.path = settings.data_dir / "channel_connections.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def get(self) -> ChannelConnections:
        if not self.path.exists():
            return ChannelConnections()
        raw = self.path.read_text(encoding="utf-8").strip()
        if not raw:
            return ChannelConnections()
        return ChannelConnections.model_validate(json.loads(raw))

    def save_instagram(self, access_token: str, instagram_user_id: str) -> ChannelConnections:
        connections = self.get().model_copy(
            update={
                "instagram": InstagramConnection(
                    access_token=access_token,
                    instagram_user_id=instagram_user_id,
                )
            }
        )
        self._write(connections)
        return connections

    def save_threads(self, access_token: str, threads_user_id: str) -> ChannelConnections:
        connections = self.get().model_copy(
            update={
                "threads": ThreadsConnection(
                    access_token=access_token,
                    threads_user_id=threads_user_id,
                )
            }
        )
        self._write(connections)
        return connections

    def save_blog(
        self,
        api_base_url: str = "",
        username: str = "",
        application_password: str = "",
        platform: str = "wordpress",
        blog_id: str = "",
        category_id: str = "",
        login_password: str = "",
        session_ready: bool | None = None,
    ) -> ChannelConnections:
        existing = self.get().blog
        connections = self.get().model_copy(
            update={
                "blog": BlogConnection(
                    platform=platform,
                    blog_id=blog_id or existing.blog_id,
                    category_id=category_id or existing.category_id,
                    api_base_url=api_base_url or existing.api_base_url,
                    username=username or existing.username,
                    application_password=application_password or existing.application_password,
                    login_password=login_password or existing.login_password,
                    session_ready=(
                        session_ready
                        if session_ready is not None
                        else existing.session_ready
                    ),
                )
            }
        )
        self._write(connections)
        return connections

    def _write(self, connections: ChannelConnections) -> None:
        self.path.write_text(
            json.dumps(connections.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
