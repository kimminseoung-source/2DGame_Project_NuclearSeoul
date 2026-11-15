# 바닥에 늘어놓는 인벤토리 / 근처 물건 UI 조사 (2026-11-16)

사용자: 배낭 시안 B(바닥 천에 늘어놓기)에 대해 "이 방식이 괜찮은 것 같음, 다만 조금 더 UI적으로 다듬을 필요가 있을 것 같음, 다른 게임에서는 주로 어떻게 하는지 조사를 해 보고 적용하면 좋겠음".
대상 시안: `docs/planning/ui_redesign/v3_bag_b_ground_sheet.png` (도구 `tools/ui/ui_mockup_bag.py`). 원칙: [UI_NOT_AI_RESEARCH.md](UI_NOT_AI_RESEARCH.md) (640×360 도트 격자, Galmuri, 둥근 칩·옆 색 띠·유리판 금지, 세상에서 뽑은 색).
**그림·소리는 가져오지 않고 규칙과 배치만 본다.** 사이드 세션 조사, 코드·시안 수정은 메인 세션.

> 근거 수준: 웹 검색으로 확인된 것은 출처를 달았다. 검색에서 화면 설명을 찾지 못한 게임(Darkwood, RE4, Cataclysm 등)은 **널리 알려진 일반 지식**으로 적고 "(일반 지식)"으로 표시했다. 적용 전에 영상·스크린샷으로 한 번 확인하면 좋다.

## 0. 지금 B 시안 (출발점)

- 가운데 "배낭에서 꺼낸 것" 천(올리브색) 위에 붕대 ×2, 통조림 ×1, 배낭 아이콘. 오른쪽 위 무게 `0.6 / 2.0`.
- 오른쪽 "근처" 상자에 통조림 ×1. 왼쪽 몸 상태(58%, 부위 상처), 손 = 마체테.
- 아래 설명 줄(붕대: 피를 멈추고 체력 +15%, 개당 0.1)과 키 안내(Enter 쓰기, X 버리기, F 다 줍기, WASD 고르기, Tab 닫기).
- 다듬을 점(Claude 판단): 천 아래 절반이 비어 "덜 만든 화면"처럼 보임 / 물건 자리가 정해져 있지 않아 어디가 다음 칸인지 모름 / 근처 칸과 천이 따로 놀아 옮기는 흐름이 안 보임 / 무게가 숫자만 있어 얼마나 남았는지 한눈에 안 들어옴 / 고른 표시(노란 모서리)는 좋음.

## 1. 다른 게임들이 공통으로 쓰는 장치

| 장치 | 게임들이 하는 방식 | 예 |
|---|---|---|
| **물건 배치** | ① 칸 격자(자리 고정) ② 크기 격자(물건이 차지하는 칸 = 부피, 회전) ③ 목록(줄) | ① Don't Starve 슬롯 줄(일반 지식) ② Tarkov·DayZ·RE4 가방 격자, R/Space로 회전 [PC Gamer][gfinity] ③ Project Zomboid 목록 + 무게 열 |
| **바닥에 펼친 물건** | 바닥을 **하나의 칸 묶음**으로 보여 주고 거기서 몸·가방으로 옮김 | NEO Scavenger: 바닥 물건과 인형(몸)을 한 화면에 [Steam 토론] / DayZ: "근처(Vicinity)" 칸이 왼쪽 세로 줄 [DayZ 포럼, 모드 설명] |
| **내 것 ↔ 근처 나누기** | 화면을 **좌우 두 판**으로: 한쪽 내 몸·가방, 한쪽 근처(바닥·상자). 근처 상자는 탭/아이콘으로 바꿈 | Project Zomboid: 내 인벤토리 창 + 근처 보관함(Loot) 창, 근처 바닥 물건도 보임 [PZ wiki] / DayZ: 근처 칸에서 상자 아이콘을 누르면 그 아래로 펼쳐짐 |
| **고른 물건 표시** | 칸 테두리를 밝게 / 모서리 꺾쇠 / 칸 배경 한 단계 밝게. 들고 옮길 때는 반투명으로 커서에 붙음 | Tarkov·DayZ 격자(일반 지식), 우리 B 시안의 노란 꺾쇠 |
| **이름·개수·무게** | 개수는 **아이콘 오른쪽 아래 작은 숫자**, 이름·무게·설명은 **아래 또는 옆 설명칸 한 곳**에 몰아서 | Tarkov·DayZ: 칸 안엔 아이콘+개수만, 이름은 마우스 올리면 / PZ: 목록에 이름·무게 열 |
| **한 번에 옮기기** | "모두 줍기(Loot All)"·"같은 종류 옮기기" 버튼, Shift+클릭 | PZ: Loot All·Transfer All [PZ wiki, CleanUI 토론], 같은 종류 줍기는 모드에서 시작해 본편에 들어옴 [Easy Drop'n'Loot] |
| **빈 공간** | 빈 칸을 **흐린 칸 무늬**로 그대로 보여 줌 → "더 넣을 자리"로 읽힘 | Tarkov·RE4 격자(일반 지식), Don't Starve 빈 슬롯 |
| **용량** | 숫자(현재/최대) + **막대 또는 칸 수**. 넘치면 빨강, 넘친 채로 들면 느려짐 | PZ: 무게 숫자 `x / y`, 넘치면 무거움 상태 / This War of Mine: 가방 크기가 칸 수(사람마다 8~17) [twinfinite] |
| **조작** | 마우스 끌어 놓기 + 단축키(우클릭 메뉴, Shift 옮기기), 패드는 방향키로 칸 이동 + 버튼 | PZ 끌어 놓기·Shift+우클릭 [Steam 토론], DayZ·Tarkov R/Space 회전 |
| **세상과 이어짐** | 화면을 열어도 뒤 세상이 보이거나 시간이 흐름(긴장 유지) | PZ·DayZ: 인벤토리 열어도 시간 흐름 / Darkwood: 열면 시간 흐름(일반 지식) |

