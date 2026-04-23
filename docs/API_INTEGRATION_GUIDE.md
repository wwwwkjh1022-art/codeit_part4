# Instagram / Blog API 연동 가이드

## 기본 방향

이 프로젝트는 계정과 비밀번호를 직접 저장하는 방식이 아니라 OAuth/API 토큰 기반으로 확장하는 것이 안전합니다.

목표 자동화 흐름은 다음과 같습니다.

1. 사용자가 광고 브리프를 입력합니다.
2. AI가 Instagram, Threads, Blog용 문구와 이미지를 생성합니다.
3. 품질 평가 점수가 기준 이상이면 게시 후보로 올립니다.
4. 사용자가 OAuth로 채널을 연결합니다.
5. 서비스가 예약 시간에 API를 호출해 게시합니다.
6. 댓글/문의 응대는 사용자가 직접 관리합니다.

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

### Naver Blog

현재 공개 문서 기준으로 네이버 Open API는 블로그 검색 API는 제공하지만, 외부 서비스에서 네이버 블로그에 글을 작성하는 공식 공개 API 흐름은 WordPress만큼 명확하지 않습니다.

따라서 제출용 또는 안정적인 서비스 구조에서는 다음 중 하나가 현실적입니다.

- 네이버 블로그용 글 초안을 생성하고 사용자가 직접 복사해 게시합니다.
- 공식 제휴/API 가능 여부를 별도로 확인합니다.
- RPA/브라우저 자동화는 가능하더라도 계정 보안, CAPTCHA, 정책 리스크가 있어 기본 전략으로 두지 않습니다.

## 프로젝트에 붙일 때의 구현 순서

1. `publishers/` 또는 `services/publishers/` 폴더를 만듭니다.
2. `BasePublisher` 인터페이스를 정의합니다.
3. `InstagramPublisher`, `WordPressPublisher`, `MockPublisher`를 나눕니다.
4. 현재 `campaign.publish_jobs`의 mock 상태를 실제 adapter 결과로 갱신합니다.
5. 이미지 파일은 API가 접근할 수 있게 public storage 또는 signed URL 구조로 바꿉니다.
6. 게시 성공 후 external post id, permalink, published_at을 저장합니다.
7. 실패하면 에러 메시지와 retry count를 저장합니다.

## 다음 구현 후보

- Instagram OAuth 버튼을 실제 `/auth/instagram/start` 라우트에 연결
- WordPress 연결 정보 입력 UI 추가
- WordPress draft 생성 adapter 구현
- Instagram publish adapter는 public URL 저장소가 생긴 뒤 구현
- 예약 큐는 현재 JSON 저장소에서 SQLite 또는 PostgreSQL로 이전

