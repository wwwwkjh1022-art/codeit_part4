from pydantic import BaseModel


class InstagramConnection(BaseModel):
    access_token: str = ""
    instagram_user_id: str = ""

    @property
    def is_configured(self) -> bool:
        return bool(self.access_token.strip() and self.instagram_user_id.strip())


class ThreadsConnection(BaseModel):
    access_token: str = ""
    threads_user_id: str = ""

    @property
    def is_configured(self) -> bool:
        return bool(self.access_token.strip() and self.threads_user_id.strip())


class BlogConnection(BaseModel):
    platform: str = "naver_blog"
    blog_id: str = ""
    category_id: str = ""
    api_base_url: str = ""
    username: str = ""
    application_password: str = ""
    login_password: str = ""
    session_ready: bool = False

    @property
    def is_configured(self) -> bool:
        platform = self.platform.strip().lower()
        if platform == "wordpress":
            return bool(
                self.api_base_url.strip()
                and self.username.strip()
                and self.application_password.strip()
            )
        if platform == "naver_blog":
            return bool(
                self.blog_id.strip()
                and (
                    self.session_ready
                    or (self.username.strip() and self.login_password.strip())
                )
            )
        return False


class ChannelConnections(BaseModel):
    instagram: InstagramConnection = InstagramConnection()
    threads: ThreadsConnection = ThreadsConnection()
    blog: BlogConnection = BlogConnection()
