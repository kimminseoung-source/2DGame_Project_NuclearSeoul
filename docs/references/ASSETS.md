# 자료 및 출처

## 콘셉트

`survival_view_comparison.png`: 이 프로젝트 기획 대화에서 내장 AI 이미지 생성 도구로 제작한 콘셉트 이미지. 선택한 화면은 왼쪽 탑뷰이며 오른쪽은 비교 시안입니다. 실제 게임 스크린샷이나 게임용 스프라이트가 아닙니다. 이미지 내 상점 간판은 구현 시 창작 디자인으로 교체합니다.

- `assets/characters/concepts/hero_concept_a.webp`: 2026-11-11 사용자가 Google Gemini 웹사이트(gemini.google.com)에서 생성한 주인공 콘셉트 이미지. 요청 문안은 `tools/gen/prompts/hero_a.txt`, 참고 이미지는 이 게임의 거리 배경. 오른쪽 아래 Gemini 표시는 정리 과정에서 지웠다. 게임용 스프라이트는 이 이미지를 정리한 `hero_concept_a_sprite.png`.

- Mixamo(Adobe), 캐릭터 Alex와 동작 Breathing Idle, Walking, Crouch Walk Forward, Standing Melee Attack Horizontal, Hit Reaction, Standing React Death Backward, Picking Up Object, https://www.mixamo.com . 2026-11-11 무료 계정으로 내려받음. 주인공 3D 바탕과 동작으로 사용하고, 시안 색으로 다시 칠해 도트 스프라이트로 렌더함. 원본 파일은 저장소에 올리지 않음.

## 사실 확인 참고

- CDC Radiation Safety: https://www.cdc.gov/radiation-health/safety/index.html
- CDC Radiation Emergencies: https://www.cdc.gov/radiation-emergencies/response/index.html
- CDC NIOSH 호흡 장비: https://www.cdc.gov/niosh/ppe/respirators/asr.html

방호복과 호흡 보호구는 모든 외부 방사선을 막지 않습니다. 보호 장비의 한계와 정보 확인을 반영합니다. 이동 경로·적·게이지·체력은 게임의 가상 규칙입니다.

향후 추가하는 이미지·음원은 파일별 제작자·출처·이용 조건을 이 문서에 기록합니다.

## 캐릭터 3D 원본 (2026-11-10)

- Quaternius, Universal Base Characters [Standard], https://quaternius.itch.io/universal-base-characters , CC0 1.0. 기본 몸으로 사용.
- Quaternius, Universal Animation Library [Standard], https://quaternius.itch.io/universal-animation-library , CC0 1.0. 대기·걷기·웅크려 걷기·공격·피격·쓰러짐·줍기 동작으로 사용.
- Quaternius, Universal Animation Library 2 [Standard], https://opengameart.org/content/universal-animation-library-2 , CC0 1.0. 휘두르기(나무 베기 동작) 등으로 사용.
- 이 3D 원본을 Blender로 렌더해 만든 스프라이트 시트는 `assets/characters/` 아래에 있다. 원본 목록과 받는 방법은 `assets/source3d/README.md`.
