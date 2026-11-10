# 캐릭터 제작 작업 기준

이 문서는 캐릭터를 **어떤 기준으로, 어떤 순서로, 어디에** 만드는지 정리하고, 작업할 때마다 갱신한다. 칸 크기·동작 목록 같은 숫자 규격은 [기본형 캐릭터 제작 규격](CHARACTER_SPEC.md), 방식을 고른 근거는 [고품질 도트 캐릭터 제작 방식 조사](../../docs/research/CHARACTER_PIPELINE.md)에 있다.

- 시작: 2026-11-10.
- 사용자 지시
  - "해야 할 작업들을 너가 하세요. 관련 작업들을 어떻게 하고 어떤 기준으로 캐릭터들을 만들고 작업하는지 md를 만들어서 유지하세요."
  - "작업하는 곳은 모두 동일한 파일에서 진행하세요." "동일한 파일 안에서 잘 분류해서 제가 언제 봐도 잘 알 수 있게끔 분류를 잘하면서 작업하세요. md에 반드시 기록하세요."
- 담당: 캐릭터 제작 작업(내려받기, 3D 준비, 렌더, 정리, 게임 연결, 기록)은 Claude가 한다. 사용자는 미리보기를 보고 결정한다.

## 0. 폴더 지도 (모든 작업은 이 프로젝트 폴더 안에서)

임시 폴더나 다운로드 폴더에 결과를 두지 않는다. 새 종류의 파일이 생기면 아래 표에 먼저 자리를 정하고 넣는다.

| 위치 | 무엇 | 저장소 |
| --- | --- | --- |
| `assets/characters/CHARACTER_WORKFLOW.md` | 이 문서(기준·순서·기록) | 올림 |
| `assets/characters/CHARACTER_SPEC.md` | 칸·동작·레이어 숫자 규격 | 올림 |
| `assets/characters/templates/` | 손으로 그릴 때 쓰는 안내 시트 | 올림 |
| `assets/characters/base/` | **기본 몸** 동작 시트 7종(`idle.png` … `pickup.png`) | 올림 |
| `assets/characters/<캐릭터 이름>/` | 완성 캐릭터의 동작 시트(예: `hero/`) | 올림 |
| `assets/characters/previews/` | 확인용 미리보기 이미지(`<대상>_v<번호>.png`) | 올림 |
| `assets/characters/**/_frames/` | 렌더 중 생기는 낱장 프레임 | 안 올림 |
| `assets/source3d/` | 3D 원본 팩(용량 큼). 목록은 `assets/source3d/README.md` | README만 올림 |
| `tools/blender/render_sprites.py` | 3D → 도트 시트 렌더 스크립트 | 올림 |
| `tools/sprites/preview_sheets.ps1` | 미리보기 이미지 만드는 스크립트 | 올림 |

## 1. 지켜야 할 기준

### 기획과의 관계

- 교수님 지침에 따라 [1차 발표](../../docs/presentation/부산까지_기획2_1차발표.pdf)에서 벗어나지 않는다. 주인공은 1차 발표 콘셉트의 **노란 방호복 생존자**를 기준으로 한다.
- 세계관: 핵 재난 이후의 가상 한국. 판타지·사이버펑크 요소(마법, 갑옷, 네온, 로봇)는 넣지 않는다.

### 화풍

- 다크풍 도트. 배경은 어둡게, 캐릭터는 배경 위에서 또렷하게 보이도록 외곽선과 밝은 면을 둔다.
- 모든 캐릭터는 같은 방식(3D → 도트 렌더)과 같은 렌더 설정(4절)으로 만든다. 한 캐릭터만 다른 설정으로 뽑지 않는다.
- 색은 채도를 낮춘 현실적인 색. 캐릭터마다 **대표 색 1개**만 선명하게 둔다(예: 주인공 = 방호복 노랑).

### 특색이 드러나는 기준 (사용자 요구: "캐릭터 특색이 도드라지면 좋겠다")

