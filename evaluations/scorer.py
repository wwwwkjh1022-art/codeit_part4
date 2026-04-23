from dataclasses import dataclass

from app.schemas.form import AdGenerationForm
from app.schemas.result import GenerationResult
from evaluations.testset import GenerationEvalCase


@dataclass(frozen=True)
class EvaluationScore:
    case_id: str
    overall_score: int
    channel_score: int
    keyword_score: int
    hook_score: int
    specificity_score: int
    differentiation_score: int
    cta_score: int
    compliance_score: int
    structure_score: int
    quality_report_score: int
    passed: bool
    reasons: tuple[str, ...]


GENERIC_PHRASES = (
    "핵심 메시지",
    "홍보 문구",
    "업종에 어울리는",
    "확인해보세요",
    "지금 가장 눈에 띄는",
)

RISKY_CLAIMS = (
    "무조건",
    "100% 보장",
    "완전 보장",
    "최고의",
    "1위",
    "유일한",
    "확실한 효과",
    "치료",
    "완치",
    "오늘 마감",
    "마감 임박",
)

ACTION_TERMS = {
    "매장 방문": ("방문", "오세요", "들러", "매장"),
    "예약하기": ("예약", "시간", "문의"),
    "DM 문의": ("dm", "문의", "메시지"),
    "링크 클릭": ("링크", "클릭", "프로필"),
    "팔로우/저장": ("팔로우", "저장"),
}


def score_generation(case: GenerationEvalCase, result: GenerationResult) -> EvaluationScore:
    reasons: list[str] = []
    combined_text = _combined_text(result)

    keyword_score = _keyword_score(case, combined_text)
    hook_score = _hook_score(case.form, result)
    specificity_score = _specificity_score(case.form, result, combined_text)
    channel_score = _channel_score(case.form, result)
    differentiation_score = _differentiation_score(result)
    cta_score = _cta_score(case.form, result, combined_text)
    compliance_score = _compliance_score(result, combined_text)
    structure_score = _structure_score(result)
    quality_report_score = _quality_report_score(case.form, result)
    overall_score = round(
        keyword_score * 0.12
        + hook_score * 0.14
        + specificity_score * 0.14
        + channel_score * 0.18
        + differentiation_score * 0.10
        + cta_score * 0.10
        + compliance_score * 0.08
        + structure_score * 0.06
        + quality_report_score * 0.08
    )

    if keyword_score < 80:
        reasons.append(f"brief keyword coverage is low: {keyword_score}")
    if hook_score < 78:
        reasons.append(f"opening hook is not strong enough: {hook_score}")
    if specificity_score < 78:
        reasons.append(f"copy is too generic or lacks offer/context: {specificity_score}")
    if channel_score < case.min_channel_score:
        reasons.append(f"channel-native readiness is below threshold: {channel_score}")
    if differentiation_score < 80:
        reasons.append(f"channel versions are too similar: {differentiation_score}")
    if cta_score < 78:
        reasons.append(f"CTA and next action are weak: {cta_score}")
    if compliance_score < 90:
        reasons.append(f"risky or unsupported ad claims detected: {compliance_score}")
    if structure_score < 90:
        reasons.append(f"automation-ready structure is incomplete: {structure_score}")
    if quality_report_score < 78:
        reasons.append(f"quality report is too weak: {quality_report_score}")
    if overall_score < case.min_overall_score:
        reasons.append(
            f"overall score {overall_score} is below threshold {case.min_overall_score}"
        )

    return EvaluationScore(
        case_id=case.id,
        overall_score=overall_score,
        channel_score=channel_score,
        keyword_score=keyword_score,
        hook_score=hook_score,
        specificity_score=specificity_score,
        differentiation_score=differentiation_score,
        cta_score=cta_score,
        compliance_score=compliance_score,
        structure_score=structure_score,
        quality_report_score=quality_report_score,
        passed=not reasons,
        reasons=tuple(reasons),
    )


