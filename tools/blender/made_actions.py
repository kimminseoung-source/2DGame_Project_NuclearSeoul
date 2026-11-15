"""Motions the free packs lack, made by turning a few bones of a pack pose (2026-11-16: the stomp
on a crawling infected, "기어 다니는 거는 발로 밟는 동작으로").

Each entry: the pose it starts from (an action and its frame), how many frames it lasts, and keys
{frame: {bone: (axis, degrees), ...}} - every bone not named keeps the start pose; a named bone is
turned that far from the start pose about its own local axis, eased between keys. Asked for by
name in a sheet map like any pack action (render_sprites.get_action).
"""

# Bone axes (probed 2026-11-16 on the Quaternius body, figure facing right): thigh +X swings the
# leg back, so -X lifts the knee forward; calf +X folds the shin back under the knee; spine_01 /
# spine_02 +X lean the upper body forward, spine_01 Y twists it; upperarm_r (the weapon arm) +X
# raises the arm forward; lowerarm_r +X bends the elbow. A bone may take several turns: a list.
MADE = {
    # The stomp on a crawling infected (2026-11-16 "기어 다니는 거는 발로 밟는 동작으로"): lift the
    # knee high, then lean in and drive the foot down in front, the standing knee giving; 16 frames
    # at 30 fps, back to standing at the end. Tried: an upright stomp read as sitting down.
    "Stomp": {"from": ("Idle_Loop", 0), "length": 16, "keys": {
        0: {},
        5: {"thigh_r": ("X", -100), "calf_r": ("X", 105), "spine_02": ("X", -10)},
        8: {"thigh_r": ("X", -48), "calf_r": ("X", 0), "thigh_l": ("X", -32), "calf_l": ("X", 55),
            "spine_02": ("X", 30)},
        11: {"thigh_r": ("X", -45), "calf_r": ("X", 3), "thigh_l": ("X", -28), "calf_l": ("X", 50),
             "spine_02": ("X", 25)},
        16: {},
    }},
    # Plain, grounded attacks (2026-11-16 "돌아서 때리기 이런 거는 이상함, 애니메이션 동작이 일반적이어야"):
    # feet stay put, the body turns a little, the arm does the work. 16 frames at 30 fps.
    # Overhead chop: raise the weapon over the head, bring it down in front.
    "Chop": {"from": ("Idle_Loop", 0), "length": 16, "keys": {
        0: {},
        5: {"upperarm_r": ("X", 165), "lowerarm_r": ("X", 70), "spine_01": ("X", -8)},
        7: {"upperarm_r": ("X", 170), "lowerarm_r": ("X", 75), "spine_01": ("X", -10)},
        9: {"upperarm_r": ("X", 70), "lowerarm_r": ("X", 5), "spine_01": ("X", 18)},
        12: {"upperarm_r": ("X", 55), "lowerarm_r": ("X", 5), "spine_01": ("X", 15)},
        16: {},
    }},
    # Sideways swing: weapon raised back past the shoulder, swung level across the front, follow-
    # through low (the wrist tilt keeps the blade flat at the hit; tried without it: blade upright).
    "Swing": {"from": ("Idle_Loop", 0), "length": 16, "keys": {
        0: {},
        5: {"upperarm_r": [("X", 30), ("Z", 75)], "lowerarm_r": ("X", 25), "spine_01": ("Y", -35), "hand_r": ("Y", -40)},
        7: {"upperarm_r": [("X", 30), ("Z", 80)], "lowerarm_r": ("X", 25), "spine_01": ("Y", -40), "hand_r": ("Y", -40)},
        9: {"upperarm_r": ("X", 85), "lowerarm_r": ("X", 0), "spine_01": ("Y", 15), "hand_r": ("Y", -75)},
        11: {"upperarm_r": [("X", 85), ("Z", -35)], "lowerarm_r": ("X", 5), "spine_01": ("Y", 35), "hand_r": ("Y", -75)},
        16: {},
    }},
}
