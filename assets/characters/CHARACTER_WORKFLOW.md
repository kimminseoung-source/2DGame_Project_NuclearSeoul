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
     --map idle=Idle_Loop walk=Walk_Loop "sneak=Walk_Loop+Crouch_Idle_Loop*0.3" hurt=Hit_Chest down=Death01 pickup=Fixing_Kneeling@0-20 \
     --frames-for idle=4 walk=8 sneak=6 swing=6 hurt=3 down=5 pickup=4 \
     --tilt 20 --head 1.15 --bulk 1.1 --legs 1.0 --shift-for down=16 \
     --flat 0.80,0.62,0.50 --bands 4 --outline
   ```
   두 번째 동작 팩(UAL2)에서 가져오는 동작은 `--anim-file`만 바꿔 따로 렌더한다(한 번에 한 파일).
   ```
   blender -b -P tools/blender/render_sprites.py -- \
     --model "assets/source3d/quaternius_base_characters/Base Characters/Godot - UE/Superhero_Male_FullBody.gltf" \
     --anim-file "assets/source3d/quaternius_animation_library_2/Unreal-Godot/UAL2_Standard.glb" \
     --out assets/characters/base \
     --map "swing=Sword_Regular_A,Sword_Regular_A_Rec@7-23" --frames-for swing=6,3 \
     --tilt 20 --head 1.15 --bulk 1.1 --legs 1.0 --flat 0.80,0.62,0.50 --bands 4 --outline
   ```
   제자리 은신(`sneak_idle`)은 첫 명령의 `--map`에 `"sneak_idle=Idle_Loop+Crouch_Idle_Loop*0.3"`, `--frames-for`에 `sneak_idle=4`를 더한다.
4. **미리보기** — 보여 주기 전에 [그림 작업 피드백과 교훈](ART_FEEDBACK.md)의 점검표를 반드시 통과시킨다. `tools/sprites/preview_sheets.ps1 -SheetDir <시트 폴더> -Out assets/characters/previews/<대상>_v<번호>.png -Title <제목>`으로 만들고 사용자에게 보여 준다.
5. **기준 확정** — 미리보기를 보고 렌더 설정을 조정해 4절에 적는다. 이후 모든 캐릭터는 같은 설정을 쓴다.
6. **주인공 만들기** — 기본 몸에 방호복·후드·방독면·공기통·방망이를 입혀 `assets/characters/hero/`에 렌더한다.
7. **게임 연결** — 실제 화면에서 크기·발 위치·재생 속도를 확인한다. 시트 폴더 이름만 넘기면 `src/character_look.py`의 `SheetLook`이 동작 이름(idle·walk·sneak·swing·pickup·hurt·down)과 시간으로 칸을 골라 그린다. 주인공은 `main.py`의 `PLAYER_LOOK`에 폴더 이름을 적는다. 반복 동작의 칸 시간은 `SheetLook.FRAME_TIME`, 초상화 자르기 영역은 `SheetLook.PORTRAIT`. 걷는 동작은 `look.json`에 다리 한 바퀴에 나아가는 거리(`stride_m`, 걷기(가볍게 뛰기) 1.48m·은신 0.65m)를 적는다. 그러면 시간 대신 유닛이 실제로 걸은 거리(`walk_distance`, m)로 칸을 골라 어떤 이동 속도에서도 발이 미끄러지지 않는다. 보폭은 Blender에서 발이 땅에 닿아 있는 동안 움직인 거리 ×2로 잰다. 공격 동작은 시트 폴더의 `look.json`에 맞는 칸을 적는다(예: `{"swing": {"impact": 3}}`). 공격 객체가 판정 시점(`contact`, 0~1)을 알려 주면, 그 전에는 준비 칸들이, 판정 순간에는 맞는 칸이(히트스톱 동안 유지), 그 뒤에는 나머지 칸이 재생된다. 새 무기나 적의 공격도 맞는 칸만 적으면 같은 방식으로 맞춰진다.
8. **변형 캐릭터** — 1절 특색 기준표를 채워 설계한 뒤 같은 방식으로 렌더한다.
9. **기록** — 매 단계 결과·결정·문제를 6절 작업 기록에 남기고 커밋한다.

### 동작 연결표 (게임 동작 ← 애니메이션 라이브러리)

| 게임 동작 | 사용 애니메이션 | 칸 수 | 메모 |
| --- | --- | --- | --- |
| idle | `Idle_Loop` | 4 | |
| walk | `Jog_Fwd_Loop` | 8 | 2026-11-11부터. 이동 2.2m/s에 걷기 동작(보폭 1.22m)을 쓰면 다리가 너무 바빠져, 보폭이 넓은(1.48m) 가볍게 뛰기로 바꿈 |
| sneak | `Walk_Loop` 위에 `Crouch_Idle_Loop`를 30% 얹음(`Walk_Loop+Crouch_Idle_Loop*0.3`) | 6 | 2026-11-11 30%로 조정(처음 40%). 1.0m/s에 맞게 보폭을 넓힘(0.57→0.65m). 섞을 때는 COMBINE(회전을 곱해 더함)을 써야 함. 단순 평균(REPLACE)은 다리가 뒤로 뒤집힘 |
| swing | `Sword_Regular_A` 6칸 + 복귀 `Sword_Regular_A_Rec` 7~23프레임 3칸 (두 번째 팩 UAL2) | 9 | 사용자 결정 "칼 베기 A + 맞는 칸 맞추기 + 복귀"(2026-11-11). 크게 숙였다가 베어 올린 뒤 제자리로 돌아옴. 맞는 칸은 4번째 칸(인덱스 3)이고 `base/look.json`에 적음. 이전 후보 나무 베기는 `TreeChopping_Loop@0-20` |
| sneak_idle | `Idle_Loop` 위에 `Crouch_Idle_Loop`를 40% 얹음 | 4 | Shift만 누르고 서 있을 때. 시트가 없는 캐릭터는 `sneak` 첫 칸으로 대신함(`character_look.FALLBACK`) |
| hurt | `Hit_Chest` | 3 | |
| down | `Death01` | 5 | 마지막 칸 유지 |
| pickup | `Fixing_Kneeling` 0~20프레임 | 4 | v2부터. 무릎 꿇고 바닥에 손을 뻗는 구간만 사용(v1의 `PickUp_Table`은 테이블 높이라 교체) |

## 4. 렌더 설정

| 항목 | 값 | 상태 |
| --- | --- | --- |
| 칸 | 96×64, 오른쪽을 봄(모델을 Z축으로 90° 회전) | 확정 |
| 비율 | 1.8m = 54px, 발 기준선 위에서 60px | 확정 |
| 렌더 엔진 | Workbench, 안티앨리어싱 끔, 투명 배경, 빈 구덩이 음영(cavity) 끔 | 확정(v2) |
| 체형 | 머리 1.7배(`--head`), 몸통·팔·다리 굵기 1.3배(`--bulk`), 다리 길이 0.8배(`--legs`). 뼈 제약(Limit Scale)으로 고정해 동작이 덮어쓰지 않음 | v3 값 |
| 바닥 맞춤 | 렌더 후 칸마다 가장 아래 픽셀을 바닥선(위에서 59번째 줄)에 맞춤. 다리를 줄여 떠도, 누운 자세라도 항상 바닥에 닿음 | 확정(v3) |
| 칸 안 위치 | 쓰러짐은 뒤로 넘어가므로 그림을 오른쪽으로 16px 옮김(`--shift-for down=16`) | 확정(v3) |
| 색 | 기본 몸은 단색 살색 0.80,0.62,0.50(`--flat`). 옷을 입힌 캐릭터는 재질 색 사용 | v2 |
| 명암 | 스튜디오 조명을 세로축으로 70° 돌려 옆면에 밝은 면·어두운 면이 생기게 하고, 밝기를 4단계로 끊음(`--bands 4`, 셀 셰이딩) | v2 |
| 제자리 고정 | 렌더할 때 root 뼈 위치를 항상 0으로 고정(`pin_root`, 끄려면 `--keep-root`). 두 번째 팩 동작은 root에 앞으로 나가는 이동이 들어 있어, 고정하지 않으면 끝난 뒤 뒤로 툭 튐. 1팩 동작(서 있기·걷기·쓰러짐)은 고정해도 결과가 같음을 확인 | 확정(2026-11-11) |
| 동작 이어 붙이기 | `--map "시트=동작A,동작B@시작-끝"`, `--frames-for 시트=6,3`처럼 쉼표로 이어 붙이면 한 시트에 차례로 렌더. 공격 뒤에 복귀 동작을 붙일 때 씀 | 2026-11-11 |
| 외곽선 | 렌더 후 그림 둘레에 1px 짙은 남색 외곽선(`--outline`). Workbench 자체 외곽선은 작은 크기에서 거의 안 보여 쓰지 않음 | 확정(v2) |

## 5. 결과 이력

| 버전 | 미리보기 | 결과 | 다음에 고칠 점 |
| --- | --- | --- | --- |
| **기본 몸 v4 (2026-11-10, 현재 기준 캐릭터)** | `previews/base_body_v4.png`, 게임 화면 `previews/base_body_v4_ingame.png` | 카메라를 20° 위에서 내려다보게 하고 비율을 거의 원래대로(머리 1.15·몸 1.1·다리 1.0) 되돌림. 사용자 선택 "B가 제일 낫다". 서 있기·걷기·줍기·쓰러짐은 평범한 사람으로 읽힘 | 점검표 결과: ① 은신이 깊게 쪼그린 자세 → v4b에서 해결 ② 휘두르기가 칼 찌르기처럼 팔을 벌림 → v4c에서 해결 ③ 지금 주인공보다 가늘고 조금 큼(옷·장비로 덩치를 만들 예정) |
| 기본 몸 v3 (2026-11-10) | `previews/base_body_v3.png` | 다리를 0.8배로 줄여 키가 지금 주인공과 비슷해짐. 쓰러진 자세까지 모든 칸이 바닥선에 닿고 칸 밖으로 잘리지 않음 | ① 휘두르기는 칼 동작이라 팔을 크게 벌림(무기를 쥐여 보고 판단) ② 웅크려 걷기에서 손이 몸 앞으로 늘어짐 |
| 기본 몸 v2 (2026-11-10) | `previews/base_body_v2.png` | 머리가 커지고 몸이 굵어져 덜 왜소함. 외곽선이 또렷하고, 옆 조명으로 밝은 면·어두운 면이 구분됨. 줍기가 무릎 꿇고 바닥에 손을 뻗는 동작으로 바뀜 | ① 아직 지금 주인공보다 키가 크고 다리가 김(옷을 입힌 뒤 다시 판단) ② 쓰러짐 3~5칸에서 머리가 칸 왼쪽 밖으로 잘림 → 쓰러짐만 칸 안으로 당기는 처리 필요 ③ 휘두르기가 칼 동작이라 팔을 크게 벌림 → 방망이를 쥐여 보고 판단 |
| 기본 몸 v1 (2026-11-10) | `previews/base_body_v1.png` | 동작 7종이 옆모습·같은 발 위치로 나옴. 걷기·공격·쓰러짐 동작이 자연스러움 | ① 체형이 길고 가늘어(Superhero 비율) 지금 주인공보다 왜소해 보임 → 머리·몸통을 키워 2~3등신 쪽으로 ② 외곽선이 약함 ③ 피부 질감이 작은 크기에서 얼룩처럼 보임 → 단색 위주로 ④ 줍기가 바닥 줍기가 아님 |

## 6. 작업 기록

| 날짜 | 한 일 | 결과·결정 |
| --- | --- | --- |
| 2026-11-10 | 기본형 규격과 템플릿 작성 | 칸 96×64, 동작 7종, 레이어 6종 |
| 2026-11-10 | 제작 방식 조사 | 3D → 도트 렌더(Dead Cells 방식)를 무료 도구로 시험하기로 함 |
| 2026-11-10 | Blender 설치, 렌더 스크립트 작성 | 도형 시험에서 칸 크기·발 기준선 확인 |
| 2026-11-10 | Quaternius 기본 몸·동작 팩 내려받기(CC0) | `assets/source3d/`에 정리, README에 출처 기록. 용량이 커 저장소에는 README만 올림 |
| 2026-11-10 | 스크립트에 다른 파일 동작 붙이기·시트 이름 연결 추가, 회전 오류(glTF 쿼터니언) 수정 | 기본 몸 v1 동작 7종 렌더, 미리보기 작성 |
| 2026-11-10 | v2(사용자 지시 "v2 진행"): 체형 조절(머리·굵기), 단색, 셀 셰이딩, 1px 외곽선, 옆 조명, 동작 구간 지정(`동작@시작-끝`), 떠 있는 보조 도형 제거 | `assets/characters/base/` 시트를 v2로 교체(v1 시트는 git 기록에 남음) |
| 2026-11-10 | v3(사용자 지시 "기본 몸 더 다듬기"): 다리 길이 조절, 칸마다 바닥 맞춤, 시트별 가로 위치 조정. 처음 시도한 "몸 전체 내리기"는 누운 자세를 바닥 아래로 밀어 버려 바닥 맞춤으로 바꿈 | `base/` 시트를 v3로 교체 |
| 2026-11-10 | 사용자 지시 "캐릭터는 기본 캐릭터로 우선 진행" | v3 기본 몸을 기준 캐릭터로 삼아 다음 작업을 이어 감 |
| 2026-11-10 | v3 비율 점검(`previews/base_body_v3_zoom.png`): 머리 1.7배로 뒤통수가 길쭉해지고 팔다리가 가늘어 좀비처럼 보임. 사용자 지시 "일단 지금 한 거 적용해 보고" | v3를 게임 주인공에 연결(`src/character_look.py`의 `SheetLook`, `main.py`의 `PLAYER_LOOK = "base"`). 게임 화면 `previews/base_body_v3_ingame.png`. 사용자 의견을 받아 v4에서 비율을 고칠 예정 |
| 2026-11-10 | 사용자 지적 "아래에서 쳐다보는 느낌", "은신 자세도 이상함". 렌더 스크립트에 `--tilt`(카메라를 위에서 내려다보는 각도) 추가, 시험판 A(카메라만)·B(카메라+비율 되돌림 머리 1.15·몸 1.1·다리 1.0) 렌더 | 비교 `previews/base_body_v4_trial.png`. B가 가장 나음. 원인 분석과 점검표는 [ART_FEEDBACK.md](ART_FEEDBACK.md) |
| 2026-11-10 | 사용자 선택 "B가 제일 낫다" | 동작 7종을 B 설정으로 다시 렌더해 `base/`를 v4로 교체, 게임에 바로 반영. 점검표로 남은 문제(은신·휘두르기)를 결과 이력에 적음 |
| 2026-11-11 | 사용자 지시 "은신 먼저". 렌더 스크립트에 동작 섞기(`동작+다른동작*비율`) 추가. 첫 시도(REPLACE)는 다리가 뒤로 뒤집혀 실패, COMBINE으로 바꿔 해결. 시험판 비교 `previews/sneak_trial.png` | 사용자 선택 "B (40%)". `base/sneak.png` 교체(v4b), 게임 화면 `previews/sneak_v4b_ingame.png`. 남은 점: 걸음 중간 칸에서 고개가 조금 숙여짐, 팔이 늘어짐(방망이를 쥐이면 다시 판단) |
| 2026-11-11 | 사용자 지시 "Shift를 누르면 은신 상태로 바로 돌입, 그다음 휘두르기 고치기" | ① 은신 판정(좀비 감지 거리)은 원래 Shift 즉시였고 그림만 서 있는 자세였음 → 제자리 은신 `sneak_idle` 추가. ② 1팩에 방망이 동작이 없어 두 번째 무료 팩 Universal Animation Library 2 [Standard](CC0)를 받음. 후보 5종 중 나무 베기(양손)로 휘두르기 교체(v4c). 게임 화면 `previews/sneak_idle_swing_ingame.png`. 남은 점: 빨간 휘두르기 궤적선은 예전 주인공 기준 위치라 손과 조금 어긋남 |
| 2026-11-11 | 사용자 지시 "칼 베기 A로 해 보세요" | 휘두르기를 `Sword_Regular_A`로 교체해 게임에 넣음. 게임 화면 `previews/swing_sword_a_ingame.png`. 점검표: ① 3칸째에 몸이 바닥 가까이 낮게 숙여짐 ② 마지막 칸이 팔을 치켜든 넓은 자세로 끝나 서 있기로 돌아올 때 툭 바뀜(팩의 `Sword_Regular_A_Rec` 복귀 동작은 아직 안 붙임) ③ 아래에서 위로 베어 올리는 동작이라 옆으로 휘두르기보다는 올려치기로 읽힘 |
| 2026-11-11 | 사용자 결정 "진행"(칼 베기 A + 맞는 칸 맞추기 + 복귀 동작) | 렌더 스크립트에 동작 이어 붙이기와 root 고정 추가. 공용 맞는 칸 방식(`look.json`의 `impact`, 공격의 `contact`) 추가. 판정 순간에 베는 칸이 보이고 히트스톱 동안 유지됨을 게임 화면으로 확인(`previews/swing_impact_ingame.png`). 중간에 점검표에서 "끝나면 30픽셀 앞에서 끝나 뒤로 튐"을 발견해 root 고정으로 해결. 남은 점: 빨간 궤적선은 예전 주인공 기준이라 따라 휘두르는 칸에서 몸 뒤쪽에 그려짐 |
| 2026-11-11 | 사용자 지시 "애니메이션이 빠르다", 선택 "느긋한 걸음, 이동 속도도 낮춤" | 원본 동작 보폭 측정(걷기 한 바퀴 1.22m/1.33초, 은신 0.57m). 걷기 1.2m/s·은신 0.55m/s로 낮추고 다리를 걸은 거리로 재생. 서 있기 칸 시간 0.22→0.55초, 제자리 은신 0.6초. 휘두르기 판정 0.20→0.30초(준비 길게). 게임 화면 `previews/walk_feet_ingame.png`(파란 눈금으로 발이 땅에 붙는지 확인) |
| 2026-11-11 | 사용자 지시 "이동 속도가 너무 느리다, 올리고 동작도 자연스럽게" | 걷기 2.2m/s·은신 1.0m/s·전투 3.0m/s. 걷기 시트를 `Jog_Fwd_Loop`로, 은신·제자리 은신을 웅크림 30%로 다시 렌더. 다리 한 바퀴 약 0.67초(원본의 1.4배)로 자연스러운 범위. 게임 화면 `previews/walk_feet_ingame.png` 갱신 |
