# 좀보이드 커뮤니티·공략 조사 (2026-11-16)

사용자 지시: "좀보이드 관련 글이 디시, 유튜브에 많은 것 같습니다. 관련 정보를 먼저 싹 다 조사하죠. md를 따로 만들고 진행을 하죠. 막 진행하지 말고."
→ **이 문서는 조사만 한다. 게임은 바꾸지 않는다.** 적용할 것은 6절 후보 목록에서 사용자가 고른 뒤에.

함께 보는 문서: [ZOMBOID_REA_ANALYSIS.md](ZOMBOID_REA_ANALYSIS.md)(게임 파일에서 확인한 규칙과 숫자), [ZOMBOID_VISUAL_REFERENCE.md](../planning/ZOMBOID_VISUAL_REFERENCE.md), 사용자 자료 `Zombode/`(저장소 제외: 입문 공략 자막, UI 스크린샷과 메모).

## 1. 조사 방법과 한계
- 한국: 디시 프로젝트 좀보이드 마이너 갤러리, 아카라이브 좀보이드 채널, 에펨코리아·루리웹 후기, 나무위키, 인벤·공략 사이트.
- 영어: 팬 위키(pzwiki, fandom), 공식 개발 블로그, PC Gamer·PCGamesN·GamesRadar 기사, 스팀 토론, 리뷰 요약.
- **유튜브는 직접 볼 수 없다**(소리를 못 들음). 사용자가 준 입문 공략 자막(`Zombode/참고자료.txt`)과 스크린샷으로 대신했다.
- 출처마다 빌드(B41/B42)가 섞여 있고, 일부 팬 사이트는 질이 낮다. 숫자는 게임 파일에서 확인한 값(REA 분석 문서 3부)을 우선한다.

## 2. 사람들이 꼽는 재미 (공통)
| 재미 | 내용 | 출처 |
|---|---|---|
| **소리가 곧 위험** | "소리가 좀비를 부른다"는 규칙 하나로 모든 소리가 위험이 된다. 조용히 마을을 지나가는 긴장감 | 리뷰들, 영문 가이드 |
| **언젠가 죽는다** | 시작 문구 "이것이 당신이 죽은 방법이다". 죽음이 정해져 있어 오래 살아남은 것 자체가 성취, 정든 캐릭터가 죽는 아쉬움이 다시 하게 만든다 | 리뷰들 |
| **쌓아 가는 맛** | 내가 모은 물자로 채운 거점, 파밍 한 번이 원정처럼 느껴짐 | 리뷰들 |
| **현실감과 자유도** | "굉장히 현실적인 게 장점", 몰입하면 정말 재밌다, 전투 손맛도 생각보다 괜찮다 | 에펨코리아 80시간 후기, minimap |
| **친구와 함께** | 아무것도 모르고 친구랑 할 때가 제일 재밌다, 멀티에서 역할 나누기(운전, 의사 등) | 루리웹, 입문 공략 자막 |

## 3. 사람들이 꼽는 단점
| 단점 | 내용 | 출처 |
|---|---|---|
| **진입 장벽** | 공략 없이는 처음에 계속 죽는다, 튜토리얼이 불친절, 조작이 어렵다 | 리뷰 요약, 위키 리뷰, 디시 뉴비 가이드 |
| **UI** | 오래된 UI, 복잡함, 글자가 작다(입문 공략도 "글자 크기를 두 배로" 권함) | GamingOnLinux, 리뷰 요약, 입문 공략 자막 |
| **중반 이후 반복** | 거점이 안정되면 목표가 줄어 반복만 남는다 | 에펨코리아 후기, 스팀 의견 |
| **억울한 죽음** | 실내에서 뜻밖의 감염, 무리에게 끌려가 즉사(아포칼립스 설정) | 에펨코리아 후기, 입문 공략 자막 |
| **멀티 버그·최적화** | 멀티 버그, 성능 문제 | 리뷰 요약 |

## 4. 시스템별로 알게 된 것

### 4-1. 소리와 어그로
- 근접 무기는 비교적 조용, 총은 크게 끈다. 뛰면 소리가 커서 좀비가 몰리고 지친다 → **걷거나 웅크리고 다녀라**(입문 공략, 영문 가이드).
- 세상 소리: 총소리, 건설, 발전기, 차, 경보, **헬리콥터**가 좀비를 부른다(B42 가이드).
- **헬리콥터 이벤트**: 보이지 않고 소리만 들리는 "먼 사건". 6~9일째 낮에 한 번, 플레이어를 발견하면 머리 위를 맴돌며 좀비 무리를 끌고 다닌다. 발견되지 않아도 좀비가 조금 이동(PC Gamer, pzwiki).
- 무리 이동(meta): 큰 소리를 따라 좀비 무리가 맵을 가로질러 이동.
- **동적 음악**: 41.71부터 긴장 상황에 맞춰 음악이 바뀌는 "액션 음악" 시스템(PCGamesN, 공식 블로그).
- (파일에서 확인) 좀비 목소리 개체별 3종, 놀람 소리, 시체 파리 소리, 심장 박동.

