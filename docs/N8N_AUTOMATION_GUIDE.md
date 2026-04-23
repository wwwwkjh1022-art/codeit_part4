# n8n 전체 자동화 설계

## 결론

n8n으로 이 프로젝트의 전체 자동화 흐름을 만들 수 있습니다.

이 프로젝트의 FastAPI는 생성 엔진, 품질 평가, 캠페인 저장, 이미지 생성, 게시 adapter를 담당하고, n8n은 스케줄링, 조건 분기, 알림, 외부 API 연결을 담당하는 구조가 가장 안정적입니다.

## 추천 역할 분리

FastAPI 담당:

- 광고 브리프 검증
- Instagram, Threads, Blog용 문구 생성
- 이미지 프롬프트 또는 배경 이미지 생성
- 배너 합성
- 품질 점수 계산
- 캠페인 저장
- 게시 adapter 인터페이스 제공

n8n 담당:

- 매일/매주 정해진 시간에 캠페인 생성 트리거
- 생성 결과 점수 확인
- 점수가 기준 이상이면 예약/게시 진행
- 점수가 낮으면 Slack, Discord, 이메일 등으로 검수 요청
- Instagram, Threads, WordPress, Google Sheets 같은 외부 도구 연결
- 실패 시 재시도와 운영 알림

## 추가된 FastAPI 자동화 API

브라우저용 HTML 라우트와 별도로 n8n이 쓰기 쉬운 JSON API를 추가했습니다.

### 캠페인 생성

```http
POST /api/campaigns/generate
Content-Type: application/json
```

요청 예시:

```json
{
  "business_category": "카페",
  "business_name": "오카페",
  "product_name": "딸기 라떼",
  "product_description": "신선한 딸기와 부드러운 우유로 만든 봄 시즌 한정 라떼입니다.",
  "offer_details": "오전 방문 고객 10% 할인",
  "target_customer": "동네 주민과 감성 카페를 찾는 20-30대",
  "promotion_goal": "신메뉴 홍보",
  "tone": "친근한",
  "platform": "인스타그램",
  "visual_style": "따뜻한 감성",
  "cta_focus": "방문 유도",
  "campaign_type": "신상품/신메뉴",
  "desired_action": "매장 방문",
  "post_timing_preference": "AI 추천",
  "keywords": "딸기라떼, 봄메뉴, 동네카페"
}
```

`product_description`은 비워도 됩니다. 비어 있으면 FastAPI가 `business_category`, `business_name`, `product_name`, `tone`을 바탕으로 기본 설명을 자동 생성합니다.

응답 핵심:

- `campaign.id`
- `campaign.result.auto_approved`
- `campaign.result.quality_report.overall_score`
- `campaign.result.channel_quality.instagram_score`
- `campaign.result.channel_quality.threads_score`
- `campaign.result.channel_quality.blog_score`
- `campaign.result.banner_preview_path`
- `n8n_next_step`

### 캠페인 조회

```http
GET /api/campaigns/{campaign_id}
```

### 예약 준비 표시

```http
POST /api/campaigns/{campaign_id}/ready
```

### 예약 작업 생성

```http
POST /api/campaigns/{campaign_id}/schedule
Content-Type: application/json
```

```json
{
  "channels": ["instagram", "threads", "blog"],
  "scheduled_at": "2026-04-21T18:30:00",
  "automation_provider": "n8n",
  "repeat_interval": "daily",
  "repeat_count": 7
}
```

브라우저 결과 화면에서도 같은 값을 선택할 수 있습니다.

- 자동화 방식: `n8n 실제 업로드 큐` 또는 `Mock 테스트 게시`
- 채널: Instagram, Threads, Blog
- 예약 시간: 업로드 시작 시간
- 반복: 한 번만, 매일 같은 시간, 매주 같은 요일/시간
- 반복 횟수: 최대 30회

### mock 게시 실행

```http
POST /api/campaigns/{campaign_id}/publish-now
```

현재는 실제 게시가 아니라 mock external id를 저장합니다. 나중에 Instagram/Threads/Blog adapter가 붙으면 같은 n8n 흐름에서 실제 게시로 교체할 수 있습니다.

### 게시 payload 조회

```http
GET /api/campaigns/{campaign_id}/publish-payload
```

n8n이 실제 업로드 노드에 넘길 데이터를 반환합니다.

응답 핵심:

- `campaign_id`
- `job_id`
- `payloads.instagram.text`
- `payloads.instagram.image_url`
- `payloads.instagram.hashtags`
- `payloads.threads.text`
- `payloads.blog.title`
- `payloads.blog.text`
- `payloads.blog.image_url`

### 예약 시간이 지난 작업 조회

```http
GET /api/publish-jobs/due
```

n8n Cron workflow에서 주기적으로 호출하면, 현재 시점 기준으로 업로드해야 하는 queued 작업을 가져올 수 있습니다.

선택 파라미터:

```text
due_at=2026-04-21T18:30:00
limit=20
```

브라우저에서 반복 예약을 저장하면 여러 개의 queued job이 만들어지고, n8n은 이 endpoint를 계속 확인하면서 시간이 된 작업만 업로드하면 됩니다.

### n8n 업로드 결과 저장

```http
POST /api/campaigns/{campaign_id}/publish-jobs/{job_id}/complete
Content-Type: application/json
```

성공 예시:

