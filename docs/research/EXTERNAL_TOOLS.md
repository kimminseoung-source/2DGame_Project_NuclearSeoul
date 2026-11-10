# 외부 도구·맵 에디터·에셋 활용 방안

작성 2026-11-10. 수업에서 외부 에셋과 맵 에디터 사용을 적극 권장한다는 안내를 받고([개발 계획](../../PLAN.md)의 사용자 지시 기록), 「부산까지」에 맞는 도구와 에셋 후보를 조사했다. 가격과 라이선스는 조사 시점 기준이며, 내려받기 전에 각 페이지에서 다시 확인한다.

## 1. 결론 요약

| 분야 | 추천 | 이유 |
| --- | --- | --- |
| 맵 에디터 | **Tiled** (무료) | 지금의 통짜 배경 그림을 이미지 레이어로 그대로 쓰고, 시작점·출구·폐차·적 배치·걸을 수 있는 바닥을 오브젝트(사각형·다각형)로 찍을 수 있다. JSON으로 내보내 pico2d에서 직접 읽는다. |
| 도트 편집 | **Pixelorama**(무료) 또는 **Aseprite**(유료, Steam $19.99) | 외부 스프라이트를 우리 크기·색감에 맞게 다듬고, 프레임을 시트로 내보낸다. |
| 효과음 | **Kenney 오디오**(CC0), **freesound**(CC0만 골라서) | 출처 표기 부담이 적고 공개 저장소에 올려도 된다. |
| 에셋 원칙 | **공개 저장소에 올려도 되는 라이선스만** (CC0, CC-BY, OGA-BY) | 과제 규칙상 실행에 필요한 리소스를 모두 공개 저장소에 올려야 한다. |

## 2. 우리 게임에 맞춰 따질 조건

- **장르 구조**: 횡스크롤에 바닥 깊이(위아래 이동)가 있는 구조다. 타일을 촘촘히 까는 플랫포머보다, 큰 배경 그림 위에 **걸을 수 있는 바닥 영역과 장애물**을 표시하는 방식(벨트 스크롤형)이 맞다.
- **캐릭터 동작**: 턴제 전투와 탐색에 옆모습 대기·걷기·조용히 걷기·공격·피격·쓰러짐 프레임이 필요하다. 동료가 생기면 같은 화풍의 캐릭터가 여러 명 필요하다.
- **화풍 통일**: 배경·캐릭터·적은 가능하면 한 제작자나 한 팩 계열로 맞춘다. 섞으면 해상도와 색감이 어긋난다.
- **공개 저장소와 라이선스**: 과제는 모든 리소스를 공개 GitHub 저장소에 올려야 한다. 그런데 일부 에셋은 "게임에는 써도 되지만 원본 파일 재배포는 금지"다. 공개 저장소에 PNG를 그대로 올리는 것은 재배포에 해당할 수 있으므로 피한다.
- **기록**: 쓰는 파일마다 제작자·출처·라이선스를 [자료 및 출처](../references/ASSETS.md)에 남기고 e-Class 제출란에도 적는다.

## 3. 맵 에디터

### Tiled (추천)

