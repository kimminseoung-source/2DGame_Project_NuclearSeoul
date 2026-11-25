# 적은 스프라이트로 역동적인 동작 만들기 (조사, 2026-11-19)

## 2026-11-24 · 보행에는 별도 기법을 적용

이 문서의 공격 2~3장/스미어/히트스톱은 보행 접지 해결책이 아니다. 사용자 요청으로 기존 기록을 재사용하며 [보행 적용 계획](../plans/2026-11-24_보행기법_적용.md)과 [D 실제 결과](../../assets/characters/previews/hero_pistol_gait_v4/README.md)를 연결했다.

- [SLYNYRD Human Walk Cycle](https://www.slynyrd.com/blog/2024/5/24/pixelblog-50-human-walk-cycle): 참고→좌우 색 구분 모형→의상, 4/6/8장 비교. D는 8단계 모형 검토 후 AI 외형을 적용하고 잘못된 2/3/5번을 지정 수정했다.
- [SLYNYRD Side View Run 'N Gun](https://www.slynyrd.com/blog/2026/1/26/side-view-run-n-gun): 기본 보행 뒤 총 든 팔 변형, 이동 사격 하체 재생 유지. D는 낮춰 들기/조준의 보행 순서를 맞추고 전신 반동이 다리 표시를 멈추지 않도록 적용했다. 이동 중 전용 상체 반동 그림은 미완성이며 효과만 유지한다.
- [Monmouth University Walk Cycle](https://animation.monmouth.edu/instruct/animation/walk-cycle/): 반 주기의 반대 발 접촉, 통과/다운/밀어내기, 끝의 중복 시작 프레임 제외. D 원화는 0/4 반대 발 접촉으로 대조했다.
- 8장 생성 자체는 성공 근거가 아니며 실제 다리 정체성, 발 궤적, 입력 이동, 게임 크기로 검수한다. 발 오차는 아직 남아 있다. 세부 근거/수치는 위 결과 문서를 따른다.

사용자: "어떻게 하면 스프라이트를 최소화해서 모션들을 만들 수 있을까? 임팩트 효과 같은 걸로 가려서 할 수 있나? 그런 기법들이 있을 것 같은데 조사를 좀 해 봐, 내가 말하는 선 안에서만 움직이지 말라고!"

배경: 서 있는 몸에 무기만 돌리면 약하고, 몸을 코드로 늘이고 미는 건 "이상해"였다(ART_FEEDBACK). PixelLab 직접 설명 휘두르기는 역동적이지만 방향마다 1회가 든다.

## 찾은 기법

| 기법 | 무엇 | 출처·예 | 그림 수 |
|---|---|---|---|
| 핵심 자세만 (key pose) | 준비 → 치기 → 회복 2~3장만. 중간은 안 그림. 적은 장수가 오히려 더 세 보인다 | Slynyrd Pixelblog 9·56, gamedev 포럼 | 방향당 2~3 |
| 스미어 프레임 (smear) | 휘두르는 중간 1장을 늘어진 잔상 모양으로. 한 장이면 충분, 휘두르는 쪽 아크를 따라 | Slynyrd 9, GDQuest | 방향당 1 (또는 효과 그림으로 대신) |
| 베기 효과로 가리기 (slash VFX) | 팔이 지나가는 자리에 큰 베기 궤적 그림을 덮어서, 팔 동작은 효과가 보여 줌. 효과만 빠르게 바뀌면 몸은 2장이어도 됨 | GDQuest(정지 스미어 1장), 무료 효과 팩(OpenGameArt CC0, itch) | 효과 1세트, 몸은 그대로 |
| 맞는 순간 멈춤 + 타격 불꽃 | 친 자세를 4~8프레임 붙잡고(히트스톱) 그 자리에 불꽃·번쩍임. 눈은 효과를 보느라 몸 동작을 덜 봄 | Slynyrd 56(친 자세를 오래, 반동 1장), 게임필 글 | 0 (이미 있음) |
| 준비 자세를 보이게 | 들어 올린 자세를 잠깐 붙잡으면 "의도 있는 공격"으로 읽힘. 2장으로 바로 베면 경련처럼 보임 | 게임필 글 | 준비 1장 |
| 무기·손 따로 (layered) | 몸과 무기를 따로 그리고 무기를 코드로 돌림. 손까지 떼어 내 손 그림 두 개만 움직이는 게임도 있음 | Enter the Gungeon·Nuclear Throne 손 모드(무기마다 손 좌표) | 0 (이미 함) |
| 위·아래 몸 나누기 | 다리(걷기)와 윗몸(공격)을 따로. 걸으면서 공격해도 공격 그림은 한 벌 | Hotline Miami식 질문, Velocity 2X 애니메이션 글 | 윗몸만 공격 그림 |
| 방향 줄이기 | 이동은 8방향, 공격은 4방향(대각선은 가까운 쪽). 효과가 각도를 정확히 보여 주니 몸 방향이 조금 어긋나도 티가 덜 남 | 일반적 | 공격 4방향 |
| 무기마다 같은 몸, 다른 효과 | 몸은 한 동작, 무기마다 효과 모양·크기·색만 다르게(도끼는 두껍고 느리게, 칼은 가늘고 빠르게) | 일반적 | 0 |

## 우리 게임에 맞춘 제안

**공격 1개당: 몸 3장 × 4방향 + 베기 효과 1세트, 나머지는 코드**

1. **몸 3장:** PixelLab 직접 설명 휘두르기(방향당 1회, 9장)에서 **준비·치기·회복 3장만** 골라 쓴다. 4방향이면 무료 4회.
2. **효과로 가리기:** 준비 → 치기 사이에 베기 궤적 효과 한 번(2~3프레임). 무기는 지금처럼 손에 붙어 돌고, 궤적이 그 위를 덮는다.
3. **맞는 순간:** 이미 있는 히트스톱·흔들림·하얀 번쩍임에 타격 불꽃 1개를 더한다. 친 자세를 그동안 붙잡는다.
4. **무기 차이는 효과로:** 도끼·방망이·식칼은 같은 몸 3장, 효과 모양만 다르게.
5. **칼날 팔:** 같은 몸 3장 + 칼날을 손에 붙이고 보라색 궤적.

그림 수 비교:

| 방법 | 공격 하나 | 무기 5개 + 칼날 |
|---|---|---|
| 무기마다 8방향 9장 | 72장 | 432장 |
| 이 제안 | 몸 12장 + 효과 1세트 | 몸 12장 + 효과 6세트 |

## 효과 그림은 어디서

- 무료(CC0): OpenGameArt "pixel art sword slash effect", "more pixelated attack/hit animations" 등. 받기 전에 사용자 허락, 라이선스 확인.
- PixelLab에도 VFX 도구가 있다(무료분 사용).
- Claude가 직접 그리지 않는다(ART_FEEDBACK). 코드로 그린 매끈한 반달은 도트 위에서 스티커처럼 보인다는 지적(2026-11-13)이 있어서, 효과도 도트 그림을 쓴다.

## 출처

- [Pixelblog 9 - Melee Attacks (Slynyrd)](https://slynyrd.com/blog/2018/9/8/pixelblog-9-melee-attacks)
- [Pixelblog 56 - Top Down Character Attack Animation (Slynyrd)](https://www.slynyrd.com/blog/2025/5/23/pixelblog-56-top-down-character-attack-animation)
- [Juicing up your game attacks (GDQuest)](https://gdquest.com/library/juicy_attack)
- [Game feel 2D combat juice tricks](https://freegamesprites.com/es/news/game-feel-2d-combat-juice-tricks)
- [Hands Mod for Nuclear Throne Together](https://splattie.itch.io/hands-mod)
- [The animation system of Velocity 2X (80.lv)](https://80.lv/articles/the-animation-system-of-velocity-2x)
- [Slash Shape Fundamentals (jasontomlee)](https://jasontomlee.itch.io/slashfx/devlog/629732/tutorial-2-slash-shape-fundamentals)
- [pixel art sword slash effect (OpenGameArt)](https://opengameart.org/content/pixel-art-sword-slash-effect)