def _combined_text(result: GenerationResult) -> str:
    packages = result.channel_packages
    background_prompt = result.background_asset.prompt if result.background_asset else ""
    parts = [
        result.headline,
        result.body_copy,
        result.caption,
        result.cta,
        result.strategy_note,
        result.image_direction,
        packages.instagram.caption,
        " ".join(packages.instagram.hashtags),
        packages.instagram.alt_text,
        packages.instagram.visual_hook,
        packages.threads.thread_text,
        packages.threads.reply_prompt,
        packages.threads.short_hook,
        packages.blog.title,
        packages.blog.intro,
        " ".join(packages.blog.body_outline),
        " ".join(packages.blog.seo_keywords),
        packages.blog.cta,
        packages.blog.meta_description,
        packages.poster.headline,
        packages.poster.subcopy,
        packages.poster.cta,
        packages.poster.visual_direction,
        background_prompt,
    ]
    parts.extend(f"{variant.headline} {variant.body_copy}" for variant in result.variants)
    parts.extend(result.pre_publish_checklist)
    return _normalize(" ".join(parts))


def _keyword_score(case: GenerationEvalCase, text: str) -> int:
    expected_terms = [
        *case.expected_terms,
        case.form.business_name,
        case.form.product_name,
        case.form.business_category,
    ]
    expected_terms.extend(case.form.keyword_list[:3])
    if not expected_terms:
        return 100
    matched = sum(1 for term in expected_terms if _normalize(term) in text)
    return round((matched / len(expected_terms)) * 100)


def _hook_score(form: AdGenerationForm, result: GenerationResult) -> int:
    instagram_first = _first_line(result.channel_packages.instagram.caption)
    threads_hook = result.channel_packages.threads.short_hook
    poster_headline = result.channel_packages.poster.headline
    variant_heads = " ".join(variant.headline for variant in result.variants[:2])
    score = 0
    score += 20 if _contains_any(instagram_first, [form.product_name, form.business_name]) else 0
    score += 15 if _contains_any(instagram_first, _benefit_terms(form)) else 0
    score += 15 if 12 <= len(instagram_first) <= 85 else 5
    score += 15 if _contains_any(threads_hook, [form.product_name, *form.keyword_list[:2]]) else 0
    score += 15 if 6 <= len(threads_hook) <= 34 else 5
    score += 10 if _contains_any(poster_headline, [form.product_name, form.offer_details]) else 0
    score += 10 if _contains_any(variant_heads, [form.product_name, form.offer_details]) else 0
    return min(score, 100)


def _specificity_score(
    form: AdGenerationForm,
    result: GenerationResult,
    text: str,
) -> int:
    score = 0
    score += 16 if _normalize(form.business_name) in text else 0
    score += 16 if _normalize(form.product_name) in text else 0
    score += 14 if _normalize(form.target_customer) in text else 0
    score += 16 if _offer_coverage(form, text) >= 0.5 else 0
    score += 14 if _contains_any(text, form.keyword_list[:3]) else 0
    score += 12 if _contains_any(text, _description_terms(form.product_description)) else 0
    score += 12 if _generic_phrase_penalty(result) == 0 else 6
    return min(score, 100)


def _channel_score(form: AdGenerationForm, result: GenerationResult) -> int:
    return round(
        _instagram_score(form, result) * 0.35
        + _threads_score(form, result) * 0.30
        + _blog_score(form, result) * 0.35
    )


def _differentiation_score(result: GenerationResult) -> int:
    packages = result.channel_packages
    instagram = packages.instagram.caption
    threads = packages.threads.thread_text
    blog = f"{packages.blog.title} {packages.blog.intro} {' '.join(packages.blog.body_outline)}"
    score = 0
    score += 20 if _similarity(instagram, threads) <= 0.55 else 5
    score += 20 if _similarity(instagram, blog) <= 0.60 else 5
    score += 20 if _similarity(threads, blog) <= 0.60 else 5
    score += 15 if len(blog) > len(threads) * 1.5 else 5
    score += 15 if "?" in threads and "?" not in packages.blog.title else 5
    score += 10 if len(packages.instagram.hashtags) >= 4 and len(packages.blog.seo_keywords) >= 4 else 5
    return min(score, 100)


