"""Motions the free packs lack, made by turning a few bones of a pack pose (2026-11-16: the stomp
on a crawling infected, "기어 다니는 거는 발로 밟는 동작으로").

Each entry: the pose it starts from (an action and its frame), how many frames it lasts, and keys
{frame: {bone: (axis, degrees), ...}} - every bone not named keeps the start pose; a named bone is
turned that far from the start pose about its own local axis, eased between keys. Asked for by
name in a sheet map like any pack action (render_sprites.get_action).
"""

# Bone axes (probed 2026-11-16 on the Quaternius body, figure facing right): thigh +X swings the
# leg back, so -X lifts the knee forward; calf +X folds the shin back under the knee; spine_02 +X
# leans the upper body forward.
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
}
