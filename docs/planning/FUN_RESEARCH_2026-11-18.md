# 재미 요소 조사 (2026-11-18)

사용자: "지금 어떤 게임 내부적인 요소를 해야 재미가 있을까요? 게임 기획 중 이런 게 있지 않나요? 조사해 보세요"

## 찾아본 기획 이론 네 가지

| 이론 | 한 줄 | 출처 |
|---|---|---|
| **MDA** (Hunicke·LeBlanc·Zubek, 2004) | 규칙(Mechanics) → 플레이 중 생기는 움직임(Dynamics) → 플레이어가 느끼는 감정(Aesthetics). 만드는 사람은 규칙부터, 하는 사람은 감정부터 겪는다. 감정은 "8가지 재미"(감각, 판타지, 이야기, 도전, 동료, 발견, 표현, 시간 보내기)로 나눈다 | [Wikipedia: MDA framework](https://en.wikipedia.org/wiki/MDA_framework) |
| **30초의 재미** (Halo, Jaime Griesemer) | 30초짜리 재미를 제대로 만들면 그걸 늘려 게임 전체를 만들 수 있다. 3초 루프 안에 30초 루프, 그 바깥에 늘 다른 3분 루프 | [Engadget 인터뷰](https://www.engadget.com/2011-07-14-half-minute-halo-an-interview-with-jaime-griesemer.html) |
| **흥미로운 선택** (Sid Meier) | 게임은 흥미로운 선택의 연속. 좋은 선택은 득실이 있고, 상황에 따라 답이 다르다. 위험과 보상이 대표적 | [Game Developer: GDC 2012](https://gamedeveloper.com/design/gdc-2012-sid-meier-on-how-to-see-games-as-sets-of-interesting-decisions) |
| **AI 디렉터의 긴장 곡선** (Left 4 Dead) | 긴장을 쌓고(Build Up) → 터뜨리고(Peak) → 쉬게 한다(Relax). 플레이어가 힘들어하면 적을 줄이고 회복템을 늘린다 | [Valve Developer Wiki](https://developer.valvesoftware.com/wiki/Left_4_Dead_2/Scripting/Director_Scripts), [Shacknews](https://shacknews.com/article/82787/how-evolve-assures-action-peaks-and-valleys) |

## 우리 게임에 대 보기

**목표 감정(MDA):** 도전(살아남기) + 감각(때리는 맛) + 이야기(서울에서 부산까지).

**루프(30초의 재미):**
- 3초: 피폭체 하나와 주고받기(예고 보고 피하고 베기). **지금 가장 약함:** "답답하고 시원하지 않다" → F4 실험(빠르게·세게)
- 30초: 한 무리와 만나기(들킬까, 숨을까, 쏠까)
- 3분: 골목 탐색·파밍 → 역 디펜스 → 기차

**선택(Sid Meier):** 총을 쏠까(강하지만 시끄러움) / 한 집 더 뒤질까 / 시민을 구하러 갈까. 지금 탄약을 주울 곳이 없어서 첫 번째 선택이 한 번뿐이다.

**긴장 곡선(L4D):** 지금은 6~9초마다 일정하게 들어오고, 디펜스도 60초 내내 같은 세기. 쌓고-터뜨리고-쉬는 흐름이 없다.

## 추천

1. **3초 루프 먼저:** 실험(빠르게·세게)을 직접 해 보고 정한다. 이게 재미없으면 나머지가 다 소용없다(Griesemer).
2. **AI 디렉터:** 긴장도에 따라 피폭체가 들어오는 때와 수를 바꾼다. 탐색은 조용히 쌓고, 디펜스 막판에 터뜨리고, 기차 뒤엔 쉰다. 지금 있는 `play.spawn`을 바꾸는 일이라 범위가 작고, 발표 때 "Left 4 Dead의 AI 디렉터 기법"으로 설명할 수 있다.
3. **선택을 늘리기:** 탄약을 귀하게 두되 주울 곳을 만든다(위험한 곳일수록 많이).