## 2. 우리 게임에 맞춰 B 시안에 넣을 것

조건: 물자 3종, 무게 한도 2.0, 키보드 WASD/Enter/X/F/Tab + 마우스.

| # | 적용 항목 | 구체적으로 | 근거 게임 |
|---|---|---|---|
| 1 | **천 위에 흐린 칸 격자** | 천을 4×2(또는 5×2) 칸으로 나누고 빈 칸은 바느질 자국 같은 점선 네모(천 색에서 한 단계 어둡게). 아래 절반이 "빈 자리"로 읽힘 | Tarkov·RE4·Don't Starve 빈 칸 |
| 2 | **크기 = 무게** | 칸 하나 = 0.1. 붕대 1칸, 통조림 2칸(가로), 물병 2칸(세로) 식으로 무게만큼 칸 차지 → 숫자를 안 봐도 얼마나 남았는지 보임. 회전은 넣지 않음(3절) | Tarkov·DayZ 크기 격자, This War of Mine 칸 수 = 용량 |
| 3 | **무게 막대** | `0.6 / 2.0` 옆(또는 천 아래 가장자리)에 20칸 막대(칸 하나 0.1). 1.6 넘으면 주황, 2.0 넘으면 빨강 | PZ 무게 숫자 + 넘침 상태 |
| 4 | **개수는 아이콘 오른쪽 아래, 이름은 아래 설명칸만** | 천 위에서는 이름 글자를 빼고 `×2`만(아이콘 오른쪽 아래, 테두리 글씨). 이름·효과·개당 무게는 지금 아래 설명 줄에 이미 있음 → 천이 덜 붐빔 | Tarkov·DayZ 칸 표기 |
| 5 | **근처 칸을 천과 같은 격자로** | 오른쪽 "근처"도 같은 칸 크기(땅바닥 색 아스팔트 격자). 칸 크기가 같으니 옮기면 어디로 가는지 보임. 근처 아래 작은 글씨 "바닥", 상자가 여럿이면 `◀ 바닥 · 차 트렁크 ▶`로 바꿈 | DayZ 근처 칸, PZ 근처 보관함 |
| 6 | **옮기는 흐름 표시** | 근처 칸에서 고른 물건에 Enter → 천의 다음 빈 칸으로 이동하는 짧은 이동(2~3칸 그림). 반대로 X는 천 → 근처(바닥)로 | PZ·NEO Scavenger 바닥 ↔ 몸 옮기기 |
| 7 | **WASD로 두 판 사이 이동** | 천의 오른쪽 끝에서 D → 근처 칸으로 커서가 넘어감. Tab은 닫기 그대로. 지금 키 안내 유지 | 패드 방식 칸 이동(Tarkov/DayZ 패드) |
| 8 | **F = 같은 종류 다 줍기 / Shift+F = 근처 전부** | 지금 "F 다 줍기"를 둘로: 고른 물건과 같은 종류 모두 / 근처 전부. 무게 넘으면 들어가는 만큼만 넣고 나머지는 근처에 남김 + 무게 막대 깜빡 | PZ Loot All·같은 종류 줍기 |
| 9 | **마우스** | 끌어 놓기(천 ↔ 근처), 우클릭 = 쓰기, 칸 위에 올리면 아래 설명 줄 갱신. 들고 있을 때 놓일 칸을 밝게 | PZ·Tarkov 끌어 놓기 |
| 10 | **고른 표시는 지금 꺾쇠 유지** | 노란 꺾쇠 + 칸 배경 한 단계 밝게. 들 수 없을 때(무게 초과)는 꺾쇠를 빨강으로 | Tarkov 놓을 수 없는 칸 빨강(일반 지식) |
| 11 | **뒤 세상 시간** | 배낭 열면 시간이 느려지거나(우리 시간 느리게와 연결) 그대로 흐름 — 기획 결정 필요. 화면 가장자리에 뒤 장면을 어둡게 비침 | PZ·DayZ·Darkwood 열어도 시간 흐름 |

