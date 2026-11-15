# 좀보이드 동작(애니메이션) 조사 → 우리 게임용 정리 (2026-11-15)

사용자: "애니메이션이나 동작들도 어떻게 하면 될지 미리 싹 다 조사해, 참고해서 하게. 꼭 그대로 따라 하는 건 아닌데 변형해서 해야 하면 참고 자료가 있으면 좋잖아."
사이드 세션 조사. **좀보이드의 그림·코드·파일은 가져오지 않고, 동작 구성과 규칙만 기록한다.**

근거
- 좀보이드 무료 서버 파일 `C:\Users\doboh\pz_research\pzserver\media\AnimSets` (본편 폴더도 같은 구조). 폴더 이름 = 동작 상태, XML 하나 = 그 상태의 동작 하나 + 고르는 조건.
- 공식 개발 블로그(애니메이션 재작업 글): 동작은 상태(AnimState) → 노드(AnimNode) → 트랙 3층, 노드가 바뀔 때 **무게를 서서히 넘기며 섞는다(blend)**. 예전 "프레임 번호를 보고 상태를 바꾸는" 방식을 **이벤트로 바꾸는 상태 기계**로 교체.
- 우리 동작 재료: Quaternius UAL1·UAL2 (`assets/source3d/quaternius_animation_library*/…/UAL*_Standard.glb`, 각 43개).

## 0. 좀보이드 동작 시스템에서 배울 규칙 5개

1. **상태 하나 = 폴더 하나, 변형은 조건으로 고른다.** 예: `zombie/turnalerted/TurnL90.xml`은 `TurnAlertedValue = 90L`일 때, `player/actions/LootLow.xml`은 `LootPosition = Low`일 때 재생. → 우리도 `pose 이름 + 조건값`으로 시트를 고르는 공용 표 하나로 만든다(generic-systems).
2. **무기·자세마다 같은 상태의 다른 버전.** `movement/`에 defaultWalk, walk2handed, walkHeavy, sneakWalk, sneakWalkLow… / `melee/`에 1handed·2handed·heavy 폴더. → 상태는 같고 "무기 종류"만 조건으로 붙인다.
3. **맞은 방향별 반응.** `staggerback/`이 fromFront·fromBehind·fromleft·fromright + small(약하게) 버전. 넘어짐도 `knockeddown-headLeft/Right/Top`. → 2D에서는 앞·뒤 2개면 충분(좌우는 좌우 반전).
4. **같은 동작에 여러 버전을 섞어 반복감을 없앤다.** walktoward1~5, sprint1~5, lunge1·2. 속도 배율(`m_SpeedScale` 0.64 등)과 섞는 시간(`m_BlendTime` 0.5 등)으로 같은 동작도 다르게.
5. **공격은 시작 → 성공/실패 → 끝으로 쪼갠다.** `zombie/attack/`: start, success, fail, interrupted, gracePeriod(물기 직전 유예), enddeath. → 우리 피폭체 공격(예고 → 때리기 → 회복)과 같은 구조. "유예"가 바로 **플레이어가 피할 틈**이다.

## 1. 주인공 동작

