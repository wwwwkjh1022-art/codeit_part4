from app.config import Settings
from app.services.channel_connection_store import ChannelConnectionStore


def _settings(tmp_path):
    return Settings(
        data_dir=tmp_path / "data",
        campaign_store_path=tmp_path / "data" / "campaigns.json",
        generated_dir=tmp_path / "generated",
        upload_dir=tmp_path / "generated" / "uploads",
        banner_dir=tmp_path / "generated" / "banners",
        static_dir=tmp_path / "static",
        templates_dir=tmp_path / "templates",
        copy_provider="mock",
    )


def test_channel_connection_store_saves_all_connections(tmp_path):
    settings = _settings(tmp_path)
    settings.ensure_runtime_directories()
    store = ChannelConnectionStore(settings)

    store.save_instagram("ig-token", "1789")
    store.save_threads("threads-token", "thr-22")
    connections = store.save_blog(
        platform="naver_blog",
        blog_id="my-blog",
        username="naver-user",
        login_password="naver-pass",
    )

    assert connections.instagram.is_configured is True
    assert connections.threads.is_configured is True
    assert connections.blog.is_configured is True

    saved = store.get()
    assert saved.instagram.instagram_user_id == "1789"
    assert saved.threads.threads_user_id == "thr-22"
    assert saved.blog.blog_id == "my-blog"
    assert saved.blog.username == "naver-user"