### 4-2. 전투
- **혼자 여러 마리를 상대하지 마라**, 밀치기(Shove)로 거리를 벌려라(입문 가이드들).
- **밀쳐 넘어뜨리고 머리를 밟는다**: 맨손일 때 유일한 처치 방법이지만 지구력이 많이 들어 위험(입문 공략 자막).
- 물리는 동작 중이라도 **판정 전에 움직이거나 밀치면 공격이 무효**. 이미 물리면 경직돼 다른 좀비에게 더 맞을 수 있다(인벤 공략).
- **넘어진 좀비는 치명타 대상**(무방비). 낮은 울타리·창문을 넘어오는 좀비는 무조건 넘어진다(입문 공략 자막, 인벤).
- 무기는 쓰면 닳는다. 프라이팬 → 야구 배트 → 소방도끼 순으로 구하라(인벤, 겜가이드).
- 뒤로 물러나며 치는 "카이팅"이 기본이지만, 뒤에서 오는 좀비에 약하고 방향을 틀 때 잠깐 멈칫한다(입문 공략 자막).
- **B42 변화**: 근접 공격이 근육 피로를 쌓아 오래 휘두르기 위험, 총 맞은 좀비는 비틀거림, 멀리서 근접 처치하기 막힘(팬 가이드, PCGamesN). 초기 B42 근접 전투가 더 나빠졌다는 불만도 있음.

### 4-3. 은신
- 웅크리면 시야·소음이 줄어든다, 벽·나무·그림자에 숨기(영문 가이드).
- (파일에서 확인) 차 뒤에 숨으면 안 보임, 발견은 확률, 살금살금이면 덜 들킴.
- 비판: 특정 구역에 들어가면 좀비가 한꺼번에 깨어나 은신이 깨진다는 지적(커뮤니티 제안 글, 다른 게임 맥락 섞임 — 참고만).

### 4-4. 상태(무들)와 부상
- 무들은 19~24종(빌드마다 다름): 배고픔, 목마름, **공황**, 지루함, **스트레스**, 우울, 취함, 무거움, 지구력, 피곤, 더위·추위, 젖음, **부상**, **고통**, **출혈**, 움직임 제한, 감기, 아픔 등.
- **공황**: 좀비를 마주하면 생기고, 심하면 명중률·시야가 크게 줄어든다. 좀비에게서 멀어지면 풀림, 약(베타 차단제), 특성(용감함), 오래 살수록 덜 긴장.
- **스트레스**: 무기 피해가 줄어든다(손이 떨림). 담배, 책, 좀비와 거리 두기로 완화.
- **고통**: 4단계(10·20·50·75), 진통제로 완화.
- **감염 확률**: 긁힘 7%, 찢어짐 25%, 물림 100%. 메스꺼움 → 구토감 → 아픔 → 고열로 진행, 약 72시간 안에 죽어 좀비가 된다. 메스꺼움은 단순 식중독일 수도 있으니 건강창에서 상처를 확인(PC Gamer, GameRevolution).
- **부상 치료**(입문 공략 자막, 건강창 스크린샷): 부위별(손·팔목·다리 등)로 상처가 기록되고, 붕대·소독, 깊은 상처는 봉합, 골절은 부목. 우클릭으로 치료.

### 4-5. 인벤토리·파밍
- 무게 기반. 통조림은 0.8로 무겁다(입문 공략). 내 소지품 ↔ 인접 보관함 두 창(스크린샷).
- 첫 집은 오래 뒤지지 말고 물·장비만 챙겨 떠나라, 좀비에 많이 노출될수록 수명이 짧다, 꼭 필요할 때만 나가라(영문 가이드).
- 거점: 2층, 싱크대·냉장고, 높은 울타리와 좁은 입구(디시·아카 가이드, 입문 공략).
- 시작 지점 고르기: 장점보다 **싫은 조건부터 걸러라**(디시 뉴비 가이드).

### 4-6. 진행·이벤트
- 30일 안에 전기·물이 끊김(기본 설정), 헬리콥터 이벤트, 시간이 갈수록 어려워짐(입문 공략, 가이드).

