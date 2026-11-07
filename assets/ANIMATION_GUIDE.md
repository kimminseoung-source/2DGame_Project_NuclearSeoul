# 주인공 도트 애니메이션 제작 기준

현재 게임에서는 초기 도트 버전을 사용한다. 색과 장비는 황토색 후드, 청록색 렌즈, 올리브색 배낭, 짙은 회색 바지·장갑·부츠와 어두운 외곽선을 기준으로 맞춘다.

| 동작 | 게임에서 쓰는 시트 | 기본 재생 방식 |
| --- | --- | --- |
| 서기와 걷기 | [기존 걷기 시트](survivor_walk.png) | 첫 칸은 대기 자세다. 이동은 네 단계, 한 주기 0.48초다. |
| 조용히 걷기 | [초기 조용히 걷기 시트](survivor_sneak_walk.png) | 상체를 앞으로 기울인 채 디딤과 두 발이 가까워지는 중간 자세를 번갈아 재생한다. 이동은 네 단계, 한 주기 0.60초다. |
| 줍기 | [기존 줍기 시트](survivor_pickup.png) | 한 방향당 몸을 낮춘 자세 한 장을 사용한다. 시작 후 0.28초에 필터를 획득한다. |

걷기와 조용히 걷기의 행 순서는 아래, 왼쪽, 오른쪽, 위다. 게임의 이동 속도 설정에 따라 두 이동 동작의 재생 속도도 달라진다. 줍기 재생 시간은 0.58초다.

조용히 걷기는 게임에서 46픽셀 높이로 그린다. 일반 걷기와 같은 바닥 기준점에 발을 맞추고 Shift 전환 시 발걸음 주기에서 현재 위치를 이어받는다.

일반 걷기 8방향은 2→3→4→3칸을 반복한다. 좌우와 대각선은 반대 디딤을 그린 자세를 사용한다. 상하에서는 4번째 칸을 그릴 때 2번째 칸의 다리만 좌우 반전하고 상체는 4번째 칸을 유지한다. 일반 걷기 시트를 내장 imagegen에 참조로 넣어 새 디딤 자세를 요청했다. 카메라에 가까운 다리의 밝은 무릎 패드와 먼 다리의 어두운 면을 구분하고, 두 디딤 자세에서 앞발과 뒷발이 교대하게 했다.

Shift 전환 때 조용히 걷기 시트가 밝아 보이는 차이를 줄이기 위해, 게임이 이미지를 불러올 때 조용히 걷기 시트에만 색을 보정한다. Pico2D에서 같은 위치와 발걸음 단계의 우향·좌하향 후드 색을 읽어 보정 전보다 일반 걷기 색에 가까워진 것을 확인했다.

새 동작을 만들 때는 이 시트를 참조 이미지로 사용한다. 실제 게임 크기에서 원본과 비교해 장비 색과 크기, 발이 닿는 위치, 첫 프레임과 마지막 프레임 사이의 이어짐을 확인한다. 공통 제작 양식은 [도트 리소스 제작 가이드](ART_GUIDE.md)를 따른다.

## 대각선 네 방향

직선에서 대각선으로 전환할 때 후드의 색 차이를 줄이기 위해 대각선 시트의 색을 보정한다. 일반 걷기는 다시 그린 네 번째 칸의 밝기가 달라 방향별로 별도 보정값을 쓴다. Pico2D에서 대각선 네 방향의 대기·이동 프레임을 인접한 직선 방향과 비교해 일반 걷기와 조용히 걷기 모두 후드 색 차이가 줄어든 것을 확인했다.

좌하향 일반 걷기의 네 번째 칸은 같은 발을 다시 내밀던 자세를 교체한 것이다. 기존 시트를 내장 imagegen에 참조로 넣고, 화면 왼쪽의 먼 다리는 앞으로 디디고 오른쪽의 밝은 무릎 패드가 달린 가까운 다리는 뒤에서 들어 올리는 자세를 요청했다. 기존 2→3→4→3칸 재생 순서에서 두 디딤 자세의 앞발이 교대한다.

`survivor_diagonal_walk.png`, `survivor_diagonal_sneak.png`, `survivor_diagonal_pickup.png`는 초기 도트 원본을 참조해 내장 imagegen으로 제작했다. 칸은 192×248픽셀이고, 행 순서는 좌하·우하·좌상·우상이다. 걷기와 조용히 걷기는 방향당 대기 자세와 이동 자세를 포함한 네 칸, 줍기는 방향당 한 칸이다.

방향 0~3은 기존 아래·왼쪽·오른쪽·위이고, 4~7은 좌하·우하·좌상·우상이다. 대각선에서도 이동 벡터 길이를 나눠 직선과 같은 이동 속도를 유지한다. 멈춘 뒤와 줍는 동안 마지막으로 바라보던 방향을 유지한다. 원본과 같은 높이 배율과 발 기준점으로 그리고, 대각선의 넓은 실루엣을 수용할 수 있도록 칸 너비를 늘렸다.

