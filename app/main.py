from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.routes.api import router as api_router
from app.routes.health import router as health_router
from app.routes.pages import (
    CAMPAIGN_TYPE_OPTIONS,
    DESIRED_ACTION_OPTIONS,
    GOAL_OPTIONS,
    PLATFORM_OPTIONS,
    POST_TIMING_OPTIONS,
    TONE_OPTIONS,
    CTA_FOCUS_OPTIONS,
    VISUAL_STYLE_OPTIONS,
    router as pages_router,
)

FIELD_LABELS = {
    "business_category": "업종",
    "business_name": "상호명",
    "product_name": "상품/서비스명",
    "product_description": "상품/서비스 설명",
    "offer_details": "프로모션 상세",
    "target_customer": "타깃 고객",
    "promotion_goal": "홍보 목적",
    "tone": "톤",
    "platform": "게시 채널",
    "visual_style": "비주얼 스타일",
    "cta_focus": "CTA 목표",
    "campaign_type": "캠페인 유형",
    "desired_action": "최종 행동",
    "post_timing_preference": "게시 타이밍",
    "keywords": "강조 키워드",
}


def _build_error_messages(exc: RequestValidationError) -> list[str]:
    messages: list[str] = []
    for error in exc.errors():
        location = error.get("loc", [])
        field_name = location[-1] if location else "입력값"
        label = FIELD_LABELS.get(str(field_name), str(field_name).replace("_", " "))
        messages.append(f"{label}: {error.get('msg', '입력값을 확인해주세요.')}")
    return messages


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    if request.url.path == "/generate":
        form = await request.form()
        form_values = {
            "business_category": form.get("business_category", ""),
            "business_name": form.get("business_name", ""),
            "product_name": form.get("product_name", ""),
            "product_description": form.get("product_description", ""),
            "offer_details": form.get("offer_details", ""),
            "target_customer": form.get("target_customer", ""),
            "promotion_goal": form.get("promotion_goal", GOAL_OPTIONS[0]),
            "tone": form.get("tone", TONE_OPTIONS[1]),
            "platform": form.get("platform", "Instagram, Threads, Blog"),
            "visual_style": form.get("visual_style", VISUAL_STYLE_OPTIONS[0]),
            "cta_focus": form.get("cta_focus", CTA_FOCUS_OPTIONS[0]),
            "campaign_type": form.get("campaign_type", CAMPAIGN_TYPE_OPTIONS[0]),
            "desired_action": form.get("desired_action", DESIRED_ACTION_OPTIONS[0]),
            "post_timing_preference": form.get(
                "post_timing_preference", POST_TIMING_OPTIONS[0]
            ),
            "keywords": form.get("keywords", ""),
        }
        errors = _build_error_messages(exc)
        return request.app.state.templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "request": request,
                "tone_options": TONE_OPTIONS,
                "platform_options": PLATFORM_OPTIONS,
                "goal_options": GOAL_OPTIONS,
                "visual_style_options": VISUAL_STYLE_OPTIONS,
                "cta_focus_options": CTA_FOCUS_OPTIONS,
                "campaign_type_options": CAMPAIGN_TYPE_OPTIONS,
                "desired_action_options": DESIRED_ACTION_OPTIONS,
                "post_timing_options": POST_TIMING_OPTIONS,
                "form": form_values,
                "result": None,
                "warning": "입력값을 다시 확인해주세요.",
                "errors": errors,
            },
            status_code=422,
        )

    return JSONResponse(status_code=422, content={"detail": exc.errors()})


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.state.settings = settings
    app.state.templates = Jinja2Templates(directory=str(settings.templates_dir))
    app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.include_router(health_router)
    app.include_router(api_router)
    app.include_router(pages_router)
    return app


app = create_app()
