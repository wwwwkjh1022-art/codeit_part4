# Instagram / Threads / Blog 연동 가이드

## 기본 방향

이 프로젝트는 가능한 범위에서는 OAuth/API 토큰 기반으로 연결하고, 공식 게시 API가 부족한 채널만 브라우저 자동화로 보완하는 방향으로 확장합니다.

목표 자동화 흐름은 다음과 같습니다.

1. 사용자가 광고 브리프를 입력합니다.
2. AI가 Instagram, Threads, Blog용 문구와 이미지를 생성합니다.
3. 품질 평가 점수가 기준 이상이면 게시 후보로 올립니다.
4. 사용자가 채널별 연결 정보를 입력하거나 연결 창을 완료합니다.
5. 서비스가 예약 시간에 API를 호출해 게시합니다.
6. 댓글/문의 응대는 사용자가 직접 관리합니다.

현재 구현 상태:

- Instagram: direct API adapter 구현
- Threads: direct API adapter 구현
- WordPress: REST API adapter 구현
- Naver Blog: Playwright adapter 구현
- Mock: 테스트 게시 adapter 구현

## Instagram 연동

Instagram은 공식 API 기반으로 붙이는 것이 맞습니다.

추천 방식:

- Instagram Professional 계정 또는 Business/Creator 계정 사용
- Meta Developer App 생성
- Instagram API 권한 설정
- OAuth 로그인으로 access token 획득
- 서버에서 token을 안전하게 저장
- 게시 시 이미지가 외부에서 접근 가능한 URL이어야 함

일반 게시 흐름:

1. 생성된 배너 이미지를 public URL로 노출합니다.
2. `/{ig_user_id}/media`에 `image_url`, `caption`을 보내 media container를 만듭니다.
3. 응답으로 받은 container id를 `/{ig_user_id}/media_publish`에 `creation_id`로 보내 게시합니다.
4. 예약 게시가 필요하면 Instagram API 자체 예약이 아니라 서비스 내부 예약 큐가 정해진 시간에 publish를 실행합니다.

필요한 서버 기능:

- OAuth 시작 라우트
- OAuth callback 라우트
- access token 저장소
- token refresh 또는 long-lived token 관리
- public 이미지 URL 제공
- publish adapter
- 실패 시 재시도 큐

주의:

- 개인 계정 자동 로그인/비밀번호 입력 방식은 보안과 정책 리스크가 큽니다.
- 이미지 파일은 Instagram API가 접근 가능한 HTTPS URL이어야 합니다.
- 앱 검수와 권한 승인이 필요할 수 있습니다.

현재 구현:

- 결과 페이지에서 Access Token + Instagram User ID 저장 가능
- direct API 게시 시 `/{ig_user_id}/media` → `/{ig_user_id}/media_publish` 흐름 사용
- `PUBLIC_BASE_URL`이 로컬 주소면 게시 실패로 처리

## Threads 연동

Threads는 현재 direct API 게시 adapter가 구현되어 있습니다.

현재 구현:

- 결과 페이지에서 Access Token + Threads User ID 저장 가능
- direct API 게시 시 `/{threads_user_id}/threads` → `/{threads_user_id}/threads_publish` 흐름 사용
- 공개 이미지 URL이 없으면 텍스트 게시로 fallback

## Blog 연동

블로그는 어떤 플랫폼을 대상으로 하느냐에 따라 전략이 갈립니다.

### WordPress

가장 API 친화적입니다.

추천 방식:

- WordPress REST API 사용
- Application Password 또는 OAuth 사용
- `/wp-json/wp/v2/media`로 대표 이미지 업로드
- `/wp-json/wp/v2/posts`로 글 생성
- `status=draft`, `publish`, `future`를 이용해 초안/즉시발행/예약발행 처리

이 프로젝트와 잘 맞는 이유:

- Blog 패키지에 이미 `title`, `intro`, `body_outline`, `seo_keywords`, `meta_description`, `cta`가 있습니다.
- 이 구조를 HTML 본문으로 변환하면 바로 WordPress post payload로 넘길 수 있습니다.

현재 구현:

- 결과 페이지에서 `WordPress` 선택 시 API URL + Username + Application Password 저장 가능
- 대표 이미지 업로드 후 post 생성까지 direct API adapter에서 처리
- 예약 시 `future`, 즉시 게시 시 `publish` 사용

### Naver Blog

현재 공개 문서 기준으로 네이버 Open API는 블로그 검색 API는 제공하지만, 외부 서비스에서 네이버 블로그에 글을 작성하는 공식 공개 API 흐름은 WordPress만큼 명확하지 않습니다.

그래서 현재 프로젝트는 `Playwright 브라우저 자동화`를 네이버 블로그 경로로 채택했습니다.

현재 구현:

1. 결과 페이지에서 `Naver Blog (Playwright)`를 선택합니다.
2. `Naver Blog ID`를 입력하고 `네이버 로그인 창 열기` 버튼을 누릅니다.
3. 서버가 Chromium 창을 띄우고, 사용자는 그 창에서 네이버 로그인 후 글쓰기 화면까지 진입합니다.
4. 연결이 완료되면 브라우저 세션이 저장되고, 이후 Blog 게시 시 해당 세션을 사용합니다.

주의:

- CAPTCHA, 2차 인증, 로그인 정책 변화에 따라 자동화가 실패할 수 있습니다.
- Playwright + Chromium + 시스템 라이브러리 의존성이 필요합니다.
- 네이버 에디터 DOM 변경 시 selector 유지보수가 필요할 수 있습니다.

## 프로젝트에 붙일 때의 구현 순서

1. `services/publishers.py`의 adapter를 채널별로 유지/확장합니다.
2. Instagram / Threads는 OAuth 흐름으로 고도화합니다.
3. WordPress는 draft / category / tag 확장값을 추가합니다.
4. Naver Blog는 세션 재사용 안정화와 selector 보강을 진행합니다.
5. 이미지 파일은 public storage 또는 signed URL 구조로 고도화합니다.
6. 게시 성공 후 external post id, permalink, published_at을 저장합니다.
7. 실패하면 에러 메시지와 retry count를 저장합니다.

## 다음 구현 후보

- Instagram / Threads OAuth 버튼 실제 연동
- WordPress category, tag, draft 옵션 확장
- Naver Blog 연결 상태 UI 개선
- 게시 큐 저장소를 JSON에서 SQLite 또는 PostgreSQL로 이전
- Playwright 기반 브라우저 세션 보안 저장 구조 개선