| 좀보이드 상태(폴더) | 쓰임 | 우리 게임에서 | UAL 동작 | 없으면 변형 |
|---|---|---|---|---|
| idle | 대기 | 대기 | `Idle_Loop` (UAL1), 무기 들고 `Sword_Idle` | — |
| movement/defaultWalk | 걷기 | 걷기(기본 이동) | `Walk_Loop` | — |
| run / sprint | 달리기·전력질주 | 달리기(Shift 등, 소리 큼) | `Jog_Fwd_Loop`, `Sprint_Loop` | — |
| movement/sneakWalk, sneakWalkLow | 웅크려 걷기(높/낮) | 은신 걷기 | `Crouch_Fwd_Loop`, 대기 `Crouch_Idle_Loop` | 너무 낮으면 걷기 위에 웅크림 40% 섞기(ART_FEEDBACK 기존 해결법) |
| actions/Loot, LootLow, LootHigh | 줍기 높이별 | 물건 줍기·상자 뒤지기 | 중간 `Interact`, 낮게 `PickUp_Table`, 상자 `Chest_Open` | 높은 곳은 `Interact`에서 팔만 위로(드물게 쓰므로 생략 가능) |
| shove (ShoveDefault 등) | 밀치기: 좀비를 넘어뜨리거나 거리 벌림 | 밀치기(비용 없는 거리 벌리기, 피폭체 비틀) | `Push_Loop`(앞 절반만), 짧게 `Punch_Jab` | Push_Loop에서 미는 순간까지 0.25초만 잘라 쓰기 |
| stomp | 쓰러진 좀비 밟기 | 쓰러진 피폭체 마무리 | 없음 | `Jump_Land`의 한쪽 발 내리찍기 부분 또는 `Sword_Regular_*`를 아래로 내려 베기(카메라 위라 크게 문제 없음) |
| melee/1handed: 1HDefault, Overhead, Uppercut, Crit, Miss, OnFloor | 한손 무기 휘두르기 | **마체테 한 번 베기**(마우스 방향) | `Sword_Regular_A/B/C` + 각 `_Rec`(복귀), `Sword_Attack` | 방향 다양화: A=가로, B=반대 가로, C=내려 베기 → 연속 클릭 시 번갈아 |
| melee/…OnFloor | 바닥의 적 공격 | 쓰러진 적 마무리 | 위 stomp와 같음 | — |
| melee/2handed, heavy, SpearCharge | 양손·무거운 무기·창 돌진 | (보류) 무기 늘릴 때 | `TreeChopping_Loop`(양손), `Sword_Dash_RM`(돌진) | — |
| hitreaction, HitReactionFromBehind | 맞음 앞/뒤 | 피격 | `Hit_Chest`, `Hit_Head` | 뒤에서 맞음 = Hit_Chest 좌우 반전 |
| hitreaction-bite | 물림 | 피폭체에게 물림(큰 피격) | `Hit_Knockback` | — |
| knockeddown, falldown, getup | 넘어짐·일어남 | 구르기 실패/강한 피격 후 넘어짐 | 넘어짐 `Hit_Knockback`, 일어남 `LayToIdle` | — |
| death | 죽음 | 쓰러짐(즉시 재시작) | `Death01` | — |
| (좀보이드엔 회피 없음) | — | **구르기** | `Roll` | — |
| climbfence, climbwindow, climbwall | 울타리·창문 넘기 | 담 넘기(지름길) | `ClimbUp_1m_RM` | 낮은 울타리는 `Jump_Start`→`Jump_Land` 짧게 |
| openwindow, smashwindow, forceopendoor | 창문 열기·깨기, 문 따기 | 문·창 열기 | `Interact` | 깨기 = `Punch_Cross` |
| aim, strafe | 조준 중 옆걸음 | 마우스로 보며 옆·뒤로 이동 | `Walk_Loop` 그대로 | 바라보는 방향 고정 + 이동은 따로(아래 3절) |
| bumped | 다른 몸과 부딪힘 | (선택) 피폭체와 부딪혀 휘청 | `Hit_Chest` 약하게 | — |
| draggingBody, pickUpBody 등 | 시체 끌기·옮기기 | 쓰지 않음 | `Walk_Carry_Loop` | — |

## 2. 피폭체(좀비) 동작

| 좀보이드 상태 | 쓰임 | 우리 게임에서 | UAL 동작 | 없으면 변형 |
|---|---|---|---|---|
| idle | 서 있기 | 서성이기 | `Zombie_Idle_Loop` | — |
| walktoward 1~5, zombieWalkSlow 1~3 | 걷기 5종 + 느린 걷기 3종 | 추격(개체마다 다른 걸음) | `Zombie_Walk_Fwd_Loop` | 속도 배율 0.8~1.2로 같은 동작을 다르게, 상체 기울기 차이 |
| sprint1~5, sprintToward | 뛰는 좀비 | (선택) 피폭견·빠른 피폭체 | `Sprint_Loop` | 팔을 늘어뜨리게 상체 뼈 회전 덧입히기 |
| turnalerted (L/R 45·90·135·180) | 소리 듣고 돌아보기 | **소리 들은 피폭체가 돌아봄**(무리 몰려오기 시작 신호) | 없음 | 2D 8방향이면 따로 동작 없이 "멈칫(0.2초) → 방향 바꿈 → 걷기". 멈칫 = `Zombie_Idle_Loop` 첫 칸 |
| lunge, lunge1·2 | 가까이서 덮치기 | **공격 예고 후 덮침** | `Zombie_Scratch` 앞부분 | 몸이 앞으로 기울어지는 칸을 예고(!)로, 할퀴는 칸을 타격으로 |
| attack: start / gracePeriod / success / fail / interrupted | 물기 시작·유예·성공·실패·중단 | 예고 → 유예(피할 틈) → 성공(맞음) / 실패(헛침, 빈틈) / 중단(베여 죽음) | `Zombie_Scratch` | 실패 = 헛친 뒤 휘청(아래 비틀거림 재사용) |
| staggerback (fromFront/Behind/Left/Right, small*) | 맞은 방향별 뒤로 비틀 | 밀치기 맞음 | `Hit_Chest`(앞), `Hit_Knockback` 약하게 | 뒤에서 = 앞으로 고꾸라짐: Hit_Chest 반전 |
| knockeddown-head*, falldown-* | 넘어짐(머리 방향별), 부위별 | 한 방 베임 → 쓰러짐 | `Death01`, `Hit_Knockback` | 베인 방향으로 넘어지게 좌우 반전 |
| onground, getup-fromOnBack/Front | 바닥에 누움·일어남 | (선택) 밀쳐 넘어진 피폭체가 일어남 | `LayToIdle` | — |
| zombie-crawler 전체(walktoward, attack, fakedead) | 기어 다니는 좀비 | (선택) 다리 잃은 피폭체 | 없음 | 정지 그림 몇 장(엎드림) + 앞으로 끌기 2칸 손으로 그리기. 또는 `Death01` 마지막 칸 위에 팔만 움직임 |
| fakedead, fakedead-attack | 죽은 척하다 덮침 | **쓰러진 줄 알았던 피폭체가 일어남**(긴장감 장치) | `LayToIdle` 빠르게 → `Zombie_Scratch` | — |
| thump: DoorBang, DoorClaw | 문 두드리기·긁기 | 문 너머 피폭체 쾅쾅(소리로 위치 알림) | `Zombie_Scratch` 반복, `Punch_Jab` 반복 | — |
| climbfence / climbwindow, hitreaction-fencewindow | 울타리·창문 넘다 넘어짐 | 창문으로 넘어오는 피폭체 | `ClimbUp_1m_RM` | 넘어오다 고꾸라짐 = 끝에 `Hit_Knockback` |
| eatbody | 시체 먹기 | (분위기) 시체에 몰린 피폭체 | 없음 | `Fixing_Kneeling`(무릎 꿇고 손 움직임)을 고개 숙이게 |
| face-target, bumped | 대상 바라보기, 부딪힘 | 방향 바꾸기 | 동작 없이 방향만 | — |

