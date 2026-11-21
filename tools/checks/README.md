# 점검 스크립트 (tools/checks)

2026-11-21 임시 폴더에서 옮김(계획서 [점검_스크립트_옮기기](../../docs/plans/2026-11-21_점검_스크립트_옮기기.md)). 모두 **프로젝트 폴더에서** 실행하고, 게임 창은 숨김으로 띄운다.

```powershell
.venv\Scripts\python.exe tools/checks/run_hidden.py tools/checks/check_combat.py   # 하나
.venv\Scripts\python.exe tools/checks/run_all.py                                 # 전부 → LAST_RUN.md
.venv\Scripts\python.exe tools/checks/run_all.py roll sneak                       # 이름에 든 것만
```

- 점검은 숫자를 출력한다. PASS는 "끝까지 돌았다"는 뜻이니 [LAST_RUN.md](LAST_RUN.md)의 마지막 줄을 읽는다.
- 그림을 `docs/planning`에 저장하는 점검이 있다. `run_all.py`는 끝나고 바뀐 그림을 되돌린다. 하나씩 돌렸을 때는 커밋 전에 `git checkout -- docs/planning/<그림>`.
- 새 점검: `check_<무엇>.py`, 첫 줄 문서 문자열에 무엇을 확인하는지, `sys.path.insert(0, "src")`.

## 점검 (check_*.py)

