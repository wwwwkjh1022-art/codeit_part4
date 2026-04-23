from typing import Annotated

from fastapi import Form
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator


class AdGenerationForm(BaseModel):
    business_category: str = Field(..., min_length=1, max_length=50)
    business_name: str = Field(..., min_length=1, max_length=50)
    product_name: str = Field(..., min_length=1, max_length=80)
    product_description: str = Field(default="", max_length=400)
    offer_details: str = Field(default="", max_length=120)
    target_customer: str = Field(..., min_length=1, max_length=80)
    promotion_goal: str = Field(..., min_length=1, max_length=60)
    tone: str = Field(..., min_length=1, max_length=30)
    platform: str = Field(..., min_length=1, max_length=30)
    visual_style: str = Field(..., min_length=1, max_length=30)
    cta_focus: str = Field(..., min_length=1, max_length=30)
    campaign_type: str = Field(..., min_length=1, max_length=40)
    desired_action: str = Field(..., min_length=1, max_length=40)
    post_timing_preference: str = Field(..., min_length=1, max_length=40)
    keywords: str = Field(default="", max_length=120)

    @field_validator("*", mode="before")
    @classmethod
    def strip_text(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value

    @model_validator(mode="after")
    def fill_missing_product_description(self) -> "AdGenerationForm":
        if not self.product_description:
            self.product_description = (
                f"{self.business_name}의 {self.product_name}은 {self.business_category} 고객에게 "
                f"{self.tone} 분위기로 소개할 수 있는 대표 상품/서비스입니다."
            )
        return self

    @property
    def keyword_list(self) -> list[str]:
        return [item.strip() for item in self.keywords.split(",") if item.strip()]

    @classmethod
    def as_form(
        cls,
        business_category: Annotated[str, Form(...)],
        business_name: Annotated[str, Form(...)],
        product_name: Annotated[str, Form(...)],
        target_customer: Annotated[str, Form(...)],
        promotion_goal: Annotated[str, Form(...)],
        tone: Annotated[str, Form(...)],
        platform: Annotated[str, Form(...)],
        visual_style: Annotated[str, Form(...)],
        cta_focus: Annotated[str, Form(...)],
        campaign_type: Annotated[str, Form(...)],
        desired_action: Annotated[str, Form(...)],
        post_timing_preference: Annotated[str, Form(...)],
        product_description: Annotated[str, Form()] = "",
        offer_details: Annotated[str, Form()] = "",
        keywords: Annotated[str, Form()] = "",
    ) -> "AdGenerationForm":
        try:
            return cls(
                business_category=business_category,
                business_name=business_name,
                product_name=product_name,
                product_description=product_description,
                offer_details=offer_details,
                target_customer=target_customer,
                promotion_goal=promotion_goal,
                tone=tone,
                platform=platform,
                visual_style=visual_style,
                cta_focus=cta_focus,
                campaign_type=campaign_type,
                desired_action=desired_action,
                post_timing_preference=post_timing_preference,
                keywords=keywords,
            )
        except ValidationError as exc:
            raise RequestValidationError(exc.errors()) from exc
