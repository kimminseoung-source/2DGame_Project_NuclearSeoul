# 「부산까지」 공동 작업 규칙 — Claude Code · GPT(Codex)

두 AI가 같은 폴더에서 번갈아 작업한다. 이 파일이 **공동 규칙 한 곳**이다(Codex는 이 파일을 읽고, Claude는 `CLAUDE.md`의 `@AGENTS.md`로 읽는다). 조사·근거: `docs/research/AI_COLLAB_2026-11-25.md`, 계획: `docs/plans/2026-11-25_GPT_공동작업_방식.md`.

## 1. 함께 일하는 법 (2026-11-25 사용자 "GPT가 주로 3D 작업, 이미지 생성 쪽을 맡고, 나눠서 할 수 있는 작업은 GPT한테")

### 역할

| 누구 | 맡는 일 |
|---|---|
| **GPT(Codex)** | 캐릭터·몬스터 원화, AI 이미지 생성, 3D 자세 안내·Blender 작업, 스프라이트 제작, 그림 쪽 시험판 |
| **Claude Code** | 게임 코드(`src/`), 받은 그림을 게임에 연결, 숨긴 창 점검(`tools/checks`), 문서 정리, **커밋·푸시** |
| **사용자** | 방향 결정, 직접 플레이 판단. 사용자가 말한 것만 "확정" |

### 작업 시작할 때 (둘 다)

1. `docs/COLLAB_BOARD.md`(작업판)와 `git status`를 본다. 상대가 커밋 안 한 작업이 있으면 그 파일은 건드리지 않는다.
2. 작업판 "진행 중"에 **내 이름 · 할 일 · 고칠 파일**을 적는다.
3. 작업 계획은 `docs/plans/<날짜>_<주제>.md`(문제 → 근거 문서 → 적용 기법 → 고칠 곳 → 검수 → **손맛(게임 쥬스)** 줄).

### 폴더 담당 (같은 파일 동시 수정이 가장 흔한 충돌)

| 담당 | 폴더 |
|---|---|
| GPT | `assets/characters/previews/`, `assets/characters/concepts/`, `tools/sprites/`, `tools/blender/`, 그림 시험 실행판(`tools/*_look.py`, `tools/run_*_trial.py`) |
| Claude | `src/`, `tools/checks/`, `main.py` |
| 함께(덧붙이기만, 남의 줄 고치지 않기) | `docs/planning/DESIGN_LOCK.md`, `docs/DEVLOG.md`, `docs/RESEARCH_INDEX.md`, `docs/references/*`, `assets/characters/ART_FEEDBACK.md`, `CHARACTER_WORKFLOW.md`, 이 파일 |

- 상대 담당 파일을 꼭 고쳐야 하면 작업판에 먼저 적고, 기본 게임 동작이 바뀌지 않게(시험 스위치는 기본 꺼짐) 한다.
- 그림은 Claude가 그리지 않는다. 필요하면 Claude가 `docs/collab/ASSET_REQUEST.md` 양식으로 **요청서**를 작업판에 남기고 GPT가 만든다.

### 작업 끝날 때

1. 작업판에서 "진행 중" → "끝남"으로 옮기고 **무엇을 했나 · 검수 결과(숫자·그림 경로) · 게임에 연결됐나 · 남은 것**을 적는다.
2. **확정 / 제안 / 시험 중**을 구분해 적는다. 제안을 확정처럼 쓰지 않는다.
3. **커밋은 한 곳**: GPT는 커밋하지 않고 작업판에 적어 둔다. Claude가 `tools/checks/run_all.py`로 점검한 뒤 묶음별로 커밋·푸시한다(커밋 메시지는 한국어).
4. 올리지 않는 것: `docs/CLAUDE_HANDOFF.md`, `참고/`, `.vscode/`, 발표 영상·pptx·pdf, `src/item_ui.py`, `assets/source3d/` 안, 비밀 토큰 파일.

### Claude가 GPT에게 직접 부탁할 때 (Codex CLI, 2026-11-25 설치)

- 읽기만: `codex exec --sandbox read-only --ephemeral "<부탁>"` — 코드·계획 검토, 문서 요약.
- 일 맡기기: `--sandbox workspace-write` + 부탁에 "AGENTS.md와 docs/COLLAB_BOARD.md를 먼저 읽고, 끝나면 작업판에 적을 것"을 넣는다. 작업판 "진행 중"에 GPT 이름으로 먼저 적는다.
- ChatGPT 사용량 한도에 걸리면 멈추고 사용자에게 알린다(결제 안 함).

