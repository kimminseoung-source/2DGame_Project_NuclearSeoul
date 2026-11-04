# 게임 리소스

실제 게임용 스프라이트·타일·음원을 배치할 위치입니다. 발표용 콘셉트 이미지는 docs/references에 보관합니다. 사용 리소스의 출처와 이용 조건을 함께 기록합니다.

## 방공호와 주인공

두 파일은 내장 이미지 생성 도구로 제작했습니다.

- `shelter.png`는 시작 방공호의 배경입니다.
- `survivor_walk.png`는 주인공의 대기 및 걷기 스프라이트입니다. 위에서부터 정면, 왼쪽, 오른쪽, 뒷모습 순서입니다.

### 방공호 생성 프롬프트

Create a landscape 3:2 game-ready background texture for a dark 2D top-down pixel art Korean post-nuclear underground shelter. It is a single playable rectangular room seen from straight overhead, with only very shallow top wall front faces, no isometric diagonal perspective. Show the entire square-cornered room from edge to edge. A dark charcoal concrete border occupies outer 10% on each edge. Keep the center large flat open slate floor navigable. Clusters of bunks and storage shelves occupy ONLY the upper-left and upper-right corners along the top wall, a few muted amber wall lamps. One closed bunker door centered in right wall with tiny green light. Floor uses sharp crisp blocky pixel texture and subtle scuffing. Palette charcoal blue-gray, desaturated amber glow, dark grungy nuclear Seoul style with good floor readability. Professional indie game background, no HUD, no text, no actors, no perspective vanishing point, no supply crates in central floor. Stable flat top-down view for sprite compositing.

### 주인공 생성 프롬프트

Create a transparent PNG sprite sheet for one identical Korean post-apocalyptic survivor in a yellow ochre hooded jacket, charcoal pants, chunky boots, dark respirator gas mask, teal tinted visor and compact backpack. True crisp pixel art, no outline glow, black charcoal outline and limited palette. Strict mechanically regular 4 columns by 4 rows across a square canvas. Each of the 16 identical-size cells contains ONE entire equally scaled sprite, centered in cell with a large transparent margin on all sides and consistent feet baseline. Rows from top to bottom: facing DOWN toward viewer, facing LEFT, facing RIGHT, facing UP away from viewer. Columns left to right: neutral standing idle, walk with left foot forward, walk passing pose, walk with right foot forward. Every image faces its row direction, all 16 frames share silhouette scale, colors, outfit. Strict positions centered at 12.5%, 37.5%, 62.5%, 87.5% on each axis. No labels, borders, grid lines, shadows, background objects or text. Transparent background. 2D top-down adventure character, designed to be legible when rendered 40px tall.
