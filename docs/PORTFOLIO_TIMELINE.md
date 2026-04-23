# 소상공인 AI 홍보 자동화 서비스 개발 일지

## 프로젝트 한 줄 소개

소상공인이 상품 정보만 입력하면 AI가 Instagram, Threads, Blog에 맞는 홍보 콘텐츠를 생성하고, 향후 자동 예약 게시까지 확장할 수 있도록 설계한 AI 마케팅 자동화 MVP입니다.

## 사용 기술스택

### Backend

- Python 3.12
- FastAPI
- Uvicorn
- Pydantic / Pydantic Settings
- Jinja2 Template
- python-multipart

### AI

- OpenAI Responses API
- gpt-5-mini 기본 사용
- Structured Outputs 기반 JSON Schema 응답 강제
- mock/rule-based fallback 생성기

### Image

- Pillow
- 로컬 템플릿 기반 배너/포스터 합성
- 한글 폰트 렌더링: NanumGothic

### Testing

- pytest
- pytest-asyncio
- FastAPI TestClient
- mock provider 기반 로컬 테스트

### Frontend

- HTML
- CSS
- Jinja2 SSR
- Vanilla JavaScript

## 핵심 문제 정의

소상공인은 좋은 상품이나 서비스를 가지고 있어도 온라인 홍보 콘텐츠를 꾸준히 만들기 어렵습니다. 특히 Instagram, Threads, Blog는 같은 내용을 올리더라도 문체, 길이, 정보량이 달라야 합니다.

이 프로젝트는 단순 문구 생성기를 넘어서, 소상공인이 댓글 응대만 직접 하고 나머지 콘텐츠 생성, 게시 준비, 향후 예약 발행까지 자동화할 수 있는 기반을 만드는 것을 목표로 했습니다.

## 개발 타임라인

### 1단계: 로컬 개발 환경 구성

- 현재 폴더 밖으로 나가지 않고 `.venv` 가상환경을 생성했습니다.
- Python 3.12.3 기반으로 프로젝트를 시작했습니다.
- `.env`를 통해 API 키를 관리하고, `.gitignore`에 `.env`, `.venv`, 생성 파일 경로를 제외했습니다.

막힌 부분:

- 초기 폴더에는 `.venv` 외에 아무 코드가 없는 완전 빈 상태였습니다.

해결:

- 처음부터 `app/`, `routes/`, `services/`, `schemas/`, `templates/`, `static/`, `tests/`로 구조를 나눠 확장 가능한 형태로 시작했습니다.

### 2단계: FastAPI 기반 MVP 구축

- `GET /` 입력 페이지를 만들었습니다.
- `POST /generate` 생성 라우트를 만들었습니다.
- `GET /health` 상태 확인 라우트를 만들었습니다.
- Jinja2 템플릿으로 입력 화면과 결과 화면을 구성했습니다.
- CSS로 소상공인 마케팅 도구처럼 보이는 따뜻한 톤의 UI를 만들었습니다.

실험한 것:

- Streamlit보다 FastAPI + HTML 구조를 선택했습니다.
- 이유는 추후 Instagram/Threads OAuth, 예약 게시 API, 상태 저장 구조로 확장하기 좋기 때문입니다.

### 3단계: 생성 계층 분리

- `CopyGenerator` 개념을 도입해 AI 생성기를 교체 가능한 구조로 만들었습니다.
- OpenAI API가 없거나 실패해도 mock 생성기로 fallback되도록 했습니다.
- 실제 API 연동 전에도 테스트가 가능하도록 mock provider를 기본 테스트 모드로 사용했습니다.

막힌 부분:

- OpenAI API 키가 잘못되어 `401 invalid_api_key`가 발생했습니다.
- 사용자는 화면에서 단순히 `mock-fallback` 결과만 보게 되어 원인을 알기 어려웠습니다.

해결:

- 인증 실패와 API 실패를 구분해 사용자에게 더 정확한 경고 메시지를 보여주도록 바꿨습니다.
- `.env` 수정 후 서버를 재시작해야 새 키가 반영된다는 운영 흐름도 확인했습니다.

### 4단계: 배너/포스터 미리보기 생성

- Pillow를 사용해 로컬에서 배너 이미지를 생성했습니다.
- 업로드 이미지가 있으면 배너에 합성하고, 없으면 텍스트 중심 플레이스홀더를 그렸습니다.
- `따뜻한 감성`, `미니멀`, `강한 세일형`, `프리미엄`, `산뜻한 시즌형` 스타일에 따라 색감이 바뀌도록 했습니다.

막힌 부분:

- 업로드 이미지 경로가 정적 파일 경로와 로컬 파일 경로 사이에서 어긋났습니다.

해결:

- `/static/...` URL을 `settings.static_dir` 기준 파일 경로로 변환하도록 수정했습니다.

### 5단계: 입력 검증 안정화

