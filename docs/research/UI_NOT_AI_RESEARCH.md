# UI에서 "AI 티"를 없애는 법: 조사와 검증 (2026-11-16)

사용자: "UI들이 AI 느낌이 강하게 든다. AI 티가 안 나게 만들면 좋겠음. 관련 정보를 md 만들어서 조사해서 어떻게 하면 될지 조사, 검증 진행해. 이때 내가 해 줘야 할 것들이 있으면 말하고."
대상: 1차 UI 제안([UI_REDESIGN_PROPOSAL.md](../planning/ui_redesign/UI_REDESIGN_PROPOSAL.md)의 new_play / new_bag).
결과: 2차 제안 그림 [v2_play.png](../planning/ui_redesign/v2_play.png), [v2_bag.png](../planning/ui_redesign/v2_bag.png), 비교 [compare_v1_v2_play.png](../planning/ui_redesign/compare_v1_v2_play.png), [compare_v1_v2_bag.png](../planning/ui_redesign/compare_v1_v2_bag.png). 만든 도구 `tools/ui/ui_mockup_v2.py`.

## 1. 왜 AI가 만든 UI는 티가 나나 (조사)
- **평균으로 수렴한다.** 생성 모델은 가장 흔한 선택(안전한 기본값)으로 간다. "깔끔하게, 모던하게"처럼 막연히 요청하면 웹 앱 화면에서 가장 자주 본 모양이 나온다.
- 디자이너들이 꼽는 대표적인 흔적:
  1. **둥근 카드·둥근 알약 칩**이 모든 곳에 있음
  2. **카드 한쪽 옆에 굵은 색 띠**(가장 알아보기 쉬운 AI UI 흔적으로 꼽힘)
  3. **흔한 산세리프 글꼴**(Inter 같은 기본 글꼴): 글꼴이 가장 강한 단서라는 의견
  4. 그라데이션, 반투명 유리판, 부드러운 그림자, 흐림
  5. 라이브러리 기본 색·간격 그대로(Tailwind, shadcn 기본값)
- 해결책으로 반복해서 나오는 말: **기본값부터 죽여라**(색·모서리·글꼴을 바꿔라), 막연한 요청 대신 **구체적인 제약**(색 목록, 간격 규칙, 글꼴 규칙)을 정해라.

## 2. 1차 제안에서 찾은 AI 흔적 (자기 점검)
| # | 흔적 | 1차 제안에서 |
|---|---|---|
| 1 | 둥근 카드·알약 칩 | 상태 칩(●출혈), 빠른 칸, 프롬프트, 배낭 판 전부 둥근 모서리 |
| 2 | 옆 색 띠 | 배낭에서 고른 줄 왼쪽에 호박색 띠, **바로 그 흔적** |
| 3 | 흔한 매끈한 글꼴 | Noto Sans KR. 도트 그림 위에 매끈한 웹 글꼴 |
| 4 | 반투명 유리·흐림·부드러운 그림자 | 반투명 판, 흐린 붉은 가장자리, 글자 그림자 |
| 5 | 기본 강조색 | 아무 데서나 쓰는 호박색(앰버) |
| 6 | 세상과 무관 | 어느 게임에 붙여도 되는 앱 화면. 핵 재난·한국·도망이라는 우리 이야기가 없음 |
| 7 | 도트와 안 맞음 | 게임은 도트(한 칸 = 2.5화면 픽셀)인데 UI는 매끈한 벡터라 "따로 붙인 스티커" |

7번은 ART_FEEDBACK 3-16(반달이 "스티커처럼 보임")과 같은 실수다.

