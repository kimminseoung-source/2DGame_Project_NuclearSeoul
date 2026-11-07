# 주인공 도트 애니메이션 제작 기준

현재 게임에서는 초기 도트 버전을 사용한다. 색과 장비는 황토색 후드, 청록색 렌즈, 올리브색 배낭, 짙은 회색 바지·장갑·부츠와 어두운 외곽선을 기준으로 맞춘다.

| 동작 | 게임에서 쓰는 시트 | 기본 재생 방식 |
| --- | --- | --- |
| 서기와 걷기 | [기존 걷기 시트](survivor_walk.png) | 첫 칸은 대기 자세다. 이동은 네 단계, 한 주기 0.48초다. |
| 조용히 걷기 | [초기 조용히 걷기 시트](survivor_sneak_walk.png) | 상체를 앞으로 기울인 채 디딤과 두 발이 가까워지는 중간 자세를 번갈아 재생한다. 이동은 네 단계, 한 주기 0.60초다. |
| 줍기 | [기존 줍기 시트](survivor_pickup.png) | 한 방향당 몸을 낮춘 자세 한 장을 사용한다. 시작 후 0.28초에 필터를 획득한다. |

걷기와 조용히 걷기의 행 순서는 아래, 왼쪽, 오른쪽, 위다. 게임의 이동 속도 설정에 따라 두 이동 동작의 재생 속도도 달라진다. 줍기 재생 시간은 0.58초다.

조용히 걷기는 게임에서 46픽셀 높이로 그린다. 일반 걷기와 같은 바닥 기준점에 발을 맞추고 Shift 전환 시 발걸음 주기에서 현재 위치를 이어받는다.

새 동작을 만들 때는 이 시트를 참조 이미지로 사용한다. 실제 게임 크기에서 원본과 비교해 장비 색과 크기, 발이 닿는 위치, 첫 프레임과 마지막 프레임 사이의 이어짐을 확인한다. 공통 제작 양식은 [도트 리소스 제작 가이드](ART_GUIDE.md)를 따른다.

## 대각선 네 방향

`survivor_diagonal_walk.png`, `survivor_diagonal_sneak.png`, `survivor_diagonal_pickup.png`는 초기 도트 원본을 참조해 내장 imagegen으로 제작했다. 칸은 192×248픽셀이고, 행 순서는 좌하·우하·좌상·우상이다. 걷기와 조용히 걷기는 방향당 대기 자세와 이동 자세를 포함한 네 칸, 줍기는 방향당 한 칸이다.

방향 0~3은 기존 아래·왼쪽·오른쪽·위이고, 4~7은 좌하·우하·좌상·우상이다. 대각선에서도 이동 벡터 길이를 나눠 직선과 같은 이동 속도를 유지한다. 멈춘 뒤와 줍는 동안 마지막으로 바라보던 방향을 유지한다. 원본과 같은 높이 배율과 발 기준점으로 그리고, 대각선의 넓은 실루엣을 수용할 수 있도록 칸 너비를 늘렸다.

### 생성 요청

2026-11-07에 실제 Pico2D 실행으로 8방향 일반·조용히 걷기, 직선·대각선 속도 일치, 멈춘 뒤 방향 유지, 8방향 줍기, 방공호 경계 충돌, 구간 전환과 재시작을 확인했다. 공통 체크리스트의 입력·속도·애니메이션 방향·기준점·충돌 항목을 이번 변경의 확인 대상으로 삼았다.

> Match the attached original 2D pixel sprite EXACTLY in ochre colors, charcoal outline, teal gas mask lenses, compact olive backpack, Korean arm patch and pixel density, same head size and proportions. Create ONLY four NEW DIAGONAL orientations as 45 degree three-quarter views, NOT cardinal orientations. Rows TOP TO BOTTOM: DOWN-LEFT (front face and left side visible, looking bottom left), DOWN-RIGHT (front face and right side visible), UP-LEFT (back and left side visible), UP-RIGHT (back and right side visible). For bottom two rows the backpack is prominent and only an edge of mask may be visible. Every character in a row faces that row's diagonal direction, no pure front/side/back views. Uniform regular grid with full sprite centered in each cell, plenty of transparent space, consistent feet baseline. Transparent PNG, no shadows, lettering or grids.

- `survivor_walk.png`를 참조한 **walk** 요청. FOUR columns and FOUR rows. Each row is the same direction. Columns 1 idle boots together, 2 left boot forward, 3 right boot forward, 4 feet passing. Normal upright walk.
- `survivor_sneak_walk.png`를 참조한 **sneak** 요청. FOUR columns and FOUR rows. Each row is the same direction. Columns 1 cautious stationary pose, 2 left boot forward, 3 right boot forward, 4 feet passing. Knees flexed, torso leaning forward, elbows bent, cautious tiptoe walk.
- `survivor_pickup.png`를 참조한 **pickup** 요청. ONE column and FOUR rows. Each row shows one lowered ground pickup pose, one knee on floor and one hand touching floor.