- `product_description`이 너무 짧을 때 Pydantic 검증 에러가 그대로 올라와 500 에러가 발생했습니다.

해결:

- `RequestValidationError`를 처리하는 예외 핸들러를 추가했습니다.
- 500 대신 입력 화면으로 돌아가고, 사용자가 어떤 필드를 고쳐야 하는지 한국어 라벨로 보여주게 했습니다.
- 회귀 방지를 위해 짧은 설명 입력 테스트를 추가했습니다.

### 6단계: 생성 품질 1차 고도화

- 기존 결과는 단일 캡션 중심이어서 최종 자동화 서비스로 확장하기에는 부족했습니다.
- 결과 구조를 `채널별 게시 패키지` 중심으로 확장했습니다.

추가된 생성 결과:

- Instagram 패키지: 캡션, 해시태그, ALT 텍스트, 비주얼 후킹, 추천 게시 시간
- Threads 패키지: 스레드 본문, 댓글 유도 질문, 짧은 후킹 문구, 추천 게시 시간
- Blog 패키지: 헤드라인, 보조 문구, CTA, 비주얼 방향
- 품질 리포트: 후킹 점수, 명확성 점수, CTA 점수, 채널 적합도 점수, 전체 점수, 수정 제안
- 자동예약 전 체크리스트: 게시 전 확인해야 할 운영 항목

실험한 것:

- 단순 JSON 요청 대신 OpenAI Responses API의 Structured Outputs를 적용했습니다.
- 모델이 임의 형식으로 응답하는 위험을 줄이고, 채널별 결과 구조를 안정적으로 받을 수 있게 했습니다.

막힌 부분:

- 기존에는 응답 텍스트에서 JSON을 찾아 파싱하는 방식이라, 모델이 형식을 조금만 벗어나도 실패 가능성이 있었습니다.

해결:

- `text.format`에 JSON Schema를 넣어 응답 구조를 강제했습니다.
- 그래도 일부 필드가 부족할 상황에 대비해 normalize fallback 로직을 추가했습니다.

### 7단계: 테스트 확장

- 기존 테스트 7개에서 생성 고도화 후 8개 테스트로 확장했습니다.
- mock 생성기가 Instagram, Threads, Blog 패키지를 모두 반환하는지 확인했습니다.
- 품질 점수가 0~100 범위인지 확인했습니다.
- OpenAI normalize 로직이 누락 필드를 안전하게 채우는지 확인했습니다.
- 배너 생성기가 보조 포스터 패키지의 헤드라인, 보조 문구, CTA를 반영하는지 확인했습니다.

현재 테스트 결과:

```text
8 passed
```

### 8단계: 생성 품질 평가 테스트셋 구축

- 기능 테스트만으로는 “생성물이 실제로 좋은지” 판단하기 어렵다고 보고 별도 평가 체계를 만들었습니다.
- `evaluations/testset.py`에 카페, 꽃집, 네일샵, 식당 시나리오를 고정 테스트셋으로 만들었습니다.
- 각 케이스에는 기대 키워드, 최소 전체 점수, 최소 채널 점수를 지정했습니다.
- `evaluations/scorer.py`에 휴리스틱 채점기를 구현했습니다.
- 참고 프로젝트의 `eval_resources` 구조처럼 `METRICS.md`, `eval_dataset.yaml`, `eval_report_latest.md`를 분리해 발표/실험 관리용 리소스로 정리했습니다.

평가 기준:

- 기대 키워드가 결과에 반영되었는지
- Instagram, Threads, Blog 패키지 구조가 모두 채워졌는지
- Threads 문구가 너무 길지 않고 댓글 유도 문장이 있는지
- Blog 헤드라인이 짧고 CTA가 명확한지
- 품질 리포트 점수가 0~100 범위인지
- 수정 제안이 2개 이상 제공되는지

현재 전체 테스트 결과:

```text
12 passed
```

최근 평가 리포트:

```text
eval_resources/eval_report_latest.md
```

### 9단계: 자동화 기반을 위한 생성 이력 관리

- 생성 결과가 화면에서만 사라지는 문제를 해결하기 위해 로컬 JSON 저장소를 추가했습니다.
- `data/campaigns.json`에 생성 캠페인, 입력 브리프, 채널별 결과, 품질 리포트, 배너 경로를 저장하도록 했습니다.
- `/campaigns` 이력 페이지를 추가해 과거 생성물을 다시 열 수 있게 했습니다.
- `/campaigns/{id}` 상세 페이지에서 저장된 결과를 다시 확인할 수 있게 했습니다.
- 같은 브리프로 재생성하는 기능을 추가했습니다.
- 캠페인 상태를 `초안`에서 `예약 준비 완료`로 바꿀 수 있게 했습니다.

의미:

