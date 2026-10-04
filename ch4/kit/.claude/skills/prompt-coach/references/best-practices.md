# 공통 원칙 (모든 현재 모델)

- 출처: [Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- 기준일: 2026-10-04. 원문을 옮기지 않고 요점만 정리했습니다. 판단이 갈리면 링크한 원문을 따릅니다.
- 원문은 특정 모델에서 측정한 기법이면 그 모델을 밝힙니다. 다른 모델에 적용할 때는 직접 확인하라고 권합니다.

## B1 명확하고 직접적으로

- 맥락을 모르는 새 동료에게 이 프롬프트를 보여 줬을 때 헷갈릴 부분이 있으면 Claude도 헷갈립니다(동료 테스트).
- 원하는 출력 형식과 제약을 구체적으로 적습니다. 순서나 빠짐없는 수행이 중요하면 번호 목록으로 단계를 줍니다.
- 기본 이상의 결과를 원하면 추측하게 두지 말고 그렇게 요청합니다.
- 근거: [BP#be-clear-and-direct](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#be-clear-and-direct)

## B2 이유와 맥락 주기

- 지시만 두지 말고 왜 필요한지 설명합니다. 예: "말줄임표 금지"보다 "음성 합성기가 읽을 글이라 말줄임표를 발음할 수 없으니 쓰지 마세요".
- 이유를 알면 Claude가 비슷한 경우로 일반화합니다.
- 근거: [BP#add-context-to-improve-performance](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#add-context-to-improve-performance)

## B3 예시 쓰기

- 형식, 어조, 구조를 맞추는 데 가장 확실한 방법입니다. 실제 사용 사례와 비슷하고, 경계 사례를 포함해 서로 다르게, `<example>`(여러 개면 `<examples>`) 태그로 감쌉니다.
- 3~5개가 좋습니다.
- 근거: [BP#use-examples-effectively](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#use-examples-effectively)

## B4 XML 태그로 구분하기

- 지시, 맥락, 예시, 입력이 섞이면 `<instructions>`, `<context>`, `<input>`처럼 종류별 태그로 나눕니다. 태그 이름은 일관되게, 계층이 있으면 중첩합니다.
- 근거: [BP#structure-prompts-with-xml-tags](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#structure-prompts-with-xml-tags)

## B5 역할 주기

- 시스템 프롬프트에서 역할을 한 문장만 줘도 행동과 어조가 맞춰집니다.
- 근거: [BP#give-claude-a-role](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#give-claude-a-role)

## B6 긴 자료는 위에, 질문은 끝에

- 긴 문서나 데이터(대략 2만 토큰 이상)는 지시와 질문보다 위에 둡니다. 질문을 끝에 두면 응답 품질이 테스트에서 최대 30%까지 좋아졌습니다.
- 문서가 여럿이면 `<document>` 안에 `<source>`, `<document_content>`로 나눕니다.
- 긴 문서 작업은 관련 부분을 먼저 인용하게 한 뒤 그 인용을 바탕으로 답하게 합니다.
- 근거: [BP#long-context-prompting](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#long-context-prompting)

## B7 하지 말 것 대신 할 것을 말하기

- "마크다운 쓰지 마"보다 "자연스럽게 이어지는 문단으로 쓰세요"처럼 원하는 모습을 말합니다.
- 프롬프트의 형식이 출력 형식에 영향을 줍니다. 마크다운을 줄이고 싶으면 프롬프트에서도 마크다운을 줄입니다.
- 근거: [BP#control-the-format-of-responses](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#control-the-format-of-responses)

## B8 행동을 원하면 행동을 요청하기

- "개선점을 제안해 줄래?"라고 하면 제안만 합니다. 바꾸길 원하면 "이 함수를 바꿔서 성능을 개선해"처럼 씁니다.
- 예전 모델에서 도구를 덜 쓰던 문제를 막으려고 쓴 "CRITICAL: 반드시 이 도구를 써야 한다" 같은 문구는 최신 모델에서 과하게 작동합니다. "이럴 때 이 도구를 쓰세요" 정도로 낮춥니다.
- 근거: [BP#tool-usage](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#tool-usage)

## B9 예전 모델용 과잉 지시 걷어내기

- "애매하면 무조건 도구를 써라", "철저히, 빠짐없이, 최대한" 같은 문구는 최신 모델에서 과도한 탐색과 비용을 부릅니다. 상황을 지정한 지시로 바꾸고, 그래도 과하면 effort를 낮춥니다.
- 더 꼼꼼하게 하라고 다그치는 문구(anti-laziness)는 줄입니다.
- 근거: [BP#overthinking-and-excessive-thoroughness](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#overthinking-and-excessive-thoroughness), [BP#migration-considerations](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#migration-considerations)

## B10 prefill 대신 다른 방법 쓰기

- Claude 4.6 계열부터 마지막 assistant 턴을 미리 채우는 prefill은 지원되지 않고 400 오류가 납니다.
- 형식 강제는 structured outputs나 형식 지시로, 서두 생략은 "서두 없이 바로 답하세요" 같은 직접 지시나 XML 태그 출력으로 바꿉니다.
- 근거: [BP#migrating-away-from-prefilled-responses](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#migrating-away-from-prefilled-responses)

## B11 생각의 양은 effort로

- 최신 모델은 adaptive thinking으로 얼마나 생각할지 스스로 정하고, 깊이는 effort로 조절합니다. Claude 4.7 이후 모델에 `budget_tokens`를 주면 400 오류가 납니다.
- 프롬프트로 "깊이 생각하라"를 덧붙이기 전에 effort 설정을 먼저 봅니다. 쓰는 곳별 위치: Claude Code 대화는 `/effort`, 스킬은 frontmatter `effort:`, API는 effort 파라미터.
- 근거: [BP#thinking-and-reasoning](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#thinking-and-reasoning), [Effort](https://platform.claude.com/docs/en/build-with-claude/effort)

## B12 중간 결과를 봐야 하면 나눠서

- 대부분의 여러 단계 추론은 모델 안에서 처리됩니다. 중간 결과를 확인하거나 파이프라인을 강제해야 할 때만 초안 → 기준 검토 → 수정처럼 호출을 나눕니다.
- 근거: [BP#chain-complex-prompts](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#chain-complex-prompts)

## 모델별 차이

모델마다 따로 읽을 페이지가 있습니다: [BP#model-specific-guidance](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#model-specific-guidance). 이 스킬의 `references/models/` 파일이 그 요점입니다.
