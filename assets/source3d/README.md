# 3D 원본 (캐릭터 렌더용)

캐릭터 스프라이트를 만드는 데 쓰는 3D 원본을 두는 곳이다. 게임 실행에는 필요 없고(게임은 렌더된 PNG 시트만 읽는다), 용량이 커서(기본 캐릭터 압축 파일 129MB, GitHub 파일 한도 100MB 초과) **이 README만 저장소에 올린다.** 같은 파일이 필요하면 아래 주소에서 무료로 다시 받아 같은 폴더 구조로 푼다. 작업 방법은 [캐릭터 제작 작업 기준](../characters/CHARACTER_WORKFLOW.md)을 따른다.

| 폴더 | 내용 | 출처 | 라이선스 | 받은 날 |
| --- | --- | --- | --- | --- |
| `quaternius_base_characters/` | Universal Base Characters [Standard] — 리깅된 기본 몸(무료판은 Superhero 남·여), 머리 모양 | [quaternius.itch.io/universal-base-characters](https://quaternius.itch.io/universal-base-characters) (Quaternius) | CC0 1.0 (`License_Standard.txt`) | 2026-11-10 |
| `quaternius_animation_library/` | Universal Animation Library [Standard] — 동작 43종(대기·걷기·웅크려 걷기·칼 공격·피격·쓰러짐·줍기 등) | [quaternius.itch.io/universal-animation-library](https://quaternius.itch.io/universal-animation-library) (Quaternius) | CC0 1.0 (`License.txt`) | 2026-11-10 |
| `quaternius_animation_library_2/` | Universal Animation Library 2 [Standard] — 근접 공격(칼 베기·훅·나무 베기), 좀비 걷기·할퀴기, 밀려남 등. 1팩과 같은 뼈대 | [opengameart.org/content/universal-animation-library-2](https://opengameart.org/content/universal-animation-library-2) (Quaternius) | CC0 1.0 (`License.txt`) | 2026-11-11 |
| `mixamo/` | Mixamo(Adobe) 캐릭터 **Alex**(`Alex.fbx`, 옷·피부 포함 T자 자세)와 동작 7개(`Breathing_Idle`, `Walking`(제자리), `Crouch_Walk_Forward`(제자리), `Melee_Attack_Horizontal`(도끼 수평 휘두르기 → 방망이 공격), `Hit_Reaction`, `Death_Backward`(Standing React Death Backward), `Picking_Up`(한 손 줍기)). 동작은 피부 없이 30fps. `textures/Alex_diffuse.png`는 FBX에 묶인 텍스처를 꺼낸 것 | [mixamo.com](https://www.mixamo.com) (Adobe, 무료 계정으로 내려받음) | Mixamo 이용 조건: 개인·상업 게임에 무료로 쓸 수 있음. 원본 파일 자체를 재배포하지 않음(그래서 저장소에 올리지 않음) | 2026-11-11 |
| `_downloads/` | 위 팩들의 원본 압축 파일 | 같음 | 같음 | 2026-11-10 ~ 11 |

- 기본 몸 파일: `quaternius_base_characters/Base Characters/Godot - UE/Superhero_Male_FullBody.gltf`
- 동작 파일: `quaternius_animation_library/Unreal-Godot/UAL1_Standard.glb` (루트 모션 없는 판. `_RM`은 루트 모션 포함판)
- 동작 파일 2: `quaternius_animation_library_2/Unreal-Godot/UAL2_Standard.glb`
- 세 팩은 같은 뼈 이름을 써서, 동작을 기본 몸에 그대로 붙일 수 있다.