def _instagram_score(form: AdGenerationForm, result: GenerationResult) -> int:
    package = result.channel_packages.instagram
    caption_lines = [line for line in package.caption.splitlines() if line.strip()]
    caption_length = len(package.caption)
    hashtag_count = len(package.hashtags)
    hashtag_text = _normalize(" ".join(package.hashtags))
    score = 0
    score += 16 if 60 <= caption_length <= 420 else 8
    score += 12 if 2 <= len(caption_lines) <= 5 else 5
    score += 14 if 4 <= hashtag_count <= 8 else 7
    score += 10 if _normalize(form.product_name) in hashtag_text else 0
    score += 12 if package.visual_hook and len(package.visual_hook) >= 18 else 0
    score += 12 if package.alt_text and len(package.alt_text) >= 18 else 0
    score += 12 if _contains_any(package.caption, _action_terms(form)) else 0
    score += 12 if package.recommended_post_time else 0
    return min(score, 100)


def _threads_score(form: AdGenerationForm, result: GenerationResult) -> int:
    package = result.channel_packages.threads
    text = package.thread_text
    score = 0
    score += 20 if 60 <= len(text) <= 280 else 10
    score += 16 if "?" in text or "?" in package.reply_prompt else 0
    score += 14 if _contains_any(text, [form.product_name, form.business_name]) else 0
    score += 14 if _contains_any(text, [form.target_customer, *form.keyword_list[:2]]) else 0
    score += 12 if len(package.short_hook) <= 34 else 4
    score += 12 if package.reply_prompt and len(package.reply_prompt) >= 12 else 0
    score += 12 if package.recommended_post_time else 0
    return min(score, 100)


def _blog_score(form: AdGenerationForm, result: GenerationResult) -> int:
    package = result.channel_packages.blog
    title = package.title
    keyword_text = _normalize(" ".join(package.seo_keywords))
    score = 0
    score += 14 if 16 <= len(title) <= 90 else 7
    score += 14 if _contains_any(title, [form.business_name, form.product_name]) else 0
    score += 14 if len(package.intro) >= 120 else 7
    score += 12 if len(package.body_outline) >= 4 else 0
    score += 12 if len(package.seo_keywords) >= 4 else 6
    score += 10 if _normalize(form.product_name) in keyword_text else 0
    score += 10 if _normalize(form.business_name) in keyword_text else 0
    score += 10 if 50 <= len(package.meta_description) <= 170 else 5
    score += 14 if _contains_any(package.cta, _action_terms(form)) else 0
    return min(score, 100)


def _cta_score(form: AdGenerationForm, result: GenerationResult, text: str) -> int:
    action_terms = _action_terms(form)
    cta_text = _normalize(
        " ".join(
            [
                result.cta,
                result.channel_packages.instagram.caption,
                result.channel_packages.blog.cta,
                result.channel_packages.poster.cta,
                result.channel_packages.threads.reply_prompt,
            ]
        )
    )
    score = 0
    score += 30 if _contains_any(cta_text, action_terms) else 0
    score += 20 if _contains_any(cta_text, [form.desired_action, form.cta_focus]) else 0
    score += 15 if "?" in result.channel_packages.threads.reply_prompt else 0
    score += 15 if _contains_any(text, ["조건", "혜택", "문의", "예약", "방문", "저장", "링크"]) else 0
    score += 20 if len(result.pre_publish_checklist) >= 3 else 0
    return min(score, 100)


def _compliance_score(result: GenerationResult, text: str) -> int:
    risky_hits = sum(1 for claim in RISKY_CLAIMS if _normalize(claim) in text)
    generic_hits = _generic_phrase_penalty(result)
    score = 100 - risky_hits * 25 - generic_hits * 4
    return max(0, min(score, 100))


def _structure_score(result: GenerationResult) -> int:
    score = 0
    score += 10 if len(result.variants) >= 3 else 0
    score += 10 if len(result.hashtags) >= 3 else 0
    score += 10 if len(result.channel_packages.instagram.hashtags) >= 4 else 5
    score += 10 if len(result.pre_publish_checklist) >= 3 else 0
    score += 10 if result.channel_packages.instagram.alt_text else 0
    score += 10 if result.channel_packages.instagram.visual_hook else 0
    score += 10 if result.channel_packages.threads.reply_prompt else 0
    score += 10 if len(result.channel_packages.blog.body_outline) >= 4 else 0
    score += 10 if len(result.channel_packages.blog.seo_keywords) >= 4 else 5
    score += 5 if result.channel_quality.blog_score >= 0 else 0
    score += 5 if result.background_asset is None or result.background_asset.prompt else 0
    return min(score, 100)