캐릭터를 하나 만들 때 아래 네 가지 중 **세 가지 이상**이 다른 캐릭터와 달라야 한다.

| 요소 | 예시 |
| --- | --- |
| 실루엣(체형·머리 모양·등 소품) | 큰 배낭, 긴 코트, 헬멧, 묶은 머리 |
| 대표 색 | 노랑, 주황, 흰색, 짙은 초록 |
| 무기·손 소품 | 방망이, 쇠파이프, 렌치, 구급가방 |
| 자세·동작 느낌 | 웅크림, 곧은 자세, 큰 보폭 |

게임 크기(실제 화면 1배)에서 **검게 칠한 실루엣만 보고도** 누구인지 구분되는지 확인한다.

### 기본형과 변형 (사용자 요구: "제일 기본형을 만들고 거기서 변형")

- 모든 사람 캐릭터는 **같은 기본 몸 + 같은 동작**에서 시작한다.
- 변형은 옷·머리·등 소품·무기 교체와 색 바꾸기로 한다. 동작을 캐릭터마다 새로 만들지 않는다.
- 무기는 손 뼈에 붙인다. 무기를 바꿔도 휘두르기 동작은 그대로 쓴다(모든 공격에 공통인 전투 구조와 같은 원칙).
- 피폭체(좀비)는 사람 기본 몸의 변형으로 만들 수 있으면 그렇게 하고, 어렵다면 외부 무료 좀비 스프라이트를 같은 색감으로 맞춘다.

### 무료·출처

- 무료 도구와 무료 에셋만 쓴다.
- 쓰는 모든 외부 파일은 [자료 및 출처](../../docs/references/ASSETS.md)와 `assets/source3d/README.md`에 제작자·주소·라이선스를 적는다.
- 리소스는 프로젝트 기준 상대경로로 불러온다.

## 2. 도구와 원본

| 도구·원본 | 용도 | 비고 |
| --- | --- | --- |
| Blender 5.2.3 LTS | 3D 캐릭터 준비, 도트 렌더 | 2026-11-10 winget으로 설치. `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe` |
| `tools/blender/render_sprites.py` | 3D → 96×64 옆모습 시트 렌더 | 화면 없이 실행 |
| `tools/sprites/preview_sheets.ps1` | 시트 확대 + 게임 화면 비교 미리보기 | |
| Quaternius Universal Base Characters [Standard] | 기본 몸 | CC0. 무료판은 Superhero 남·여 체형만 |
| Quaternius Universal Animation Library [Standard] | 동작 43종 | CC0. 기본 몸과 뼈 이름이 같아 바로 붙음 |
| Pixelorama | 렌더 결과 손질 | 필요할 때만 |

## 3. 작업 순서와 명령

1. **3D 원본 확보** — `assets/source3d/<팩 이름>/`에 압축을 풀고 `assets/source3d/README.md`에 기록한다.
2. **동작 이름 확인**
   ```
   blender -b -P tools/blender/render_sprites.py -- --model <동작 파일> --out <아무 폴더> --list
   ```
3. **시트 렌더** — 동작 7종을 규격 칸 수로 렌더한다(현재 동작 연결은 아래 표).
   ```
   blender -b -P tools/blender/render_sprites.py -- \
     --model "assets/source3d/quaternius_base_characters/Base Characters/Godot - UE/Superhero_Male_FullBody.gltf" \
     --anim-file "assets/source3d/quaternius_animation_library/Unreal-Godot/UAL1_Standard.glb" \
     --out assets/characters/base \
     --map idle=Idle_Loop walk=Walk_Loop sneak=Crouch_Fwd_Loop swing=Sword_Attack hurt=Hit_Chest down=Death01 pickup=PickUp_Table \
     --frames-for idle=4 walk=8 sneak=6 swing=6 hurt=3 down=5 pickup=4
   ```
