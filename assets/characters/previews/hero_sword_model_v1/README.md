# 검 주인공 — 3D→도트 첫 제작

2026-11-23. 기준 시안은 `assets/characters/concepts/hero_codex_v1/hero_concept_v4_sword.png`.

## 이번 결과

- 기존 MPFB 리깅 모델을 보존하고 별도 복사본에서 작업했다. 체형 폭 1.16배, 머리 배율 1.18, 황토색 재킷·어두운 안옷·어깨 보강·주머니, 작은 배낭·왼팔 천·검을 구성했다. 두루마리는 없다.
- 기존 스웨터 메시의 앞을 열고 소매를 조정한 재킷 해석이며, 승인 시안의 주름·주머니·얼굴과 완벽히 같은 모델이 아니다. 재킷 실루엣과 얼굴 표현은 후속 보완 여지가 있다.
- 남동 대기/숨쉬기 두 프레임만 제작. 앞/뒤 큰 렌더는 3D 구조 확인용이며 8방향 스프라이트 완성을 의미하지 않는다.
- 같은 카메라에서 몸만 / 검 포함 ID·light 패스를 렌더하고, 고정 색 램프와 외곽선으로 도트 처리했다. 프레임별 자동 크기 맞춤은 하지 않았다.

## 파일

| 파일 | 의미 |
|---|---|
| `comparison.png` | 콘셉트·3D 앞/뒤·기존/새 도트 비교 |
| `game_preview.png` | 게임 배경에서 새 외형의 크기·색 확인. 이 캡처 프로세스에서만 draw를 임시 교체했으며 실제 게임 자산은 교체하지 않음 |
| `idle_preview.gif` | 두 대기 프레임을 600ms 간격으로 보는 확대 미리보기 |
| `body/Idle/rotations/south-east.png`, `body/Breath/south-east/0.png`, `1.png` | 무기가 없는 몸. 64×64 RGBA |
| `held/...` | 검까지 3D에서 함께 렌더한 시각 확인용. 몸과 검의 게임 연결을 완료한 파일이 아님 |
| `body/hands.json`, `held/hands.json` | Blender에서 투영한 손잡이 좌표 |
| `body/pivot.json`, `held/pivot.json`, `renders/anchors.json` | 고정 지면 피벗과 손잡이·검끝 위치. 기존 로더는 이 새 pivot.json을 자동 사용하지 않음 |
| `validation.json` | 프레임 크기·불투명 경계·색 수·기준점 검사 결과 |
| `renders/` | ID·light 패스, 큰 3D 앞/뒤 이미지, 최신 카메라 보정 기록 |
| `intermediate_relative_path_run/` | 첫 렌더의 경로 처리 문제 때 생긴 중간 출력 보관. 최종 결과로 사용하지 않음 |

최종 모델은 `assets/source3d/scenes/hero_sword_v1/hero_sword_v6.blend`. 앞선 모델 파일은 이번 작업 중간 버전이며, 기존 원본 `C:/Users/doboh/busan_ai/mpfb/busan_hero.blend`는 변경하지 않았다. 새 애드온·외부 에셋·모델은 다운로드하지 않았다.

## 확인 결과

- 몸 두 프레임 모두 64×64 RGBA, bbox `(26,17,40,53)`, 실제 높이 **36px**, 발끝 행 동일.
- 검 포함 두 프레임도 실제 높이 36px, 캔버스 가장자리 접촉 없음. 몸/검 포함 총 4장 모두 잘림 경고 없음.
- 몸은 17~20색, 검 포함은 20~23색(불투명 픽셀 기준). 색 램프는 `production_v1.json`에 고정했으며 장면의 빛에 따라 실제 등장 색 수는 달라진다.
- 게임 배경 캡처 정상. 검 공격·이동·다른 방향·충돌 판정은 이번에 검증한 범위가 아니다.
- 작은 검이 끊기거나 어둡게 읽히는 문제를 줄이려고 칼날 폭과 방향을 조정했다. ID 패스에서는 그림자를 꺼 부위가 다른 팔레트로 잘못 분류되지 않게 했다.

## 재현

제작 사양: `assets/characters/concepts/hero_codex_v1/production_v1.json`.

Blender: `tools/blender/hero_sword_preview.py`에 `--spec`, `--model-out`, `--out`, `--anim` 전달. 원본 MPFB .blend를 Blender의 `-b` 입력으로 사용한다. `--model-out`은 기존 파일을 보호하므로 다시 실행할 때 새 파일명을 지정한다. 출력 경로는 저장 전에 절대경로로 고정한다.

정리·검수·미리보기:

```powershell
.\.venv\Scripts\python.exe -B -X utf8 tools\sprites\hero_sword_preview.py --out assets/characters/previews/hero_sword_model_v1 --capture-game
```

## 다음 단계

이 외형의 재킷·배낭·얼굴과 검 가독성을 먼저 확인한 뒤 준비·타격·회복 한 방향 제작으로 넘어간다. 이번 패키지를 기존 hero_3d 폴더에 복사하거나 게임 기본값으로 설정하지 않는다.
