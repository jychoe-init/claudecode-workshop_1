# claudecode-workshop_1

Claude Code Deep Dive Workshop 실습 자료 저장소입니다.

| 폴더 | 챕터 | 내용 |
|---|---|---|
| [`ch4/`](ch4/) | Chapter 4 · Settings 슈퍼랩 | 팀 스타터 킷 빌드: 울타리 · 연결 · 반복작업 · 점검·배포 |

## Chapter 4 슈퍼랩 시작하기

실습 전에 한 번만 실행합니다.

```bash
git clone https://github.com/jychoe-init/claudecode-workshop_1.git ~/claude-lab/claudecode-workshop_1
bash ~/claude-lab/claudecode-workshop_1/ch4/setup.sh
cd ~/claude-lab/superlab
```

`setup.sh`는 `~/claude-lab/superlab`에 실습 프로젝트를 **독립된 git 저장소**로 만듭니다.
클론한 이 폴더에서는 작업하지 않습니다. 실습 결과는 `superlab`에만 쌓입니다.

### 필요한 도구

| 도구 | 버전 | 용도 |
|---|---|---|
| Claude Code | v2.1.283 이상 | `/doctor prompt-audit` 등 |
| git | 2.20 이상 | 실습 프로젝트, 브랜치 |
| Node.js | 18 이상 | 예제 앱 테스트 |
| Python 3 | 3.9 이상 | Slack mock 수신기, 가짜 HR MCP 서버, 사용량 기록 |
| jq | 선택 | 없어도 됩니다 |

### 다시 만들기

실습 프로젝트를 처음 상태로 되돌리려면:

```bash
SUPERLAB_FORCE=1 bash ~/claude-lab/claudecode-workshop_1/ch4/setup.sh
```

기존 폴더는 `superlab.bak-<시각>`으로 옮겨 둡니다.
