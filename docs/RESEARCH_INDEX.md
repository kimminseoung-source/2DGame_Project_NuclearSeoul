# 조사·참고 자료 목차 (한 곳에서 찾기)

- 11-24 최우선 보완: [얼굴 일관성과 실행 버전](plans/2026-11-24_얼굴일관성과_실행버전.md) — 같은 방향의 정지/이동/조준 머리 레이어 공유, 실제 로더/머리 픽셀 검사, FACE-R1 빌드 식별, UI601개 캐시 종료 오류 재현·수정.

- 11-24 적용: [기존 조사 기반 보행 기법 적용](plans/2026-11-24_보행기법_적용.md) — 좌우 교대8단계/기준 보행 뒤 팔 변형/이동 사격 하체·입력 유지, 실제 C/D 검사와 남은 발 오차. 다음 동작 작업은 프로젝트 AGENTS/CLAUDE와 캐릭터 제작 기준의 조회 순서를 따른다.

- 11-23 보완: [양손 검·걷기 자세 안내](plans/2026-11-23_양손검_자세안내_걷기보완.md) — 사용자 빨간 선 방향의 양손 검, 상체 안정화와 8시점 하체 비교.

- 11-23 시험: [3D 자세 가이드 + AI 걷기](plans/2026-11-23_3D자세가이드_AI걷기.md) — AI 외형 유지, 실제 기존 관절 투영을 참고한 걷기 6프레임 비교.

- 11-23 비교: [기존 동작·새 외형 재사용](plans/2026-11-23_기존동작_새외형_재사용.md) — 기존 MPFB/Mixamo 걷기를 유지한 붉은 재킷 모델 복사본 시험.

- 11-23 진행: [붉은 재킷 걷기와 검 공격](plans/2026-11-23_붉은재킷_걷기와_검공격.md) — 승인된 외형의 걷기 6자세·공격 3자세를 시험 실행에 연결.

- 11-23 진행: [붉은 재킷 주인공 외형 확인](plans/2026-11-23_붉은재킷_주인공_외형확인.md) — 세 번째 시안 선택, 한 방향 대기/검 준비 2장만 먼저 검토.

- 11-23 진행: [원거리 피폭체 시험](plans/2026-11-23_원거리_피폭체_시험.md) — 기존 주인공 유지, 별도 시험에서 핵심 자세·발광·직선 탄 검토.

