# Claude Haiku 4.5

- 기준일: 2026-10-04
- 전용 프롬프트 가이드 페이지가 없습니다. [Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)가 적용 대상 모델로 Haiku 4.5를 포함하므로 `best-practices.md`의 공통 원칙(B1~B12)을 적용합니다.
- 진단표와 변경표에서 Haiku 4.5만의 동작을 근거로 들 수 없습니다. 모델별 근거가 필요한 변경은 "확인 필요"로 표시합니다.

## H1 공통 원칙 우선

- 짧고 명확한 지시(B1), 이유(B2), 예시 3~5개(B3), 태그 구분(B4)처럼 모델과 무관한 원칙만으로 개선합니다.

## H2 설정 차이는 확인 후

- thinking과 effort 지원 범위는 모델마다 다릅니다. 이 모델에 effort나 thinking 설정을 권하기 전에 [Effort](https://platform.claude.com/docs/en/build-with-claude/effort)와 [Models overview](https://platform.claude.com/docs/en/about-claude/models/overview)에서 지원 여부를 확인하라고 적습니다.
- prefill 제한(B10)은 Claude 4.6 계열부터 적용됩니다. Haiku 4.5는 그 이전 모델이지만, 다른 모델로 옮길 수 있는 프롬프트라면 prefill에 기대지 않는 형태로 고치길 권합니다.

## H3 다른 모델과 비교하기

- 같은 프롬프트를 상위 모델과 함께 `tools/usage_log.sh`로 실행해 비용과 결과를 비교하는 방법을 확인 방법에 적습니다.
