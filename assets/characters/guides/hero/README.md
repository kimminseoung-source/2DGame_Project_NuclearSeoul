# 주인공 자세 안내 그림 (Gemini로 한 칸씩 고쳐 그리기)

작성 2026-11-11. 사용자 지시 "만들어 줘"(시안 스프라이트를 기준으로 한 칸씩 고쳐 그리는 방법). 만드는 도구: `tools/blender/pose_frames.py`(Mixamo 동작 → 회색 인형 한 장씩, 방망이·배낭 포함, 마젠타 배경).

## 받는 방법
1. Gemini 웹(gemini.google.com)에 **두 장을 첨부**한다: ① 시안 `assets/characters/concepts/hero_concept_a.webp` ② 아래 표의 안내 그림.
2. 공통 문안 + 그 칸의 한 줄을 넣는다.
3. 받은 그림을 `assets/characters/concepts/frames/<안내 그림과 같은 이름>.png`로 저장한다(예: `walk_1.png`). Claude가 배경 제거·팔레트 고정·크기·발 위치를 맞춘다.

## 공통 문안
```text
Image 1 is my game character. Image 2 is a pose reference (a grey mannequin holding a bat).
Redraw the character from image 1 in EXACTLY the pose of image 2.
Keep EVERYTHING else identical to image 1: face, hair, mustard-yellow hooded jacket (hood down), olive backpack, dark grey cargo trousers, black gloves, dark boots, wooden baseball bat, pixel size, palette, 1-pixel dark outline, character size.
Side view facing RIGHT, full body. Plain solid flat magenta background (#FF00FF). No text, no shadow, no ground.
Only the pose changes.
```

## 칸별 안내 그림과 한 줄
| 안내 그림 | 동작 | 덧붙일 한 줄 |
| --- | --- | --- |
| `idle_1.png` | 서 있기 1 | Relaxed standing, breathing in. |
| `idle_2.png` | 서 있기 2 | Relaxed standing, breathing out, shoulders 1 pixel lower. |
| `walk_1.png` | 걷기 1 | Walking: right leg forward touching the ground, left leg behind. |
| `walk_2.png` | 걷기 2 | Walking: legs passing under the body. |
| `walk_3.png` | 걷기 3 | Walking: left leg forward touching the ground, right leg behind. |
| `walk_4.png` | 걷기 4 | Walking: legs passing under the body, the other way. |
| `swing_1.png` | 공격 1 | Bat swing wind-up: the bat raised high behind the head, body twisted back. |
| `swing_2.png` | 공격 2 | Bat swing impact: the bat swung horizontally in front at chest height. |
| `swing_3.png` | 공격 3 | Bat swing follow-through: the bat carried past the body, arms extended. |
| `sneak_1.png` ~ `sneak_4.png` | 은신 1~4 | Sneaking: knees bent, body low and leaning forward, careful steps. |
| `hurt_1.png` | 피격 | Hit reaction: body jerks back, face in pain. |
| `down_1.png` | 쓰러짐 1 | Falling backwards. |
| `down_2.png` | 쓰러짐 2 | Lying on the back on the ground, head to the left, bat dropped beside. |

전체 미리보기: `_all_guides_small.png`.
