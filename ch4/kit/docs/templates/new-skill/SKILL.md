---
# 이 폴더를 .claude/skills/<스킬 이름>/ 으로 복사한 뒤 ____ 여섯 곳을 채우세요.
#   cp -R docs/templates/new-skill .claude/skills/<스킬 이름>
# 다 채우면 # 로 시작하는 안내 줄은 지워도 됩니다.
name: ____
# ① 목적: 무엇을 하고, 언제 쓰는지. Claude도 부르게 하려면 이 문장이 트리거입니다.
description: ____
# ③ 호출 방식: 사람만 부르면 true. Claude도 부르게 하려면 이 줄을 지웁니다.
disable-model-invocation: ____
# ④ 입력 힌트: /이름 뒤에 무엇을 붙이는지
argument-hint: "____"
---

# ____

## 독자

② 이 결과물을 누가 읽고, 무엇에 쓰는지: ____

## 입력

④ 무엇을 받고, 없으면 어떻게 하는지: ____ ($ARGUMENTS 로 받은 값을 씁니다)

## 출력

⑤ `${CLAUDE_SKILL_DIR}/template.md`의 양식을 그대로 따릅니다. 양식 외 규칙: ____

## 하지 않을 것

⑥ ____
