# 고품질 도트 캐릭터 제작 방식 조사

작성 2026-11-10. 사용자 지시: "다른 곳에서 저런 고퀄 캐릭터는 어떤 작업을 통해서 뽑아내는지 조사하고 저희도 그런 방식으로 해서 뽑아내 보죠" ([개발 계획](../../PLAN.md) 사용자 지시 기록). 조건: 무료 도구·에셋만, 기본형 하나에서 변형해 여러 캐릭터를 만들 것, 1차 발표의 노란 방호복 주인공을 지킬 것.

## 1. 다른 게임들이 쓰는 방식

| 방식 | 대표 사례 | 과정 | 장점 | 단점 |
| --- | --- | --- | --- | --- |
| **손으로 한 장씩 그리기** | 대부분의 인디 도트 게임 | 콘셉트 → 비율·자세 기준표 → 핵심 자세(키프레임) → 중간 프레임 → 정리 → 실제 게임 크기에서 확인 ([파이프라인 정리](https://relishgames.com/journal/pixel-art-pipelines-best-tools-for-2026/)) | 품질 상한이 가장 높음 | 시간과 그림 실력이 많이 필요. 캐릭터마다 다시 그려야 함 |
| **3D 모델을 도트로 렌더링** | **Dead Cells** (Motion Twin) | 3D 모델에 키프레임 애니메이션을 만들고, 자체 도구로 저해상도 2D 스프라이트로 일괄 변환 ([Dead Cells 3D 파이프라인](https://www.jikguard.com/news/art-design-deep-dive-using-a-3d-pipeline-for-2d-animation-in-dead-cells), [캐릭터 아트 사례](https://80.lv/articles/case-study-dead-cells-character-art-pipeline/)) | 동작이 부드럽고, 옷·무기를 바꿔도 모든 동작이 자동으로 다시 나옴. 수정이 빠름 | 3D 준비와 렌더 설정이 필요. 손그림 도트보다 덜 "그린 느낌" |
| **조합형(옷 갈아입히기)** | LPC 생성기, 조합형 팩 | 기본 몸 동작 위에 옷·머리·무기 레이어를 겹침 | 변형이 쉬움 | 모든 레이어를 모든 프레임에 맞춰 그려야 함 |
| **AI 원화 후 정리** | 지금 주인공 | 이미지 생성 → 투명 배경·크기·기준점 정리 | 빠름 | 프레임마다 모양이 흔들려 동작 일관성이 약함 |

## 2. 우리에게 맞는 방식: 3D → 도트 렌더링 (Dead Cells 방식, 무료 도구로)

"기본형 하나에서 변형"이라는 요구와 가장 잘 맞는다. 3D에서는 **기본 몸 + 옷·머리·소품을 갈아 끼우는 것**이 원래 쉬운 구조이고, 동작은 한 번 붙이면 모든 변형이 같은 동작을 공유한다.

| 단계 | 도구 (모두 무료) | 하는 일 |
| --- | --- | --- |
| 기본 몸 | [Quaternius Universal Base Characters](https://quaternius.com/packs/universalbasecharacters.html) | 남·여, 보통·청소년 체형의 리깅된 기본 몸, 머리 모양 교체 가능 (CC0로 표기, 최근 자체 라이선스 공지가 있어 받을 때 확인) |
| 옷·소품 | Quaternius 조합형 옷([Fantasy 예시](https://quaternius.com/packs/modularcharacteroutfitsfantasy.html)), Blender에서 직접 만든 단순한 방호복·후드·공기통·방망이 | 기본 몸에 갈아 입힘. 방호복처럼 단순한 옷은 기본 도형으로 만들 수 있음 |
| 동작 | Mixamo(무료, Adobe 계정 필요) 또는 Quaternius 애니메이션 | 대기·걷기·휘두르기·피격·쓰러짐 등을 붙임 |
| 렌더링 | Blender + 렌더 스크립트([mixamo-to-2d](https://awesome.ecosyste.ms/projects/github.com%2Falexferl%2Fmixamo-to-2d) 같은 공개 스크립트 참고, [GameFromScratch 예시](https://gamefromscratch.com/creating-a-walk-cycle-spritesheet-in-under-15-minutes/)) | 옆모습 고정 카메라로 저해상도(칸 96×64) 렌더, 계단식 음영(툰 셰이딩)·외곽선·색 수 제한 → 도트처럼 |
| 다듬기 | Pixelorama | 필요한 칸만 손으로 정리 |

### 우리 규격과 연결

- 렌더 결과는 [기본형 캐릭터 제작 규격](../../assets/characters/CHARACTER_SPEC.md)의 칸(96×64), 발 기준점, 동작 7종에 그대로 맞춘다.
- 3D에서 레이어를 따로 렌더하지 않아도 된다. **옷을 바꿔 다시 렌더하면** 그 캐릭터의 전체 시트가 나온다. 색 바꾸기는 3D 재질 색만 바꾸면 된다.
- 무기는 손 뼈에 붙이므로 방망이·쇠파이프·렌치를 바꿔 끼워도 휘두르기 동작이 그대로 맞는다(모든 공격에 공통인 전투 구조와 같은 생각).

### 역할

- **직접 해 주실 일**: Blender 설치, Quaternius 팩 내려받기, (쓴다면) Mixamo 계정 만들기와 동작 내려받기. 계정 만들기와 내려받기는 직접 하셔야 한다.
- **제가 할 일**: Blender를 명령줄로 실행하는 렌더 스크립트 작성(카메라·조명·툰 셰이딩·외곽선·칸 크기·발 기준점), 시트 정리, 게임 연결, 크기·속도 확인. Blender가 설치되면 이 컴퓨터에서 제가 직접 렌더를 돌릴 수 있다.

## 3. 시험 순서 (제안)

1. 기본 몸 1개 + 걷기 동작 1개로 렌더 스크립트를 시험한다. 지금 주인공과 나란히 놓고 크기·느낌을 비교한다.
2. 괜찮으면 대기·휘두르기·피격·쓰러짐을 추가하고, 방호복·후드·공기통·방망이를 입혀 1차 발표의 주인공을 다시 만든다.
3. 옷과 색을 바꿔 동료·생존자·적대 생존자를 만든다.
4. 결과가 마음에 들지 않으면 손그림 방식(Pixelorama + [템플릿](../../assets/characters/templates/))으로 돌아간다.

## 출처

- [Art Design Deep Dive: Using a 3D pipeline for 2D animation in Dead Cells](https://www.jikguard.com/news/art-design-deep-dive-using-a-3d-pipeline-for-2d-animation-in-dead-cells)
- [80.lv: Dead Cells character art pipeline](https://80.lv/articles/case-study-dead-cells-character-art-pipeline/)
- [GameFromScratch: walk cycle spritesheet with Mixamo and Blender](https://gamefromscratch.com/creating-a-walk-cycle-spritesheet-in-under-15-minutes/)
- [alexferl/mixamo-to-2d](https://awesome.ecosyste.ms/projects/github.com%2Falexferl%2Fmixamo-to-2d)
- [OpenGameArt: 2D pixel art from 3D models (Blender)](https://opengameart.org/node/44067)
- [Quaternius Universal Base Characters](https://quaternius.com/packs/universalbasecharacters.html)
- [Pixel art pipelines: best tools for 2026](https://relishgames.com/journal/pixel-art-pipelines-best-tools-for-2026/)
