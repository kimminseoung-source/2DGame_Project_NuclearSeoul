# 애니메이션 만들기 참고 모음 (사용자가 준 자료)

- 2026-11-24 최우선 얼굴 일관성 보완: [FACE-R1](../../assets/characters/previews/hero_pistol_gait_v4/identity/README.md). 정지/이동 원화가 달라 얼굴 크기가 흔들린 문제는 몸 높이 검사로 해결되지 않았다. 같은 방향 머리 레이어를26키에 공유하고 목 기준/실제 로더/게임 전환을 검수했다. 새 얼굴을 다시 생성하지 않았다. 다른 방향·표정·죽음 키는 따로 검수해야 하며 이번 완료 범위와 구분한다.

- 2026-11-24 후속 적용: [D 낮은 통과 자세/접지 반응](../../assets/characters/previews/hero_pistol_gait_v4/refinement/README.md). 사용자 D 개선 긍정/높은 무릎 지적 → 들린 다리 원화4키만 낮춤 → 기존 GAME_JUICE의 동작 순간 피드백 원리로 디딤 소리 동기화와 작은 기존 입자 적용. F10 수정 전후, 접지·소리 중복/정지·차단/실사격 검사 통과. 스미어·전신 흔들림으로 보행을 대신하지 않는다.

## 2026-11-24 · 기존 조사를 실제 D 보행에 적용

- 사용자: 기존 Claude 조사 기록을 계속 재사용하고 조사 후 적용하라. 조회/적용/검수 순서를 프로젝트 AGENTS/CLAUDE와 [캐릭터 제작 기준](../../assets/characters/CHARACTER_WORKFLOW.md)에 연결했다.
- [적용 계획과 근거](../plans/2026-11-24_보행기법_적용.md), [원화·코드·게임 검사 결과](../../assets/characters/previews/hero_pistol_gait_v4/README.md). SLYNYRD 50/60의 색 구분 모형·기준 보행 뒤 팔 변형·이동 사격 하체 유지, Monmouth의 반대 발 접촉/반복 연결을 적용했다.
- C 보존, D 시작/F8 A/B/C/D. 8키 실제 보행, 발 표시에서 cycle distance 산정, 권총 공격 상태가 입력 이동을 막던 경로를 D에서만 해제. 프레임 유지 중 추정 발 이동 C6.519→D3.259native px지만 D 후보 지지 전체 범위7.654px가 남는다. 접지 완료로 해석하지 않는다.
- 생성의 같은 발 반복 출력은 반려하고 잘못된 2/3/5번만 지정 수정했다. AI 포즈 안내는 강제 제어가 아니며 실제 검수가 필요하다. 현 단계는 좌우만, 전용 후진/상하 및 이동 중 상체 반동 원화/최종 총 분리 미완성이다.

## 2026-11-23 · 발동작 보완 조사

