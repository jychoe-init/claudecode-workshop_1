# Claude Fable 5.1

- 출처: [Prompting Claude Fable 5.1](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1)
- 기준일: 2026-10-04. Claude Fable 5와의 차이 중심입니다. Fable 5용 프롬프트는 대체로 그대로 잘 동작합니다.
- 기본 effort: `high`. `low`, `medium`, `xhigh`, `max`도 직접 비교하길 권합니다.

## F1 effort 단계 전부 비교하기

- `high`에서 시작해 다른 단계를 직접 비교합니다. `medium`은 Fable 5와 비슷한 결과를 더 적은 비용으로 냅니다. `low`에서는 검색·조회 도구를 덜 부르고 기억으로 답하는 경향이 있습니다.
- 근거: [FB#consider-all-effort-levels](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1#consider-all-effort-levels), [FB#search-triggering-at-low-effort](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1#search-triggering-at-low-effort)

## F2 응답 본문에 생각을 쓰게 하는 지시 제거

- 프롬프트, 스킬, 도구 설명에서 생각이나 추론을 써 내라고 하면 `reasoning_extraction`으로 거절될 수 있습니다. 짧은 설명이나 한 일의 요약을 요청합니다.
- 근거: [Prompting Claude Fable 5.1](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1) (문서 첫머리 안내)

## F3 진행 상황 알림

- Fable 5보다 긴 도구 작업 중 알림이 적습니다. "결과는 마지막에 모아서" 같은 문구를 먼저 지우고, 필요하면 "시작 전에 한 줄로 할 일을 말하고, 끝에 그것만 읽어도 이해되는 짧은 요약을 남겨라"는 문장을 둡니다.
- 근거: [FB#ask-for-user-facing-progress-updates](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1#ask-for-user-facing-progress-updates)

## F4 글이 빽빽할 때

- 문장이 길고 문단 나눔이 적어질 수 있습니다. 비유와 꾸밈으로 직설을 대신하는 문체(mannered prose)를 정의하고 피하라는 지시가 도움이 되고, 짧게 "Please remove all mannered prose."도 대체로 통합니다. 시스템 프롬프트보다 사용자 메시지에 두는 쪽을 권합니다.
- 근거: [FB#writing-density](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1#writing-density)

## F5 서식 금지 규칙 걷어내기

- 예전 모델의 과한 목록·굵은 글씨를 막으려던 "서식 쓰지 마" 규칙은 이 모델에서 필요한 구조까지 없앱니다. 지우거나, 언제 목록과 서식을 쓸지 말하는 규칙으로 바꿉니다.
- 근거: [FB#formatting-in-chat](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1#formatting-in-chat), [BP#control-the-format-of-responses](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#control-the-format-of-responses)

## F6 일을 끝까지 하게

- 비동기 작업에서 "다음에 ~하겠습니다"라고 예고만 하거나, 이미 요청한 단계를 해도 되는지 묻고 멈출 수 있습니다. 사용자가 실시간으로 보지 않는다는 사실과, 되돌릴 수 있는 후속 작업은 묻지 말고 하라는 지시가 효과적입니다.
- 사람이 함께하는 작업에는 맞지 않을 수 있으니 쓰는 곳을 보고 판단합니다.
- 근거: [FB#finish-the-whole-task](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1#finish-the-whole-task)

## F7 범위와 테스트를 요청만큼

- 주변 코드 수정이나 요청에 없는 확장, 과한 테스트 파일이 생길 수 있습니다. "작업에 없는 버그나 개선점은 고치지 말고 후속 과제로 보고하라"는 지시로 줄어듭니다.
- 근거: [FB#keep-changes-and-tests-to-what-the-task-asks-for](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1#keep-changes-and-tests-to-what-the-task-asks-for)

## F8 출처 요약에서 인용 표시

- 문서를 요약할 때 원문을 따옴표 없이 옮기는 경향이 있습니다. 올바른 응답 예시 하나(요청, 응답, 왜 올바른지)를 시스템 프롬프트에 넣습니다.
- 근거: [FB#quoting-retrieved-sources](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1#quoting-retrieved-sources)

## F9 작은 수정에 파일 전체를 다시 쓰는 경우

- 결과가 같다면 파일 전체 재작성보다 필요한 부분만 고치라는 지시를 둡니다.
- 근거: [FB#prefer-targeted-edits-over-whole-file-rewrites](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1#prefer-targeted-edits-over-whole-file-rewrites)