## 3. 넣지 않을 것

| 항목 | 이유 |
|---|---|
| 물건 회전(R/Space) | 물자 3종·한도 2.0이라 테트리스식 정리의 재미가 생길 만큼 칸이 많지 않음. 조작만 늘어남 |
| 옷·가방 여러 개(몸 부위별 칸) | DayZ·Tarkov·PZ의 깊이는 물건 종류가 수백 개라 필요. 우리는 배낭 하나로 충분 |
| 마우스 올렸을 때 뜨는 떠 있는 설명창 | 아래 설명 줄이 이미 있음. 떠 있는 창은 유리판·그림자 등 "AI 티" 요소가 되기 쉬움(UI_NOT_AI 원칙) |
| 우클릭 메뉴 목록 | 할 수 있는 일이 쓰기·버리기·줍기 3개뿐 → 키 안내 줄로 충분 |
| 내구도·신선도 막대 | 지금 기획에 없음(보류함: 무기 내구도) |
| 물건 정렬 버튼·검색 | 3종이라 필요 없음 |
| 둥근 칩 모양 개수 표시, 옆 색 띠로 종류 구분 | UI_NOT_AI 원칙 금지 항목 |

## 4. 메인 세션에 넘기는 적용 순서 제안

1. 천에 칸 격자 + 무게만큼 칸 차지(1·2) → 빈 화면 문제와 용량 문제를 한 번에 해결
2. 무게 막대(3), 개수만 남기고 이름 빼기(4)
3. 근처를 같은 격자로(5), WASD로 넘어가기(7)
4. F/Shift+F, 마우스, 옮기는 짧은 이동(6·8·9)
5. 11은 기획 결정 후

## 출처
- [PC Gamer: Escape from Tarkov is a compelling game about gear, and how we store it](https://www.pcgamer.com/escape-from-tarkov-is-a-compelling-game-about-gear-and-how-we-store-it)
- [gfinity: DayZ 인벤토리에서 물건 돌리기](https://www.gfinityesports.com/dayz/dayz-how-to-rotate-items-inventory-make-space-ps4-xbox-pc/)
- [DayZ 포럼: 근처 칸이 필요한 이유 토론](https://forums.dayz.com/topic/230908-open-inventory-scan-environment-rinse-and-repeat-how-can-we-change-loot-and-scavenging-should-we-even/?page=2)
- [DayZ Inventory 모드 설명(근처 칸 구성 참고)](https://modrinth.com/project/dayz-inventory)
- [Gamepressure: DayZ 줍기](https://www.gamepressure.com/dayz/picking-up-items/zc3d2c), [DayZ 인벤토리 창](https://gamepressure.com/dayz/inventory-window/zb3d2b)
- [NEO Scavenger 화면 설명(Steam 토론)](https://steamcommunity.com/app/248860/discussions/1/630800445086175236)
- [PZ Wiki: 보관함과 Loot All](https://pzwiki.net/wiki/Bin)
- [PZ CleanUI 토론: Transfer All](https://steamcommunity.com/workshop/filedetails/discussion/2799848602/3807281445014067131)
- [PZ Easy Drop'n'Loot: 같은 종류 옮기기](https://steamcommunity.com/sharedfiles/filedetails/comments/2871469707)
- [PZ Inventory Tetris(근처 바닥을 격자로)](https://steamcommunity.com/sharedfiles/filedetails/changelog/2982070344)
- [twinfinite: This War of Mine 가방 크기](https://twinfinite.net/?p=248578)
- [Game Developer: This War of Mine UX/UI 분석](https://gamedeveloper.com/design/learning-and-improving-upon-this-war-of-mine-a-ux-ui-analysis)
- [TV Tropes: Grid Inventory](https://tvtropes.org/pmwiki/pmwiki.php/Main/GridInventory)