- 아직 Instagram/Threads 게시 API를 붙이지 않았지만, 이후 예약 게시 큐나 DB로 확장할 수 있는 최소 단위가 생겼습니다.
- 최종 자동화에서 필요한 `생성 결과 저장 -> 검수 -> 예약 준비 -> 게시` 흐름의 첫 기반을 만들었습니다.

현재 전체 테스트 결과:

```text
16 passed
```

### 10단계: Instagram/Threads API 연동 전 예약 큐 설계

- 계정/비밀번호 입력 방식은 보안과 정책 리스크가 크기 때문에 공식 API + OAuth 방향으로 결정했습니다.
- 실제 Meta 연동 전 단계로 게시 어댑터 인터페이스와 mock 게시자를 만들었습니다.
- 캠페인 안에 `publish_jobs`를 저장해 예약 채널, 예약 시간, 게시 상태, 외부 게시 ID를 기록할 수 있게 했습니다.
- `/campaigns/{id}/schedule`로 Instagram/Threads 예약 작업을 만들 수 있습니다.
- `/campaigns/{id}/publish-now`로 mock 게시를 실행해 이후 실제 API 연동 흐름을 시뮬레이션할 수 있습니다.

의미:

- 지금은 실제 게시를 하지 않지만, 나중에 `MockPublishAdapter`를 `InstagramPublisher`, `ThreadsPublisher`로 교체하면 됩니다.
- 최종 자동화 목표인 `생성 -> 검수 -> 예약 -> 게시 -> 결과 ID 저장` 흐름의 기본 뼈대가 생겼습니다.

현재 전체 테스트 결과:

```text
18 passed
```

### 11단계: 제출용 생성 자동화 범위 정리

- 실제 Instagram/Threads API 연동은 제출 범위에서 제외하고, 광고문구 생성 자동화에 집중하기로 했습니다.
- 하나의 원본 브리프를 바탕으로 Instagram, Threads, Blog 세 가지 버전이 생성되도록 구조를 바꿨습니다.
- 각 채널은 서로 다른 목적과 분위기를 갖도록 분리했습니다.
- Instagram은 감성적이고 시각 후킹 중심으로 생성합니다.
- Threads는 짧고 자연스러운 대화형 문구로 생성합니다.
- Blog는 설명력, 신뢰감, SEO 키워드 중심으로 생성합니다.
- 자동 평가 기준은 전체 82점 이상, 채널별 80점 이상으로 설정했습니다.
- 기준을 통과하지 못하면 자동 재생성 루프를 통해 더 나은 결과를 선택하도록 했습니다.

실제 OpenAI 검증 결과:

```text
provider_used = openai
auto_approved = True
attempts = 2
instagram_score = 90
threads_score = 84
blog_score = 80
```

### 12단계: Gemini/Nano Banana 이미지 생성 확장 설계

- 배경 이미지를 바로 API로 생성하면 비용이 발생할 수 있어, 기본값은 `prompt_only`로 유지했습니다.
- 결과 화면에 Gemini/Nano Banana용 배경 이미지 프롬프트를 자동 생성하도록 추가했습니다.
- 사용자는 이 프롬프트를 Gemini 웹 또는 Google AI Studio에 복사해 무료/수동 생성한 이미지를 다시 업로드할 수 있습니다.
- 추후 예산이 생기면 `IMAGE_PROVIDER=gemini`, `GEMINI_API_KEY`, `ALLOW_PAID_IMAGE_GENERATION=true` 설정만으로 Gemini 이미지 API 호출을 켤 수 있도록 어댑터 구조를 만들었습니다.
- API 호출이 켜진 경우에는 생성된 배경 이미지를 `app/static/generated/backgrounds/`에 저장하고, 배너 합성의 배경으로 사용하도록 설계했습니다.

막힌 부분:

- Nano Banana API는 무료 티어가 없는 모델이라 제출용 개발 중 자동 호출하면 비용이 발생할 수 있습니다.
- 계정 로그인 기반 자동화는 보안과 정책 리스크가 있어 배제했습니다.

해결:

- 비용이 드는 실제 이미지 생성은 명시적인 환경 변수 2개가 모두 켜졌을 때만 실행되도록 했습니다.
- 기본 흐름은 “프롬프트 생성 -> Gemini 웹에서 수동 생성 -> 이미지 업로드 -> 배너 합성”으로 잡아 비용 없이 시연 가능하게 했습니다.

현재 전체 테스트 결과:

```text
21 passed
```

### 13단계: 최신 광고 흐름 반영 평가 지표 강화

