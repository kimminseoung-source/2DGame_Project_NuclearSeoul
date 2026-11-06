# 주인공 도트 애니메이션 제작 기준

`survivor_walk.png`를 색과 장비의 기준으로 쓴다. 황토색 후드, 청록색 렌즈, 올리브색 배낭, 짙은 회색 장갑·바지·부츠와 어두운 외곽선을 맞춘다. 같은 캐릭터의 동작마다 조명과 색조를 바꾸지 않는다.

| 동작 | 시트 | 한 주기 |
| --- | --- | --- |
| 서 있기 | `survivor_idle_6frames.png` | 1.08초. 두 발을 고정한 채 미세하게 호흡한다. |
| 걷기 | `survivor_walk_classic_6frames.png` | 기본 속도에서 0.48초. 발을 디디고 체중을 옮기는 자세를 반복한다. |
| 조용히 걷기 | `survivor_sneak_classic_6frames.png` | 기본 속도에서 0.60초. 무릎을 굽히고 몸을 앞으로 기울인다. |
| 줍기 | `survivor_pickup_classic_6frames.png` | 0.58초간 한 번 재생한다. 4번째 프레임에서 필터를 획득한다. |

모든 시트는 투명 PNG이며 6열×4행이다. 행 순서는 아래, 왼쪽, 오른쪽, 위다. 대기 칸은 160×224픽셀이고 나머지 동작은 팔과 발을 뻗을 공간을 확보하기 위해 192×224픽셀이다. 게임에서 칸 높이 50픽셀과 바닥 기준점을 공통으로 쓴다. 서기와 걷기는 그림 높이 약 208픽셀, 조용히 걷기는 약 198픽셀을 기준으로 맞췄다. 줍기는 한 방향 안에서 같은 배율로 모든 자세를 배치해 굽히는 깊이를 살렸다.

게임 크기에서 동작을 전환하며 후드와 배낭의 크기, 발 위치, 색 변화, 첫 프레임과 마지막 프레임의 연결을 확인한다. 보행은 발이 교대하도록 프레임을 재배치하고, 정면 잠입과 뒷모습의 일부 프레임은 좌우 반전을 사용했다.

## 이전 동작을 참고한 이미지 생성 요청

내장 imagegen에 기존 `survivor_walk.png`, `survivor_sneak_walk.png`, `survivor_sneak.png`, `survivor_pickup.png`에 해당하는 사용자 첨부 이미지를 동작별로 전달했다.

> Production pixel sprite sheet. Match attached earlier game art exactly, dark charcoal pixel outline and muted ochre hood, teal lenses, dark gray boots and olive backpack, no relighting or proportion changes. Six equally spaced columns and FOUR rows on a landscape canvas, one centered full-body character per cell, ample gutters. Row order DOWN/front, LEFT, RIGHT, UP/back. Each row has the same six sequential poses seen from that direction. Same floor contact line across every frame in each row. PNG transparent alpha outside each character, no cast shadow, gradient, grid, text, props. Exact six columns, exact four rows.

- **걷기** — Rebuild the reference ordinary walking motion. Preserve the original walking silhouettes and alternate legs. Sequence near-foot contact, weight on near foot, passing pose, far-foot contact, weight on far foot, passing pose. Side views must visibly swap the leading boot halfway through.
- **조용히 걷기** — Rebuild the FIRST reference's low cautious gait with the SECOND reference's bent-knee, forward-leaning body, and held-in bent elbows. Keep shoulders forward and hips lowered in ALL six frames. Feet alternate clearly, one leads then the other, with a passing pose between. No kneeling; standing height achieved by pose, no scaling.
- **줍기** — A one-shot ground pickup, not a loop. Exact pose of first reference at frame 4: one knee down and one gloved hand reaching floor. Start upright like second reference at frame 1, frame 2 bend knees and hips, frame 3 lower onto one knee reaching, frame 4 touch the ground, frame 5 rise halfway with closed hand, frame 6 stand upright. Boots fixed and same mask/head size even while lowered. No visible object.

## 대기 이미지 생성에 사용한 요청

내장 imagegen 도구에 `survivor_walk.png`를 참조로 전달했다.

> A production game atlas of the exact same original 2D dark pixel-art Korean survivor in the attached reference. Match the exact ochre hood, teal visor, olive backpack, charcoal pants and boots, Korean arm patch, thick dark outlines, same head/body proportions, scale, colors, camera and dot size. Single perfectly regular grid of SIX columns and FOUR rows, full figure centered in each cell with roomy transparent gutters. Rows in exact order top to bottom: facing down/front, facing left, facing right, facing up/back. Same direction across each row. Exactly six distinct frames across every row, chronological seamless loop. Keep bottom of supporting foot consistent. Transparent PNG, no grid, text, shadow, or props.

- **서 있기** — Idle breathing. Both boots planted and hands relaxed in all six frames; tiny rhythmic shoulder rise and return. No steps.
- **걷기** — Ordinary walk, left contact, left load, left passing, right contact, right load, right passing. Clearly alternate boots.
- **조용히 걷기** — Cautious walk, slightly flexed knees and leaning torso, never kneeling. Left contact, left load, left passing, right contact, right load, right passing. Keep head, boots and equipment physically the same size as reference; lower head only slightly through pose.