「부산까지」를 만들며 조사한 것, 사용자가 준 자료, 정한 규칙을 **카테고리별로** 모은 목차다(2026-11-20 처음 정리).
- 보는 곳: 프로젝트 `docs/RESEARCH_INDEX.md`, 또는 GitHub [docs/RESEARCH_INDEX.md](https://github.com/kimminseoung-source/2DGame_Project_NuclearSeoul/blob/main/docs/RESEARCH_INDEX.md) (어디서든).
- 작업 전에는 계획서(9절)를 먼저 쓴다.
- 지키는 법: 새 조사·자료·규칙 문서를 만들면 **같은 작업 안에서** 이 목차의 맞는 카테고리에 한 줄을 넣는다. 결론이 바뀌면 "결론·지금" 칸을 고친다. Claude는 관련 작업을 시작할 때 이 목차부터 본다.
- 표시: ★ = 지금 따르는 기준, ✓ = 결론 나서 반영됨, ○ = 참고만(미확정·보류), ✗ = 시험했지만 안 씀.

---

## 1. 그림 방향과 스타일

| 문서 | 날짜 | 무엇 | 결론·지금 |
|---|---|---|---|
| [planning/ART_BIBLE.md](planning/ART_BIBLE.md) | 11-25 | **아트 바이블(그래픽·UI·UX 기준)**: 회청색+초록 위험+붉은 주인공, 3/4 탑뷰, 세상 물건 같은 UI, 점검표 | ★ 초안, 모든 그림·UI가 따름 |
| [planning/ART_STYLE_RESEARCH.md](planning/ART_STYLE_RESEARCH.md) | 11-14 | 2D 그래픽 스타일 6가지(도트+네온, 3D→도트, 고딕, 실루엣, 손그림, 도트+3D 배경) | ○ 3D→도트(Dead Cells 방식) 추천 |
| [planning/ZOMBOID_VISUAL_REFERENCE.md](planning/ZOMBOID_VISUAL_REFERENCE.md) | 11-14 | 좀보이드 화면·동작 분석을 탑뷰에 적용 | ✓ 탑뷰 전환에 반영 |
| [../assets/characters/ART_FEEDBACK.md](../assets/characters/ART_FEEDBACK.md) | 계속 | 사용자의 그림 지적, 원인, 교훈 + 보여 주기 전 점검표 | ★ 그림 보여 주기 전 반드시 |

## 2. 캐릭터 만들기 (도트·3D·옷)

| 문서 | 날짜 | 무엇 | 결론·지금 |
|---|---|---|---|
| [research/CHARACTER_PIPELINE.md](research/CHARACTER_PIPELINE.md) | 11-10 | 다른 게임들이 고퀄 도트 캐릭터를 뽑는 방식 | ✓ 3D 동작 → 도트 방향의 출발점 |
| [../assets/characters/CHARACTER_SPEC.md](../assets/characters/CHARACTER_SPEC.md) | 11-10 | 기본형 캐릭터 규격(칸, 기준점, 동작 목록) | ★ 규격 |
| [../assets/characters/CHARACTER_WORKFLOW.md](../assets/characters/CHARACTER_WORKFLOW.md) | 계속 | 캐릭터를 어떤 순서로 어디에 만드는지 | ★ 순서 (3D 새 방식은 아래 2-3줄 참고) |
| [research/CLOTHING_OPTIONS.md](research/CLOTHING_OPTIONS.md) | 11-11 | 기본 몸에 옷 입히는 방법 비교 | ✓ 부피 껍데기 → 지금은 MPFB 실제 옷 |
| [research/ASSET_SITES.md](research/ASSET_SITES.md) | 11-14 | 캐릭터 에셋 사이트(무료) | ○ |
| [references/USEFUL_TOOLS.md](references/USEFUL_TOOLS.md) 3D 캐릭터 절 | 11-20 | 무료 3D 캐릭터 출처(MPFB2, Mixamo, VRoid, KayKit …) | ★ MPFB2 사용 중 |
| [../assets/characters/mpfb/hero.json](../assets/characters/mpfb/hero.json) | 11-20 | **기준 3D 주인공 사양**(마른 체형, 머리 1.45배, 긴팔 + 바지, Mixamo 뼈대) | ★ 기준 모델 |
| [planning/hero3d_model_board.png](planning/hero3d_model_board.png) | 11-20 | 기준 모델 점검 4가지: 실루엣·비율, 부위 나눔, 동작, 36px | ★ 3D에서 중요한 것 |
| [../assets/characters/hero_concept/PROMPTS.md](../assets/characters/hero_concept/PROMPTS.md) | 11-19 | 주인공 생성 프롬프트(PixelLab·ChatGPT) | ✓ 지금 게임 주인공 그림 |

## 3. 동작(애니메이션)

| 문서 | 날짜 | 무엇 | 결론·지금 |
|---|---|---|---|
| [권총 전신 동작 흐름 보완](plans/2026-11-23_권총_전신동작_흐름보완.md) | 11-23 | 같은 전신 기준 일반/조준 보행과 조준 전환·반동·피격/사망, C 비교 | 진행 · A 정지 조준 유지, B 강제 상하체 합성 보류 |
| [공통 하체 권총 시험](../assets/characters/previews/hero_pistol_shared_v2/README.md) | 11-23 | 좁힌 같은 하체/팔만 조준, 상체2+기존 걷기 하체8+분리 권총 재사용 | ○ 작은 합성 시험. 게임 미연결, 허리/손·총구/접지 보완 필요 |
| [plans/2026-11-23_총중심_주인공_제작계획.md](plans/2026-11-23_총중심_주인공_제작계획.md) | 11-23~ | 총 중심 AI 주인공 단계별 실행 목록·확인 기준 | ★ 권총 양손 기준 자세 → 몸/총 분리 → 조준 이동 → 발사 → 작은 플레이 → 방향/누락 복구 |
| [planning/HERO_MOTION_STATUS.md](planning/HERO_MOTION_STATUS.md) | 11-23~ | **주인공 동작 구현 비교·누락 방지 기준표**: 기존 3D/PixelLab/옛 시트/새 실행/최신 미리보기와 총 중심 추가 항목 | ★ 새 동작 작업 전후 여기 상태 갱신. 파일/실제 연결/임시 대체/검수 구분 |
| [planning/MOTION_FEW_SPRITES_2026-11-19.md](planning/MOTION_FEW_SPRITES_2026-11-19.md) | 11-19 | **적은 스프라이트로 역동적인 동작**: 핵심 자세 2~3장, 스미어, 베기 효과로 가리기, 히트스톱, 무기 따로, 방향 줄이기 | ★ 공격 = 몸 3장 + 효과 + 멈춤 |
| [planning/MOTION_RULES.md](planning/MOTION_RULES.md) | 11-19, 11-20 | 위 조사로 정한 **동작 제작 기준**과 점검표. 11-20: 공격 3장, 장수 기준(2-1), 3D 만드는 순서(5-1) | ★ |
| [references/ANIMATION_GUIDES.md](references/ANIMATION_GUIDES.md) | 11-11~23 | **사용자가 준 방법 글 모음**: 일관성 해결법, AI 제작 방식 4가지, 5대 파이프라인과 실행 지침 | ★ 최신 AI 외형+3D 자세 안내. 과거 3D 본체 선택·실패 기록과 구분. 11-23 적용/누락 대조 추가 |
| [plans/2026-11-23_양손검_자세안내_걷기보완.md](plans/2026-11-23_양손검_자세안내_걷기보완.md) 후속 대조표 | 11-23 | 기존 조사/규칙 대비 최신 AI 걷기 적용·누락·다음 단계 | ★ 최신: AI 외형+3D 자세 안내. 접지 측정·무기 분리·최신 결과 게임 검수 미완료 |
| [research/ZOMBOID_ANIMATION_RESEARCH.md](research/ZOMBOID_ANIMATION_RESEARCH.md) | 11-15 | 좀보이드 동작 구성과 규칙 | ○ 동작 목록 참고 |
| [research/ZOMBOID_REA_ANALYSIS.md](research/ZOMBOID_REA_ANALYSIS.md) | 11-14 | 좀보이드 피폭체 동작 분석(REA) | ○ |
| [planning/hero3d_swing_v2.png](planning/hero3d_swing_v2.png) | 11-20 | 3D 휘두르기 다듬기(허리 회전 줄이기, 무기 방향) | ✓ 동작 교체로 넘어감 |
| [planning/hero3d_attacks4_v2.png](planning/hero3d_attacks4_v2.png) | 11-20 | Mixamo 공격 4개 비교, 무기 방향 z | ✓ Downward로 정함 |
| [planning/arena_hero3d_chop.png](planning/arena_hero3d_chop.png) | 11-20 | 3D 주인공 게임 안 내려치기 8방향 (`BUSAN_HERO=hero_3d`, `tools/sprites/build_hero3d.py`) | ★ 시험 중 |

## 4. 3D → 도트 변환 기법

| 문서 | 날짜 | 무엇 | 결론·지금 |
|---|---|---|---|
| [study/05_3D를_도트로.md](study/05_3D를_도트로.md) | 11-20 | Dead Cells 방식, 셀 셰이딩, 셀렉티브 외곽선, 외톨이 픽셀, 큰 머리 | ★ `repaint.py` 마무리 |
| [study/04_스프라이트와_뼈대.md](study/04_스프라이트와_뼈대.md) | 11-19 | 스프라이트(프레임) vs 뼈대(Spine), 뼈대로 만들고 그림으로 굽기 | ✓ |
| [planning/hero3d_mpfb_dots_v1.png](planning/hero3d_mpfb_dots_v1.png) | 11-20 | 질감 그대로는 36px에서 탁함 → 부위별 단색 + 3단 명암 | ★ 부위별 색 방식 |

## 5. 효과·그림 에셋

| 문서 | 날짜 | 무엇 | 결론·지금 |
|---|---|---|---|
| [planning/ASSET_CANDIDATES_2026-11-18.md](planning/ASSET_CANDIDATES_2026-11-18.md) | 11-18 | 무료 효과 팩·타일·소품 후보, 품질 올리기 | ✓ 베기·타격 효과 받음 |
| [references/ASSETS.md](references/ASSETS.md) | 계속 | 쓰는 자료와 출처·라이선스 | ★ 크레딧 근거 |
| [references/USEFUL_TOOLS.md](references/USEFUL_TOOLS.md) 효과 절 | 11-20 | pixelfx(코드 효과 244종), Pixelbolt | ○ 무기마다 다른 효과에 쓸 후보 |

## 6. 도구 (AI·외부 프로그램)

| 문서 | 날짜 | 무엇 | 결론·지금 |
|---|---|---|---|
| [references/USEFUL_TOOLS.md](references/USEFUL_TOOLS.md) | 11-20~, 11-23 재조사·영상 추가 | **사용자가 준 도구 링크 모음**(무료 여부·라이선스·쓰임), 공유 영상과 스프라이트 제작 스킬·MCP 재검토 | ★ 새 링크는 여기. MGD 도구 총정리 영상은 시간표·확인 범위·활용 메모 포함. 3D→도트 기준, 대안은 비교 후보 |
| [research/AI_GAME_TOOLS.md](research/AI_GAME_TOOLS.md) | 11-14 | AI 게임 제작 리소스·GitHub(무료만) | ○ |
| [research/EXTERNAL_TOOLS.md](research/EXTERNAL_TOOLS.md) | 11-10 | 외부 도구·맵 에디터·에셋 활용 | ○ |
| [research/PRODUCTION_REFERENCES.md](research/PRODUCTION_REFERENCES.md) | 11-13 | 제작 사이트·참고 사이트 | ○ |
| [research/REFERENCE_WORK_LIST.md](research/REFERENCE_WORK_LIST.md) | 11-13 | 참고 자료로 Claude가 할 수 있는 작업 목록 | ○ |
| 시험 기록: LoRA, Sprite Sheet Diffusion, Meshy, LPC | 11-20 | [DEVLOG.md](DEVLOG.md) 11-20 항목 | ✗ 품질·유료 문제로 안 씀 |

## 7. 게임 재미·전투·UI 조사

| 문서 | 날짜 | 무엇 | 결론·지금 |
|---|---|---|---|
| [planning/FUN_RESEARCH_2026-11-18.md](planning/FUN_RESEARCH_2026-11-18.md) | 11-18 | 재미 요소 기획 이론 | ✓ |
| [research/FUN_APPLICATION_REPORT.md](research/FUN_APPLICATION_REPORT.md) | 11-16 | 우리 게임에 무엇을 적용하면 재미있나 | ✓ |
| [research/ZOMBOID_COMMUNITY_RESEARCH.md](research/ZOMBOID_COMMUNITY_RESEARCH.md) | 11-16 | 좀보이드 커뮤니티·공략 | ○ |
| [research/GAME_JUICE_2026-11-20.md](research/GAME_JUICE_2026-11-20.md) | 11-20 | **전투 손맛(게임 쥬스)**: 지금 있는 것(히트스톱·흔들림·번쩍·궤적·피·소리)과 더할 후보 12개 | ○ 다음 계획 |
| [research/BG3_COMBAT_RESEARCH.md](research/BG3_COMBAT_RESEARCH.md) | 11-08 | 발더스 게이트 3 전투·UI | ✗ 턴제는 버림 |
| [research/MOOD_UI_2026-11-25.md](research/MOOD_UI_2026-11-25.md) | 11-25 | **분위기(어둠·색·공기·화면 효과)와 총 중심 UI**: Darkwood·Zero Sievert·Fallout·The Long Dark, 탄약 표시 연구, 지금 화면 점검, 후보 A~H | ★ 사용자 선택 대기 |
| [research/UI_NOT_AI_RESEARCH.md](research/UI_NOT_AI_RESEARCH.md) | 11-16 | UI에서 "AI 티" 없애기 | ★ UI 원칙 |
| [research/GROUND_INVENTORY_UI_RESEARCH.md](research/GROUND_INVENTORY_UI_RESEARCH.md) | 11-16 | 바닥에 늘어놓는 인벤토리 UI | ✓ |
| [planning/ui_redesign/UI_REDESIGN_PROPOSAL.md](planning/ui_redesign/UI_REDESIGN_PROPOSAL.md) | 11-16 | UI 전면 개편 제안 | ✓ |

## 8. 기획 방향과 점검

| 문서 | 날짜 | 무엇 | 결론·지금 |
|---|---|---|---|
| [planning/STATUS_2026-11-20.md](planning/STATUS_2026-11-20.md) | 11-20 | **진행 상황 정리**: 오늘 한 일, 게임 상태, 점검표, 파일 정리 목록, 앞으로 할 일 | ★ 지금 기준 |
| [planning/DESIGN_LOCK.md](planning/DESIGN_LOCK.md) | 계속 | **정한 기획(고정)** | ★ 바꿀 때 먼저 고침 |
| [planning/ORIGINAL_VS_CURRENT.md](planning/ORIGINAL_VS_CURRENT.md) | 11-10 | 1차 발표 기획과 지금의 차이(교수님: 벗어나지 말 것) | ★ 바꿀 때 비교 |
| [planning/GAME_CONCEPT.md](planning/GAME_CONCEPT.md) | | 콘셉트와 핵심 재미 | ★ |
| [planning/DIRECTION_ONE_PAGER.md](planning/DIRECTION_ONE_PAGER.md) | 11-12 | 방향 한 장 정리 | ○ |
| [planning/NEW_DIRECTION_2026-11-13.md](planning/NEW_DIRECTION_2026-11-13.md) | 11-13 | 새 기획 방향 | ✓ PRD 반영 |
| [planning/REVIEW_1_2026-11-17.md](planning/REVIEW_1_2026-11-17.md), [REVIEW_2](planning/REVIEW_2_2026-11-19.md) | 11-17, 19 | 1·2차 점검 | ✓ |

## 9. 계획서 (작업 전에 쓰는 것)

- [총 중심 주인공 제작 계획](plans/2026-11-23_총중심_주인공_제작계획.md): 사용자 선택 권총 양손 조준, 단계별 작업/검수/누락 복구. 첫 자세 초안까지 착수.

- [2026-11-23 주인공 스프라이트 기준 방식과 비교 계획](plans/2026-11-23_주인공_스프라이트_기준방식과_비교계획.md): 기존 3D→도트 기준으로 진행하고, 2D 생성·후처리 도구는 동일 조건의 결과로 비교한다.
- [검 주인공 남동 대기 첫 제작](../assets/characters/previews/hero_sword_model_v1/README.md): 새 모델 복사본·36px 몸/검 출력·기존 캐릭터 비교·게임 배경 미리보기. 외형 확인 단계이며 게임 정식 교체 전.

2026-11-20부터 작업을 시작하기 전에 계획서를 `docs/plans/<날짜>_<주제>.md`로 쓰고, 끝나면 결과를 적는다.

| 계획서 | 날짜 | 무엇 | 상태 |
|---|---|---|---|
| [plans/2026-11-20_hero3d_장수_줄이기.md](plans/2026-11-20_hero3d_장수_줄이기.md) | 11-20 | 3D 주인공 서 있기 2장, 걷기 6장, 공격 3장(준비·치기·회복) | 완료 |
| [plans/2026-11-20_공격동작_바꿔가며_시연.md](plans/2026-11-20_공격동작_바꿔가며_시연.md) | 11-20 | F4에서 공격 동작 4개 × 장수(2/3/전체)를 바꿔 가며 시연 | 완료 |
| [plans/2026-11-20_조준자세_하체걷기.md](plans/2026-11-20_조준자세_하체걷기.md) | 11-20 | 방망이 조준 자세, 조준한 채 걷기(윗몸·다리를 Blender에서 합쳐 굽기) | 완료 → 아래에서 다시 |
| [plans/2026-11-20_조준_서있기_다시.md](plans/2026-11-20_조준_서있기_다시.md) | 11-20 | 조준 서 있기부터 다시: 머리 방향, 무기 종류별 조준 | 완료 |
| [plans/2026-11-20_사무라이_베기_자세.md](plans/2026-11-20_사무라이_베기_자세.md) | 11-20 | 휘두른 뒤 자세를 야구 → 사무라이 베기(준비는 방망이 그대로, 치기·회복은 양손 검) | 완료 |
| [plans/2026-11-20_공격_8방향.md](plans/2026-11-20_공격_8방향.md) | 11-20 | 공격을 8방향으로, 조준 걷기 머리, 3D 주인공 모든 동작 8방향 | 완료 |
| [plans/2026-11-20_기본_주인공_교체.md](plans/2026-11-20_기본_주인공_교체.md) | 11-20 | 기본 주인공을 3D로, 빠진 동작(맞기·쓰러짐·줍기·살금살금·밀치기·구르기·밟기·찌르기·쏘기) | 진행 중 |
| [plans/2026-11-20_클릭공격_준비시간.md](plans/2026-11-20_클릭공격_준비시간.md) | 11-20 | 짧게 클릭한 공격의 준비 시간 줄이기(QUICK_SKIP, F4) | 완료 |
| [plans/2026-11-20_피폭체_공격_예고.md](plans/2026-11-20_피폭체_공격_예고.md) | 11-20 | 피폭체 할퀴기 범위를 은은한 빨강으로 예고, 받아치기 때 조금 밝게 | 완료 |
| [plans/2026-11-20_다리_기어다니기_끄기.md](plans/2026-11-20_다리_기어다니기_끄기.md) | 11-20 | 다리 부위·기어다니는 피폭체·밟기를 설정으로 끄기(머리·몸통만) | 완료 |
| [plans/2026-11-20_숨고르기_점검_정리.md](plans/2026-11-20_숨고르기_점검_정리.md) | 11-20 | 숨 고르기: 전체 점검, 파일 정리 목록, 진행 상황·앞으로 할 일 → [STATUS_2026-11-20](planning/STATUS_2026-11-20.md) | 완료 |
| [plans/2026-11-20_밀치기_끄기_받아치기_공격으로.md](plans/2026-11-20_밀치기_끄기_받아치기_공격으로.md) | 11-20 | 밀치기 끄기, 받아치기를 베기로, 기본 주인공 3D | 완료 |
| [plans/2026-11-21_살금살금_자세_칼_쥐기.md](plans/2026-11-21_살금살금_자세_칼_쥐기.md) | 11-21 | 살금살금: 후보 비교 → Mixamo Sneaking Forward 8방향 | 완료 |
| [plans/2026-11-21_구르기_회피.md](plans/2026-11-21_구르기_회피.md) | 11-21 | 회피: 연출 4가지 비교 → 구르기 그림 | 완료 |
| [plans/2026-11-21_구르기_다듬기.md](plans/2026-11-21_구르기_다듬기.md) | 11-21 | 구르기 다듬기: 제자리 굽기·타이밍 홀드·무기 방향·구르는 먼지 | 완료 |
| [plans/2026-11-21_구르기_회전_앞뒤감지.md](plans/2026-11-21_구르기_회전_앞뒤감지.md) | 11-21 | 구르기 6장 8방향(4장과 비교 후), 피폭체 등 뒤 감지 110px | 완료 |
| [plans/2026-11-21_무기_들고다니는_각도.md](plans/2026-11-21_무기_들고다니는_각도.md) | 11-21 | 들고 다니는 무기: 아래로 vs 앞 위로 → 앞 위로 | 완료 |
| [plans/2026-11-21_구르기_속도감.md](plans/2026-11-21_구르기_속도감.md) | 11-21 | 구르기 속도: 처음 1.6배 → 끝 0.4배, 거리 그대로 | 완료 |
| [plans/2026-11-21_점검_스크립트_옮기기.md](plans/2026-11-21_점검_스크립트_옮기기.md) | 11-21 | 점검 스크립트를 tools/checks로, run_all, 68/68 | 완료 |
| [plans/2026-11-21_공격방식_휘두르기_하나.md](plans/2026-11-21_공격방식_휘두르기_하나.md) | 11-21 | 근접은 휘두르기 하나(식칼도), 총은 나중에 | 완료 |
| [plans/2026-11-21_스태미나_대신_구르기_횟수.md](plans/2026-11-21_스태미나_대신_구르기_횟수.md) | 11-21 | 스태미나 끄고 구르기 2번 저장 | 완료 |
| [plans/2026-11-21_연속_구르기.md](plans/2026-11-21_연속_구르기.md) | 11-21 | 구르기 사이 텀 0.35 → 0.05초, 미리 눌러 두기 | 완료 |
| [plans/2026-11-22_맞을때_흔들림_번쩍임.md](plans/2026-11-22_맞을때_흔들림_번쩍임.md) | 11-22 | 맞을 때 방향 흔들림 + 붉은 번쩍임 | 완료 |
| [plans/2026-11-25_GPT작업_점검_커밋.md](plans/2026-11-25_GPT작업_점검_커밋.md) | 11-25 | GPT와 한 작업(11-23~24) 점검·묶음 커밋 | 완료 |
| [plans/2026-11-25_GPT_공동작업_방식.md](plans/2026-11-25_GPT_공동작업_방식.md) | 11-25 | Claude·GPT 공동 작업 방식: AGENTS.md 한 곳, 작업판, 그림 요청서 | 완료 |
| [plans/2026-11-25_분위기_UI_조사.md](plans/2026-11-25_분위기_UI_조사.md) | 11-25 | 게임 분위기·UI 조사 | 완료 |
| [plans/2026-11-25_낮_살짝_밝게.md](plans/2026-11-25_낮_살짝_밝게.md) | 11-25 | 낮 살짝 밝게(사실 모드 덮개 낮 45, 낮 시야 밖 40), 밤 그대로 | 완료 |
| [plans/2026-11-25_아트바이블_먼저.md](plans/2026-11-25_아트바이블_먼저.md) | 11-25 | 그래픽·UI·UX 기준 먼저(Scavland 분석) | 진행 중 |
| [research/AI_COLLAB_2026-11-25.md](research/AI_COLLAB_2026-11-25.md) | 11-25 | 조사: Claude Code·Codex 함께 쓰기(AGENTS.md 불러오기, 공식 Codex 플러그인, 작업판·폴더 담당) | |
| [COLLAB_BOARD.md](COLLAB_BOARD.md) | 11-25 | **작업판** — 둘 다 시작·끝에 읽고 고침 | 계속 |

## 10. 공부 노트 (왜 그렇게 하는지)

[study/README.md](study/README.md): 00 공부 지도, 01 역 울타리, 02 시야 시스템, 03 레이어 그리기, 04 스프라이트와 뼈대, 05 3D를 도트로.

## 11. 작업 기록

| 문서 | 무엇 |
|---|---|
| [DEVLOG.md](DEVLOG.md) | 날짜별 개발일지(무엇을 왜 바꿨는지) |
| [DEVELOPMENT_RETROSPECTIVE.md](DEVELOPMENT_RETROSPECTIVE.md) | 반복해서 막힌 부분과 교훈 |
| [TODO.md](TODO.md) | 할 일 |
