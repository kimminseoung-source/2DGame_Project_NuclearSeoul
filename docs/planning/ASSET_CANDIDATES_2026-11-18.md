# 무료 그림 후보와 그래픽·효과 품질 올리기 (2026-11-18)

사용자 결정: 캐릭터(주인공, 피폭체, 군인·시민)는 우리 것. 바닥 타일, 거리 소품, 효과(먼지·불꽃·피)는 화풍이 맞는 무료 팩에서 가져와 우리 색으로 다시 칠한다. **아직 아무것도 내려받지 않았다.** 받을 때는 파일마다 사용자에게 묻는다. 좀보이드 그림은 쓰지 않는다.

라이선스 표시: ✔ = 페이지에서 직접 확인, △ = 검색 결과로만 확인(받기 전에 다시 확인).

## 효과 (가장 쓸 만함)

| 팩 | 라이선스 | 들어 있는 것 | 맞는 정도 |
|---|---|---|---|
| [Free 2D VFX Pack (bigdamnhero6)](https://bigdamnhero6.itch.io/free-2d-vfx-pack) | CC0 ✔ (0원 가능) | **피 튀김, 총구 불꽃 2종, 먼지 2종**, 폭발, 독 연기, 불꽃, 번개 불똥, 물보라 | ★★★ 우리에게 필요한 게 거의 다 있음. 크기는 받아 봐야 앎 |
| [PVFX Foundry (Pixel VFX Studio)](https://nerijs.itch.io/pvfx-foundry) | CC0 ✔ (무료) | 효과 253개: **타격 불똥, 피 튀김**, 착지 먼지, 떠다니는 먼지, 연기, 끊긴 전선 불꽃 등 | ★★★ 타격감용. 크게 그린 것(96px)이 많아 줄여야 할 수 있음 |
| [Free Pixel Loops (cs5475)](https://store.godotengine.org/asset/cs5475/free-pixel-loops/) | CC0 ✔ (무료) | 불 7종, **연기 기둥**(회색·먼지·증기, 32/48/64px) | ★★ 폐허의 타는 차, 연기. 같은 사람의 유료 묶음은 CC0가 아님 |

## 바닥 타일·거리 소품

| 팩 | 라이선스 | 들어 있는 것 | 맞는 정도 |
|---|---|---|---|
| [pixel art wasteland (OpenGameArt)](https://opengameart.org/content/pixel-art-wasteland) | CC0 △ | 탑뷰 도시·포스트 아포칼립스 타일 | ★★ 주제는 맞음. 페이지가 열리지 않아 크기·내용 미확인 |
| [Pixel Pack #1 (isaiah658, OpenGameArt)](https://opengameart.org/node/153914/) | CC0 △ | 16px 탑뷰: 차, 트럭, 승합차, 건물, 도로, 인도, 나무 | ★★ 도로·인도·차가 있음. 16px라 2배로 키워 씀. 작가가 고친 그림도 CC0로 내 달라고 부탁함 |
| [topdown pack (CALWebDevelopment)](https://calwebdevelopment.itch.io/topdown-pack) | CC0 ✔ | 32px 탑뷰 슈터용 타일·UI, 산업 시설 | ★ 도시·폐허가 아님 |
| [Top-Down Tanks Redux (Kenney)](https://kenney-assets.itch.io/top-down-tanks-redux) | CC0 ✔ | 드럼통, 상자, 도로, 폭발 | ✘ 벡터 그림이라 도트와 안 맞음 |

무료 + CC0이면서 "한국 도시 폐허"에 딱 맞는 타일 팩은 찾지 못했다. 쓸 만한 것(CC BY: 출처만 밝히면 됨)도 있지만, 상업 금지(NC)나 수정 금지(ND) 팩은 뺐다.

## 직접 그리는 도구

- **[Pixelorama](https://github.com/Orama-Interactive/Pixelorama)**: 무료, 오픈소스(MIT). 레이어·프레임 타임라인, 앞뒤 프레임 겹쳐 보기(어니언 스킨), 픽셀 완벽 선, 타일 모드, PNG·GIF·스프라이트 시트 내보내기. Windows에서 그대로 실행. ([소개](https://itsfoss.com/pixelorama/))
- 우리 쪽 작업 방식: 지금처럼 3D 렌더 → 도트로 줄이기까지는 내가 하고, 윤곽·얼굴·옷 주름은 Pixelorama에서 손으로 덧칠. 결과 PNG를 `assets/characters/`에 넣으면 게임이 그대로 읽는다.

## 효과 품질을 높이는 방법 (조사)

출처: [Mega Cat Juice Guide](https://megacatstudios.com/blogs/game-development/mega-cat-developer-juice-guide-v1-0-08-23-17), [Game feel 정리](https://eastondev.com/blog/en/posts/dev/20260521-game-feedback-feel/), [Godot 게임 필 체크리스트](https://forum.godotengine.org/t/game-feel-checklist-for-godot-4-hit-stop-trauma-shake-coyote-time-and-more/145340)

| 기법 | 권장 | 우리 게임 지금 |
|---|---|---|
| 화면 흔들림 | 아무 때나 흔들면 플레이어가 무뎌진다. 약한 것 1~2px·0.1초, 센 것 4~8px·0.25초로 **단계를 나눠** 중요한 순간에만 | 가로로만 ±2, 모든 타격이 비슷함 |
| 맞을 때 번쩍임 | 맞은 프레임에 하얗게, 2프레임 뒤 원래대로 | 실험 "세게"에만 있음(0.12초) |
| 히트스톱 | 세기에 따라: 약한 타격 2프레임, 센 타격 8~10프레임 | 0.035~0.1초(2~6프레임) |
| 입자 | 동작 사이를 먼지·불똥·파편으로 채운다. 도트 게임은 크고 각진 입자가 잘 어울림 | 피·불똥 몇 가지 |
| 빛 | 그라데이션·동적 조명이 도트 게임 분위기를 크게 바꾼다 | 시야 원뿔(빛) 있음, 손전등·가로등 없음 |

## 다음 단계 (제안)

1. 효과 팩 1개(bigdamnhero6) 받기 허락 → 피 튀김·총구 불꽃·먼지만 골라 우리 색으로 바꿔 넣고 전후 비교
2. 흔들림을 약/강 두 단계로 나누고, 센 타격(머리, 마지막 일격)에만 강하게
3. 바닥 타일은 미리보기를 같이 보고 고르기(화풍이 가장 중요)
