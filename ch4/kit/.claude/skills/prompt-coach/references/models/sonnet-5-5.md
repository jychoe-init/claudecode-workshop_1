# Claude Sonnet 5.5

- 출처: [Prompting Claude Sonnet 5.5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5-5)
- 기준일: 2026-10-04. Claude Sonnet 5와의 차이 중심입니다. Sonnet 5용 프롬프트는 대체로 그대로 잘 동작합니다. 가장 어려운 장기 작업에는 Opus 계열이 낫다고 안내합니다.
- 기본 effort: API 기본값 `high`. 단계가 다시 조정되어 Sonnet 5의 같은 단계와 생각의 양이 다릅니다.

## S1 effort로 조절하기

- 일반 작업은 `high`에서 시작합니다. 명확한 에이전트 코딩·여러 단계 도구 작업은 `medium`, 채팅처럼 지연이 중요한 작업은 `medium`이나 `low`에서 시작합니다.
- 시스템 프롬프트에 "덜 생각하라"고 써도 생각이 확실히 줄지 않습니다. 줄이려면 effort를 낮춥니다. `low`에서는 단순한 요청 대부분에서 생각을 건너뜁니다.
- 근거: [SN#calibrate-effort](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5-5#calibrate-effort)

## S2 주도성과 범위

- 낮은 effort의 코딩 작업에서 끝나기 전에 확인을 묻는 경우가 있습니다. "요청한 것이 다 끝날 때까지 계속하고, 사용자 없이는 진행할 수 없거나 위험한 단계 전에만 멈추라"는 문단이 도움이 됩니다.
- 요청하지 않은 테스트, 문서, 파일을 덧붙이는 경향이 있습니다. 범위를 좁히려면 "끝나고 확인했으면 멈추고 보고하라. 요청하지 않은 기능, 테스트, 파일, 문서, 리팩터링은 추가하지 말고 제안만 하라"는 문단을 씁니다.
- 아이디어나 계획만 원하면 그렇게 말합니다. "아이디어, 선택지, 계획을 요청하면 그것만 주고 멈춰라"를 시스템 프롬프트에 둘 수 있습니다.
- 근거: [SN#steer-initiative-and-scope](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5-5#steer-initiative-and-scope)

## S3 계산·판단이 필요한 JSON 출력

- 합계 계산, 규칙 적용, 순위 매기기처럼 몇 단계 추론이 필요한 작업에서 JSON만 요청하면 생각 없이 답하는 경우가 있습니다.
- 가능하면 structured outputs를 쓰고, 시스템 프롬프트 끝에 "Think the problem through before you answer."를 둡니다(adaptive thinking에서). 또는 `xhigh` effort를 씁니다.
- structured outputs를 못 쓰면 응답의 마지막 JSON 값을 파싱합니다. 처음 `{`부터 마지막 `}`까지 자르지 않습니다.
- 근거: [SN#reasoning-tasks-with-json-output](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5-5#reasoning-tasks-with-json-output)

## S4 도구 사용을 억누르는 문구 제거

- "꼭 필요할 때만 도구를 써라", "도구 호출을 최소화하라" 같은 문구가 있으면 지웁니다. 바뀌었을 수 있는 정보(허용, 요구, 요금 등)를 학습 지식으로 답하는 원인이 됩니다.
- 검색 도구가 있다면 바뀌었을 수 있는 세부 사항은 확신이 있어도 검색해 확인하라는 문장을 둡니다.
- 근거: [SN#tool-use-in-chat-and-knowledge-work](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5-5#tool-use-in-chat-and-knowledge-work)

## S5 응답 본문에 추론을 쓰게 하는 지시 제거

- 응답에 추론을 포함하라는 지시는 `reasoning_extraction` 거절을 부르므로 지웁니다. 짧은 설명이나 한 일의 요약은 요청해도 됩니다.
- 근거: [SN#safeguard-refusals](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5-5#safeguard-refusals)

## S6 진행 상황 알림

- "모든 결과는 마지막 응답에 모아서" 같은 예전 지시는 지웁니다. 알림 시점을 원하면 시스템 프롬프트에 적습니다.
- 근거: [SN#user-facing-progress-updates](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5-5#user-facing-progress-updates)

## S7 코딩 작업의 검증

- `low` effort에서 테스트나 빌드 없이 완료를 보고하는 경우가 있습니다. "실행 가능한 변경이면 보고 전에 실제 검사를 돌리고, 못 돌렸으면 무엇을 왜 못 했는지 말하라"는 문단이 도움이 됩니다.
- 근거: [SN#verification-on-coding-tasks](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5-5#verification-on-coding-tasks)

## S8 up-front thinking 없이 실행할 때

- API에서 thinking을 `between_tools`로 쓰는 경우, "생각하지 마라" 같은 지시는 지웁니다. 내부 XML 태그가 출력에 섞일 가능성을 높입니다. 도구 없는 추론 작업에는 adaptive thinking을 씁니다.
- 근거: [SN#running-without-up-front-thinking](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5-5#running-without-up-front-thinking)
