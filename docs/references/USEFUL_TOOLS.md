# 도움 될 도구·자료 모음

사용자가 작업 중간중간 알려 준 도구와 자료를 한곳에 모은다. 새로 받으면 여기에 한 줄 추가한다.
기준: 무료만(유료 결제 없음), 우리 게임(pico2d, 36px 도트, 4방향 공격)에 어떻게 쓸지를 같이 적는다.

## 동작·스프라이트 만들기

| 도구 | 하는 일 | 무료? 필요한 것 | 라이선스 | 우리에게 | 받은 날 |
|---|---|---|---|---|---|
| [2dimg2motion](https://github.com/WU-HAOTIAN34/2dimg2motion) | 그림 한 장 + 동작 설명 → 투명 14프레임, 스프라이트 시트, gif | Claude Code 스킬. 그림 생성 기능이 따로 있어야 함(모델은 정해져 있지 않음) | MIT | 프레임 정리·시트 만드는 뼈대만 참고. 그림 생성은 우리 LoRA/PixelLab으로 대신 | 2026-11-20 |
| [sprite-gen](https://github.com/aldegad/sprite-gen) | 그림 → 상태별 스프라이트, AI 영상에서 프레임 뽑아 배경 지우기·정리 | Python CLI. 생성은 본인 로그인/API 키(OpenAI는 호출마다 과금), 영상은 ffmpeg | Apache-2.0 | 영상 → 프레임 → 투명 처리 부분이 쓸모 있음. 유료 생성기는 안 씀 | 2026-11-20 |
| [Sprite Sheet Diffusion](https://github.com/chenganhsieh/Sprite-Sheet-Diffusion) | 캐릭터 그림 + 자세 순서 → 동작 프레임 (Moore-AnimateAnyone 기반) | 내 컴퓨터 GPU, 학습된 가중치 공개(Google Drive) | MIT, 학습 데이터 CC0 | **시험함, 실패(2026-11-20)**: 공개 가중치에 자세 읽는 부분(pose guider)이 빠져 있음. AnimateAnyone 것을 끼워 돌리니 자세 윤곽만 따르고 그림은 푸른 얼룩(`docs/planning/ssd_try_se.png`). 8GB GPU에서 한 장 4초로 돌아가긴 함. 코드 `tools/ai/ssd_pose.py` | 2026-11-20 |
| [Agent Sprite Forge](https://github.com/0x0funky/agent-sprite-forge) | 그림 한 장 → 대기·걷기·달리기·공격·피격 세트, 맵·타일 | 생성은 본인 API 키(OpenAI/Gemini 등 호출마다 과금) 또는 구독 CLI. 모델 없이 코드로 그리는 대체 경로 있음 | MIT | 유료 경로는 안 씀. 루프 맞추기·배경 지우기·내보내기 과정만 참고 | 2026-11-20 |
| [Codixel](https://github.com/mankidev/codixel) | 참고 그림 → 도트 캐릭터, 뼈대를 붙여 코드로 움직임 | Claude Code 스킬, 유료 API 언급 없음 | MIT | 우리 사이트(tools/animator)와 같은 뼈대 방식. 캐릭터는 내가 그리지 않는 원칙이라 그림 변환은 쓰지 않고, 뼈대 붙이는 방법만 비교 | 2026-11-20 |
| [PixelLab](https://www.pixellab.ai) | 도트 캐릭터 8방향·걷기, 뼈대로 자세 그리기(API) | 무료 생성 횟수 + 하루 5회 | 서비스 약관 | 지금 주인공 그림과 남동 내려치기(PL_chop) | 2026-11-18 |
| [Meshy](https://www.meshy.ai) | 그림 → 3D 모델, 리깅·동작 | 크레딧. 다운로드는 PRO(유료)라 막힘 | 서비스 약관 | 모델은 잘 나옴, 받기가 막혀 보류 | 2026-11-20 |
| LPC 생성기 | 공개 도트 캐릭터 조합, 휘두르기 시트 | 무료 | CC-BY-SA / GPL / OGA-BY | `assets/characters/lpc_hero` 비교용 | 2026-11-19 |

## 도트로 바꾸기 (후처리)

| 도구 | 하는 일 | 무료? 필요한 것 | 라이선스 | 우리에게 | 받은 날 |
|---|---|---|---|---|---|
| [PixelOE](https://github.com/KohakuBlueleaf/PixelOE) | 일반 그림 → 도트. 윤곽을 먼저 넓히고 줄여서 선과 명암이 살아남음(AI 아님) | `pip install pixeloe`, CPU로 됨 | Apache-2.0 | `tools/ai/lora_pose.py`, `redraw_pose.py`의 to_dots(그냥 줄이기 + 색 맞추기)를 대신할 후보. 팔·무기 같은 가는 선이 덜 사라짐 | 2026-11-20 |

## 효과

| 도구 | 하는 일 | 무료? 필요한 것 | 라이선스 | 우리에게 | 받은 날 |
|---|---|---|---|---|---|
| [pixelfx](https://github.com/patch-gg/pixelfx) | 코드로 그리는 도트 효과 244종(불, 폭발, 마법, 날씨, UI), 색 바꾸기, PNG 시트 + JSON 내보내기, Claude Code 스킬 포함 | 무료, Node(`tools/sheets.mjs`) | MIT(폰트 제외) | MOTION_RULES의 "무기마다 다른 효과"에 바로 쓸 후보: 시트로 뽑아 `assets/effects`에 넣고 SpriteFx로 재생 | 2026-11-20 |
| [Pixelbolt](https://github.com/skulitom/Pixelbolt) | JSON 설계도(팔레트, 글자 격자 도트, 그리기 명령) → PNG 시트·gif | 무료, Node 20, AI·네트워크 없음 | MIT | 효과·UI 아이콘처럼 모양이 단순한 것만. 캐릭터는 손으로 그리지 않는 원칙(사용자가 "드로잉하지 마라")이라 제외 | 2026-11-20 |
| tbbk 베기 효과 | 베기 초승달 | 무료 | CC0 | `slash` 효과로 사용 중 | 2026-11-18 |
| Viktor Hahn 타격 효과 | 맞는 순간 번쩍 | 무료 | CC-BY | `hit`, `hit_big` 사용 중 | 2026-11-18 |

## 방법·글

- 게임 전용 AI 툴(Scenario 등)로 내 화풍을 LoRA로 학습시켜 일관성 유지 → 우리는 무료로 내 컴퓨터에서 학습(`C:\Users\doboh\busan_ai`, SD1.5 LoRA, 트리거 단어 `busanhero`). 2026-11-20