- 기존 평가는 구조 완성도와 키워드 포함 여부 중심이라, 실제 광고처럼 설득력 있는지 판단하기에는 부족했습니다.
- 최신 SNS 운영 흐름을 참고해 평가 축을 `Hook Strength`, `Specificity`, `Channel-Native Readiness`, `CTA Strength`, `Compliance Safety` 중심으로 재설계했습니다.
- Instagram은 첫 줄 후킹, 2~6줄 캡션, 4~8개 해시태그, ALT 텍스트, visual_hook, 저장/방문 유도를 평가합니다.
- Threads는 60~280자 대화형 문장, 댓글 유도 질문, 짧은 hook, 과도한 광고문 회피를 평가합니다.
- Blog는 검색 의도형 제목, 충분한 도입문, 본문 개요, SEO 키워드, 메타 설명 길이, CTA를 평가합니다.
- “좋은 상품입니다”, “확인해보세요”처럼 일반적인 문구를 일부러 넣은 실패 테스트를 추가해 평가기가 허술한 결과를 통과시키지 않는지 확인했습니다.
- Instagram, Threads, Blog 문구가 거의 같은 복붙 결과일 때 실패하도록 `Channel Differentiation` 평가를 추가했습니다.
- 품질 리포트의 수정 제안도 실제 입력 브리프의 상호명, 상품명, 혜택, 행동 유도를 반영하는지 확인하도록 강화했습니다.
- 평가 리포트는 `Keyword/Structure/Quality` 중심에서 `Hook/Specificity/CTA/Compliance`까지 보이는 형태로 확장했습니다.

현재 전체 테스트 결과:

```text
24 passed
```

최근 평가 리포트:

```text
passed: 4/4
min_overall_score: 88
min_channel_score: 86
latest_overall_score: 99
```

## 현재 서비스 흐름

1. 사용자가 업종, 상호명, 상품 설명, 타깃 고객, 캠페인 유형, CTA 목표, 비주얼 스타일을 입력합니다.
2. OpenAI 또는 mock 생성기가 채널별 홍보 패키지를 생성합니다.
3. 결과 화면에서 Instagram, Threads, Blog 문구를 각각 확인하고 복사할 수 있습니다.
4. 품질 점수와 수정 제안을 보고 게시 전 보완할 수 있습니다.
5. 배너/포스터 이미지를 다운로드할 수 있습니다.
6. 생성 품질 테스트셋으로 시나리오별 최소 점수를 자동 검증할 수 있습니다.
7. 생성 이력에서 과거 캠페인을 다시 열고, 같은 브리프로 재생성하거나 예약 준비 상태로 표시할 수 있습니다.
8. Instagram/Threads 게시 예약 큐를 만들고 mock 게시로 자동화 흐름을 검증할 수 있습니다.
9. Gemini/Nano Banana용 배경 이미지 프롬프트를 복사해 수동 생성하거나, 추후 API 설정으로 자동 배경 생성까지 확장할 수 있습니다.
10. 최신 광고 흐름을 반영한 평가 지표로 후킹, 구체성, 채널 적합성, CTA, 과장광고 리스크를 자동 검수합니다.

### 14단계: 업로드 예상 초안 프리뷰 추가

- 결과 화면에서 텍스트만 확인하면 실제 업로드 후 화면을 상상하기 어렵다는 문제가 있었습니다.
- Instagram, Threads, Blog 각각의 업로드 화면을 흉내 낸 `업로드 예상 초안` 섹션을 추가했습니다.
- Instagram 프리뷰는 프로필, 대표 이미지, 반응 버튼, 캡션이 함께 보이도록 구성했습니다.
- Threads 프리뷰는 짧은 본문, 댓글 유도 질문, 첨부 이미지가 대화형 카드처럼 보이도록 구성했습니다.
- Blog 프리뷰는 대표 이미지, 제목, 도입문, 본문 개요, 메타 설명이 한 카드에 보이도록 구성했습니다.
- 실제 게시 API 연동 전에도 사용자가 “이대로 올려도 되는지” 시각적으로 검수할 수 있게 했습니다.

현재 전체 테스트 결과:

```text
24 passed
```

최근 평가 리포트:

```text
passed: 4/4
latest_overall_score: 99
```

### 15단계: 업로드 초안 피드형 레이아웃 개선

- 초기 업로드 초안은 세 채널을 한 줄에 압축해서 보여주면서 카드가 서로 겹치고 사이드 영역을 침범하는 문제가 있었습니다.
- 프리뷰 섹션을 결과 레이아웃 전체 폭으로 분리하고, Instagram, Threads, Blog를 세로 피드처럼 길게 쌓는 구조로 변경했습니다.
- Instagram은 실제 피드처럼 프로필, 이미지, 액션, 캡션을 순서대로 보여주도록 했습니다.
- Threads는 대화형 게시물과 첨부 이미지, 답글/리포스트/공유 액션이 보이도록 했습니다.
- Blog는 대표 이미지, 제목, 도입문, 본문 개요, CTA, 메타 설명이 긴 카드 안에서 자연스럽게 이어지도록 했습니다.
- 한 화면에 모두 욱여넣는 대신 스크롤을 허용해 실제 업로드 전 검수 흐름에 더 가깝게 개선했습니다.

현재 전체 테스트 결과:

```text
24 passed
```

