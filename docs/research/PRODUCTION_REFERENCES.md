# 제작 도구와 참고 자료

작성 2026-11-13. 사용자 요청 "제 프로젝트에 도움이 될 제작 사이트, 참고할 사이트가 있는지 조사해 보세요."
조건: **무료만**(사용자 예산 없음), 지금 방향(옆 시점 실시간 근접 전투, 은신, 3D 동작 → 2D 도트).
맵 에디터·에셋 팩·도트 편집 도구는 이미 [외부 도구 방안](EXTERNAL_TOOLS.md)에 있으므로 여기서는 **그 밖의 제작 도구**와 **참고할 글·영상**을 정리한다.

## 1. 바로 쓸 만한 제작 도구 (무료)

| 도구 | 무엇 | 우리 게임에 쓸 곳 | 라이선스·주의 |
| --- | --- | --- | --- |
| [ChipTone](https://sfbgames.itch.io/chiptone) | 브라우저에서 효과음을 만드는 도구 | 베기·찌르기·내려치기, 완벽 회피, 반격, 대시 소리를 무기별로 따로 만들기(지금은 타격음 하나뿐) | 만든 소리는 CC0(어디든 사용 가능). 내보내기가 잘린다는 사용자 보고가 있어 확인 필요 |
| [jsfxr](https://github.com/chr15m/jsfxr) | sfxr 계열 8비트 효과음 생성기(웹) | ChipTone 대안. 줍기·UI 소리 | 무료(유료 Pro판은 필요 없음) |
| [Kenney 효과음 팩](https://kenney.nl/assets/rpg-audio) | 게임용 효과음 묶음(RPG Audio, Interface Sounds 등) | 발소리, 문, 배낭·UI 소리. "Impact Sounds" 팩은 타격음 후보 | CC0, 출처 표기 선택 |
| [Galmuri(갈무리)](https://github.com/quiple/galmuri) | 한글 도트 글꼴(7·9·11·14px 등) | 지금 UI 글꼴(맑은 고딕 계열)을 도트 화풍에 맞는 글꼴로 바꾸기 — 대사창·HUD·피해 숫자 | SIL OFL 1.1: 게임에 넣어 배포 가능, 글꼴만 따로 판매 금지 |
| [Pixelorama](https://orama-interactive.itch.io/pixelorama) | 무료·오픈소스(MIT) 도트 편집기 | 2D 옷 그리기 도구가 만든 시트를 손으로 다듬기, 효과(먼지·피) 프레임 그리기. 어니언 스킨·시트 내보내기 지원 | 무료. Aseprite(유료) 대신 |
| [Lospec Palette List](https://lospec.com/palette-list) | 도트 그림용 색 팔레트 모음 | 맵·캐릭터·이펙트를 한 팔레트로 묶어 화풍 통일(다크풍 팔레트를 골라 2D 옷 그리기 색에도 적용) | 무료 |

## 2. 참고할 글·영상

### 3D 동작으로 2D 도트 만들기 — 우리 방식과 가장 비슷
- **Dead Cells의 3D → 2D 제작 방식** ([Game Developer 원문 미러](https://www.jikguard.com/news/art-design-deep-dive-using-a-3d-pipeline-for-2d-animation-in-dead-cells), [80.lv 사례 연구](https://80.lv/articles/case-study-dead-cells-character-art-pipeline)). 3D 모델·동작을 도트 시트로 렌더하는 방식으로, 우리 Blender → 2D 옷 그리기 도구와 같은 생각이다. 배울 점: **열쇠 칸(keyframe)을 먼저 적은 칸으로 읽히게 만든 뒤 사이 칸을 더한다**, 무기 무게감은 칸을 다시 그리지 않고 동작 쪽에서 고친다. → 우리 `windup`·`hold`·적은 칸 수 연타와 같은 방향.

### 타격감(손맛)
- **Juice It or Lose It** (Martin Jonasson·Petri Purho, [GDC Vault](https://gdcvault.com/play/1016487/Juice-It-or-Lose)): 밋밋한 벽돌깨기에 연출을 하나씩 더해 손맛을 키우는 시연.
- **The Art of Screenshake** (Jan Willem Nijman, Vlambeer, 2013 INDIGO): 화면 흔들림, 느린 화면, 맞은 자리 흔적(탄피·핏자국이 남는 것) 등 액션 게임 손맛 기법.
- **Masahiro Sakurai on Creating Games** (스매시브라더스 감독의 유튜브, [소개 기사](https://www.videogameschronicle.com/news/masahiro-sakurais-new-youtube-channel-gives-his-thoughts-on-game-design)): 첫 강의가 히트스톱("Stop for Big Moments"), 이후 [히트스톱 기법 8가지](https://www.gonintendo.com/contents/13581-sakurai-s-latest-game-dev-video-features-8-hit-stop-techniques). 짧고 핵심만 있어 한 편씩 보기 좋다.
- 우리에게 남은 손맛 거리(이 자료들에서 나온 것): 맞은 자리에 남는 흔적(핏자국·파편이 잠깐 남기), 무기별 효과음, 피폭체가 맞을 때 흰색으로 번쩍, 마무리 타에 잠깐 확대.

### 옆 시점 은신과 시야
- **Mark of the Ninja** 설계 이야기 ([은신 설계 5원칙](https://www.pcgamer.com/stealth-game-design-mark-of-the-ninja), [2D 은신 다시 만들기](https://www.gamedeveloper.com/design/reinventing-stealth-in-2d-with-i-mark-of-the-ninja-i-)). 옆 시점 은신의 대표작. **빛과 어둠을 "보인다/안 보인다" 둘로만 나누고, 소리가 닿는 범위를 원으로 화면에 그려서** 계기판 없이 상태를 알 수 있게 했다. → 우리 방향(어둠 + 손전등 시야, 은신)에 바로 참고할 만하다.
- **Darkwood의 시야 연출** ([Game Developer](https://gamedeveloper.com/design/how-i-darkwood-i-s-visibility-mechanics-create-a-new-kind-of-horror)): 보는 방향만 보이게 하자 공포가 생겼다는 개발자 이야기. 시야 밖 소리로 긴장을 만든다.

## 3. 우리 게임에 적용한다면 (제안, 우선순위 순)

1. **효과음 늘리기 (ChipTone·Kenney)** — 지금은 모든 타격이 같은 소리. 무기 데이터(`weapon.py`)에 타격마다 소리를 붙이는 공통 구조로 하면 다른 무기에도 그대로 쓴다. 작업이 작고 손맛 차이가 크다.
2. **한글 도트 글꼴 (Galmuri)** — UI가 한눈에 "도트 게임"처럼 보인다. 글꼴 파일 하나 바꾸는 작업.
3. **은신 표시를 Mark of the Ninja처럼** — 은신 중 들키는 거리를 원으로 그려 주기. 이미 있는 `ALERT_DISTANCE`를 보여 주기만 하면 된다.
4. **팔레트 통일 (Lospec)** — 그림이 늘어날 때 색이 따로 놀지 않게 한 팔레트를 정해 두기.

## 출처
- [ChipTone (sfbgames, itch.io)](https://sfbgames.itch.io/chiptone)
- [jsfxr (GitHub)](https://github.com/chr15m/jsfxr)
- [Kenney RPG Audio](https://kenney.nl/assets/rpg-audio), [Kenney Interface Sounds](https://kenney.nl/assets/interface-sounds), [Impact Sounds (Godot Asset Library 이식판, CC0)](https://www.godotengine.org/asset-library/asset/edit/7694)
- [Galmuri (산돌구름 소개, OFL)](https://www.sandollcloud.com/free-font/17347/Galmuri11), 원본 [github.com/quiple/galmuri](https://github.com/quiple/galmuri)
- [Pixelorama (itch.io)](https://orama-interactive.itch.io/pixelorama), [소개 기사(It's FOSS)](https://itsfoss.com/pixelorama/)
- [Lospec Palette List](https://lospec.com/palette-list)
- [Dead Cells 3D 제작 방식 (Game Developer 미러)](https://www.jikguard.com/news/art-design-deep-dive-using-a-3d-pipeline-for-2d-animation-in-dead-cells), [80.lv 사례 연구](https://80.lv/articles/case-study-dead-cells-character-art-pipeline), [80.lv 인터뷰](https://80.lv/articles/interview-with-the-developers-of-dead-cells)
- [Juice It or Lose It (GDC Vault)](https://gdcvault.com/play/1016487/Juice-It-or-Lose), [Vlambeer 액션 게임 조언 (Game Developer)](https://gamedeveloper.com/design/vlambeer-co-founder-shares-advice-on-building-better-action-games)
- [Sakurai 채널 소개 (VGC)](https://www.videogameschronicle.com/news/masahiro-sakurais-new-youtube-channel-gives-his-thoughts-on-game-design), [히트스톱 8가지 (GoNintendo)](https://www.gonintendo.com/contents/13581-sakurai-s-latest-game-dev-video-features-8-hit-stop-techniques)
- [Mark of the Ninja 은신 5원칙 (PC Gamer)](https://www.pcgamer.com/stealth-game-design-mark-of-the-ninja), [Reinventing stealth in 2D (Game Developer)](https://www.gamedeveloper.com/design/reinventing-stealth-in-2d-with-i-mark-of-the-ninja-i-)
- [Darkwood 시야 연출 (Game Developer)](https://gamedeveloper.com/design/how-i-darkwood-i-s-visibility-mechanics-create-a-new-kind-of-horror)