### 생성 요청

2026-11-07에 실제 Pico2D 실행으로 8방향 일반·조용히 걷기, 직선·대각선 속도 일치, 멈춘 뒤 방향 유지, 8방향 줍기, 방공호 경계 충돌, 구간 전환과 재시작을 확인했다. 공통 체크리스트의 입력·속도·애니메이션 방향·기준점·충돌 항목을 이번 변경의 확인 대상으로 삼았다.

> Match the attached original 2D pixel sprite EXACTLY in ochre colors, charcoal outline, teal gas mask lenses, compact olive backpack, Korean arm patch and pixel density, same head size and proportions. Create ONLY four NEW DIAGONAL orientations as 45 degree three-quarter views, NOT cardinal orientations. Rows TOP TO BOTTOM: DOWN-LEFT (front face and left side visible, looking bottom left), DOWN-RIGHT (front face and right side visible), UP-LEFT (back and left side visible), UP-RIGHT (back and right side visible). For bottom two rows the backpack is prominent and only an edge of mask may be visible. Every character in a row faces that row's diagonal direction, no pure front/side/back views. Uniform regular grid with full sprite centered in each cell, plenty of transparent space, consistent feet baseline. Transparent PNG, no shadows, lettering or grids.

- `survivor_walk.png`를 참조한 **walk** 요청. FOUR columns and FOUR rows. Each row is the same direction. Columns 1 idle boots together, 2 left boot forward, 3 right boot forward, 4 feet passing. Normal upright walk.
- `survivor_sneak_walk.png`를 참조한 **sneak** 요청. FOUR columns and FOUR rows. Each row is the same direction. Columns 1 cautious stationary pose, 2 left boot forward, 3 right boot forward, 4 feet passing. Knees flexed, torso leaning forward, elbows bent, cautious tiptoe walk.
- `survivor_pickup.png`를 참조한 **pickup** 요청. ONE column and FOUR rows. Each row shows one lowered ground pickup pose, one knee on floor and one hand touching floor.

## 오른쪽 야구 방망이 공격 시험

[오른쪽 시험 시트](survivor_bat_right.png)는 준비·타격·회수 세 칸으로 구성한다. 칸은 실제 표시 크기인 77×58픽셀이고, 캐릭터 발 기준점을 기존 이동 자세와 맞춘다. 공격은 초기 시제품의 70% 속도로 재생해 약 0.14초에 타격 자세로 전환하고, 약 0.20초에 접촉을 판정한다. 약 0.31초부터 회수 자세를 표시하고 약 0.49초에 공격을 마친다.

[오른쪽 대기 자세](survivor_bat_right_idle.png)는 방망이 손잡이를 잡은 전용 도트다. 초기 걷기와 방망이 공격 시트를 내장 imagegen의 참조로 쓰고, 오른쪽을 보며 양발을 딛고 방망이를 아래로 늘어뜨린 자세를 요청했다. 공격 시트와 같은 칸 크기와 발 기준점으로 그린다.

> Single full-body 2D pixel game sprite. Exact existing character from the right-facing third row of the reference, match muted ochre hood, teal respirator, small olive backpack, charcoal boots and Korean shoulder patch; same proportions, same outline, same neutral light. Pure right-facing profile. Standing still upright relaxed, both boots next to each other planted on the same line. Holds one wooden baseball bat down naturally at their right side: gloved near hand wrapped clearly around the narrow grip near thigh, barrel extends diagonally forward and down toward screen right, does not touch floor. Far arm relaxed. Keep entire body and bat visible. Centered transparent PNG with ample margins. No other poses, objects, grid, ground shadow, highlights or glow.

내장 imagegen에 `survivor_walk.png`를 참조로 전달했다. 생성 후보에서 오른쪽을 바라보는 한 줄만 골랐다.

> Game-ready pixel-art sprite sheet of this exact original Korean post-apocalyptic yellow ochre hood, teal visor gas mask, charcoal outfit, olive backpack and Korean sleeve patch. SAME color palette, shading, proportions, camera and pixel density as reference. Exactly THREE columns and FOUR rows, regular grid, generous transparent gutters for entire character and baseball bat. Each row has 3 distinct stages of the SAME two-handed wooden baseball bat swing: column 1 wind-up bat drawn back near shoulder, column 2 contact bat extended forward in facing direction with hips/shoulders turning and one foot planted, column 3 recovery bat lowered after follow-through. Bat firmly held in both gloved hands, no effects. Grounded foot at consistent floor level, no background/shadows, no lettering. Full body and entire bat visible in each cell. Rows top to bottom: DOWN facing viewer, LEFT profile, RIGHT profile, UP showing backpack.

## 방망이 캐릭터 8방향 통합

