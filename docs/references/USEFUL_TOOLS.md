# 도움 될 도구·자료 모음

사용자가 작업 중간중간 알려 준 도구와 자료를 한곳에 모은다. 새로 받으면 여기에 한 줄 추가한다. "어떻게 만들면 좋을지" 같은 글은 [ANIMATION_GUIDES.md](ANIMATION_GUIDES.md)에 모은다.
기준: 무료만(유료 결제 없음), 우리 게임(pico2d, 36px 도트, 4방향 공격)에 어떻게 쓸지를 같이 적는다.

> 아래 기존 표는 주로 2026-11-20 당시 조사·시험 기록이다. 최신 재검토는 문서 끝의 **2026-11-23 재조사**를 먼저 본다. 특히 생성 한도·비용과 스킬의 지원 환경은 당시 기록과 달라질 수 있다. 현재 3D 주인공 동작은 8방향이므로 위의 4방향 표현을 새 제작 규격으로 사용하지 않는다.

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
- 사용자 공유 영상: [AI 게임 리소스 제작에 사용할 수 있는 오픈소스 8가지 | 1편](https://www.youtube.com/watch?v=_U5wuMhZXI0) — 받은 날 2026-11-23. 영상 제목·URL만 확인. 본문·자막은 확보하지 못해 영상에 나오는 8개 도구와 세부 내용은 확인 전이며, 위 목록과 같은 자료라고 단정하지 않는다. 내용 확인 후 도구별 원본 저장소·비용·라이선스·우리 게임 적용 가능성을 기존 표에 정리한다.
- 사용자 공유 영상: [AI로 게임 만들 때 쓰는 도구 총정리 (Claude Code, Codex, Godot, Blender…)](https://www.youtube.com/watch?v=kZM0qx4hDbg) — MGD - Midnight Game Devs, 받은 날 2026-11-23. AI 작업 환경·MCP·엔진·Git·아트·음성 도구를 다루는 참고 영상. 공개 설명 기준 시간표와 활용 메모는 문서 끝의 같은 제목 항목에 정리했다.

## 3D 캐릭터 (무료로 쓸 수 있는 곳, 2026-11-20 조사)

사용자 "무료 캐릭터 이용할 수 있는 사이트도 조사해 봐요". 3D 동작 → 도트(방식 5)의 몸으로 쓸 후보.

| 곳 | 무엇 | 라이선스 | 우리에게 |
|---|---|---|---|
| [MPFB2 (MakeHuman, Blender 확장)](https://extensions.blender.org/add-ons/mpfb/) + [자산 묶음](https://static.makehumancommunity.org/assets/assetpacks/) | 체형·얼굴·머리·옷을 골라 사람을 만듦, 게임 뼈대 | 도구 GPL, 자산 대부분 CC0(일부 묶음 CC-BY) | **진행 중**: 마른 청년 + 티셔츠 + 바지 + 부츠 + 머리 |
| [Mixamo](https://www.mixamo.com) | 사람 캐릭터와 동작, 올린 모델에 뼈대 자동 붙이기 | 게임 안에서 상업 사용 가능, 모델·동작만 따로 파는 건 안 됨([Adobe 커뮤니티 FAQ](https://community.adobe.com/t5/mixamo-discussions/mixamo-faq-licensing-royalties-ownership-eula-and-tos/td-p/13234775)) | 이미 `assets/source3d/mixamo`에 Alex와 동작 몇 개. Adobe 로그인 필요 |
| [VRoid Studio](https://vroid.com/en/studio/guidelines) | 애니메 풍 사람 캐릭터 만들기(무료 프로그램) | 기본 제공 자산은 상업 사용 가능, 일부 예외 | 머리카락·옷이 애니메 풍이라 우리 그림과 다를 수 있음 |
| [KayKit](https://kaylousberg.itch.io/kaykit-adventurers) | 귀여운 저폴리 캐릭터·동작 | CC0 | 비율이 장난감 같아 주인공보단 참고용 |
| Quaternius | 기본 몸·동작 라이브러리 | CC0 | 지금 쓰는 몸과 동작(UAL1·UAL2) |
| [CGTrader 무료 "Realistic Male Character Rigged"](https://www.cgtrader.com/free-3d-models/character/man/realistic-male-character-rigged) | 사실적인 남자, 뼈대 있음 | 로열티 프리(AI 금지 조항) | 옷 확인 필요, 대부분 재킷·청바지 모델은 유료 |
| Ready Player Me | (아바타 만들기) | 2026-01-31 서비스 종료 | 쓸 수 없음 |

## 2026-11-23 재조사 — 새 주인공·원거리 피폭체에 쓸 도구

> 최종 적용 순서(사용자: 우선 기준 방식으로 진행하고 더 좋은 방식이 있으면 전환): **현재 3D→도트가 기본**, 아래 직접 2D 생성은 비교 후보. 세부 단계는 [기준 방식과 비교 계획](../plans/2026-11-23_주인공_스프라이트_기준방식과_비교계획.md)을 따른다. 아래의 '추천 시험 순서'는 직접 2D 경로를 시험할 때의 절차이며 전체 기본 제작을 2D로 바꾼 결정이 아니다.

요청: 기존에 모아 둔 자료와 공유 영상에서 실제 도움 되는 도구를 찾고, 추가 스킬·플러그인도 조사. 이번에는 공식 README·서비스 문서와 기존 실패 기록을 대조했으며, 새 설치·모델 다운로드·생성 서비스 결제나 호출은 하지 않았다. 아래 추천은 실제 적용 성공 판정이 아니라 비교 시험의 우선순위다.

### 공유 영상과 확인 범위

- [원본 영상](https://www.youtube.com/watch?v=_U5wuMhZXI0)은 직접 본문·자막을 확보하지 못했다.
- 대신 [영상 자막을 대조한 정리 글](https://gyuha.com/post/2026/11/2026-11-05-open-source-ai-game-assets-four-tools/)을 찾았다. 이 글은 1편의 네 도구를 **2dimg2motion / sprite-gen / pixelfx / PixelOE**로 설명한다. 영상 내용은 이 글을 통한 간접 확인이며, 각 기능은 아래 원본 저장소에서 별도로 확인했다. 제목의 8개 전체를 직접 검증한 것으로 보지 않는다.

### 후보와 판단

| 후보 | 공식 문서에서 확인한 기능 | 이번 프로젝트에서의 판단 | 비용·제약 |
|---|---|---|---|
| [2dimg2motion](https://github.com/WU-HAOTIAN34/2dimg2motion) | Codex·Claude Code용 스킬. 기준 외형과 손·무기 관계를 고정하고 주요 자세·중간 프레임을 이미지 모델로 생성. 투명 프레임·시트·GIF·구조 검증 | **직접 2D 제작을 비교할 첫 후보.** 황토색 재킷·배낭을 고정한 한 방향 베기만 시험. 원거리 적 준비·발사도 후보 | MIT 스킬 자체와 별도로 이미지 생성 기능·사용량이 필요. 설치만으로 동작이 생성되지 않으며, 현재 내장 생성 도구와의 전체 실행 연결은 미검증. 기본 14프레임은 우리 게임의 공격 3장 규격과 달라 핵심 자세 선정이 필요 |
| [sprite-gen](https://github.com/aldegad/sprite-gen) | Codex·Claude용 스킬과 Python CLI. 상태별 이미지 시트, 투명화·프레임 추출·아틀라스·프레임 좌표. 별도로 영상→루프 경로 | 생성 이미지가 모인 뒤 **프레임 정렬·투명화·패키징** 후보. 기존 게임 로더에 맞춘 출력 변환 필요 | 이미지·영상 생성 제공자의 인증·사용량은 별도. 영상 경로는 ffmpeg 등 추가 도구 필요. README도 걷기·달리기는 모션 검증 전 실험적이라고 명시 |
| [PixelOE](https://github.com/KohakuBlueleaf/PixelOE) | 윤곽 확장 뒤 대비를 고려한 축소, 색 수 조정. AI·신경망 없이 처리, CPU 경로 및 ComfyUI 노드 제공 | **후처리 우선 후보.** 그냥 축소한 36px와 비교해 검·얼굴·목의 밝은 부분이 남는지 확인 | 무료 오픈소스. 그림이나 동작을 생성하는 도구는 아니며, 프레임별 자동 색 변경·윤곽 변화가 깜빡임을 만들지 확인 필요 |
| [pixelfx](https://github.com/patch-gg/pixelfx) | 244개 코드 기반 도트 효과, Claude Code 스킬, 색 변경, 투명 PNG 시트와 Aseprite형 JSON 내보내기 | **효과 제작 우선 후보.** 검 궤적·총구 불꽃·원거리 탄의 충돌 효과에 활용. pico2d에는 JS 런타임 대신 PNG 시트를 연결 | 코드·효과 MIT. 저장소 폰트는 별도 조건. 효과의 크기·팔레트·타격 시점을 게임에 맞춰 조정 |
| [MCP for Blender](https://github.com/ahujasid/mcp-for-blender) (기존 ahujasid/blender-mcp 링크에서 이동) | Blender 물체·재질 조작, Python 실행, 여러 각도·렌더·애니메이션 스트립 확인 | **기존 3D 경로를 편하게 하는 선택사항.** 몸·배낭·검 위치 확인에 도움. 기존 Blender CLI 스크립트도 있으므로 필수는 아님 | 커뮤니티 도구이며 Blender 재단 공식 플러그인이 아님. 연결 도구와 외부 AI 3D 생성 서비스의 비용을 구분. 우리 환경 연결 미검증 |
| [Sprite Fusion Pixel Snapper](https://github.com/Hugo-Dz/spritefusion-pixel-snapper) | AI 이미지의 불규칙한 픽셀을 격자에 맞추는 도구, 웹·데스크톱 경로 | 새롭게 구체화한 후보. 생성 시안의 픽셀 크기가 제각각일 때 PixelOE와 비교 | 프레임의 외형·해부학·동작 오류를 고치는 도구는 아님. 설치·실행은 아직 하지 않음 |
| [PixelLab 공식 Claude 플러그인](https://github.com/pixellab-code/pixellab-claude-plugin), [공식 MCP 안내](https://www.pixellab.ai/mcp) | 캐릭터·방향·애니메이션 생성 등을 MCP로 호출. 플러그인은 Claude Code 설치 경로, 공식 문서는 Codex 등 MCP 클라이언트도 안내 | 연결 방식은 유용하지만 **무료 우선 경로에서는 보류**. 기존 PixelLab 실패·비교 기록을 먼저 확인 | 계정 토큰과 구독 또는 크레딧 필요. 옛 표의 무료 횟수를 현재 보장으로 사용하지 않음. 현재 연결 안 됨 |

### 기존 후보에서 당장 우선하지 않는 것

- Sprite Sheet Diffusion: 기존 11-20 기록은 pose guider 가중치 문제와 품질 실패. 새로운 해결 근거를 확인하지 않은 상태에서 같은 대용량 모델을 다시 받지 않는다.
- LoRA·ControlNet: 기존 문서에 자세·팔·무기 불일치 실패 기록이 있어 새 콘셉트의 첫 제작 경로로 반복하지 않는다. 기록은 실제 현재 재시험 결과와 구분한다.
- [Codixel](https://github.com/mankidev/codixel): 참고 이미지와 코드 기반 파츠·뼈대로 움직이는 방식. 이전 tools/animator의 36px 품질 문제와 겹쳐 이번 사람형 검 공격의 우선 후보로 두지 않는다.
- [Agent Sprite Forge](https://github.com/0x0funky/agent-sprite-forge): 현재 README에는 API와 로그인된 Codex/Grok CLI 경로가 함께 있다. 유료 API 전용으로 단정할 수 없지만, 기능·경로가 넓고 코드 아트 대체도 있어 현재의 단일 동작 실험에는 후순위. 프로젝트의 내장 이미지 생성 우선·코드로 캐릭터를 그리지 않는 기준이 우선한다.

### 추천 시험 순서 (아직 실행 전)

1. 검 모양·자세가 정해진 기준 캐릭터 한 장을 준비한다. 지금 마체테 시안을 최종 검 디자인으로 확정하지 않는다.
2. 2dimg2motion의 외형 고정·핵심 자세 생성 방식을 적용해 **남동 한 방향 베기 하나**를 시험한다. 설치가 필요하면 구체적인 설치 대상부터 정한다.
3. 기존 방식의 단순 축소와 PixelOE/격자 정리 후보를 같은 크기·팔레트·발 기준으로 비교한다. 36px에서도 손·검·얼굴·재킷이 읽히는지 본다.
4. 동작은 미리보기로 검수하고, 외형이 바뀌거나 무기 손이 뒤집히면 확장하지 않는다. 좋은 결과가 확인돼도 처음부터 14장을 모두 게임에 적용하지 않고 기존 공격 3장·타이밍 기준과 대조한다.
5. 검 효과는 pixelfx 후보를 작게 비교. 2D 외형 일관성이 부족하면 기존 3D→도트 방식으로 몸을 제작한다.

### 설치·연결 상태

- Codex의 플러그인 검색에서 Blender·PixelLab·Meshy 이름으로 일치 항목을 찾지 못했다. 이는 외부 MCP나 Claude 플러그인이 없다는 뜻이 아니다.
- 프로젝트의 기존 자료와 원본 문서를 읽은 조사이며, 위 도구를 이번에 설치·연결·실행한 것은 아니다. 새 프로그램이나 모델은 추가하지 않았다.

### 추가로 찾은 3D 렌더 도구와 최종 활용

- [Sprite Sheet Maker](https://github.com/ManasMakde/SpriteSheetMaker): Blender 애드온. 자동 카메라·정사영, 프레임 크기와 정렬, 픽셀화·시트 출력을 지원한다. 현재 `mpfb_pose.py`·`build_hero3d.py`와 역할이 겹치므로 바로 설치하지 않는다. 렌더 설정 관리가 병목일 때 비교 후보로 둔다.
- [SpriteForge](https://github.com/arqsbo3d/spriteforge) (arqsbo3d): Blender를 외부 렌더러로 사용하는 3D→픽셀 앱. 방향별 렌더·공유 팔레트·시트·JSON을 지원한다. README는 초기 버전이며 Windows와 Blender 4.4에서 시험했다고 명시한다. **0x0funky의 Agent Sprite Forge와 별개 도구**다. 현재 Blender 5.2 환경의 호환성은 미검증이므로 보류.
- 결론: 주인공 몸·방향·동작은 기존 3D 경로부터 만들고, 효과는 pixelfx, 후처리는 PixelOE/Pixel Snapper, 직접 이미지 동작 생성은 2dimg2motion 순으로 필요한 단계에만 비교 도입한다. 도구를 쓰기 위해 현재 규격이나 게임 로더부터 바꾸지 않는다.

## 2026-11-23 공유 영상 — AI 게임 제작 도구 총정리

| 항목 | 내용 |
|---|---|
| 제목 | AI로 게임 만들 때 쓰는 도구 총정리 (Claude Code, Codex, Godot, Blender…) |
| 원본 | [YouTube 영상](https://www.youtube.com/watch?v=kZM0qx4hDbg) |
| 채널 | [MGD - Midnight Game Devs](https://www.youtube.com/@MGD-MidnightGameDevs) |
| 공유일 | 2026-11-23 |
| 분류 | AI 개발 도구 운영·MCP 연결·Git·그래픽/음성 제작 참고 |
| 확인 범위 | YouTube 공식 oEmbed의 제목·채널과 공개 영상 설명·챕터를 확인. 본문을 재생하거나 자막 전체를 확보해 분석한 상태는 아님 |
| 시점 주의 | 공개 설명에 요금·사용량은 **2026년 10월 기준**이며 사용 전 공식 페이지에서 재확인하라고 명시 |

### 다시 볼 구간 — 제작자가 공개 설명에 적은 시간표

| 시각 | 내용 | 바로 가기 |
|---|---|---|
| 00:00 | 받은 질문들 | [00:00](https://www.youtube.com/watch?v=kZM0qx4hDbg&t=0s) |
| 00:16 | 시작 전에: 딸깍 얘기 | [00:16](https://www.youtube.com/watch?v=kZM0qx4hDbg&t=16s) |
| 00:36 | 하네스 (Claude Code, Codex) | [00:36](https://www.youtube.com/watch?v=kZM0qx4hDbg&t=36s) |
| 02:38 | MCP | [02:38](https://www.youtube.com/watch?v=kZM0qx4hDbg&t=158s) |
| 02:54 | 게임 엔진 (Godot, Unity, Unreal) | [02:54](https://www.youtube.com/watch?v=kZM0qx4hDbg&t=174s) |
| 03:50 | Git | [03:50](https://www.youtube.com/watch?v=kZM0qx4hDbg&t=230s) |
| 04:16 | Blender, Aseprite | [04:16](https://www.youtube.com/watch?v=kZM0qx4hDbg&t=256s) |
| 05:15 | 3D·도트 생성 서비스 | [05:15](https://www.youtube.com/watch?v=kZM0qx4hDbg&t=315s) |
| 06:01 | ElevenLabs | [06:01](https://www.youtube.com/watch?v=kZM0qx4hDbg&t=361s) |
| 06:19 | 마무리 | [06:19](https://www.youtube.com/watch?v=kZM0qx4hDbg&t=379s) |

### 우리 프로젝트에서의 활용 메모 — 영상 내용 요약과 구분한 판단

- **우선 참고할 구간:** Claude Code·Codex(00:36), MCP(02:38), Git(03:50). 두 AI의 역할·작업 전달·변경 이력 관리 방법을 살펴볼 자료다. 실제 공동 작업 현황은 프로젝트 문서와 Git에서 확인한다.
- **현재 제작과 연결할 구간:** Blender·Aseprite(04:16), 3D·도트 생성 서비스(05:15). 기준인 3D→도트 제작과 비교 도구를 검토할 때 참고한다. 공개 설명에는 생성 서비스의 개별 이름이 없어 임의로 채우지 않는다.
- **소리 작업 시 참고:** ElevenLabs(06:01)는 필요할 때 공식 비용·사용 조건을 별도 확인한다. 이번 자료 등록으로 사용·구독을 결정하지 않는다.
- 엔진 설명은 비교 자료로 보관하며, 현재 Python+pico2d 제작 기준을 변경한 결정으로 해석하지 않는다.
- 구체적인 설치 명령·서비스별 장단점·성능은 본문이나 공식 문서를 추가 확인한 뒤 기록한다. 이번에는 링크·메타데이터·설명의 시간표를 등록했다.

### 관련 프로젝트 문서

- [주인공 스프라이트 기준 방식과 비교 계획](../plans/2026-11-23_주인공_스프라이트_기준방식과_비교계획.md)
- [애니메이션 제작 참고 모음](ANIMATION_GUIDES.md)
- [조사·참고 자료 목차](../RESEARCH_INDEX.md)
