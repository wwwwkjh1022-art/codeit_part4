# Generation Evaluation Metrics

소상공인 SNS 홍보 콘텐츠 생성 결과를 평가하기 위한 기준입니다. 기존 평가는 구조 완성도에 치우쳐 있어 실제 광고 품질을 충분히 걸러내지 못했습니다. 2026년 현재 SNS 광고 흐름을 반영해 `후킹`, `구체성`, `채널 네이티브성`, `CTA`, `과장광고 리스크`를 핵심 평가 축으로 강화했습니다.

## 총점 계산

자동 테스트에서는 각 항목을 0~100점으로 환산해 가중 평균을 냅니다.

- Keyword Coverage: 15%
- Hook Strength: 15%
- Specificity: 15%
- Channel-Native Readiness: 20%
- Channel Differentiation: 10%
- CTA Strength: 10%
- Compliance Safety: 8%
- Structure Completeness: 6%
- Quality Report Reliability: 8%

현재 기본 통과 기준:

- case별 overall score >= 88
- channel score >= 86
- Instagram/Threads/Blog 결과가 모두 채널 문법을 만족
- improvement suggestions >= 2
- pre-publish checklist >= 3
- 근거 없는 최상급/보장성/마감 임박 표현 없음

## 1. Keyword Coverage

입력 브리프의 핵심 키워드가 결과물에 반영되었는지 평가합니다.

확인 항목:

- 기대 키워드
- 상호명
- 상품/서비스명
- 업종
- 사용자가 입력한 강조 키워드

낮은 점수를 받는 경우:

- 상호명이나 상품명이 누락됨
- 키워드는 있으나 맥락 없이 해시태그에만 있음
- 입력 브리프와 무관한 일반 광고 문구로 보임

## 2. Hook Strength

최신 SNS 광고는 첫 줄/첫 장면에서 관심을 붙잡지 못하면 이후 문구가 읽히지 않습니다. 따라서 첫 문장과 짧은 후킹 문구를 별도 점수로 봅니다.

확인 항목:

- Instagram 첫 줄에 상품명 또는 핵심 혜택이 있는가
- Threads short_hook이 짧고 구체적인가
- Poster headline이 상품/혜택 중심으로 압축되어 있는가
- variant headline이 서로 다른 후킹 각도를 제공하는가

낮은 점수를 받는 경우:

- “좋은 상품입니다”, “확인해보세요”처럼 일반적임
- 첫 줄이 길고 핵심 혜택이 늦게 나옴
- 상품명/상호명/혜택 없이 분위기만 말함

## 3. Specificity

광고가 실제 소상공인에게 쓸 수 있으려면 구체적인 맥락이 있어야 합니다.

확인 항목:

- 상호명, 상품명, 타깃 고객이 자연스럽게 포함됨
- 혜택 조건 또는 이용 조건이 반영됨
- 상품 설명의 차별점이 반영됨
- “홍보 문구”, “핵심 메시지” 같은 생성기 냄새가 적음

낮은 점수를 받는 경우:

- 어떤 매장/상품인지 바꿔도 그대로 쓸 수 있는 문구
- 혜택이 있는데 조건이 빠짐
- “업종에 어울리는 홍보 문구”처럼 메타 설명이 결과에 섞임

## 4. Channel-Native Readiness

같은 캠페인이라도 Instagram, Threads, Blog는 서로 다른 문법을 가져야 합니다.

Instagram:

- 캡션이 2~5줄 정도로 짧고 읽기 쉬움
- 첫 줄에 상품명/핵심 혜택/이용 조건이 정보 중심으로 드러남
- 해시태그가 4~8개이며 상품/상호/카테고리를 포함
- ALT 텍스트와 visual_hook이 실제 이미지 제작에 쓸 만큼 구체적
- 저장/방문/문의 등 다음 행동이 있음

Threads:

