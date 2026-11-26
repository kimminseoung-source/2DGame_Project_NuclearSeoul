# 점검 결과 (2026-11-26 13:22, 82개 중 82개 통과, 388초)

`tools/checks/run_all.py`가 씀. PASS는 끝까지 돌았다는 뜻 — 숫자는 마지막 줄을 읽을 것.

| 점검 | 결과 | 마지막 줄 | 오류 |
|---|---|---|---|
| check_8dirs | PASS | ok [5, 5, 5, 5, 5, 5, 5, 5] |  |
| check_abc | PASS | [new] C  grabbed: yes, could walk while held: False, roll frees: True |  |
| check_aim | PASS | holding 1 s: stamina 100 ready 1.0 |  |
| check_aim3d | PASS | ok |  |
| check_aim_weapons | PASS | ok |  |
| check_arena | PASS | ok |  |
| check_bag | PASS | game runs ok |  |
| check_bag2 | PASS | ok |  |
| check_bag3 | PASS | ok |  |
| check_behind | PASS | NOTICE_NEAR 90 SIGHT_RANGE 250 |  |
| check_body3d | PASS | ok |  |
| check_cancel | PASS | heavy hit-stop 0.09 |  |
| check_carry | PASS | ok |  |
| check_combat | PASS | crawler False: pose chop, killed False |  |
| check_counter_blow | PASS | COUNTER_STAGGER 1.56 |  |
| check_daylight | PASS | ok |  |
| check_default_hero | PASS | check_default_hero: PASS |  |
| check_defense | PASS | ok |  |
| check_detect_rules | PASS | 감지 규칙 OK |  |
| check_dev | PASS | ok |  |
| check_director | PASS | ok |  |
| check_director2 | PASS | ok |  |
| check_dirlook | PASS | ok |  |
| check_dodge | PASS | ok |  |
| check_f5 | PASS | ok |  |
| check_f6 | PASS | ok |  |
| check_f6_live | PASS | ok |  |
| check_feel | PASS | ok |  |
| check_fence | PASS | ok |  |
| check_gap | PASS | shove early in the warning: {'windup': 40} / |  |
| check_hit_fx | PASS | ok |  |
| check_hud_bible | PASS | ok |  |
| check_identity | PASS | axe      noise - / torso -> health 23, flinch / quick head -> 23 |  |
| check_inv | PASS | ok |  |
| check_jolt | PASS | ok |  |
| check_keypose | PASS | ok |  |
| check_map | PASS | stuck: 1 |  |
| check_mixed | PASS | crawl speed 12.6 px/s |  |
| check_mood | PASS | ok |  |
| check_muffled | PASS | where the infected goes vs the real spot (min / avg / max px): {'behind the car': (0, 0, 0), 'in the open': (0, 0, 0)} |  |
| check_nolegs | PASS | ok |  |
| check_paperdoll | PASS | ok |  |
| check_pick | PASS | ok |  |
| check_pistol | PASS | fire frame caught: True |  |
| check_pistol_flow | PASS | {"checks": ["normal walk uses all four full-body keys", "stationary raise reaches planted A-like aim", "aimed movement uses short-step keys, then sett |  |
| check_pistol_gait | PASS | {"checks": ["all 8 normal walking phases selected by actual displacement", "all 8 aim-walk phases and raised stationary aim reachable", "real moving r |  |
| check_pistol_identity | PASS | {"checks": ["26 upright base/refined pose assets share identical 10x9 head pixels without resampling; rows32+ unchanged", "both F10 branches actually  |  |
| check_pistol_refinement | PASS | {"checks": ["four AI swing-leg edits extend lower; original upper body and planted boots stay pixel-identical", "refined D disables distance audio; on |  |
| check_pz2 | PASS | ok |  |
| check_range | PASS | axe: range 45px / marked at the edge -> hit (shown torso) / outside range -> not hit / blow 1.01s + rest 0.35s (느림) |  |
| check_real | PASS | ok |  |
| check_redjacket_motion | PASS | ["all six walk frames during real movement", "idle does not advance walking distance", "blocked wall movement does not cycle feet", "quick cut: real d |  |
| check_reel | PASS | shoved idle, hero gone -> idle no crash |  |
| check_rings | PASS | ok |  |
| check_roll8 | PASS | ok |  |
| check_roll_chain | PASS | gap between rolls (s): [0.066] / rolls: 2 / dust puffs at starts: 2 / moved 417 px (walking adds the rest) |  |
| check_roll_charges | PASS | ok |  |
| check_roll_ease | PASS | ease (1.6, 0.4) 144fps: distance 72.8px, half the time 47.0px (65%) |  |
| check_rush | PASS | 2.77s windup  rush 0.00 speed 0 |  |
| check_samurai | PASS | ok [5, 5, 5, 5, 5, 5, 5, 5] |  |
| check_seeing | PASS | ok |  |
| check_senses | PASS | windup_behind  old: None     new: None |  |
| check_shadow_match | PASS | ok |  |
| check_shadow_match_13 | PASS | ok |  |
| check_shadow_match_22 | PASS | ok |  |
| check_shove_crawler | PASS | draw ok |  |
| check_slider | PASS | ok |  |
| check_sneak8 | PASS | ok |  |
| check_spawn | PASS | after a slash: next arrival 5.02s later, target (524, 352) (hero at 120,120) |  |
| check_spitter | PASS | OK |  |
| check_spitter_mix | PASS | PASS |  |
| check_spot | PASS | 살금 {30: True, 95: True, 135: True, 145: True, 240: True, 260: False} / 등 돌림 80: True 150: False 30: True |  |
| check_stage1 | PASS | ok |  |
| check_stamina | PASS | draw ok |  |
| check_stomp | PASS | 50px cursor low, far        held : shown torso  pose chop   -> ALIVE |  |
| check_tells | PASS | ok |  |
| check_toolcmp | PASS | ok |  |
| check_top2 | PASS | ok |  |
| check_tough2 | PASS | staggered (shoved): [(3, 7), (4, 3)] |  |
| check_ui | PASS | ok |  |
| check_variants | PASS | ok 18 rows |  |
| check_walk | PASS | ok |  |

되돌린 그림 14개(점검이 바꾼 docs/planning 그림): docs/planning/attack_tells.png, docs/planning/attack_variants_game.png, docs/planning/dev_sliders.png, docs/planning/dev_sounds_walk.png, docs/planning/hero_walk_south.gif, docs/planning/hero_walk_south_strip.png, docs/planning/paper_doll_ingame.png, docs/planning/pistol_ingame.png, docs/planning/roll_8dirs_game.png, docs/planning/roll_dots.png, docs/planning/samurai_game.png, docs/planning/sneak_8dirs_game.png, docs/planning/tool_vs_pixellab.gif, docs/planning/tool_vs_pixellab_strip.png
