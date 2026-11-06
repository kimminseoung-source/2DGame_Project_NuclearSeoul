# 주인공 도트 애니메이션 제작 기준

색과 장비의 기준은 `survivor_walk.png`다. 황토색 후드, 청록색 렌즈, 올리브색 배낭, 짙은 회색 장갑·바지·부츠, 어두운 외곽선을 맞춘다. 동작이 바뀔 때 조명이나 색조를 따로 적용하면 같은 장비도 다른 색으로 보이므로 한 팔레트와 카메라 각도를 쓴다.

## 게임에서 쓰는 시트

- `survivor_walk_8frames.png`는 일반 걷기와 조용히 걷기가 함께 쓰는 투명 PNG다. 위에서부터 아래, 왼쪽, 오른쪽, 위 방향이며 한 줄마다 이동 프레임 8장이 있다.
- 칸은 144×204픽셀이다. 각 프레임의 바닥 기준점은 칸 아래쪽에 맞추고, 캐릭터 중심이 프레임마다 좌우로 튀지 않게 후드 중심을 기준으로 배치한다.
- 한 주기는 왼발 닿기 → 체중 싣기 → 오른발 통과 → 오른발 내밀기 → 오른발 닿기 → 체중 싣기 → 왼발 통과 → 왼발 내밀기다. 중간 자세의 다리와 팔 위치가 앞뒤 프레임과 구분되는지 확인한다.
- 일반 걷기는 0.48초, 조용히 걷기는 0.60초에 한 주기를 재생한다. 조용히 걷기는 같은 프레임을 더 낮고 느리게 재생한다. 이동 중 Shift를 눌러도 발걸음 순서는 이어진다.
- 대기 자세는 `survivor_walk.png`의 각 행 첫 칸을 쓴다. 줍기 자세는 `survivor_pickup.png`를 쓴다.

## 이미지 생성에 사용한 요청

내장 이미지 생성 도구에 `survivor_walk.png`를 참조로 전달했다.

> Create a production 2D pixel-art sprite atlas for the exact original gas-mask survivor in the reference image. Treat that sheet as the source of truth for colors, dark outlines, dot density, camera angle and scale, ochre hood, dim blue-green visor, olive backpack, charcoal boots and small Korean patch. Build exactly FOUR rows by EIGHT columns, regular 8x4 grid across a landscape transparent canvas, centered sprite per cell with ample even gutters. Rows from top: facing down toward viewer, left, right, up away from viewer. EVERY row is one uninterrupted 8-frame in-place walking cycle: 1 left heel contact, 2 left weight acceptance, 3 right foot passes left, 4 right foot swings forward, 5 right heel contact, 6 right weight acceptance, 7 left foot passes right, 8 left foot swings forward. Distinct leg position changes in all 8 frames including front/back. Hips roughly fixed horizontally; consistent floor baseline, silhouette proportions, wardrobe, highlights and palette. Use compact dark pixel-art rendering with muted colors identical to reference, no labels, grid, lighting effects, cast shadow, objects or background. Do not make a 3D render. Preserve alpha. Sprite atlas for runtime cropping, prioritize the exact 8 columns and 4 rows.

완성 후 방공호에서 네 방향을 걸어보고, 이동 키를 누른 채 Shift를 눌렀다 놓는다. 후드와 장비 색, 발 위치, 동작의 이어짐을 실제 게임 크기로 확인한다.
