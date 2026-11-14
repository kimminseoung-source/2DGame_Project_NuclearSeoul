# AI 게임 제작 도움 리소스·GitHub 조사 (2026-11-14)

사용자 지시: "AI 게임 생성 도움 리소스, 깃허브도 조사해 봐." 조건: **무료만**(유료 API가 필요한 것은 표시). 받거나 설치하기 전에는 파일마다 허락.
이 컴퓨터: NVIDIA RTX 5060 노트북 GPU(8GB급), 메모리 31GB → 로컬 AI 모델을 돌릴 수 있는 사양.
라이선스·별 수는 검색 결과 기준이라 쓰기 전에 각 저장소에서 다시 확인한다.

## 1. 우리 프로젝트에 바로 쓸 만한 것 (추천 순)

| # | 이름 | 무엇 | 우리에게 | 비용·주의 |
|---|---|---|---|---|
| 1 | [BlenderMCP (ahujasid)](https://cdn.jsdelivr.net/gh/ahujasid/blender-mcp@main/README.md) | Claude가 Blender를 직접 조작(장면 만들기, 물체 배치, 화면 캡처). Poly Haven(CC0 텍스처·모델·HDRI)을 키 없이 불러옴 | 탑뷰 **배경(거리·건물·폐차) 장면을 Claude가 직접 만들고 렌더**, 주인공 8방향 렌더 카메라 조정. 지금 Blender 렌더 도구와 같은 흐름 | 무료. Claude Code 설정에 MCP 추가 필요(`claude mcp add blender uvx blender-mcp`), uv 설치 필요. 3D 생성 기능(Hyper3D, Hunyuan3D)은 별도 |
| 2 | [jsfxr](https://sfxr.me) / [rFXGen](https://git.tdem.in/raysan5/rfxgen) | 레트로 효과음 생성기(sfxr 계열) | 베기·발소리·예고음 같은 **짧은 효과음을 바로** 만들기. 도트 게임과 잘 맞음 | 무료, GPU 불필요. jsfxr는 npm 라이브러리도 있어 코드로 생성 가능 |
| 3 | Stable Audio Open (Stability AI) | 글로 설명하면 효과음·환경음(최대 47초, 44.1kHz) 생성, 로컬 실행 | 폐허 바람 소리, 피폭체 신음 같은 **현실적인 환경음** | 로컬 무료, GPU 6~8GB 필요(우리 사양으로 가능). 상업 이용 조건은 확인 필요. [Claude Code용 패키지 soundbox](https://trendshift.io/repositories/323872)도 있음 |
| 4 | [pixel-unslop (salvimateus)](https://github.com/SubmitGame/awesome-ai-game-dev-tools), spritefusion-pixel-snapper (Hugo-Dz) | AI나 렌더로 만든 흐릿한 도트를 **진짜 픽셀 격자에 맞추고 색을 정리** | Blender 렌더 → 도트 변환 결과를 더 깔끔하게(ART_FEEDBACK "3D 명암이 뭉개짐" 문제) | 무료 오픈소스(라이선스 확인 필요) |

## 2. 도트·스프라이트 생성 (참고, 신중히)

| 이름 | 무엇 | 주의 |
|---|---|---|
| [Sprite Sage](https://github.com/keystoneintelligence/spritesage) | AI로 스프라이트·애니메이션 생성·편집, GPLv3 | AI 기능은 외부 AI 제공자 설정 필요(유료일 수 있음). 편집·내보내기는 AI 없이 가능 |
| [PiXelDa](https://github.com/dada-x/pixelda) | AI 도트 에셋 생성 웹 플랫폼, MIT | 어떤 이미지 모델을 쓰는지 확인 필요 |
| Claude Code 스킬: [Agent Sprite Forge](https://openskillindex.com/skills/aradotso-trending-skills-agent-sprite-forge), [SpriteCook skills](https://github.com/SpriteCook/skills), [pixel-art-sprites (omer-metin)](https://claudemarketplaces.com/skills/omer-metin/skills-for-antigravity/pixel-art-sprites), [character-sprite (claude-office)](https://www.vibeindex.ai/skills/paulrobello/claude-office/character-sprite), [Pixel Art Animator (Aseprite MCP)](https://www.mdskills.ai/skills/pixel-art-animator) | 글로 도트 캐릭터·애니메이션 생성 | 상당수가 **유료 이미지 API**에 의존하거나 Aseprite(유료) 필요. 생성형 AI 그림은 동작마다 얼굴·옷이 달라지기 쉬워 ART_FEEDBACK 점검(일관성)에 걸림. 우리 3D → 도트 방식이 동작 일관성에서 유리 |

## 3. 모아 둔 목록 (계속 찾을 곳)
- [awesome-ai-game-dev-tools (SubmitGame)](https://github.com/SubmitGame/awesome-ai-game-dev-tools): 오픈소스 AI 게임 제작 도구, 매일 갱신
- [magictools (ellisonleao)](https://github.com/ellisonleao/magictools): 게임 제작 리소스 전반(Krita, LibreSprite 등 무료 도구 포함)
- GitHub 주제: [pixel-art-generator](https://github.com/topics/pixel-art-generator), [sprite-generator](https://github.com/topics/sprite-generator), [sprite-generation](https://github.com/topics/sprite-generation)
- Claude 게임 제작 스킬 모음: [skillselion game-dev](https://skillselion.com/game-dev)

## 4. 판단
- **가장 효과가 큰 것은 BlenderMCP.** 지금 막힌 "탑뷰 배경 그림"과 "8방향 주인공"을 Claude가 Blender에서 직접 만들 수 있다. 무료이고 지금 도구와 같은 방식(3D → 도트)이라 화풍이 이어진다.
- **효과음은 jsfxr로 시작**(바로, 가볍게), 환경음이 필요해지면 Stable Audio Open.
- AI 이미지 생성 스킬은 대부분 유료 API이거나 동작 일관성이 약해 **주인공에는 쓰지 않는 쪽**을 추천. 시안(한 장 그림) 정도에만.
- 기획 고정 문서 규칙 6(그림보다 재미 먼저)에 따라 그림 도구는 전투 재미를 확인한 뒤에 본격적으로.

## 출처
- [awesome-ai-game-dev-tools](https://github.com/SubmitGame/awesome-ai-game-dev-tools), [magictools](https://github.com/ellisonleao/magictools), [Sprite Sage](https://github.com/keystoneintelligence/spritesage), [PiXelDa](https://github.com/dada-x/pixelda)
- [BlenderMCP README](https://cdn.jsdelivr.net/gh/ahujasid/blender-mcp@main/README.md), [mcpservers: CSM blender-mcp](https://mcpservers.org/en/servers/CommonSenseMachines/blender-mcp)
- [Stable Audio Open 소개(The Decoder)](https://the-decoder.com/stable-audio-open-is-like-the-stable-diffusion-of-sound-design-and-its-completely-open-source/), [soundbox (Trendshift)](https://trendshift.io/repositories/323872)
- [sfxr.me (jsfxr)](https://sfxr.me), [rFXGen](https://git.tdem.in/raysan5/rfxgen)
- [SpriteCook skills](https://github.com/SpriteCook/skills), [skillselion game-dev](https://skillselion.com/game-dev)
