# 조사·참고 자료 목차 (한 곳에서 찾기)

「부산까지」를 만들며 조사한 것, 사용자가 준 자료, 정한 규칙을 **카테고리별로** 모은 목차다(2026-11-20 처음 정리).
- 보는 곳: 프로젝트 `docs/RESEARCH_INDEX.md`, 또는 GitHub [docs/RESEARCH_INDEX.md](https://github.com/kimminseoung-source/2DGame_Project_NuclearSeoul/blob/main/docs/RESEARCH_INDEX.md) (어디서든).
- 작업 전에는 계획서(9절)를 먼저 쓴다.
- 지키는 법: 새 조사·자료·규칙 문서를 만들면 **같은 작업 안에서** 이 목차의 맞는 카테고리에 한 줄을 넣는다. 결론이 바뀌면 "결론·지금" 칸을 고친다. Claude는 관련 작업을 시작할 때 이 목차부터 본다.
- 표시: ★ = 지금 따르는 기준, ✓ = 결론 나서 반영됨, ○ = 참고만(미확정·보류), ✗ = 시험했지만 안 씀.

---

## 1. 그림 방향과 스타일

| 문서 | 날짜 | 무엇 | 결론·지금 |
|---|---|---|---|
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
| [planning/MOTION_FEW_SPRITES_2026-11-19.md](planning/MOTION_FEW_SPRITES_2026-11-19.md) | 11-19 | **적은 스프라이트로 역동적인 동작**: 핵심 자세 2~3장, 스미어, 베기 효과로 가리기, 히트스톱, 무기 따로, 방향 줄이기 | ★ 공격 = 몸 3장 + 효과 + 멈춤 |
| [planning/MOTION_RULES.md](planning/MOTION_RULES.md) | 11-19, 11-20 | 위 조사로 정한 **동작 제작 기준**과 점검표. 11-20: 공격 3장, 장수 기준(2-1), 3D 만드는 순서(5-1) | ★ |
| [references/ANIMATION_GUIDES.md](references/ANIMATION_GUIDES.md) | 11-11~20 | **사용자가 준 방법 글 모음**: 일관성 해결법, AI 제작 방식 4가지, 5대 파이프라인과 실행 지침 | ★ 본체 = 3D→도트, 효과 = pixelfx |
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
| [references/USEFUL_TOOLS.md](references/USEFUL_TOOLS.md) | 11-20~ | **사용자가 준 도구 링크 모음**(무료 여부·라이선스·쓰임) | ★ 새 링크는 여기 |
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
| [research/BG3_COMBAT_RESEARCH.md](research/BG3_COMBAT_RESEARCH.md) | 11-08 | 발더스 게이트 3 전투·UI | ✗ 턴제는 버림 |
| [research/UI_NOT_AI_RESEARCH.md](research/UI_NOT_AI_RESEARCH.md) | 11-16 | UI에서 "AI 티" 없애기 | ★ UI 원칙 |
| [research/GROUND_INVENTORY_UI_RESEARCH.md](research/GROUND_INVENTORY_UI_RESEARCH.md) | 11-16 | 바닥에 늘어놓는 인벤토리 UI | ✓ |
| [planning/ui_redesign/UI_REDESIGN_PROPOSAL.md](planning/ui_redesign/UI_REDESIGN_PROPOSAL.md) | 11-16 | UI 전면 개편 제안 | ✓ |

## 8. 기획 방향과 점검

| 문서 | 날짜 | 무엇 | 결론·지금 |
|---|---|---|---|
| [planning/DESIGN_LOCK.md](planning/DESIGN_LOCK.md) | 계속 | **정한 기획(고정)** | ★ 바꿀 때 먼저 고침 |
| [planning/ORIGINAL_VS_CURRENT.md](planning/ORIGINAL_VS_CURRENT.md) | 11-10 | 1차 발표 기획과 지금의 차이(교수님: 벗어나지 말 것) | ★ 바꿀 때 비교 |
| [planning/GAME_CONCEPT.md](planning/GAME_CONCEPT.md) | | 콘셉트와 핵심 재미 | ★ |
| [planning/DIRECTION_ONE_PAGER.md](planning/DIRECTION_ONE_PAGER.md) | 11-12 | 방향 한 장 정리 | ○ |
| [planning/NEW_DIRECTION_2026-11-13.md](planning/NEW_DIRECTION_2026-11-13.md) | 11-13 | 새 기획 방향 | ✓ PRD 반영 |
| [planning/REVIEW_1_2026-11-17.md](planning/REVIEW_1_2026-11-17.md), [REVIEW_2](planning/REVIEW_2_2026-11-19.md) | 11-17, 19 | 1·2차 점검 | ✓ |

## 9. 계획서 (작업 전에 쓰는 것)

2026-11-20부터 작업을 시작하기 전에 계획서를 `docs/plans/<날짜>_<주제>.md`로 쓰고, 끝나면 결과를 적는다.

| 계획서 | 날짜 | 무엇 | 상태 |
|---|---|---|---|
| [plans/2026-11-20_hero3d_장수_줄이기.md](plans/2026-11-20_hero3d_장수_줄이기.md) | 11-20 | 3D 주인공 서 있기 2장, 걷기 6장, 공격 3장(준비·치기·회복) | 완료 |
| [plans/2026-11-20_공격동작_바꿔가며_시연.md](plans/2026-11-20_공격동작_바꿔가며_시연.md) | 11-20 | F4에서 공격 동작 4개 × 장수(2/3/전체)를 바꿔 가며 시연 | 완료 |
| [plans/2026-11-20_조준자세_하체걷기.md](plans/2026-11-20_조준자세_하체걷기.md) | 11-20 | 방망이 조준 자세, 조준한 채 걷기(윗몸·다리를 Blender에서 합쳐 굽기) | 완료 → 아래에서 다시 |
| [plans/2026-11-20_조준_서있기_다시.md](plans/2026-11-20_조준_서있기_다시.md) | 11-20 | 조준 서 있기부터 다시: 머리 방향, 무기 종류별 조준 | 완료 |
| [plans/2026-11-20_사무라이_베기_자세.md](plans/2026-11-20_사무라이_베기_자세.md) | 11-20 | 휘두른 뒤 자세를 야구 → 사무라이 베기(준비는 방망이 그대로, 치기·회복은 양손 검) | 완료 |

## 10. 공부 노트 (왜 그렇게 하는지)

[study/README.md](study/README.md): 00 공부 지도, 01 역 울타리, 02 시야 시스템, 03 레이어 그리기, 04 스프라이트와 뼈대, 05 3D를 도트로.

## 11. 작업 기록

| 문서 | 무엇 |
|---|---|
| [DEVLOG.md](DEVLOG.md) | 날짜별 개발일지(무엇을 왜 바꿨는지) |
| [DEVELOPMENT_RETROSPECTIVE.md](DEVELOPMENT_RETROSPECTIVE.md) | 반복해서 막힌 부분과 교훈 |
| [TODO.md](TODO.md) | 할 일 |