### 16단계: 전문적인 SaaS형 UI/UX 리디자인

- 전체 화면 톤을 과제형 데모에서 전문적인 마케팅 운영 도구 느낌으로 개선했습니다.
- 히어로 영역에 제품 요약 카드를 추가해 서비스가 단순 생성기가 아니라 캠페인 운영 도구처럼 보이도록 했습니다.
- CSS 디자인 토큰을 재정리해 배경, 패널, 카드, 버튼, 폼, 피드 프리뷰가 같은 시각 언어를 갖도록 정리했습니다.
- 입력 폼은 더 선명한 포커스 상태와 넓은 여백, 고급스러운 카드 레이어를 적용했습니다.
- 결과 화면은 품질 점수, 채널 카드, 업로드 초안, 사이드 액션의 위계를 더 명확하게 정리했습니다.
- 사이드 영역은 데스크톱에서 sticky로 동작해 배너, Gemini 프롬프트, 예약 액션을 계속 확인할 수 있게 했습니다.
- 모바일에서는 모든 섹션이 한 열로 자연스럽게 쌓이도록 반응형 규칙을 정리했습니다.

검증:

```text
12 passed
```

비고:

- 현재 샌드박스에서 FastAPI TestClient 요청이 멈추는 현상이 있어, TestClient 기반 페이지 테스트 전체 실행은 완료하지 못했습니다.
- 생성 품질, 배너 생성, 배경 프롬프트, 평가 리소스 테스트는 정상 통과했습니다.

### 17단계: GPT Image 기반 최신 광고 배너 생성 구조 적용

- 기존 배너는 단순 도형과 텍스트 템플릿 중심이라 최신 광고 소재처럼 보이지 않는 문제가 있었습니다.
- OpenAI Image API의 `gpt-image-1-mini`를 배경 이미지 생성 provider로 연결했습니다.
- `.env`에서 `IMAGE_PROVIDER=openai`, `OPENAI_IMAGE_MODEL=gpt-image-1-mini`, `OPENAI_IMAGE_QUALITY=low`, `ALLOW_PAID_IMAGE_GENERATION=true` 설정으로 실제 이미지 생성을 켜도록 구성했습니다.
- Nano Banana도 계속 사용할 수 있도록 `GEMINI_IMAGE_MODEL=gemini-2.5-flash-image` 설정을 유지했습니다.
- 배경 이미지 프롬프트는 Pinterest/Instagram 최신 광고 스타일을 참고한 방향으로 고도화했습니다.
- 배너 합성기는 기존 카드/도형 배치에서 벗어나 AI/사진 배경, 가독성 그라데이션, 강한 타이포그래피, CTA, 정보 칩이 결합된 광고형 레이아웃으로 재작성했습니다.

검증:

```text
13 passed
```

비고:

- 실제 OpenAI 이미지 생성은 비용이 발생하므로 테스트에서는 mock 처리했습니다.
- 운영 중 비용을 막으려면 `.env`에서 `ALLOW_PAID_IMAGE_GENERATION=false` 또는 `IMAGE_PROVIDER=prompt_only`로 되돌리면 됩니다.

### 18단계: 발표 슬라이드형 디자이너 UI 개선

- 사용자가 “HTML 슬라이드처럼 꾸민 디자이너 느낌”을 요청해 전체 화면의 시각 언어를 다시 조정했습니다.
- 히어로 영역을 큰 발표 슬라이드처럼 보이도록 높이, 타이포그래피, 내부 프레임, 제품 요약 메트릭을 강화했습니다.
- 주요 패널은 슬라이드 카드처럼 넓은 여백, 큰 제목, 섹션 라벨, 부드러운 유리 질감을 갖도록 다듬었습니다.
- 업로드 예상 초안 영역은 어두운 프레젠테이션 보드 위에 실제 피드 카드가 올라간 듯한 구도로 바꿨습니다.
- 전체 배경은 단순 웜톤에서 벗어나 진한 다크 그라디언트와 밝은 카드가 대비되는 프리미엄 캠페인 덱 느낌으로 조정했습니다.

검증:

```text
13 passed
```

### 19단계: 업로드 전 라이브 편집 워크벤치 추가

- 업로드 예상 화면을 단순 카드 나열에서 `라이브 게시 워크벤치` 구조로 바꿨습니다.
- 왼쪽에는 Instagram 피드처럼 보이는 미리보기 화면을 배치했습니다.
- 오른쪽에는 캡션과 해시태그를 수정할 수 있는 편집 패널을 배치했습니다.
- Vanilla JavaScript로 입력값이 바뀌면 피드 미리보기에 즉시 반영되도록 만들었습니다.
- Threads와 Blog는 아래 보조 초안 카드로 분리해, 한 화면에 억지로 겹치지 않고 검수 흐름이 이어지도록 정리했습니다.
- 사이드바에는 Instagram, Blog 로그인 연결 준비 카드를 추가했습니다.
- 실제 계정/비밀번호 저장 방식은 보안과 정책 리스크가 있어 제외하고, 향후 OAuth/API 토큰 방식으로 붙일 수 있는 UI만 먼저 만들었습니다.
- 이미지 생성은 OpenAI Image 또는 Gemini/Nano Banana provider를 켤 수 있는 구조를 유지하고, 생성된 배경이 피드 미리보기와 배너에 자연스럽게 들어가도록 설계했습니다.