## 3. 동작 전환·조준 규칙 (우리 탑뷰용)

좀보이드: 상태가 바뀔 때 0.2~0.5초 섞기, 조준(aim) 중에는 **보는 방향(마우스)과 걷는 방향이 따로**(strafe·뒷걸음).
우리(2D 시트, 섞기 불가)에서 쓸 규칙:
1. **바라보는 방향 = 마우스**, 걷는 방향 = WASD. 둘이 반대면 걷기를 거꾸로 재생(뒷걸음), 옆이면 그대로.
2. **8방향 시트**: 렌더 카메라를 위에서 3/4로 두고 캐릭터를 45°씩 돌려 8장(오른쪽 3방향은 왼쪽 반전으로 5방향만 렌더).
3. **섞기 대신 "이어 붙이기"**: 공격 끝 → `_Rec` 복귀 동작 → 대기 (이미 swing 시트에서 쓰는 방식). 걷기 ↔ 대기는 다리가 모인 칸에서만 바꾼다.
4. **끊을 수 있는 칸 표시**: 베기는 맞는 칸 이후 복귀 구간에서 구르기로 끊을 수 있게(Katana Zero식 빠른 회전).
5. **예고 칸은 길게, 타격 칸은 짧게**: 피폭체 lunge 예고 0.5초, 할퀴기 0.15초(지금 시험판 값과 같음).

## 4. 우리가 만들 우선순위

1. 주인공: 대기·걷기·뛰기·**베기(A/B/C 번갈아)**·구르기·피격·쓰러짐 — 8방향
2. 피폭체: 서성이기·걷기(속도 차)·**덮치기 예고·할퀴기**·쓰러짐·**돌아보기(멈칫)**
3. 그다음: 밀치기, 은신 걷기, 줍기, 문 두드리기, 죽은 척, 창문 넘기
4. 나중: 기어 다니는 피폭체, 밟기, 시체 먹기

## 5. 사용자가 하면 되는 일

1. 좀보이드에서 아래 장면을 **화면 녹화 또는 캡처**해 `Zombode/`에 넣고 파일 이름에 동작 이름: 한손 무기 휘두르기(가로·내려치기), 밀치기, 밟기, 좀비 돌아보기, 좀비 덮치기, 맞고 비틀거림, 문 두드리기, 창문 넘어오기.
2. 유튜브 영상을 보며 **"분:초 - 동작 - 느낌"** 메모(예: `3:12 - 밀치기 - 짧고 둔탁, 좀비가 두 걸음 밀림`). 좋았던 것 / 우리 게임엔 과한 것 표시.
3. 위 4절 우선순위가 맞는지 확인(특히 밀치기·은신 걷기를 2순위로 올릴지).
4. 렌더 시안이 나오면 "좀보이드 느낌인지" 한 줄 평가 → ART_FEEDBACK에 기록.

## 출처
- 좀보이드 개발 블로그(애니메이션 재작업): https://projectzomboid.com/blog/?p=5791 , https://projectzomboid.com/blog/?p=6276 , https://projectzomboid.com/blog/?p=7038 , https://projectzomboid.com/blog/?p=7212
- AnimSets 사용자 글(비공식): https://steamcommunity.com/app/108600/discussions/0/1694917906659694569
- 로컬: `pz_research/pzserver/media/AnimSets` (player, zombie, zombie-crawler 폴더 이름과 XML 조건값만 확인)