## 5. 우리 게임과 맞춰 보기 (기둥 기준)
| 좀보이드에서 사랑받는 것 | 우리 기둥과의 관계 | 지금 우리 상태 |
|---|---|---|
| 소리가 곧 위험 | 기둥 1(긴장감 있는 싸움)을 강하게 함 | 소리·감각·막힌 소리·조용한 처치 **있음** |
| 언젠가 죽는다, 정든 캐릭터 | 기둥 2(괴물이 되어 가는 대가)와 잘 맞음 | 즉시 재시작만 있음 |
| 쌓아 가는 맛 | 구역 사이 이월(정할 것 #3, #7)과 연결 | 배낭만 있음 |
| 현실감 | 사실적 연출 확정과 같은 방향 | 바닥·폐차·피·시체 **있음** |
| 진입 장벽·UI 불편(단점) | **피해야 할 것.** 우리는 짧은 구역 게임 | 큰 글자 UI, 목표 칸 있음 |
| 중반 반복(단점) | 구역 3개 + 결말로 짧게 끝내 피함 | 범위 고정(정할 것 #6) |

## 6. 적용 후보 (사용자가 고르기 전까지 진행하지 않음)
| # | 후보 | 근거 | 크기 | 메모 |
|---|---|---|---|---|
| 1 | **밀치기(Shove)**: 우클릭으로 밀어 비틀거리게, 넘어진 피폭체는 무방비(피니셔) | 공략 전반, 파일의 비틀거림 상태 | 중 | 우클릭은 피폭(시간 느리게)을 끈 뒤 비어 있음 |
| 2 | **물기 판정 전 회피·밀치기로 무효** | 인벤 공략 | 소 | 지금의 구르기 무적과 비슷, 밀치기와 묶기 |
| 3 | **공황의 실제 효과**: 시야(원뿔) 좁아짐, 명중(베기 범위) 줄어듦 | 무들 설명 | 소 | 지금은 베기 회복만 느려짐 |
| 4 | **부상 부위**(팔·다리·몸통) + 부위별 효과(다리: 느림, 팔: 베기 약함), 건강창을 부위 목록으로 | 건강창 스크린샷, 공략 | 중 | 지금 몸 그림에 부위 표시만 |
| 5 | **감염(물림)** 진행: 메스꺼움 → 열 → 피폭 수치와 연결(피폭을 다시 켤 때) | 감염 확률, 기둥 2 | 중 | 피폭 기능을 다시 켤 때 함께 |
| 6 | **먼 사건**: 보이지 않는 헬리콥터·총소리가 지나가며 피폭체 무리를 끌고 감 | 헬리콥터 이벤트 | 중 | 소리 파일 필요 |
| 7 | **동적 음악/긴장 연출**: 발견되면 낮은 긴장음, 공황이면 심장 소리(일부 있음) | 41.71 액션 음악 | 소~중 | 소리 파일 필요 |
| 8 | **무기 내구도**(마체테가 닳음) | 공략 | 소 | 기둥과 약함, 보류 후보 |
| 9 | **"이것이 당신이 죽은 방법이다"식 죽음 요약**: 쓰러지면 버틴 시간·처치 수·사인 | 리뷰들 | 소 | 우리 즉시 재시작과 함께 짧게 |
| 10 | **진입 장벽 낮추기**: 첫 구역에 짧은 안내(소리, 살금살금, 붕대) | 단점 3절 | 소 | 2차 발표 데모에도 도움 |

## 6-1. 고른 것 (2026-11-16)
사용자: "심장 박동 수는 전혀 필요 없어 보이는데", "제 게임에 맞게 모두를 적용하지 말고 필요한 것들만 골라서 적용하면 됩니다."
기준: 짧고 긴장감 있는 칼싸움(기둥 1)을 바로 강하게 하는가, 2차 발표 데모에 보이는가, 작게 끝나는가.

| # | 결정 | 이유 |
|---|---|---|
| 1 밀치기 | **적용** | 우클릭이 비어 있고, 공격을 끊는 수단이 생겨 전투 선택지가 늘어남. 넘어뜨리면 피니셔로 이어짐 |
| 2 물기 전 무효 | **1에 합침** | 밀치기가 예고 중인 공격을 끊음(구르기 무적도 이미 있음) |
| 3 공황 효과 | **적용** | 이미 있는 긴장 시스템에 시야가 좁아지는 효과만 더하면 됨 |
| 9 죽음 요약 | **적용(짧게)** | 2.2초 카드 후 바로 재시작(DESIGN_LOCK 즉시 재시작 유지) |
| 10 첫 안내 | **적용** | 좀보이드 최대 단점(진입 장벽)을 피함, 발표 데모에도 도움 |
| 4 부상 부위 | 보류 | 몸 그림 표시로 충분, 부위별 효과는 체력 2칸 게임에 과함 |
| 5 감염 진행 | 보류 | 피폭 기능을 다시 켤 때 함께 |
| 6 먼 사건, 7 긴장 음악 | 보류 | 좋은 소리 파일이 먼저(지금 소리는 "별로") |
| 8 무기 내구도 | 빼기 | 짧은 구역 칼싸움과 안 맞음 |
| 심장 박동 수 | **빼기** | 사용자 "전혀 필요 없어 보임" → 심박 숫자·선·소리 삭제 |

## 7. 출처
- 디시 프로젝트 좀보이드 마이너 갤러리: [지극히 개인적인 초반 공략](https://m.dcinside.com/board/pzom/26132), [시작 지점별 최악의 단점](https://gall.dcinside.com/mgallery/board/view/?id=pzom&no=236661), [뉴비 가이드 1편](https://gall.dcinside.com/mgallery/board/view/?id=pzom&no=265964), [뉴비 특성 추천](https://gall.dcinside.com/mgallery/board/view/?id=pzom&no=213132)
- [아카라이브 좀보이드 초반 가이드](https://arca.live/b/zomboid/75014340), [200시간 뉴비 후기](https://arca.live/b/zomboid/78196304?before=2023-06-08T07:04:14Z), [에펨코리아 80시간 후기](https://www.fmkorea.com/4389810845), [루리웹 후기](https://m.ruliweb.com/community/board/300143/read/65267734), [minimap 평가](https://minimap.net/user/tunhun25/library/2749430), [당근 좀보이드](https://www.daangn.com/kr/community/%EC%A2%80%EB%B3%B4%EC%9D%B4%EB%93%9C-%EA%B2%8C%EC%9E%84-bwsrv6aavmeg/)
- [나무위키 좀보이드](https://namu.wiki/w/%EC%A2%80%EB%B3%B4%EC%9D%B4%EB%93%9C), [나무위키 공략](https://namu.wiki/w/Project%20Zomboid/%EA%B3%B5%EB%9E%B5), [인벤 공략글](https://www.inven.co.kr/board/lostark/6271/3916462), [겜가이드 생존 전략](https://www.ggemguide.com/guide_pc_view.htm?uid=8195), [겜가이드 직업·특성](https://www.ggemguide.com/guides/pc/8689/), [겜북 극초반 가이드](https://book.gamess.co.kr/books/project-zomboid-guide/page/67f7f)
- [PC Gamer: 물렸을 때](https://www.pcgamer.com/project-zomboid-bitten-what-to-do), [GameRevolution: 감염](https://www.gamerevolution.com/guides/962253-project-zomboid-infection-prevent-becoming-a-zombie), [PC Gamer: 헬리콥터](https://www.pcgamer.com/project-zomboid-helicopter-event), [pzwiki: Helicopter](https://pzwiki.net/wiki/Helicopter), [pzwiki: Metagame](https://pzwiki.net/wiki/Metagame)
- [PCGamesN: 41.71 동적 음악](https://www.pcgamesn.com/project-zomboid/patch-41-71-dynamic-music), [공식 블로그(음악·FMOD)](https://projectzomboid.com/blog/?p=5065), [PCGamesN: 제작·전투 업데이트](https://www.pcgamesn.com/project-zomboid/crafting-combat-update), [games.gg: B42 전투](https://games.gg/news/project-zomboid-build-42-combat/), [pzfans: B42 개편](https://pzfans.com/build_42_madness_hunting_crafting_and_combat_overhauls_explained/)
- [fandom: Moodles](https://projectzomboid.fandom.com/wiki/Moodles), [pzfans: B42 무들](https://pzfans.com/ProjectZomboidB42Moodles/), [progameguides: 무들](https://progameguides.com/project-zomboid/all-project-zomboid-moodles-and-how-to-deal-with-them/)
- [GGServers 가이드](https://ggservers.com/blog/survival-guide-for-project-zomboid-pro-tips-to-easily-kill-zombies/), [DualShockers 팁](https://www.dualshockers.com/project-zomboid-beginner-tips-tricks/), [GamesRadar 기사](https://www.gamesradar.com/games/survival/introducing-my-friends-to-project-zomboid-ended-in-disaster-but-its-given-me-a-newfound-appreciation-for-the-best-zombie-survival-sim-around), [Gfinity 에세이](https://www.gfinityesports.com/article/maybe-hell-is-fun-why-games-like-project-zomboid-prove-were-masochists), [Alternate Atlas 리뷰](https://alternateatlas.bearblog.dev/review-project-zomboid-a-game-i-love-and-can-no-longer-love/), [Vaporlens 리뷰 요약](https://vaporlens.app/app/108600/project_zomboid), [GamingOnLinux](https://www.gamingonlinux.com/2015/01/gol-cast-surviving-the-zombie-apocalypse-in-project-zomboid), [RAWG 리뷰](https://rawg.io/games/project-zomboid/reviews), [projectzomboid.wiki 리뷰](https://projectzomboid.wiki/review/)