막힌 부분:

- 실제 Instagram/Blog 로그인과 게시 자동화는 플랫폼별 OAuth 앱 설정, API 권한, 심사 절차가 필요해 제출용 MVP에서 바로 붙이기에는 리스크가 있었습니다.

해결:

- 이번 단계에서는 “로그인 준비 UI”, “편집 후 미리보기”, “예약/게시 mock 흐름”까지만 구현했습니다.
- 다음 단계에서 OAuth redirect, token storage, 게시 adapter를 붙이면 실제 자동화로 확장할 수 있게 화면과 데이터 흐름을 먼저 맞췄습니다.

### 20단계: Stable Diffusion 3.5 Large FP8 이미지 provider 추가

- 사용자가 Stable Diffusion 3.5 Large FP8/TensorRT 계열 모델을 배경 생성에 쓰고 싶다고 요청했습니다.
- 현재 개발 환경은 GPU 접근이 막혀 있어 앱 서버 안에서 직접 diffusers/TensorRT 추론을 실행하는 대신, 외부 SD3.5 추론 엔드포인트를 호출하는 provider 구조로 구현했습니다.
- `IMAGE_PROVIDER=sd35` 설정을 추가했습니다.
- `SD35_ENDPOINT_URL`, `SD35_API_KEY`, `SD35_MODEL`, `SD35_WIDTH`, `SD35_HEIGHT`, `SD35_STEPS`, `SD35_GUIDANCE_SCALE` 환경 변수를 추가했습니다.
- SD3.5 provider는 이미지 바이너리 응답뿐 아니라 `image_base64`, `b64_json`, `data[0].b64_json`, `image_url` 응답을 모두 처리할 수 있게 했습니다.
- 이 구조 덕분에 로컬 ComfyUI, RunPod, Hugging Face Space, NVIDIA NIM, 직접 만든 FastAPI 추론 서버 중 어떤 방식으로 SD3.5를 띄워도 앱 쪽 변경을 최소화할 수 있습니다.

막힌 부분:

- 로컬 GPU 확인 시 현재 실행 환경에서 GPU 접근이 OS에 의해 차단되어 있었습니다.
- SD3.5 Large FP8은 고품질이지만 모델이 무거워 제출용 FastAPI 서버 안에 직접 올리면 실행 안정성이 떨어질 수 있습니다.

해결:

- 앱은 프롬프트 생성과 결과 저장/합성에 집중하고, 무거운 이미지 추론은 별도 엔드포인트가 담당하도록 분리했습니다.
- 비용 방지를 위해 기존과 동일하게 `ALLOW_PAID_IMAGE_GENERATION=true`가 켜진 경우에만 실제 호출하도록 유지했습니다.

### 21단계: n8n 기반 전체 자동화 준비

- 사용자가 최종 자동화를 n8n으로 운영하고 싶다고 요청했습니다.
- 기존 `/generate` 라우트는 HTML 화면용이라 n8n이 쓰기 불편했기 때문에 JSON 기반 자동화 API를 추가했습니다.
- `POST /api/campaigns/generate`로 광고 브리프를 받아 캠페인을 생성하고, 결과 점수와 다음 액션을 JSON으로 반환하도록 했습니다.
- `GET /api/campaigns/{id}`, `POST /api/campaigns/{id}/ready`, `POST /api/campaigns/{id}/schedule`, `POST /api/campaigns/{id}/publish-now`를 추가했습니다.
- 실제 업로드 자동화를 위해 `GET /api/campaigns/{id}/publish-payload`, `GET /api/publish-jobs/due`, `POST /api/campaigns/{id}/publish-jobs/{job_id}/complete`를 추가했습니다.
- 게시 채널 타입에 `blog`를 추가해 Instagram, Threads, Blog 세 채널을 하나의 예약 작업으로 다룰 수 있게 했습니다.
- `automations/n8n_campaign_automation.json`에 import 가능한 n8n 샘플 workflow를 만들었습니다.
- `docs/N8N_AUTOMATION_GUIDE.md`에 n8n 역할 분리, Webhook payload, FastAPI API 명세, 운영 시 주의사항을 정리했습니다.

의미:

- FastAPI는 생성/평가/저장/게시 adapter를 담당하고, n8n은 스케줄링/분기/알림/외부 API 연결을 담당하는 구조가 되었습니다.
- n8n이 실제 Instagram/Threads/WordPress 업로드를 수행한 뒤 external id를 FastAPI에 다시 저장할 수 있는 콜백 구조가 생겼습니다.

