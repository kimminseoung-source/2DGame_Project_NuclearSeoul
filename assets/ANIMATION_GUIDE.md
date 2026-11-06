# 주인공 도트 애니메이션 제작 기준

`survivor_walk.png`를 색과 장비의 기준으로 쓴다. 황토색 후드, 청록색 렌즈, 올리브색 배낭, 짙은 회색 장갑·바지·부츠와 어두운 외곽선을 맞춘다. 같은 캐릭터의 동작마다 조명과 색조를 바꾸지 않는다.

| 동작 | 시트 | 한 주기 |
| --- | --- | --- |
| 서 있기 | `survivor_idle_6frames.png` | 1.08초. 두 발을 고정한 채 미세하게 호흡한다. |
| 걷기 | `survivor_walk_6frames.png` | 0.48초. 두 발을 번갈아 내딛는다. |
| 조용히 걷기 | `survivor_sneak_6frames.png` | 0.60초. 무릎을 조금 굽히고 몸을 기울인다. |

세 시트 모두 투명 PNG이며 160×224픽셀 칸을 6열×4행으로 배치한다. 행 순서는 아래, 왼쪽, 오른쪽, 위다. 각 칸은 게임에서 36×50 크기로 그리고, 발이 닿는 바닥을 같은 위치에 둔다. 서기와 걷기의 그림 높이는 208픽셀이다. 조용히 걷기는 몸을 낮춘 자세를 살려 200픽셀에 맞춘다. 이동 중 Shift를 눌러도 걷기 주기의 위치는 이어진다.

게임 크기에서 동작을 전환하며 후드와 배낭의 크기, 발 위치, 색 변화, 첫 프레임과 마지막 프레임의 연결을 확인한다. 줍기는 `survivor_pickup.png`의 전용 자세를 쓴다.

## 이미지 생성에 사용한 요청

내장 imagegen 도구에 `survivor_walk.png`를 참조로 전달했다.

> A production game atlas of the exact same original 2D dark pixel-art Korean survivor in the attached reference. Match the exact ochre hood, teal visor, olive backpack, charcoal pants and boots, Korean arm patch, thick dark outlines, same head/body proportions, scale, colors, camera and dot size. Single perfectly regular grid of SIX columns and FOUR rows, full figure centered in each cell with roomy transparent gutters. Rows in exact order top to bottom: facing down/front, facing left, facing right, facing up/back. Same direction across each row. Exactly six distinct frames across every row, chronological seamless loop. Keep bottom of supporting foot consistent. Transparent PNG, no grid, text, shadow, or props.

- **서 있기** — Idle breathing. Both boots planted and hands relaxed in all six frames; tiny rhythmic shoulder rise and return. No steps.
- **걷기** — Ordinary walk, left contact, left load, left passing, right contact, right load, right passing. Clearly alternate boots.
- **조용히 걷기** — Cautious walk, slightly flexed knees and leaning torso, never kneeling. Left contact, left load, left passing, right contact, right load, right passing. Keep head, boots and equipment physically the same size as reference; lower head only slightly through pose.