| 파일 | 확인하는 것 |
|---|---|
| `check_8dirs.py` | 3D hero, 8 directions: the attack uses each direction's own pictures (no borrowing); a board of aim -> wind-up -> hit -> recover per directi |
| `check_abc.py` | (설명 없음) |
| `check_aim.py` | Aimed blows: hold to ready, release to strike; the part under the cursor sets the damage. |
| `check_aim3d.py` | 3D hero aiming: stand with the bat raised (8 directions), step with it raised, let go = bat swing. Run with BUSAN_HERO=hero_3d BUSAN_AREA=ar |
| `check_aim_weapons.py` | Aiming and standing with every weapon (south-east, south, north-east), and a knife aimed while stepping (must not show the old side sheet).  |
| `check_arena.py` | The empty test arena: chop in all 8 directions at standing infected; strip of the hit moment. |
| `check_bag.py` | Bag screen B v4: layout, keys, take / drop, mouse drag, and a screenshot. |
| `check_bag2.py` | The bag by cells: spots are remembered, dragging moves a thing (green / red preview), R turns it, a full sheet takes nothing more, taking a  |
| `check_bag3.py` | Bag step 2: stacks, joining a stack by drag, the tooltip, the hand slot, double click, tidy. |
| `check_behind.py` | Notice behind: an idle infected facing away spots a still hero within NOTICE_NEAR, not beyond. |
| `check_body3d.py` | 3D hero body motions in the game, 8 directions: hurt, down, pickup, sneak, sneak still. Also which look draws each (must be the new pictures |
| `check_cancel.py` | Attack gaps: from a pipe blow's start, when can the hero walk again and when can the next blow start, with the follow-through cancels on (no |
| `check_carry.py` | Carried weapon: hang vs ready, 8 standing directions + east walk / pickup / sneak, in the game. |
| `check_combat.py` | Tempo, reach, the infected's claw arc, the hit reaction (no blink) and the auto chop. |
| `check_counter_blow.py` | Shove off, counter moved to the blow: right click does nothing; a blow at the end of the claw wind-up reels it for COUNTER_STAGGER (pushed f |
| `check_daylight.py` | Day / dusk / night: the same scene, how much is seen outside the cone. |
| `check_defense.py` | (설명 없음) |
| `check_dev.py` | spawn one at the cursor via the panel (row by name), two crawl |
| `check_director.py` | AI director: outside build/peak/relax, defense phases; F7 graph. |
| `check_director2.py` | Director outside: three blows -> peak, then relax, then build again; hurt hero = slower arrivals. |
| `check_dirlook.py` | 8-direction PixelLab hero in the game: aim at 8 directions, day and night, beside an infected; old look too. |
| `check_dodge.py` | Dodge look, east only: 3 styles x moments, hidden window; the body uses the east walking picture (not the old side sheet); afterimages lie b |
| `check_f5.py` | (설명 없음) |
| `check_f6.py` | F5 sight / F6 sound split; a loud noise calls new infected only through entrances in its ring. |
| `check_f6_live.py` | F6 as a player meets it: press F6, stand, walk, sneak, swing - what rings are on screen each moment? |
| `check_feel.py` | a picture of the flash |
| `check_fence.py` | go there: the hero can walk in through the fence |
| `check_gap.py` | Pillar 1: the opening after its claw (one slash), the counter shove at the end of the warning. |
| `check_identity.py` | Paces of the infected; what each weapon is good and bad at. |
| `check_inv.py` | finisher: slash an idle infected from behind |
| `check_jolt.py` | Two weights of hit feel: a light hit vs a finishing blow. |
| `check_keypose.py` | Key-pose chop toward the south-east at an infected, in the game: key poses on vs off, as a GIF. |
| `check_map.py` | Real-map area: does the summary card draw, and do chasing infected get around buildings? |
| `check_mixed.py` | A crawler and a standing infected together: aim low = stomp the crawler, level = the standing one; swings and stabs pass over a crawler, a c |
| `check_muffled.py` | (설명 없음) |
| `check_nolegs.py` | Legs, crawlers and the stomp off (settings.LEGS_AND_CRAWLERS = False). |
| `check_paperdoll.py` | Paper doll check: the weapon drawn at the hand point (drawn = logic), behind the body facing north, swing angles, frame time; plus a picture |
| `check_pick.py` | panic narrows the view |
| `check_pistol.py` | The pistol: pick up -> 6 rounds; a shot hits the first infected on the line, not through a wall; the bang wakes a far one; empty -> no shot. |
| `check_pz2.py` | front sound: idle infected facing the sound goes straight to search |
| `check_range.py` | The shown range is the hit range; a marked target is hit; speeds differ by weapon. |
| `check_real.py` | (설명 없음) |
| `check_reel.py` | (설명 없음) |
| `check_rings.py` | F6: walking leaves one footstep ring, not a pile; rings go after NOISE_SHOW. |
| `check_roll8.py` | The 6-picture roll in 8 directions in the game: each picture comes from Roll_Spin (never the old sheet or a glide), drawn at the middle of i |
| `check_roll_ease.py` | Roll easing: same distance, more of it early; old even roll for comparison. |
| `check_rush.py` | an open stretch of ground: the hero, and 130 px off an infected looking at him |
| `check_samurai.py` | Default attack of the 3D hero: aim (bat) -> let go -> sword hit -> held blade. Swung weapons, south-east and south. Run with BUSAN_HERO=hero |
| `check_seeing.py` | Who can be seen, day vs night: only the cone's length changes; outside the cone and behind walls never. |
| `check_senses.py` | (설명 없음) |
| `check_shadow_match.py` | Does the drawn darkness match the computed one? Draw only the vision mesh on white, read it back, compare every 4th canvas pixel with Vision |
| `check_shadow_match_13.py` | (설명 없음) |
| `check_shadow_match_22.py` | (설명 없음) |
| `check_shove_crawler.py` | v6.6: nothing is knocked down; counter = long stagger; crawlers from the start; stomp on them. |
| `check_slider.py` | F4 sliders: click/drag the bar, type a number in the box, Esc cancels. |
| `check_sneak8.py` | Sneaking in 8 directions in the game (Sneaking Forward): 3 walking moments + standing still, the pictures come from Sneak/ and Sneak_Idle/ ( |
| `check_spawn.py` | a slash brings the next one soon, heading for the noise |
| `check_spot.py` | Fixed spot distance: in sight and this close -> "!" at once, farther -> never. |
| `check_stage1.py` | (설명 없음) |
| `check_stamina.py` | Stamina costs, tired actions, regen; the quiet takedown. |
| `check_stomp.py` | Stomping a crawler from the ways a player would click. |
| `check_tells.py` | Attack tells: the faint red wedge while an infected winds up. Drawn red pixels must lie in the claw's real wedge (drawn = logic); start / mi |
| `check_toolcmp.py` | Key-pose chop toward the south-east at an infected, in the game: key poses on vs off, as a GIF. |
| `check_top2.py` | (설명 없음) |
| `check_tough2.py` | (설명 없음) |
| `check_ui.py` | pick up: E near the bandage, check the motion |
| `check_variants.py` | F4 attack motion x picture count for the 3D hero: film a south-east chop for each, one board. Run with BUSAN_HERO=hero_3d BUSAN_AREA=arena t |
| `check_walk.py` | Walk south with the PixelLab hero: frames over time, saved as a GIF and a strip. |

## 그림·시간 (shots/)

| 파일 | 하는 일 |
|---|---|
| `gif_dodge.py` | Animated GIF: the three dodge looks, east, every frame (plus a still before and after). |
| `gif_roll.py` | Animated GIF: the three dodge looks, east, every frame (plus a still before and after). |
| `gif_roll2.py` | Animated GIF: the three dodge looks, east, every frame (plus a still before and after). |
| `gif_sneak.py` | Sneaking east in the game: now vs D, side by side, every frame (GIF) + which pictures were used. |
| `gif_sneak3.py` | Sneaking east in the game: now vs D, side by side, every frame (GIF) + which pictures were used. |
| `measure_wrecks.py` | Each standing block: its collision rect vs where its picture is drawn (play.draw_world). |
| `probe_shadow.py` | Darkness along the line hero -> wreck centre -> beyond, as the game computes and draws it. |
| `probe_shadow2.py` | Same scene as shot_cone.py: darkness at points around the wreck, and which blocker shadows them. |
| `shot_alley.py` | The hand-made alley: the whole map (no darkness), then in game at the start, the house door, inside. |
| `shot_cone.py` | Full screen at night, the hero looking straight at a wreck: is the cone lit and the shadow behind it? |
| `shot_crawl.py` | In-game shots: the hero mid-shove, and a crawler coming on. |
| `shot_fence_before_after.py` | Devlog pictures for study note 01: the station without the fence (old rule) vs with it. |
| `shot_house.py` | The house at full size: from outside (roof on) and inside (roof off), zoom 4. |
| `shot_infected.py` | The infected as they look in the game now: standing, walking, winding up, crawling - enlarged. |
| `shot_map.py` | The real-size area: at the start, at a door outside, inside the same building; frame time. |
| `shot_noise.py` | Mock-up: the noise of a blow shown as a ring; infected inside it get a "?" (2026-11-16 proposal). |
| `shot_note.py` | (설명 없음) |
| `shot_ranges.py` | (설명 없음) |
| `shot_react.py` | Shots for C: a claw coming -> [우클릭]; held by two -> [Space]; just hit -> red edge; bleeding -> [1]. |
| `shot_readywalk.py` | (설명 없음) |
| `shot_start.py` | (설명 없음) |
| `shot_teach.py` | Shots: key marks at the start; after the first moves; a '?' over infected that heard a blow. |
| `shot_wreck_shadow.py` | The hero looks across a wreck (day and night): where does the shadow behind it start? |
| `sim_sight.py` | How long an idle infected facing the hero takes to spot him by sight alone (no noise). |
| `time_draw.py` | (설명 없음) |
| `time_vision.py` | How long a frame's darkness takes to build and draw, near the house (many walls) and on the road. |
| `vision_cone_new.py` | Facing vision (2026-11-14, "내가 바라보는 방향만 보이면 좋겠음"): the world is dark except a cone in the direction the hero looks and a small clear circle  |
| `wreck_contact.py` | Walk the hero into a wreck from below, above and the side with F1 on: where does the body stop? |

## 은퇴 (retired/)

지금 게임과 맞지 않는 예전 점검. 기록으로만 둠.

| 파일 | 왜 |
|---|---|
| `check_tough.py` | 11-16에 없앤 한 방 규칙(`helpless`)을 찾음 |
| `check_map30.py` | 예전 지도 구조를 가정 |
| `check_hero3d_frames.py` | 사무라이 이전 공격 그림. check_samurai·check_8dirs가 대신 |
| `check_crawl.py` | 기어 다니는 피폭체(11-20 끔) |