4. **미리보기** — `tools/sprites/preview_sheets.ps1 -SheetDir <시트 폴더> -Out assets/characters/previews/<대상>_v<번호>.png -Title <제목>`으로 만들고 사용자에게 보여 준다.
5. **기준 확정** — 미리보기를 보고 렌더 설정을 조정해 4절에 적는다. 이후 모든 캐릭터는 같은 설정을 쓴다.
6. **주인공 만들기** — 기본 몸에 방호복·후드·방독면·공기통·방망이를 입혀 `assets/characters/hero/`에 렌더한다.
7. **게임 연결** — 실제 화면에서 크기·발 위치·재생 속도를 확인한다.
8. **변형 캐릭터** — 1절 특색 기준표를 채워 설계한 뒤 같은 방식으로 렌더한다.
9. **기록** — 매 단계 결과·결정·문제를 6절 작업 기록에 남기고 커밋한다.

### 동작 연결표 (게임 동작 ← 애니메이션 라이브러리)

| 게임 동작 | 사용 애니메이션 | 칸 수 | 메모 |
| --- | --- | --- | --- |
| idle | `Idle_Loop` | 4 | |
| walk | `Walk_Loop` | 8 | |
| sneak | `Crouch_Fwd_Loop` | 6 | 웅크려 걷기 |
| swing | `Sword_Attack` | 6 | 칼 공격을 방망이 휘두르기로 사용 |
| hurt | `Hit_Chest` | 3 | |
| down | `Death01` | 5 | 마지막 칸 유지 |
| pickup | `PickUp_Table` | 4 | 무릎 꿇는 동작이 아님(테이블 높이). 바닥 줍기는 추후 교체 검토 |

## 4. 렌더 설정

| 항목 | 값 | 상태 |
| --- | --- | --- |
| 칸 | 96×64, 오른쪽을 봄(모델을 Z축으로 90° 회전) | 확정 |
| 비율 | 1.8m = 54px, 발 기준선 위에서 60px | 확정 |
| 렌더 엔진 | Workbench, 텍스처 색, 안티앨리어싱 끔, 투명 배경 | 시험 중 |
| 조명·외곽선 | 스튜디오 조명, 짙은 남색 외곽선 | 시험 중 — v1에서 외곽선이 거의 안 보임 |
| 색 단계 | 채널당 6단계 | 시험 중 |

## 5. 결과 이력

| 버전 | 미리보기 | 결과 | 다음에 고칠 점 |
| --- | --- | --- | --- |
| 기본 몸 v1 (2026-11-10) | `previews/base_body_v1.png` | 동작 7종이 옆모습·같은 발 위치로 나옴. 걷기·공격·쓰러짐 동작이 자연스러움 | ① 체형이 길고 가늘어(Superhero 비율) 지금 주인공보다 왜소해 보임 → 머리·몸통을 키워 2~3등신 쪽으로 ② 외곽선이 약함 ③ 피부 질감이 작은 크기에서 얼룩처럼 보임 → 단색 위주로 ④ 줍기가 바닥 줍기가 아님 |

## 6. 작업 기록

| 날짜 | 한 일 | 결과·결정 |
| --- | --- | --- |
| 2026-11-10 | 기본형 규격과 템플릿 작성 | 칸 96×64, 동작 7종, 레이어 6종 |
| 2026-11-10 | 제작 방식 조사 | 3D → 도트 렌더(Dead Cells 방식)를 무료 도구로 시험하기로 함 |
| 2026-11-10 | Blender 설치, 렌더 스크립트 작성 | 도형 시험에서 칸 크기·발 기준선 확인 |
| 2026-11-10 | Quaternius 기본 몸·동작 팩 내려받기(CC0) | `assets/source3d/`에 정리, README에 출처 기록. 용량이 커 저장소에는 README만 올림 |
| 2026-11-10 | 스크립트에 다른 파일 동작 붙이기·시트 이름 연결 추가, 회전 오류(glTF 쿼터니언) 수정 | 기본 몸 v1 동작 7종 렌더, 미리보기 작성 |
