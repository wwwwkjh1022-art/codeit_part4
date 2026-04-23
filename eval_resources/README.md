# Evaluation Resources

이 폴더는 생성 품질 실험과 발표/포트폴리오 정리를 위한 평가 리소스를 관리합니다.

참고한 구조:

- `METRICS.md`: 평가 기준과 점수 루브릭
- `AD_RESEARCH_NOTES.md`: 최신 광고/채널 운영 기준 리서치 메모
- `eval_dataset.yaml`: 평가 케이스, 기대 키워드, 채널별 기대사항, 최소 통과 기준
- `eval_report_*.md`: 평가 실행 결과 리포트

현재 프로젝트에서는 RAG 정답 평가가 아니라 `소상공인 SNS 홍보 콘텐츠 생성 품질`을 평가합니다.

## 실행

전체 테스트:

```bash
.venv/bin/pytest
```

품질 게이트만 실행:

```bash
.venv/bin/pytest tests/test_generation_quality.py -q
```

평가 리포트 생성:

```bash
.venv/bin/python scripts/run_generation_eval.py
```