- [권총 전신 동작 계획의 발동작 재조사](../plans/2026-11-23_권총_전신동작_흐름보완.md): 기존 C 4키/발 미끄러짐/이동 사격 시 전신 반동으로 하체가 멈추는 문제를 확인. 개선 구현은 아직 하지 않았다.
- [SLYNYRD Human Walk Cycle](https://www.slynyrd.com/blog/2024/5/24/pixelblog-50-human-walk-cycle): 실제 보행 참고 → 좌우 구분 모형 → 의상. 4/6/8장 비교. [Side View Run 'N Gun](https://www.slynyrd.com/blog/2026/1/26/side-view-run-n-gun): 보행 완성 뒤 총 든 팔 적용, 이동 사격 시 하체 재생 유지. 측면 예시이므로 탑다운 방향 확장에는 별도 검증 필요.
- [Unity 공식 Root Motion 스크립팅](https://docs.unity3d.com/Manual/ScriptingRootMotion.html): 반복 연결과 이동 속도/모션 연결 원리 참고. pico2d 기능 설치안이 아니다.
- 추천: 기존 3D 보행의 실제 관절을 참고한 8단계 모형을 먼저 검수하고 AI 외형 적용. 8장 생성만으로 성공 판정하지 않는다. 실제 이동거리 기반 phase는 이미 있으므로 접지 궤적에서 cycle distance를 맞추고, 원화의 좌우 교대와 반동 상태 끼어들기를 함께 고친다.

## 2026-11-23 · 새 AI 주인공 작업 대조

- 최신 사용자 선택은 **AI 외형 유지 + 3D 자세 안내**다. 아래 11-20의 3D 최종 본체 선택은 과거 기록이며 현재 AI 외형을 3D 모델 외형으로 되돌리는 근거로 사용하지 않는다.
- 사용자 요청에 따라 기존 규칙/피드백과 최근 AI 걷기를 대조했다. [양손 걷기 계획서의 대조표](../plans/2026-11-23_양손검_자세안내_걷기보완.md)를 본다.
- 고정 배율/시트/3D 안내는 적용했으나, 최신 양손 결과의 1/60초 접지 발 검사와 별도 무기 레이어는 미완성이다. 발 bbox 바닥을 맞췄다는 사실만으로 접지를 검증했다고 하지 않는다. 프레임 수보다 발 교대/통과/첫-끝 연결과 타이밍을 먼저 확인한다.
- 스미어·히트스톱·베기 궤적은 공격 읽힘에 적용하고, 걷기의 접지 오류를 가리는 해결책으로 쓰지 않는다. 과거 36px 파츠 회전/SD1.5/LoRA 실패 기록도 함께 고려한다.

---

사용자가 "애니메이션 만들 때 참고할 사이트나 어떻게 만들면 좋을지" 알려 준 글을 날짜순으로 모은다(2026-11-20 정리).
새 자료를 받으면 여기에 덧붙이고, 도구·사이트 링크는 [USEFUL_TOOLS.md](USEFUL_TOOLS.md)에도 한 줄씩 넣는다.
우리가 정한 규칙은 [MOTION_RULES.md](../planning/MOTION_RULES.md), Claude가 조사한 기법은 [MOTION_FEW_SPRITES_2026-11-19.md](../planning/MOTION_FEW_SPRITES_2026-11-19.md), 3D→도트 기법은 [공부 노트 05](../study/05_3D를_도트로.md).

---

## 1. AI 스프라이트의 일관성 문제 해결법 (2026-11-11, Gemini 답변)

질문: AI로 스프라이트를 만드는데 매번 일정하게 나와야 하는데 잘 안 된다.

1. **스켈레탈(파츠 분할) 방식, 가장 권장:** 마음에 드는 캐릭터 그림 1장을 머리·몸통·팔·다리·무기로 잘라 Spine 2D나 Unity 2D Animation으로 뼈대를 심어 움직인다. 캐릭터가 변하지 않는다.
2. **한 장 안에 스프라이트 시트 전체를 생성:** 동작을 따로 뽑지 말고 한 번에 여러 프레임을 한 캔버스에. 예: `2D pixel art sprite sheet of [캐릭터], walking animation sequence, 6 frames, aligned in a row, same character, consistent design`
3. **레퍼런스·시드 고정:** Midjourney `--cref [원본] --cw 100`, Stable Diffusion은 시드 고정 + ControlNet(OpenPose)으로 포즈만 바꾸기.
4. **픽셀 후보정:** 외곽선 굵기·픽셀 크기·색은 사람이 다듬는다. 팔레트 8~16색을 정해 인덱스 색으로 덮어 맞춘다.

우리가 한 것: 1번 → 동작 만들기 사이트(`tools/animator`, 조각 돌리기)를 만들었지만 36px에서는 팔이 2~3px라 깨짐("퀄리티가 너무 구림"). 3번 → SD1.5 + ControlNet(`tools/ai/redraw_pose.py`), LoRA(`lora_pose.py`)는 자세를 잘못 읽음. 4번 → 팔레트 맞추기는 모든 도구에 들어감(서 있기 그림의 색으로 스냅, `repaint.py` 색 단계).

## 2. AI 기반 제작 방식 4가지와 실전 순서 (2026-11-19)

| 방식 | 특징 | 추천 장르 | 도구 |
|---|---|---|---|
| 스프라이트 시트 생성 | 프레임마다 그림을 생성해 이어 붙임 | 픽셀 아트, 레트로, 타격감 액션 | PixelLab, Scenario, Midjourney + Aseprite |
| 프레임 보간 | 시작·끝 키프레임만 그리고 AI가 중간을 만듦 | 수작업 2D 액션 | EbSynth, Cascadeur, DAIN-App |
| 3D 모션 → 2D 변환 | 3D 캐릭터에 모션을 입혀 2D 셰이딩·픽셀화 렌더링 | 역동적 액션, 8방향 캐릭터 | Mixamo + Blender(툰 셰이더), DeepMotion |
| 파츠 분리 + 스켈레톤 | 팔·다리·몸통을 분리해 뼈대로 제어 | 모바일 RPG, 대기 동작 | Spine 2D, Live2D |

실전 순서(스프라이트 시트 기준): ① 기준 캐릭터(컨셉 시트) 만들고 화풍 고정, Scenario 같은 툴로 화풍을 LoRA 학습 ② PixelLab 등으로 동작 프레임 생성 ③ 배경 투명화, **발 위치(피벗)를 프레임마다 같은 좌표로 정렬** ④ 시트와 좌표(JSON/Atlas)로 묶어 엔진에서 재생.

핵심 팁: 피벗을 고정하지 않으면 캐릭터가 덜덜 떨림. **2D 연속 동작에 한계가 느껴지면 Mixamo 3D 모델·동작을 Blender에서 픽셀화 렌더링하는 게 더 빠르고 일관적.** ControlNet OpenPose로 팔다리 뒤틀림 줄이기.

우리가 한 것: LoRA(무료, 내 컴퓨터)는 실패. 3D 모션 → 2D가 지금 방향(MPFB 주인공 + Mixamo 동작 + Blender, `tools/blender/mpfb_pose.py`). 발 위치 고정은 카메라를 동작 내내 하나로 두는 방식으로 함.

## 3. 도구 저장소 8개 (2026-11-20)

2dimg2motion, sprite-gen, pixelfx, PixelOE, Agent Sprite Forge, Codixel, Pixelbolt, Sprite Sheet Diffusion. 각각의 무료 여부·라이선스·쓰임은 [USEFUL_TOOLS.md](USEFUL_TOOLS.md). Sprite Sheet Diffusion은 시험했지만 자세 모듈이 공개되지 않아 실패.

## 4. 2D 게임 애니메이션 5대 제작 파이프라인과 실행 지침 (2026-11-20)

애니메이션을 만들기 전에 **먼저 로컬 환경(설치된 스킬, Python/Node 패키지, GPU)을 점검**하고, 아래 5가지 중 화풍과 목적에 맞는 조합을 추천해 승인받은 뒤 실행한다.

| 방식 | 적합 | 작동 |
|---|---|---|
| 1. 절차적·설계도 코드 렌더링 (Pixelbolt, Codixel) | 16~64px 픽셀 아트, 엄격한 프레임 일관성, Git 관리 | JSON 설계도나 관절 코드로 직접 렌더링, AI 형태 변형 없음 |
| 2. 코드 기반 VFX (pixelfx) | 타격·검기·폭발·마법·먼지 등 모든 이펙트 (화풍 불문 권장) | 244종 프리셋을 고쳐 투명 PNG 시트 + 아틀라스 JSON |
| 3. 생성형 AI + 도트 후처리 (Agent Sprite Forge, Sprite Sheet Diffusion, 2dimg2motion + PixelOE) | 기준 원화로 역동적인 픽셀 동작 | 생성 뒤 반드시 PixelOE로 윤곽 보정, 발바닥 Y(피벗) 정렬 |
| 4. AI 비디오 추출·프레임 보간 (sprite-gen, EbSynth, Cascadeur) | 고해상도 일러스트·카툰, AI 영상(Kling, Runway)의 부드러운 움직임 | 영상에서 키프레임 추출, 시작·끝 그림 사이 보간 |
| 5. 3D 모션 → 2D 셰이딩 (Blender CLI + Mixamo) | 8방향 쿼터뷰, 격렬한 검술·체술 등 2D AI가 형태를 못 지키는 액션 | 3D 모델과 모션에 툰 셰이더·픽셀화 컴포지팅, 스프라이트 시트로 렌더링 |

원칙: 추천 전에 반드시 환경을 확인한다. 한 방식만 고집하지 말고 **[캐릭터 본체: 방식 1 또는 5] + [타격 이펙트: 방식 2]** 같은 조합을 제안한다.
실행 규칙: **대기(Idle) 1개 동작만 먼저** 렌더해 미리보기로 확인한 뒤 다음 동작으로. 결과물은 투명 PNG + 아틀라스 JSON, 프레임 간 **바닥선(Y 앵커)을 1px 오차 없이** 통일.

우리가 한 것: 환경 점검(RTX 5060 8GB, Blender 5.2, Node 24) → 본체 = 방식 5, 이펙트 = 방식 2를 추천해 승인. 서 있기 먼저 → 3D 몸이 주인공과 달라 MPFB2로 새 모델 → 부위별 색으로 도트(`repaint.py`) → 바닥선 맞춤 → Mixamo 휘두르기 10장. 방식 1의 캐릭터 그리기는 "드로잉하지 마라"에 따라 쓰지 않음. pixelfx(방식 2)는 아직.

## 5. 그 밖에 짧게 준 방향

- 2026-11-19 "스프라이트를 최소화해서 모션을 만드는 기법, 임팩트 효과로 가리기, 조사해 봐" → [MOTION_FEW_SPRITES](../planning/MOTION_FEW_SPRITES_2026-11-19.md) → [MOTION_RULES](../planning/MOTION_RULES.md).
- 2026-11-20 "도트로 바꿀 때는 시중 그림을 보고 학습해서 더 퀄리티 높게" → [공부 노트 05](../study/05_3D를_도트로.md).
- 2026-11-20 3D에서 중요한 것: 실루엣, 부위 나눔, 비율, 동작(옷 세부는 상관없음) → 기준 모델을 이 네 가지로 점검(`docs/planning/hero3d_model_board.png`).