- 120~260자 안팎의 친근한 대화형 문장
- 과도한 광고문보다 관찰, 공감, 상황 기반 질문이 있음
- reply_prompt가 취향, 상황, 선택 기준을 묻는 구체적인 질문형 문장
- short_hook이 짧고 명확함

Blog:

- 제목에 상호명 또는 상품명과 검색 의도가 드러남
- 도입문이 120자 이상으로 누가/왜/무엇을 얻는지 설명
- 본문 개요가 4개 이상이며 이용 전 확인 정보가 포함됨
- SEO 키워드가 4개 이상
- meta_description이 50~170자 범위
- CTA가 명확함

## 5. Channel Differentiation

하나의 캠페인을 세 채널로 “재생성”하는 것이 목표이므로, 같은 문구를 복사해 붙인 결과는 실패해야 합니다.

확인 항목:

- Instagram caption과 Threads 본문이 지나치게 유사하지 않은가
- Blog는 Threads보다 정보량이 충분히 많고 검색형 구조를 갖는가
- Threads는 질문형/대화형이고, Blog 제목은 검색형인가
- Instagram 해시태그와 Blog SEO 키워드가 각 채널 목적에 맞게 분리되는가

낮은 점수를 받는 경우:

- Instagram, Threads, Blog가 거의 같은 문장
- Blog가 짧은 SNS 문구 수준에 머무름
- Threads가 블로그식 설명문처럼 딱딱함

## 6. CTA Strength

자동 게시까지 생각하면 사용자의 다음 행동이 명확해야 합니다.

확인 항목:

- desired_action과 cta_focus가 결과에 반영됨
- Instagram/Blog/Poster에 행동 유도가 있음
- Threads는 댓글 질문으로 자연스럽게 반응을 유도함
- 혜택 조건 확인, 예약, 문의, 방문 등 실제 행동으로 이어짐

낮은 점수를 받는 경우:

- “확인해보세요”만 반복됨
- 어떤 행동을 해야 하는지 불명확함
- 댓글/DM/예약/방문 중 어느 경로인지 드러나지 않음

## 7. Compliance Safety

소상공인 광고는 과장 표현이 쉽게 들어갈 수 있어 별도 감점합니다.

감점 표현 예:

- 무조건
- 100% 보장
- 완전 보장
- 최고의
- 1위
- 유일한
- 확실한 효과
- 치료/완치
- 브리프에 없는 오늘 마감/마감 임박

## 8. Structure Completeness

자동화 파이프라인에 넘길 수 있는 구조인지 평가합니다.

필수 구조:

- Instagram package
- Threads package
- Blog package
- Quality report
- Channel quality report
- Pre-publish checklist
- 3개 copy variant
- Gemini/Nano Banana 배경 프롬프트 또는 이후 생성 가능한 자리

## 9. Quality Report Reliability

AI가 스스로 평가한 점수를 그대로 믿지 않고, 보조 신호로만 사용합니다.

확인 항목:

- hook_score, clarity_score, cta_score, channel_fit_score, overall_score가 0~100 범위
- Instagram/Threads/Blog 점수가 0~100 범위
- improvement_suggestions가 2개 이상
- channel regeneration suggestions가 2개 이상
- auto_approved와 점수 기준이 모순되지 않음
- 수정 제안에 상호명, 상품명, 혜택, 행동 유도 중 실제 입력 브리프 요소가 반영됨

## 참고한 최신 운영 관찰

- Instagram은 짧은 정보형 캡션, 명확한 첫 줄, 저장/방문 유도, 고품질 비주얼이 중요합니다.
- Threads는 Instagram과 연결되어 있지만 동일 문구를 복붙하기보다 친근한 말투와 구체적인 질문으로 대화가 이어지게 조정해야 합니다.
- Blog는 검색 유입을 고려해 제목, 도입부, 개요, 메타 설명, 이용 전 확인 정보를 충분히 제공해야 합니다.
- 배경 이미지는 API 과금 전까지 프롬프트를 생성하고 수동 업로드하는 방식으로 검증합니다.