- 캐릭터 원본은 [오른쪽 방망이 대기 자세](survivor_bat_right_idle.png)다. 새 에셋은 황토색 후드, 청록색 방독면, 올리브색 배낭, 어두운 바지와 손에 쥔 둥근 나무 방망이를 원본 기준으로 맞춘다. 오른쪽 일반 대기 칸에는 원본을 그대로 넣었다.
- 대기·일반 걷기·조용히 걷기와 줍기·공격은 각 77×58 픽셀 칸을 사용한다. 가로 네 칸과 세로 네 줄의 시트 여섯 장으로 구성하며, 각 칸의 발 기준점을 맞췄다. RGBA 픽셀 데이터 기준 약 1.64 MiB다.
- 이동 시트는 대기 → 첫발 접지 → 두 발 교차 → 반대 발 접지 순으로 배치했다. 이동 루프는 2→3→4→3으로 재생하고, Shift 전환 시 현재 보행 단계를 유지한다. 왼쪽 위·아래 대각선의 접지 컷은 별도로 확인했다.
- 동작 시트의 열은 줍기, 공격 준비, 타격, 회수 순이다. 좌측 공격은 대응 우측 컷을 좌우 반전해 사용하므로 일부 소매 패치도 반전된다.
- 이미지 생성에는 오른쪽 방망이 대기 원본을 참조로 전달했다. 이동 자세는 ‘같은 손으로 방망이의 가는 손잡이를 잡고 끝을 낮추기’, 조용히 걷기는 ‘무릎을 굽혀 상체를 기울이기’, 왼쪽 대각선은 ‘앞발을 바꾸면서 가까운 쪽과 먼 쪽 다리의 겹침을 구분하기’를 요청했다. [Project Zomboid의 동작 전환 개발 글](https://projectzomboid.com/blog/news/2019/06/anim-transition-blog/)에서 체중 이동 표현을 참고했다.
- 생성 결과는 방향, 손잡이 접촉, 앞발 교대, 방망이 끝 잘림을 확인한 뒤 사용한다. Pico2D에서 8방향 일반·Shift 입력, 멈춤 방향, 줍기와 공격 단계의 렌더링을 확인했다.

- 방망이를 든 대기·이동 자세는 네 칸을 나란히 놓고 장갑이 가는 손잡이를 쥐는지, 둥근 끝이 진행 방향 쪽을 향하는지 확인한다. 위쪽 뒷모습에서는 몸 옆으로 보이는 짧은 원근 형태를 사용한다. 대각선에서는 멈출 때의 첫 칸도 이동 칸과 같은 방향으로 맞춘다.

## 횡스크롤 전환과 좌우 공격

- A/D는 좌우 이동과 방향을 결정한다. W/S는 통로 안에서 앞뒤 깊이만 바꾸며 마지막 좌우 자세를 유지한다. 카메라는 x축을 따라가고, 바닥 물체는 뒤에서 앞으로 그린다.
- 게임은 좌우 두 줄만 들어 있는 전용 시트를 사용한다. 이동 칸은 77×58, 공격·줍기 칸은 97×58이다. 방공호와 지상 배경은 imagegen으로 옆에서 본 벽과 앞뒤로 걸을 수 있는 바닥을 구성한 뒤 각각 768×480, 1536×480으로 정리했다.
- 공격 칸은 줍기 → 준비 → 타격 → 휘두른 뒤 → 회수 순이다. 좌우 공격의 실루엣과 발 기준점을 맞추기 위해 같은 스윙을 반전한다. 타격 칸 진입과 판정은 같은 시점을 사용한다. 실제 명중에만 75ms 멈춤, 충격 표시와 합성 타격음을 재생한다.
- 좀보이드 개발 글에서 대기·이동·은신 사이의 무게 이동과 공격 후 회수에 주목했다. 새 동작은 시작, 접촉 또는 발 디딤, 복귀를 먼저 나눠 그린다. 다음 후보인 달리기 시작·정지, 밀치기, 넘어짐·기상, 장애물 넘기는 해당 동작 한 방향부터 확인한다.
- 참고 자료. [Build 41 공식 트레일러 게시물](https://projectzomboid.com/blog/news/2021/12/project-zomboid-build-41-released/), [동작 전환](https://projectzomboid.com/blog/news/2019/06/anim-transition-blog/), [공격 회수와 후속 동작](https://projectzomboid.com/blog/news/2020/07/looks-different-somehow/)

- 공격 스프라이트는 기존 공격 그림을 자세 참고로만 쓰고, 오른쪽 대기 원본의 후드, 방독면, 배낭과 직사각형 태극기 패치를 외형 기준으로 삼는다. 대기·걷기·Shift 걷기와 공격 네 단계를 양쪽 모두 Pico2D에서 캡처해 비교한다. 마지막 회수 칸은 같은 방향의 대기 원본을 사용한다.