### 22단계: 상품 설명 선택 입력화

- 사용자가 상품/서비스 설명을 쓰지 않아도 생성이 되도록 요청했습니다.
- 기존에는 `product_description`이 10자 미만이면 Pydantic 검증에서 실패해 생성이 막혔습니다.
- `product_description`을 선택 입력으로 바꾸고, 비어 있으면 업종, 상호명, 상품/서비스명, 톤을 바탕으로 기본 설명을 자동 생성하도록 했습니다.
- 화면에서도 상품/서비스 설명의 `required` 조건을 제거하고, 비워두면 자동 설명이 만들어진다는 안내 문구를 추가했습니다.
- n8n JSON API에서도 설명이 빈 문자열이어도 동일하게 자동 보정됩니다.

의미:

- 사용자가 최소한 상품명만 입력해도 생성이 시작됩니다.
- 소상공인 사용자가 긴 설명을 직접 작성해야 하는 부담을 줄였습니다.

### 23단계: 생성 지연 원인 진단과 속도 개선

- 사용자가 생성 시간이 너무 오래 걸린다고 보고했습니다.
- OpenAI API 키는 인증 확인 결과 정상으로 확인했습니다.
- 최근 캠페인 기록을 확인한 결과, 문구 생성이 최대 3회 반복되고 있었습니다.
- 동시에 `.env`에서 `IMAGE_PROVIDER=openai`, `ALLOW_PAID_IMAGE_GENERATION=true`가 켜져 있어 문구 생성 뒤 이미지 API까지 호출되고 있었습니다.
- OpenAI 이미지 호출에는 GPT Image 모델에서 지원하지 않는 `response_format` 파라미터가 포함되어 400 오류가 발생했습니다.

해결:

- GPT Image 모델은 base64 이미지를 기본 반환하므로 `response_format` 파라미터를 제거했습니다.
- 로컬 기본 설정을 빠른 생성 우선으로 바꿨습니다.
- `.env`에 `OPENAI_REASONING_EFFORT=low`, `MAX_GENERATION_ATTEMPTS=1`을 추가했습니다.
- `.env`에서 `IMAGE_PROVIDER=prompt_only`, `ALLOW_PAID_IMAGE_GENERATION=false`로 되돌려 이미지 API 호출 대기 시간을 제거했습니다.

의미:

- 현재 로컬 실행에서는 문구 생성 1회와 로컬 배너 합성만 수행하므로 훨씬 빠르게 결과를 확인할 수 있습니다.
- 실제 이미지 API를 다시 쓰고 싶으면 `IMAGE_PROVIDER=openai`, `ALLOW_PAID_IMAGE_GENERATION=true`로 켜면 됩니다.

후속 수정:

- 이미지 생성은 최종적으로 로컬 모델을 쓰기로 했기 때문에 `.env`를 `IMAGE_PROVIDER=sd35`로 되돌렸습니다.
- 로컬 SD3.5 provider는 유료 API가 아니므로 `ALLOW_PAID_IMAGE_GENERATION=false`여도 실행되도록 수정했습니다.
- 기본 로컬 엔드포인트는 `http://127.0.0.1:8188/sd35/generate`입니다.

### 24단계: 브라우저 기반 자동 업로드 예약 UI

- 사용자가 브라우저에서 예약 시간과 자동화 방식을 선택해 시간에 맞춰 계속 자동 업로드되길 원했습니다.
- 결과 화면의 예약 폼을 `자동 업로드 예약` UI로 확장했습니다.
- Instagram, Threads, Blog 채널을 체크박스로 선택할 수 있게 했습니다.
- 자동화 방식을 `n8n 실제 업로드 큐`와 `Mock 테스트 게시` 중 선택할 수 있게 했습니다.
- 예약 시간, 반복 주기, 반복 횟수를 입력할 수 있게 했습니다.
- 반복은 `한 번만`, `매일 같은 시간`, `매주 같은 요일/시간`을 지원하며 최대 30회까지 예약 작업을 생성합니다.
- 예약된 작업에는 provider, recurrence, sequence 정보가 저장됩니다.

의미:

- 사용자는 브라우저에서 캠페인을 검수한 뒤 원하는 시간에 자동 업로드되도록 예약할 수 있습니다.
- n8n Cron workflow는 `/api/publish-jobs/due`를 계속 확인하다가 시간이 된 작업만 가져가 실제 업로드를 수행하면 됩니다.

### 25단계: 3채널 고정 편집/미리보기 UI