```json
{
  "status": "published",
  "provider": "n8n",
  "external_ids": {
    "instagram": "17890000000000000",
    "threads": "threads-post-id",
    "blog": "wordpress-post-id"
  }
}
```

실패 예시:

```json
{
  "status": "failed",
  "provider": "n8n",
  "external_ids": {},
  "error_message": "Instagram media container creation failed"
}
```

## n8n 워크플로우 파일

샘플 워크플로우:

```text
automations/n8n_campaign_automation.json
```

흐름:

1. Webhook으로 브리프 수신
2. FastAPI `/api/campaigns/generate` 호출
3. `auto_approved=true`이고 전체 점수 82점 이상인지 확인
4. 통과하면 `/api/campaigns/{id}/schedule` 호출
5. `/api/campaigns/{id}/publish-payload`로 업로드 데이터 조회
6. Instagram/Threads/Blog 업로드 노드를 연결
7. `/api/campaigns/{id}/publish-jobs/{job_id}/complete`로 업로드 결과 저장
8. 실패하면 검수 필요 응답 반환

## n8n에서 호출할 때 주의할 점

로컬에서 n8n을 직접 실행하면 FastAPI 주소는 보통 아래처럼 씁니다.

```text
http://127.0.0.1:8000
```

n8n을 Docker로 실행하면 컨테이너 안의 `127.0.0.1`은 n8n 컨테이너 자신을 의미합니다. 이 경우 다음 중 하나를 써야 합니다.

```text
http://host.docker.internal:8000
```

또는 Docker Compose로 FastAPI와 n8n을 같은 네트워크에 묶고 서비스 이름으로 호출합니다.

```text
http://fastapi:8000
```

## Webhook 테스트 payload

```json
{
  "fastapi_base_url": "http://127.0.0.1:8000",
  "scheduled_at": "2026-04-21T18:30:00",
  "brief": {
    "business_category": "카페",
    "business_name": "오카페",
    "product_name": "딸기 라떼",
    "product_description": "신선한 딸기와 부드러운 우유로 만든 봄 시즌 한정 라떼입니다.",
    "offer_details": "오전 방문 고객 10% 할인",
    "target_customer": "동네 주민과 감성 카페를 찾는 20-30대",
    "promotion_goal": "신메뉴 홍보",
    "tone": "친근한",
    "platform": "인스타그램",
    "visual_style": "따뜻한 감성",
    "cta_focus": "방문 유도",
    "campaign_type": "신상품/신메뉴",
    "desired_action": "매장 방문",
    "post_timing_preference": "AI 추천",
    "keywords": "딸기라떼, 봄메뉴, 동네카페"
  }
}
```

## 최종 자동화 비전

1. n8n Cron Trigger가 매일 오전 다음 게시물을 생성합니다.
2. FastAPI가 채널별 문구와 이미지를 생성합니다.
3. 품질 점수가 기준 이상이면 n8n이 게시 예약을 만듭니다.
4. 기준 미달이면 n8n이 재생성 또는 검수 요청으로 보냅니다.
5. 예약 시간이 되면 n8n이 Instagram, Threads, Blog adapter를 호출합니다.
6. 게시 후 external id와 URL을 FastAPI 캠페인 기록에 저장합니다.
7. 추후 성과 API가 붙으면 n8n이 조회 후 다음 콘텐츠 전략을 업데이트합니다.

## 실제 업로드 노드 구성

### Instagram

n8n HTTP Request 노드 2개로 구성합니다.

1. Media Container 생성

```text
POST https://graph.instagram.com/{version}/{ig_user_id}/media
Authorization: Bearer {instagram_access_token}
Body:
  image_url = {{$json.payloads.instagram.image_url}}
  caption = {{$json.payloads.instagram.text + "\n\n" + $json.payloads.instagram.hashtags.join(" ")}}
```

2. Container 게시

```text
POST https://graph.instagram.com/{version}/{ig_user_id}/media_publish
Authorization: Bearer {instagram_access_token}
Body:
  creation_id = {이전 노드의 id}
```

주의:

- `image_url`은 Meta 서버가 접근 가능한 public HTTPS URL이어야 합니다.
- 로컬 `127.0.0.1` URL은 실제 Meta API에서 접근할 수 없습니다.
- 로컬 시연에서는 mock complete를 사용하고, 실제 업로드는 ngrok, Cloudflare Tunnel, S3/R2 같은 public storage가 필요합니다.

### Threads

Threads도 Meta 계열 OAuth와 Threads API 권한이 필요합니다. n8n에서는 Instagram과 비슷하게 HTTP Request 노드를 두 단계로 구성합니다.

1. Threads media/text container 생성
2. publish endpoint 호출

현재 프로젝트에서는 `payloads.threads.text`와 `payloads.threads.image_url`을 바로 사용할 수 있게 반환합니다.

### Blog

WordPress 기준으로는 REST API가 가장 안정적입니다.

1. 이미지가 있으면 `/wp-json/wp/v2/media`에 업로드합니다.
2. `/wp-json/wp/v2/posts`에 `title`, `content`, `status`를 보냅니다.
3. 예약 발행이면 `status=future`, `date=...`를 사용합니다.

네이버 블로그는 공식 공개 글쓰기 API 흐름이 제한적이므로, n8n 자동 업로드보다는 초안 생성 후 수동 게시 또는 별도 제휴/API 확인이 안전합니다.