## 3. 어떻게 하면 되나 (원칙)
1. **도트 격자에 맞춘다.** UI를 게임의 낮은 해상도(640×360)에서 그리고 정수배(×2)로 키운다. 부드럽게 만드는 처리(안티에일리어싱)는 끈다. 반쯤 투명한 판 대신 **디더링**(체크무늬 점)을 쓴다. 도트 게임 UI 안내서들의 공통 조언.
2. **도트 글꼴 하나.** Galmuri(갈무리, 무료 OFL)를 12px 원래 크기로만 쓴다. 글자는 부드러운 그림자 대신 **1px 검은 테두리**(옛 도트 게임 방식).
3. **둥근 모서리·칩·옆 띠를 쓰지 않는다.** 네모 칸 + 1px 테두리 + 위쪽 1px 밝은 줄(폐차 철판 같은 느낌).
4. **세상 안의 물건으로 만든다(디제틱 UI).** 화면 위 앱 판 대신 주인공이 실제로 가진 것: 목표는 **테이프로 붙인 찢어진 쪽지**, 배낭(Tab)은 **수첩**(몸 = 응급 기록, 배낭 = 손으로 쓴 목록, 고른 줄은 **펜으로 친 동그라미**). Dead Space(옷에 붙은 체력), Chasing Static(손글씨 폴라로이드 저장) 같은 예가 있다. 다만 너무 세상 안에만 두면 읽기 어려워지므로, 체력·빠른 칸은 일반 HUD로 둔다(대부분의 게임이 섞어서 씀).
5. **색은 세상에서 뽑는다.** 아스팔트 회색, 바랜 도로 노란 선(쓸 수 있는 것), 녹, 주인공 겉옷, 피. 아무 데서나 쓰는 호박색은 버린다.
6. **아이콘을 손으로 찍는다.** 큰 벡터 아이콘(game-icons)을 12~16px로 줄여 봤더니 뭉개져서 알아볼 수 없었다(검증 4절). 그래서 16×16 도트로 한 칸씩 직접 찍었다(붕대 두루마리, 통조림, 핏방울, 마체테, 배낭).
7. **필요할 때만 보인다.** 행동이 필요한 상태만 화면에 띄운다(출혈 → 붕대, 느림). 상처 목록은 수첩에서 본다.

## 4. 검증
| 항목 | 1차 | 2차 | 확인 방법 |
|---|---|---|---|
| 둥근 모서리·칩 | 많음 | 0 | 그림 확인 |
| 옆 색 띠 | 있음 | 없음(펜 동그라미) | 그림 확인 |
| UI 층의 반투명 픽셀 | 반투명·흐림 다수 | **0** (알파 값이 0과 255뿐) | 스크립트로 UI 층 알파 값 집계 |
| UI에 쓰인 색 수 | **5,725색**(부드러운 가장자리·그라데이션) | 게임 화면 **27색**, 수첩 **10색** | 스크립트로 색 수 집계 |
| 글꼴 | 매끈한 Noto Sans KR | Galmuri 12px, 부드럽게 처리 끔 | 코드 |
| 도트 크기 | 1화면 픽셀 | 2화면 픽셀(640×360에서 그려 ×2) | 코드 |
| 아이콘 | 줄인 벡터 → 뭉개짐 | 직접 찍은 16px 도트 | 그림 확인(game-icons 줄인 버전은 붕대·물림이 덩어리로 보여 버림) |
| 세상과의 연결 | 없음 | 테이프 쪽지, 수첩, 펜 동그라미, 피 십자 표시 | 그림 확인 |

**아직 검증 못 한 것:** "AI 티가 안 난다"는 결국 사람 눈의 판단이다. Claude가 세운 기준(위 표)은 통과했지만, **사용자가 봤을 때 어떤지**가 최종 검증이다. 게임에 넣은 뒤 실제 움직이는 화면으로 한 번 더 비교한다.

## 5. 쓰기로 한 자료, 쓰지 않기로 한 자료
| 자료 | 결정 | 이유 |
|---|---|---|
| Galmuri11, Galmuri11-Bold (`assets/fonts/galmuri/`, OFL 라이선스 파일 같이 둠) | **사용** | 도트 그림과 같은 결, 무료로 게임에 넣어 배포 가능 |
| game-icons.net 아이콘 11개(받음) | **사용 안 함**, 저장소에 넣지 않음 | 작게 줄이면 뭉개지고, 많은 게임이 쓰는 벡터 아이콘이라 오히려 흔한 느낌. 직접 찍은 도트가 더 우리 것 |
| Noto Sans KR | 사용 안 함 | 3절 2번 |

## 6. 사용자가 해 주면 좋은 것
1. **2차 그림 판단(필수):** 1차와 나란히 놓은 그림을 보고 "AI 티가 아직 나는 곳"을 한 줄씩. 예: "쪽지는 좋은데 수첩 종이색이 너무 깨끗함".
2. **좋아하는 게임 UI 화면(선택):** "이런 느낌"인 게임 화면을 `Zombode/ui/`에 넣어 주면 그 결로 맞춘다.
3. **손글씨(선택, 가장 사람 냄새 남):** 종이에 "지하철 입구로", "붕대", "통조림", "몸", "배낭" 등을 펜으로 써서 사진을 찍어 주면, 도트로 바꿔 쪽지·수첩 제목에 쓴다. AI가 만들 수 없는 진짜 사람 손이 들어간다.
4. **실제 물건 사진(선택):** 쓰던 수첩·테이프·메모지 사진이 있으면 종이 질감과 색을 거기서 뽑는다.