def _quality_report_score(form: AdGenerationForm, result: GenerationResult) -> int:
    report = result.quality_report
    channel_report = result.channel_quality
    scores = [
        report.hook_score,
        report.clarity_score,
        report.cta_score,
        report.channel_fit_score,
        report.overall_score,
        channel_report.instagram_score,
        channel_report.threads_score,
        channel_report.blog_score,
    ]
    if not all(0 <= score <= 100 for score in scores):
        return 0
    score = round(sum(scores) / len(scores))
    if len(report.improvement_suggestions) < 2:
        score -= 20
    if len(channel_report.regeneration_suggestions) < 2:
        score -= 10
    if result.auto_approved and report.overall_score < 82:
        score -= 15
    suggestion_text = _normalize(
        " ".join(report.improvement_suggestions + channel_report.regeneration_suggestions)
    )
    specific_terms = [
        form.business_name,
        form.product_name,
        form.offer_details,
        form.desired_action,
        *form.keyword_list[:2],
    ]
    if not any(_normalize(term) in suggestion_text for term in specific_terms if term):
        score -= 12
    if not any(_normalize(term) in suggestion_text for term in [form.business_name, form.product_name]):
        score -= 8
    return max(0, min(score, 100))


def _normalize(value: str) -> str:
    return value.lower().replace(" ", "").replace("\n", "")


def _first_line(value: str) -> str:
    for line in value.splitlines():
        if line.strip():
            return line.strip()
    return value.strip()


def _contains_any(text: str, terms: list[str] | tuple[str, ...]) -> bool:
    normalized = _normalize(text)
    return any(_normalize(term) in normalized for term in terms if term)


def _similarity(left: str, right: str) -> float:
    left_terms = _token_set(left)
    right_terms = _token_set(right)
    if not left_terms or not right_terms:
        return 1.0
    intersection = len(left_terms & right_terms)
    union = len(left_terms | right_terms)
    return intersection / union


def _token_set(value: str) -> set[str]:
    cleaned = (
        value.lower()
        .replace("\n", " ")
        .replace(",", " ")
        .replace(".", " ")
        .replace("?", " ")
        .replace("!", " ")
        .replace("#", " ")
    )
    return {token.strip() for token in cleaned.split() if len(token.strip()) >= 2}


def _benefit_terms(form: AdGenerationForm) -> list[str]:
    terms = [
        form.offer_details,
        form.promotion_goal,
        form.desired_action,
        "혜택",
        "할인",
        "무료",
        "예약",
        "방문",
        "시즌",
    ]
    return [term for term in terms if term]


def _action_terms(form: AdGenerationForm) -> tuple[str, ...]:
    return ACTION_TERMS.get(form.desired_action, (form.desired_action, form.cta_focus))


def _description_terms(description: str) -> list[str]:
    return [
        token.strip(".,!? ")
        for token in description.replace("으로", " ").replace("하고", " ").split()
        if len(token.strip(".,!? ")) >= 2
    ][:5]


def _offer_coverage(form: AdGenerationForm, text: str) -> float:
    if not form.offer_details:
        return 1.0
    terms = [term for term in _description_terms(form.offer_details) if term]
    if not terms:
        return 1.0
    matched = sum(1 for term in terms if _normalize(term) in text)
    return matched / len(terms)


def _generic_phrase_penalty(result: GenerationResult) -> int:
    text = _combined_text_without_background(result)
    return sum(1 for phrase in GENERIC_PHRASES if _normalize(phrase) in text)


def _combined_text_without_background(result: GenerationResult) -> str:
    packages = result.channel_packages
    return _normalize(
        " ".join(
            [
                result.headline,
                result.body_copy,
                result.caption,
                result.strategy_note,
                packages.instagram.caption,
                packages.threads.thread_text,
                packages.blog.intro,
                packages.poster.subcopy,
                *[variant.body_copy for variant in result.variants],
            ]
        )
    )
