from app.services.naver_blog_connect import _looks_like_naver_blog_editor_url


def test_naver_blog_editor_url_detection_accepts_write_form_url():
    assert _looks_like_naver_blog_editor_url(
        "https://blog.naver.com/PostWriteForm.naver?blogId=panda_0108"
    )


def test_naver_blog_editor_url_detection_accepts_redirect_write_url():
    assert _looks_like_naver_blog_editor_url(
        "https://blog.naver.com/panda_0108?Redirect=Write&"
    )


def test_naver_blog_editor_url_detection_rejects_login_page():
    assert not _looks_like_naver_blog_editor_url("https://nid.naver.com/nidlogin.login")


def test_naver_blog_editor_url_detection_rejects_regular_blog_home():
    assert not _looks_like_naver_blog_editor_url("https://blog.naver.com/panda_0108")