- 사용자가 입력 화면의 게시 채널 선택을 제거하고 Instagram, Threads, Blog 3개 채널을 고정하길 원했습니다.
- 입력 폼에서 게시 채널 select를 제거하고 hidden 값으로 `Instagram, Threads, Blog`를 보내도록 변경했습니다.
- 결과 화면의 라이브 미리보기를 Instagram만이 아니라 Instagram, Threads, Blog 3개 카드로 확장했습니다.
- 편집 패널에 Instagram 캡션/해시태그, Threads 본문/댓글 유도, Blog 제목/도입문/CTA 입력란을 추가했습니다.
- Vanilla JavaScript로 각 입력값이 해당 채널 미리보기에 즉시 반영되도록 했습니다.

의미:

- 사용자는 하나의 브리프에서 생성된 3채널 결과를 한 화면에서 직접 다듬고, 그대로 n8n 자동 업로드 예약으로 넘길 수 있습니다.

### 26단계: 채널별 생성 프롬프트 재설계

- 사용자가 Instagram, Threads, Blog의 말투가 더 명확히 달라지길 요청했습니다.
- 최신 Instagram 광고 사례, Threads 대화형 운영 이슈, Google helpful content 기준을 참고해 프롬프트를 재작성했습니다.
- Instagram은 간단한 정보 중심으로 바꾸고, 상품명, 혜택, 이용 조건, 방문/예약 행동이 짧게 보이도록 지시했습니다.
- Threads는 친근한 말투, 공감, 상황 기반 질문, 댓글 대화를 유도하는 방향으로 바꿨습니다.
- Blog는 광고성 감탄문을 줄이고, 검색자가 필요한 메뉴/서비스 구성, 추천 대상, 혜택 조건, 방문 전 확인사항을 정보 중심으로 정리하도록 바꿨습니다.
- mock 생성기와 평가 지표도 같은 방향으로 조정했습니다.

검증:

```text
24 passed
eval passed: 4/4
latest overall score: 99
```

### 27단계: 이미지 생성 fallback 안정화

- 로컬 SD3.5 서버가 아직 떠 있지 않으면 결과 화면의 이미지가 비어 보이는 문제가 있었습니다.
- `SD35_FALLBACK_TO_LOCAL=true` 설정을 추가했습니다.
- SD3.5 엔드포인트 호출에 실패하면 앱 내부 Pillow 기반 배경 생성기로 대체 이미지를 생성하도록 했습니다.
- fallback 이미지는 실제 SD3.5 모델 결과는 아니지만, 로컬 서버 준비 전에도 결과 화면과 배너 합성이 정상적으로 보이도록 하는 안전장치입니다.
- SD3.5 wrapper가 정상 연결되면 기존처럼 SD3.5 결과 이미지를 우선 사용합니다.

검증:

```text
25 passed
```

## 최종 비전

최종 버전은 소상공인이 댓글만 직접 관리하면 되는 SNS 홍보 자동화 서비스입니다.

목표 흐름:

1. 소상공인이 상품/이벤트 정보를 입력합니다.
2. AI가 Instagram, Threads, 블로그용 콘텐츠를 생성합니다.
3. AI가 게시 시간과 채널별 문구를 추천합니다.
4. 사용자가 자동화 정책을 설정합니다.
5. 서비스가 예약 게시를 수행합니다.
6. 성과 데이터를 요약하고 다음 게시물을 추천합니다.
7. 사용자는 댓글, DM, 실제 고객 응대에 집중합니다.

## 향후 확장 계획

### 1차 확장

- 생성 이력 저장
- 결과 재생성 버튼
- 채널별 톤 조절
- 품질 점수 기반 자동 개선 버튼

### 2차 확장

- Instagram OAuth 연동
- Threads OAuth 연동
- 게시 전 미리보기/승인 화면
- 예약 게시 큐 설계

### 3차 확장

- 완전 자동 예약 발행
- 게시 성과 수집
- 다음 콘텐츠 추천
- 댓글/DM 응대 템플릿 추천

## 포트폴리오에서 강조할 수 있는 포인트

- 단순 AI 호출이 아니라 실제 서비스 흐름을 고려한 생성 파이프라인을 설계했습니다.
- OpenAI 응답을 Structured Outputs로 안정화했습니다.
- Instagram/Threads 자동화까지 고려해 채널별 결과 모델을 분리했습니다.
- API 실패, 인증 실패, 입력 검증 실패를 사용자 친화적으로 처리했습니다.
- 이미지 생성 모델 없이도 Pillow 기반 템플릿 합성으로 시각적 결과물을 만들었습니다.
- 테스트를 통해 생성, 라우트, 배너, 검증 오류 흐름을 로컬에서 안정적으로 확인했습니다.
- 생성 품질 평가 테스트셋을 만들어 결과물이 일정 기준 이상인지 자동으로 검증했습니다.
- 생성 이력 저장과 상태 관리를 추가해 실제 자동예약 서비스로 확장 가능한 기반을 만들었습니다.
- 공식 API 연동 전 mock 게시 어댑터를 만들어 계정/비밀번호 방식 없이 안전한 자동게시 구조를 준비했습니다.
