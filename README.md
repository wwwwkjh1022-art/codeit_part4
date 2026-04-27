# 소상공인 AI 홍보 자동화 서비스

소상공인이 상품 또는 서비스 정보만 입력하면 AI가 Instagram, Threads, Blog용 홍보 콘텐츠를 생성하고, 결과 페이지에서 이미지 재생성, 채널 연결, 예약/게시 흐름까지 이어서 처리할 수 있는 FastAPI 기반 MVP입니다.

## 제출 바로가기

- Github Repository: [codeit_part4](https://github.com/wwwwkjh1022-art/codeit_part4)
- 보고서 PDF: [보고서.pdf](제출용_패키지/보고서.pdf)
- 협업 일지 PDF: [업무일지_정리.pdf](제출용_패키지/업무일지_정리.pdf)

## 프로젝트 소개

이 프로젝트는 단순 문구 생성기가 아니라, 실제 서비스 형태로 사용할 수 있는 광고 콘텐츠 생성 도구를 목표로 만들었습니다.

- 하나의 브리프로 3개 채널용 콘텐츠 생성
- 결과 페이지에서 이미지 재생성, 채널별 미리보기, 게시 전 편집 제공
- 생성 이력 저장, 재생성, 예약 준비 상태 관리
- Instagram / Threads 직접 API 게시, Naver Blog Playwright 게시 구조 제공
- n8n 기반 자동화 확장을 위한 API 및 워크플로우 구조 제공

## 주요 기능

- Instagram, Threads, Blog 채널별 홍보 패키지 생성
- OpenAI 문구 생성 실패/지연 시 mock fallback 자동 전환
- 결과 페이지의 `이미지 생성` 탭에서 참고 이미지 업로드 + 프롬프트 수정 + 재생성
- 업로드 이미지가 있으면 사진을 우선 살린 깔끔한 배너 미리보기 생성
- 결과 페이지의 `콘텐츠 편집` 탭에서 Instagram / Threads / Blog 문구 실시간 수정
- 생성 이력 저장 및 상세 조회
- 같은 브리프로 재생성
- 직접 API 게시 / mock 게시 / 예약 게시 흐름 지원
- Instagram / Threads API 값 저장 UI 제공
- Naver Blog Playwright 연결 버튼 제공
- Stable Diffusion 3.5 / OpenAI / Gemini 계열 이미지 생성 확장 구조 제공

## 기술 스택

- Backend: FastAPI, Uvicorn, Pydantic
- Frontend: Jinja2, HTML, CSS, Vanilla JavaScript
- AI: OpenAI Responses API, mock fallback generator
- Image: Pillow, SD3.5/OpenAI/Gemini provider 확장 구조
- Browser Automation: Playwright (Naver Blog 게시용)
- Test: pytest, pytest-asyncio

## 빠른 실행

### 1. 가상환경 및 의존성 설치

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
.venv/bin/playwright install chromium
```

### 2. 서버 실행

```bash
python run.py
```

브라우저에서 `http://127.0.0.1:8000`으로 접속하면 됩니다.

### 3. 기본 동작 방식

- `OPENAI_API_KEY`가 있으면 OpenAI 생성기를 사용합니다.
- 키가 없거나 호출이 실패하면 mock fallback으로 결과를 생성합니다.
- 이미지 생성은 기본적으로 로컬 SD3.5 엔드포인트 또는 fallback 구조를 사용합니다.
- 브리프 입력 단계에서는 이미지를 받지 않고, 결과 페이지의 `이미지 생성` 탭에서 참고 이미지를 넣어 다시 생성합니다.

## 현재 UX 흐름

1. 브리프를 입력해 문구/초기 배너를 생성합니다.
2. 결과 페이지 상단 `이미지 생성` 탭에서 참고 이미지와 프롬프트를 조정합니다.
3. 필요하면 `콘텐츠 편집` 탭에서 채널별 문구를 다듬습니다.
4. 오른쪽 카드에서 Instagram / Threads / Blog 연결값을 입력합니다.
5. `예약 준비 완료`, `자동 업로드 예약 저장`, `Mock 게시 실행`으로 후속 작업을 진행합니다.

## 환경 변수

- `COPY_PROVIDER=auto`: `OPENAI_API_KEY`가 있으면 OpenAI, 없으면 mock 사용
- `PUBLIC_BASE_URL`: n8n과 외부 게시 API가 접근할 수 있는 서비스 기본 URL
- `OPENAI_API_KEY`: OpenAI API 키
- `OPENAI_MODEL`: 기본값 `gpt-5-mini`
- `OPENAI_REASONING_EFFORT`: 기본값 `low`, 빠른 생성 우선
- `MAX_GENERATION_ATTEMPTS`: 기본값 `1`, 높이면 품질 재시도는 늘지만 응답 시간이 길어짐
- `IMAGE_PROVIDER=sd35`: 로컬 SD wrapper 서버로 배경 이미지 생성
- `GEMINI_API_KEY`: 추후 Gemini/Nano Banana 이미지 생성 API를 붙일 때 사용할 키
- `GEMINI_IMAGE_MODEL`: 기본값 `gemini-2.5-flash-image`
- `OPENAI_IMAGE_MODEL`: 기본값 `gpt-image-1-mini`
- `OPENAI_IMAGE_QUALITY`: 기본값 `low`
- `SD35_ENDPOINT_URL`: 로컬 또는 원격 이미지 생성 엔드포인트
- `SD35_API_KEY`: SD3.5 엔드포인트가 Bearer 토큰을 요구할 때 사용하는 키
- `SD35_MODEL`: 기본값 `stabilityai/sdxl-turbo`
- `ALLOW_PAID_IMAGE_GENERATION=false`: 실수 과금 방지를 위해 기본값은 비활성화
- `NAVER_BLOG_HEADLESS=true`: 네이버 블로그 Playwright 실행 시 headless 여부
- `NAVER_BLOG_TIMEOUT_MS=45000`: 네이버 블로그 로그인/발행 대기 시간
- `NAVER_BLOG_CONNECT_TIMEOUT_SECONDS=300`: 웹에서 로그인 창을 열었을 때 연결 확인 대기 시간

## 프로젝트 구조

```text
app/                FastAPI 앱, 라우트, 서비스, 템플릿
automations/        n8n workflow 파일
docs/               프로젝트 문서 및 포트폴리오 자료
eval_resources/     평가 기준, 데이터셋, 최신 평가 리포트
evaluations/        자동 평가 코드
tests/              테스트 코드
제출용_패키지/      제출용 보고서/업무일지 원고
```

## 테스트

```bash
.venv/bin/pytest
```

생성 품질 평가만 따로 확인하려면 아래 명령을 사용합니다.

```bash
.venv/bin/pytest tests/test_generation_quality.py -q
```

평가 데이터셋은 `evaluations/testset.py`, 채점 로직은 `evaluations/scorer.py`에 있습니다. 현재 품질 게이트는 채널별 구조, 키워드 반영, 품질 리포트 점수, 게시 준비성을 기준으로 통과 여부를 판단합니다. 기본 기준은 전체 82점 이상, 채널 점수 80점 이상입니다.

생성 이력과 예약 큐는 로컬 개발 기준 `data/campaigns.json`에 저장됩니다. 이 파일은 `.gitignore`에 포함되어 있어 원격 저장소에 올라가지 않습니다.

## AI 배경 이미지 생성 준비 구조

현재 기본 설정은 빠른 로컬 `sd35` wrapper 엔드포인트를 호출하는 `sd35`입니다. 기본값은 `stabilityai/sdxl-turbo`와 낮은 step 설정이라 웹 시연에서 응답 속도를 우선합니다.

참고 이미지를 업로드해 재생성하는 경우에는, 현재 구현상 업로드 이미지를 우선 사용하고 과한 텍스트 오버레이를 제거한 사진 중심 배너 미리보기를 만듭니다.

로컬 모델 서버가 없거나 잠시 끄고 싶으면 아래처럼 프롬프트 전용 모드로 바꿀 수 있습니다.

```bash
IMAGE_PROVIDER=prompt_only
```

OpenAI GPT Image API로 자동 생성을 켜려면 `.env`에 아래 값을 설정합니다.

```bash
IMAGE_PROVIDER=openai
OPENAI_IMAGE_MODEL=gpt-image-1-mini
OPENAI_IMAGE_QUALITY=low
ALLOW_PAID_IMAGE_GENERATION=true
```

Gemini/Nano Banana API를 쓰려면 아래 값을 설정합니다.

```bash
IMAGE_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key
GEMINI_IMAGE_MODEL=gemini-2.5-flash-image
ALLOW_PAID_IMAGE_GENERATION=true
```

이 옵션을 켜기 전까지는 API 키가 있어도 이미지 API를 호출하지 않습니다.

로컬 wrapper 서버는 아래처럼 설정합니다. 기본은 빠른 `sdxl-turbo` 조합입니다. ComfyUI 앞에 간단한 wrapper를 붙이거나, 직접 만든 FastAPI 추론 서버처럼 `prompt`를 받아 이미지를 반환하는 엔드포인트를 연결하면 됩니다.

```bash
IMAGE_PROVIDER=sd35
SD35_ENDPOINT_URL=http://127.0.0.1:8188/sd35/generate
SD35_API_KEY=
SD35_MODEL=stabilityai/sdxl-turbo
SD35_WIDTH=1024
SD35_HEIGHT=768
SD35_STEPS=4
SD35_GUIDANCE_SCALE=2.0
SD35_FALLBACK_TO_LOCAL=true
ALLOW_PAID_IMAGE_GENERATION=false
```

로컬 `sd35` provider는 유료 API가 아니므로 `ALLOW_PAID_IMAGE_GENERATION=false`여도 실행됩니다. `sd35` provider는 응답이 `image/png`, `image/jpeg`, `image_base64`, `b64_json`, `data[0].b64_json`, `image_url` 중 하나면 자동으로 저장합니다. 따라서 실제 SD3.5 서버 구현체가 달라도 어댑터를 크게 바꾸지 않고 연결할 수 있습니다.

로컬 SD3.5 서버가 아직 떠 있지 않은 경우에도 `SD35_FALLBACK_TO_LOCAL=true`이면 앱 내부 Pillow 기반 배경 생성기로 대체 이미지를 만들고 배너 합성에 사용합니다. 이 fallback은 실제 SD3.5 모델 이미지는 아니지만, 발표/시연 중 이미지가 비어 보이지 않도록 하는 안전장치입니다.

발표/실험 관리용 평가 리소스는 `eval_resources/`에 있습니다.

- `eval_resources/METRICS.md`: 최신 광고 흐름을 반영한 평가 기준과 루브릭
- `eval_resources/AD_RESEARCH_NOTES.md`: Instagram, Threads, Blog, Gemini 이미지 생성 관련 리서치 메모
- `eval_resources/eval_dataset.yaml`: 시나리오별 평가 데이터셋
- `eval_resources/eval_report_latest.md`: 최근 평가 리포트

리포트는 아래 명령으로 다시 생성할 수 있습니다.

```bash
.venv/bin/python scripts/run_generation_eval.py
```

## 자동화 API

브라우저 UI와 별도로 n8n 같은 자동화 도구가 사용할 수 있는 JSON API를 제공합니다.

- `POST /api/campaigns/generate`
- `GET /api/campaigns/{campaign_id}`
- `POST /api/campaigns/{campaign_id}/ready`
- `POST /api/campaigns/{campaign_id}/schedule`
- `GET /api/campaigns/{campaign_id}/publish-payload`
- `GET /api/publish-jobs/due`
- `POST /api/campaigns/{campaign_id}/publish-jobs/{job_id}/complete`

## 게시 연동 상태

- Instagram: Access Token + User ID 저장 후 직접 API 게시 가능
- Threads: Access Token + User ID 저장 후 직접 API 게시 가능
- Blog / WordPress: REST API 기반 게시 가능
- Blog / Naver Blog: Playwright 브라우저 자동화 기반 게시 가능

주의:

- Instagram / Threads는 외부에서 접근 가능한 `PUBLIC_BASE_URL`이 필요합니다.
- Naver Blog는 CAPTCHA, 추가 인증, 로그인 정책에 따라 자동화가 막힐 수 있습니다.
- Playwright 브라우저 의존성이 필요한 환경에서는 `playwright install chromium` 및 시스템 라이브러리 설치가 필요할 수 있습니다.

## 포트폴리오 문서

- 발표용 슬라이드 원고: `docs/PRESENTATION_DECK.md`
- 개발 타임라인, 기술스택, 실험 과정, 막힌 부분과 해결 과정은 `docs/PORTFOLIO_TIMELINE.md`에 정리되어 있습니다.
- Instagram/Blog API 연동 설계는 `docs/API_INTEGRATION_GUIDE.md`에 정리되어 있습니다.
- n8n 자동화 설계와 import용 workflow는 `docs/N8N_AUTOMATION_GUIDE.md`, `automations/n8n_campaign_automation.json`에 정리되어 있습니다.
- 로컬 Stable Diffusion 3.5 wrapper 연결 방법은 `docs/SD35_WRAPPER_GUIDE.md`에 정리되어 있습니다.

## 네이버 블로그 연동

- Blog 채널은 기본값으로 `Naver Blog (Playwright)` 연결 폼을 제공합니다.
- 결과 페이지에서 `네이버 로그인 창 열기` 버튼을 누르면 Chromium 창이 열리고, 네이버 로그인 후 글쓰기 화면까지 진입하면 세션이 저장됩니다.
- 저장된 브라우저 세션이 있으면 이후 Blog 게시 시 해당 세션을 재사용합니다.
- 첫 로그인 시 CAPTCHA 또는 추가 인증이 걸리면 자동화가 멈출 수 있습니다. 이 경우 한 번 수동 로그인해 저장된 세션을 만든 뒤 다시 시도하는 방식이 더 안정적입니다.

## 보안 메모

- 실제 API 키는 `.env`에만 두고, 저장소에는 올리지 않습니다.
- 커밋 전에 비밀값을 막기 위한 훅은 `.githooks/pre-commit`에 있습니다.
- 관련 안내는 `SECURITY.md`에 정리되어 있습니다.

## 제출 자료

- 제출용 패키지 안내: [제출용_패키지/README.md](제출용_패키지/README.md)
- 보고서 원고: [제출용_패키지/보고서_원고.md](제출용_패키지/보고서_원고.md)
- 보고서 PDF: [제출용_패키지/보고서.pdf](제출용_패키지/보고서.pdf)
- 협업 일지 정리본: [제출용_패키지/업무일지_정리.md](제출용_패키지/업무일지_정리.md)
- 협업 일지 PDF: [제출용_패키지/업무일지_정리.pdf](제출용_패키지/업무일지_정리.pdf)
