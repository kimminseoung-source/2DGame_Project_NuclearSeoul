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

## 주인공 줍기 자세

`survivor_pickup.png`는 기존 걷기 스프라이트를 참고해 내장 이미지 생성 도구로 만든 네 방향 줍기 자세입니다.

### 생성 프롬프트

Make a NEW transparent 2D pixel-art gameplay sprite sheet referencing the identical survivor and pixel style in the supplied walking sheet. Keep exactly the same yellow ochre hood, teal visor gas mask, charcoal pants, boots and compact backpack. Output a SQUARE sheet with FOUR equally sized quadrants in a 2 by 2 grid. Each quadrant contains exactly ONE distinct frame of the SAME CHARACTER in a LOW CROUCH, one knee bent, reaching one gloved hand DOWN TOWARD THE FLOOR to pick up an invisible item. Top left: facing camera DOWN. Top right: facing LEFT. Bottom left: facing RIGHT. Bottom right: facing UP away from viewer. Very clear lowered knees and torso and hand near floor. All full-body figures centered, aligned scale, completely isolated with large transparent margins, no overlap. Cropped figure height about 3/4 of the reference character height relative to figure width. Crisp retro pixel edges, limited palette. No background, no loot item, no grid lines, no labels, no glow, no floor, no shadows. Original walking sprites are only appearance reference; use the new pickup pose in every quadrant.

## 주인공 조용히 걷기 자세

`survivor_sneak.png`는 기존 걷기 스프라이트를 참고해 내장 이미지 생성 도구로 만든 네 방향 자세입니다.

### 생성 프롬프트

Create a transparent square 2 by 2 pixel art sprite sheet, exactly four distinct low crouch-stealth-walking frames of the SAME yellow ochre hooded survivor in the attached walk sheet. Match gas mask, teal visor, charcoal trousers, backpack, colors and pixel density. Top left facing DOWN toward viewer, top right LEFT, bottom left RIGHT, bottom right UP away from viewer. Each is crouched with knees bent, torso lowered, alert forward lean, one foot stepping slowly, hands near chest, no reaching for ground. Exactly one entire figure centered in each quadrant with spacious transparent padding, feet baseline consistent within each row. Sharp retro pixels, no text, no grid, no shadow, no props. Gameplay sprites suitable for 36px height.

## 조용히 걷기 애니메이션

`survivor_sneak_walk.png`는 기존 주인공 자세를 참고해 내장 이미지 생성 도구로 만든 네 방향 걷기 시트입니다.

### 생성 프롬프트

Make a transparent square 4x4 pixel-art gameplay sprite sheet. Same ochre hood, gas mask with teal visor, backpack and charcoal trousers as references. NEW motion: cautious stealth WALK, both knees only slightly flexed, crouch just a little, torso leaning slightly forward, BOTH feet under body when idle. Never kneeling or squatting; keep knees above boots and off ground. Four rows down-facing, left-facing, right-facing, up-facing. Exactly 4 columns in each row: col1 idle standing in slight crouch, col2 long step with LEFT leg forward and RIGHT leg behind, col3 unmistakable long step with RIGHT leg forward and LEFT leg behind, col4 passing feet together. Make column 2 vs 3 meaningfully different: show alternating arms and changing pants folds and boot positions, in side view visibly swap which leg is foremost; in front/back make left boot visibly extended in one and right boot in the other. Whole character same scale and consistent floor baseline. One sprite centered per equal cell, ample transparent gutters, no shadows, captions, borders or objects, crisp retro pixel edges. Same body proportions and pixel density as walking reference. 16 full-body sprites.
