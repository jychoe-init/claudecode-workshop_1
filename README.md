# claudecode-workshop_1

Claude Code Deep Dive Workshop 실습 자료 저장소입니다.

| 폴더 | 챕터 | 내용 |
|---|---|---|
| [`ch4/`](ch4/) | Chapter 4 · Settings 슈퍼랩 | 반복작업 스킬 · 사내 API 업무 자동화 · 프롬프트 점검과 배포 |

## Chapter 4 슈퍼랩 시작하기

실습 전에 한 번만 실행합니다.

```bash
git clone https://github.com/jychoe-init/claudecode-workshop_1.git ~/claude-lab/claudecode-workshop_1
bash ~/claude-lab/claudecode-workshop_1/ch4/setup.sh
cd ~/claude-lab/superlab
```

`setup.sh`는 `~/claude-lab/superlab`에 실습 프로젝트를 **독립된 git 저장소**로 만들고, 강사에게 받은 사내 API 토큰을 `~/.config/superlab/`(권한 600, 저장소 밖)에 등록합니다.
클론한 이 폴더에서는 작업하지 않습니다. 실습 결과는 `superlab`에만 쌓입니다.

### 필요한 도구

| 도구 | 버전 | 용도 |
|---|---|---|
| Claude Code | v2.1.283 이상 | `/doctor prompt-audit` 등 |
| git | 2.20 이상 | 실습 프로젝트 |
| Python 3 | 3.9 이상 | 사내 API 도구, MCP 서버, 랩 검사 |
| Node.js | 선택 | 예제 앱 테스트(`npm test`) |

### 다시 만들기

```bash
SUPERLAB_FORCE=1 bash ~/claude-lab/claudecode-workshop_1/ch4/setup.sh   # 기존 폴더는 superlab.bak-<시각>으로
bash ~/claude-lab/claudecode-workshop_1/ch4/setup.sh --token             # 토큰만 다시 등록
```