### 공통 기준

- 한국어로 답하고 기록한다. 무료 도구만. 결제가 필요하면 멈추고 묻는다.
- 게임 창은 숨긴 창으로 점검(`tools/checks/run_hidden.py`). 그린 것과 계산을 숫자로 비교한다.
- 모든 기능에 손맛(게임 쥬스)을 같이 생각한다.

---

## 2. 캐릭터·애니메이션 작업의 조사와 검수 (2026-11-24)

상위 폴더의 과제/경로/커밋 지침을 유지한다. 아래는 사용자 2026-11-24 요청: 기존 조사 기록을 재사용하고, 조사한 기법을 실제 적용하며 같은 실패를 반복하지 않는다.

### 동작·원화 작업을 시작할 때

1. `assets/characters/CHARACTER_WORKFLOW.md`의 최신 기준과 `docs/planning/HERO_MOTION_STATUS.md`의 실제 실행 상태를 먼저 읽는다.
2. 해당 작업에 관련된 `docs/references/ANIMATION_GUIDES.md`, `docs/planning/MOTION_RULES.md`, `docs/planning/MOTION_FEW_SPRITES_2026-11-19.md`, `assets/characters/ART_FEEDBACK.md`를 확인한다. 필요하면 `docs/research/ZOMBOID_ANIMATION_RESEARCH.md`를 확인한다. 과거 제안·현재 사용자 결정·실제 적용 결과를 구분한다.
3. 기존 자료로 부족한 부분만 원저자 튜토리얼/공식 문서 등으로 추가 조사한다. 기법 이름을 나열하는 데 그치지 말고 `docs/plans/`의 작업 계획에 **문제 → 근거 문서/출처 → 적용할 기법 → 수정 대상 → 검수 방법**을 적고 적용한다. 사용자가 이미 실행을 승인했으면 같은 허락을 반복 요청하지 않는다.
4. 공격용 적은 키프레임/스미어/히트스톱을 걷기 접지의 해결책으로 쓰지 않는다. 걷기는 좌우 발 교대, 접촉·통과·들기, 골반/어깨 연결, 실제 이동거리와 보폭, 시작·끝 연결을 먼저 검수한다. 실제 이동 사격에서도 다리 표시가 멈추지 않는지 확인한다.
5. 현재 사용자 기준은 AI 최종 외형 + 3D 자세 참고다. 36px 팔다리 회전이나 전신 늘이기/밀기로 보행을 대신하지 않는다. AI의 포즈 지시 준수는 보장되지 않으므로 최종 그림의 좌우/가림/크기를 검수한다.
6. 결과는 실제 게임 크기와 확대, 정지 루프와 이동 중, 파일/상태 검사와 시각 검수로 나눠 확인한다. 접지 수치는 좌우 발과 실제 접지 구간을 표시하여 측정하고 대략적인 부츠 중심을 완전한 발 고정 검사로 보고하지 않는다.
7. 적용/보류/실패와 남은 제한을 작업 계획, 관련 참고 모음, `docs/CLAUDE_HANDOFF.md`, 실제 동작 비교표에 돌려 기록한다. 다음 작업자가 무엇을 읽고 재사용해야 하는지 연결한다. 검증하지 않은 완성/자연스러움 주장은 하지 않는다.
8. **얼굴 일관성이 최우선이다.** 몸 높이/전체 배율을 맞춘 것을 얼굴 일치로 보고하지 않는다. 같은 방향의 정지·걷기·조준은 기준 머리/얼굴 레이어 공유를 기본으로 하고 실제 로더와 원본/출력의 얼굴 크기·픽셀·목 기준을 비교한다. 방향/표정이 달라 별도 원화가 필요하면 그 범위와 검수 결과를 분명히 한다. 여러 시험 창은 눈에 보이는 빌드/모드를 표시하고 실제 사용자 창을 확인하지 않았으면 단정하지 않는다. FACE-R1 기록은 `assets/characters/previews/hero_pistol_gait_v4/identity/README.md`.

이번 보행 적용 기준: `docs/plans/2026-11-24_보행기법_적용.md`. 과거 문서의 3D 최종 외형/검 중심 추천이 최신 총 중심·AI 외형 결정을 덮어쓰지 않는다.