## 출처
- AI UI 흔적: [Vandelay Design](https://www.vandelaydesign.com/?p=61673), [SaaS UI](https://www.saasui.design/blog/saas-ui-looks-ai-generated), [UX Planet](https://uxplanet.org/how-to-spot-ai-generated-design-697aaabe76c8), [ux-skill wiki: AI slop](https://github.com/Laith0003/ux-skill/wiki/How-to-detect-AI-slop-in-your-design), [DEV: 사용자는 안다](https://dev.to/olehvolos/users-can-tell-when-your-ui-was-ai-generated-and-they-dont-like-it-33kn), [DEV: AI 느낌 고치기](https://dev.to/alanwest/how-to-fix-the-ai-generated-look-in-your-frontend-1ahh), [superdesign](https://superdesign.dev/blog/why-ai-design-looks-generic), [noqta](https://noqta.tn/en/blog/ai-design-slop-overused-ui-patterns-fix-2026)
- 도트 UI: [Defold 포럼: 도트 게임 GUI](https://forum.defold.com/t/gui-for-pixel-art-games-heres-how/77704), [Unity: 게임 UI 기초(디제틱)](https://unity.com/blog/video-game-ui-ux-basics), [Wayline: 게임 UI 도트 강좌](https://www.wayline.io/learn/game-ui-art/0), [Cinevva: 도트 렌더링](https://app.cinevva.com/tutorials/pixel-art-rendering)
- 디제틱 UI 예: [Wayline: 디제틱 인터페이스](https://www.wayline.io/blog/diegetic-interfaces-game-design), [Somniphobia](https://nathanfallon.squarespace.com/somniphobia), [gamedev.net: 수사관 책상 UI](https://gamedev.net/blogs/entry/572-designing-a-diegetic-ui-layout-psychological-survi), [10 immersive interfaces(Chasing Static)](https://gametyrantindustries.squarespace.com/news/10-immersive-interfaces-every-game-should-have), [indieklem: 디제틱 딜레마](https://indieklem.substack.com/p/19-the-diegetic-dilemma-benefits)
- 글꼴: [Galmuri](https://github.com/quiple/galmuri)

## 7. 2차 뒤 사용자 판단과 배낭 3차 시안 (2026-11-16)
- 사용자: "2차 느낌이 조금 더 괜찮은 것 같다. 다만 인벤토리 부분이 종이에 있다는 게 살짝 부자연스럽다." → 2차의 방향(도트 격자·Galmuri·세상 색, 테이프 쪽지 목표)은 유지, **배낭만** 다시.
- 이유: 쪽지는 원래 목표를 적는 물건이라 자연스럽지만, 가방 속 물건은 눈으로 보는 것이라 종이 목록이 어색하다(디제틱은 그 물건이 실제로 그 정보를 담을 때만).
- 시안 두 개(`tools/ui/ui_mockup_bag.py`): **A. 펼친 배낭 속 보기**(덮개를 젖힌 배낭 안에 물건이 놓임) / **B. 바닥 천에 늘어놓기**(올리브색 천 위에 꺼내 펼침, 빈 배낭은 모서리에). 공통: 몸은 종이 없이 어둡게 한 화면 위 선 그림, 근처 물건은 아스팔트 칸, 고른 물건은 네모 모서리 표시, 물건은 16px 도트 아이콘을 같은 격자에서 2배로.
- 처음 그린 판은 배낭·천이 화면 대부분을 덮어 물건 2개가 허전했고(예전 빈 격자 15칸과 같은 문제) 개수 글자가 아이콘에 겹쳤다 → 그릇 크기를 가방 용량에 맞게 줄이고, 개수는 옆에, 이름은 아래에.
- 그림: [A](../planning/ui_redesign/v3_bag_a_open_pack.png), [B](../planning/ui_redesign/v3_bag_b_ground_sheet.png), [2차·A·B 비교](../planning/ui_redesign/compare_bag_v2_a_b.png).