- 무료, 오래 쓰인 표준 도구. JSON 맵 형식 문서가 공개되어 있다([JSON Map Format](https://doc.mapeditor.org/en/stable/reference/json-map-format)).
- **이미지 레이어**: 지금의 `surface_side.png`, `shelter_side.png` 같은 그림 배경을 그대로 깐다. 배경을 타일로 다시 그릴 필요가 없다.
- **오브젝트 레이어**: `spawn`, `exit`, `wreck`, `enemy`(종류·능력치 이름) 같은 점·사각형, 그리고 걸을 수 있는 바닥을 **다각형**으로 찍는다. 오브젝트에 사용자 속성(예: 적 종류 `zombie_regular`, 방어 10)을 붙일 수 있다.
- **pico2d 연결**: pytmx는 pygame이 필요하므로 쓰지 않고, 내보낸 JSON을 읽는 작은 클래스(예: `MapData`)를 만든다. 지금 `tile_map.py`·`shelter.py`에 숫자로 박힌 위치(`SPAWN`, `EXIT`, `WRECK_*`, 바닥 경계)가 맵 파일로 옮겨가므로, 구간을 늘릴 때 코드는 그대로 두고 맵만 새로 만든다.

### LDtk (대안)

- 무료, Dead Cells 제작자가 만든 에디터. 엔티티와 IntGrid(충돌 칸) 중심이고, "Super Simple export"로 레벨별 `data.json`과 레이어 PNG, IntGrid CSV를 내보낸다([JSON overview](https://ldtk.io/docs/game-dev/json-overview/), [Super Simple export](https://deepnight.itch.io/ldtk/devlog/364343/110-introducing-super-simple-export)).
- 칸 단위 플랫포머에 강하다. 우리처럼 그림 배경 위 자유 다각형 바닥을 쓰는 구조에는 Tiled가 더 단순하다.

## 4. 도트 편집 도구

- **Aseprite**: 사실상 표준. Steam $19.99. 많은 에셋 팩이 `.aseprite` 원본을 함께 준다.
- **Pixelorama**: 무료·오픈소스, 꾸준히 개발 중. 애니메이션 프레임과 시트 내보내기를 지원한다.
- **LibreSprite**: 옛 Aseprite에서 갈라진 무료판. 개발 속도가 느리다.
- 용도: 외부 스프라이트의 크기를 우리 캐릭터 높이에 맞추기, 색을 어두운 화풍으로 보정하기, 프레임을 가로 시트로 정리하기.

## 5. 에셋 후보 (조사 결과)

공개 저장소 가능 여부: ✅ 가능(재배포 허용) · ⚠ 재배포 금지 또는 미표기(확인 필요)

| 후보 | 내용 | 가격 | 라이선스 | 공개 저장소 |
| --- | --- | --- | --- | --- |
| [Post-apocalyptic shelter](https://finuarts.itch.io/post-apocalyptic-shelter) (finuarts) | 16×16 횡스크롤 타일, 방공호 입구·가구·폐차·사다리 | 무료(원하는 만큼) | 개인·상업 사용 가능, 표기 선택 | ⚠ 재배포 미표기 → 제작자 확인 |
| [Post-Apocalyptic Pixel Art Asset Pack](https://loovgames.itch.io/apocalyptic-pixel-art-asset-pack-with-houses-characters-trees-tilesets) (Loovgames) | 주인공(대기·걷기·달리기·공격·피격·사망)과 적 1종, 타일, 패럴랙스 배경, `.aseprite` 원본 | $14.99 | 상업 사용 가능, 재배포 금지 | ⚠ 금지 |
| [Free Post Apocalyptic Pixel Art Backgrounds](https://free-game-assets.itch.io/free-post-apocalyptic-pixel-art-backgrounds) (CraftPix) | 1920×1080 배경 4종과 분리 레이어 | 무료 | [CraftPix 라이선스](https://craftpix.net/file-licenses/): 상업 가능, 원본 재배포 금지 | ⚠ 금지 |
| [Free Pixel City Ruin Backgrounds](https://free-game-assets.itch.io/free-city-ruin-backgrounds-pixel-art) (CraftPix) | 폐허 도시 배경 | 무료 | CraftPix 라이선스 | ⚠ 금지 |
| [Free Zombie Sprite Sheet Pack](https://free-game-assets.itch.io/free-zombie-sprite-sheet-pack-pixel-art) (CraftPix) | 좀비 3종: 대기·걷기·달리기·피격·쓰러짐 | 무료 | CraftPix 라이선스 | ⚠ 금지 |
| [Post Apocalyptic Pixel Art Backgrounds](https://opengameart.org/content/post-apocalyptic-pixel-art-backgrounds) (OpenGameArt, CraftPix 제공) | 포스트 아포칼립스 배경 | 무료 | OGA-BY 3.0 (출처 표기) | ✅ 표기하면 가능 (파일 구성은 직접 확인) |
| [128x128 2d zombies spritesheet](https://opengameart.org/content/128x128-2d-zombies-spritesheet) (OpenGameArt) | 좀비 걷기·공격 시트 (피격·쓰러짐 없음) | 무료 | CC0 | ✅ |
| [Zombie Apocalypse Pixel Pack](https://beemaxstudio.itch.io/zombie-apocalypse-pixel-pack) (beemaxstudio) | 32×32 소품 5종(칼, 좀비, 손, 핏자국, 방독면) | 무료(원하는 만큼) | CC0 | ✅ |
| [Streets of Fight](https://ansimuz.itch.io/streets-of-fight) (ansimuz) | 벨트 스크롤 액션용 전체 팩(사이버펑크 밤거리) | 무료(원하는 만큼) | 페이지에서 확인 필요 | ⚠ 확인 필요 — 구조 참고용 |
| Kenney 오디오 (예: Impact Sounds) | 타격·발소리·UI 효과음 | 무료 | CC0 | ✅ |
| [freesound](https://freesound.org) | 효과음 검색 | 무료 | 파일마다 다름(CC0만 사용) | CC0만 ✅ |

### 조사에서 나온 주의점

- **CraftPix 계열(free-game-assets 포함)은 무료여도 원본 파일 재배포가 금지**다. 게임에 쓰는 것은 되지만, 과제 규칙대로 PNG를 공개 저장소에 올리면 충돌할 수 있다. 쓰려면 교수님께 "라이선스상 공개 저장소에 올릴 수 없는 리소스"의 처리 방법을 먼저 확인해야 한다.
- 무료(CC0) 쪽은 **옆모습에 피격·쓰러짐까지 갖춘 캐릭터 세트가 드물다.** 캐릭터는 지금의 주인공·피폭체 도트를 유지하고, 외부 에셋은 배경·소품·효과음 위주로 쓰는 편이 화풍 통일과 라이선스 양쪽에 안전하다.
- 유료 팩의 가격·할인은 자주 바뀐다.

## 6. 제안하는 진행 순서

1. ~~**라이선스 기준 확정**~~ — 결정함: 교육용 과제이므로 폭넓게 사용(재배포 금지 팩 포함). 출처·라이선스는 모두 기록.
2. **Tiled로 지상 맵 1개 이전** — 지금 배경 그림을 이미지 레이어로, 시작점·출구·폐차·피폭체·바닥 영역을 오브젝트로 옮긴다. `MapData` 클래스로 읽어 기존 `TileMap` 상수를 대체하고, 같은 동작인지 탐색·전투 검사로 확인한다.
3. **방공호 맵 이전** — 같은 방식으로 옮긴다.
4. **효과음 교체·추가** — Kenney 타격음 등으로 방망이 타격, 빗나감, 발소리를 보강한다. 타격감 단계(`hit_feel.py`)에 맞춰 강한 타격은 더 묵직한 소리를 쓴다.
5. **배경·소품 보강** — 라이선스가 맞는 배경·소품을 골라 구간 2, 3의 맵을 Tiled로 만든다.
6. 매 단계 [자료 및 출처](../references/ASSETS.md)에 파일별 출처·라이선스를 기록한다.

## 7. 정해야 할 것

- 맵 에디터: Tiled(추천) / LDtk
- ~~라이선스 기준~~ → **결정(2026-11-10): 교육용 과제이므로 라이선스를 폭넓게 적용한다.** 위 표의 ⚠ 후보(CraftPix, Loovgames 등)도 사용할 수 있다. 사용하는 모든 에셋의 제작자·출처·라이선스를 [자료 및 출처](../references/ASSETS.md)와 e-Class 제출란에 적고, 재배포 금지 조건이 있는 파일은 문서에 따로 표시해 문제가 생기면 그 파일만 교체할 수 있게 한다.
- 예산: 무료 도구·에셋만 / 유료(Aseprite, 유료 팩) 허용
- 캐릭터: 지금 도트 유지 / 외부 캐릭터 팩으로 교체

## 출처

- [Tiled JSON Map Format](https://doc.mapeditor.org/en/stable/reference/json-map-format)
- [LDtk JSON overview](https://ldtk.io/docs/game-dev/json-overview/)
- [LDtk Super Simple export](https://deepnight.itch.io/ldtk/devlog/364343/110-introducing-super-simple-export)
- [CraftPix 파일 라이선스](https://craftpix.net/file-licenses/)
- [itch.io 포스트 아포칼립스·횡스크롤 에셋 태그](https://itch.io/game-assets/tag-post-apocalyptic/tag-side-scroller)
- [Aseprite 대체 도구 비교(AlternativeTo)](https://www.alternativeto.net/software/aseprite/)
- 위 표의 각 에셋 페이지
