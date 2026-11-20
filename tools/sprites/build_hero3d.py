"""Build the game's hero folder from the 3D hero (2026-11-20).

    .venv\\Scripts\\python.exe tools/sprites/build_hero3d.py [--out assets/characters/hero_3d] [--only idle walk chop]

For each action: tools/blender/mpfb_pose.py renders the id and light passes at sprite size
(64 canvas, 36 px tall, feet 12 px up, camera 30 deg above), records the right fist and the
weapon direction per picture, tools/sprites/repaint.py paints them, and the pictures land in
the layout character_look.DirLook reads (same as the PixelLab hero):
  Idle/rotations/<dir>.png, Breath/<dir>/0-1.png (standing, 2 pictures), Walking/<dir>/0-5.png,
  MP_chop/<dir>/<n>.png (only the 3 key poses), hands.json (idle, breath, walk: hand per
  picture), keyframes.json (chop: wind-up, hit and recover picture, hand, weapon angle).
  Counts follow docs/plans/2026-11-20_hero3d_장수_줄이기.md: 2 + 6 + 3. The body is drawn empty-handed; the game draws the weapon at the hand
  (MOTION_RULES 7). Directions: turn 0 faces the camera (south), +45 per step clockwise.
Model: C:/Users/doboh/busan_ai/mpfb/busan_hero.blend (tools/blender/mpfb_hero.py, spec
assets/characters/mpfb/hero.json). Actions: Mixamo files in assets/source3d/mixamo.
"""

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
BLEND = "C:/Users/doboh/busan_ai/mpfb/busan_hero.blend"
TURN = {"south": 0, "south-east": 45, "east": 90, "north-east": 135, "north": 180,
        "north-west": 225, "west": 270, "south-west": 315}
ACTIONS = {
    # name: (Mixamo file, pictures, directions, folder, extra args)
    "idle": ("Breathing_Idle", 2, list(TURN), "Breath", []),    # 2 breathing pictures; the 1st is also the still
    "walk": ("Walking", 6, list(TURN), "Walking", []),
    "chop": ("Standing_Melee_Attack_Downward", 10, ["south", "south-east", "south-west", "north-east", "north-west"],
             "MP_chop", ["--weapon", "0.75", "--hide-weapon"]),
}
CHOP_KEYS = {"windup": 3, "hit": 4, "recover": 7}   # of the 10 rendered: pipe over the head, forward-down,
                                                     # coming back; only these 3 are kept (2026-11-20 plan)
SPRITE = ["--pixel", "64", "--person-px", "36", "--feet", "12", "--tilt", "30"]
CHOP_DIRS = ["south", "south-east", "south-west", "north-east", "north-west"]
# Attack motions to try in the game (F4 "공격 동작"), all 10 pictures kept so F4 "공격 장수" can show
# 2, 3 or all of them (docs/plans/2026-11-20_공격동작_바꿔가며_시연.md). name: (Mixamo file, key poses)
VARIANTS = {
    "downward": ("Standing_Melee_Attack_Downward", {"windup": 3, "hit": 4, "recover": 7}),
    "heavy": ("Heavy_Weapon_Swing", {"windup": 3, "hit": 6, "recover": 8}),
    "bash": ("Bash", {"windup": 4, "hit": 6, "recover": 8}),
    "baseball": ("Baseball_Hit", {"windup": 4, "hit": 6, "recover": 8}),
    "greatsword": ("GreatSword_Downward", {"windup": 4, "hit": 6, "recover": 7}),
}
# Attacks put together from two motions' key poses (2026-11-20 "준비 자세는 그대로, 휘두르고 난 뒤
# 자세만 사무라이처럼"): key pose -> (variant, picture). The wind-up is the bat aim, the hit and
# the follow-through are the two-handed sword's lunge and held blade (docs/plans/2026-11-20_사무라이_베기_자세.md).
MIXED = {
    "samurai": {"windup": ("baseball", 4), "hit": ("greatsword", 6), "recover": ("greatsword", 7)},
}
# Aiming (left button held): the spine and above from the baseball wind-up, the legs standing
# or walking (docs/plans/2026-11-20_조준자세_하체걷기.md). Folder "AimStep", not "AimWalk":
# DirLook treats any folder with "walk" in its name as the plain walk.
AIM_UPPER = ["--upper", str(ROOT / "assets/source3d/mixamo/Baseball_Hit.fbx"), "--upper-at", "0.4",
             "--upper-skip", "Neck", "--weapon", "0.75", "--hide-weapon"]   # head: looks ahead, not at a pitcher
ACTIONS["aim"] = ("Breathing_Idle", 1, list(TURN), "Aim", AIM_UPPER)
ACTIONS["aim_step"] = ("Walking", 6, list(TURN), "AimStep", AIM_UPPER)
for _name, (_fbx, _) in VARIANTS.items():
    ACTIONS["v_" + _name] = (_fbx, 10, CHOP_DIRS, "MP_chop_" + _name, ["--weapon", "0.75", "--hide-weapon"])


def render(action, tmp):
    fbx, frames, dirs, _, extra = ACTIONS[action]
    turns = [str(TURN[d]) for d in dirs]
    rec = tmp / f"{action}.json"
    for p in ("id", "light"):
        cmd = [BLENDER, "-b", BLEND, "-P", str(ROOT / "tools/blender/mpfb_pose.py"), "--",
               "--anim", str(ROOT / f"assets/source3d/mixamo/{fbx}.fbx"), "--frames", str(frames),
               "--out", str(tmp / action / p), "--name", "a", *SPRITE, "--turn", *turns, "--pass", p, *extra]
        if p == "id":
            cmd += ["--record", str(rec)]
        subprocess.run(cmd, check=True, capture_output=True, cwd=ROOT)
    subprocess.run([str(ROOT / ".venv/Scripts/python.exe"), "-X", "utf8", str(ROOT / "tools/sprites/repaint.py"),
                    "--costume", str(ROOT / "assets/characters/mpfb/hero_paint.json"),
                    "--id", str(tmp / action / "id"), "--light", str(tmp / action / "light"),
                    "--out", str(tmp / action / "paint")], check=True, capture_output=True, cwd=ROOT)
    return json.loads(rec.read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="assets/characters/hero_3d")
    ap.add_argument("--only", nargs="*", default=["idle", "walk", "chop"], help=f"of {list(ACTIONS)}")
    a = ap.parse_args()
    out = ROOT / a.out
    hands_file, keys_file = out / "hands.json", out / "keyframes.json"
    hands = json.loads(hands_file.read_text(encoding="utf-8")) if hands_file.exists() else {}
    keys = json.loads(keys_file.read_text(encoding="utf-8")) if keys_file.exists() else {}
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        for action in a.only:
            fbx, frames, dirs, folder, _ = ACTIONS[action]
            rec = render(action, tmp)
            for d in dirs:
                pics = [tmp / action / "paint" / f"a_t{TURN[d]}_{i}.png" for i in range(frames)]
                notes = rec[str(TURN[d])]
                if action == "idle":
                    still = out / "Idle" / "rotations"
                    still.mkdir(parents=True, exist_ok=True)
                    shutil.copy(pics[0], still / f"{d}.png")
                    hands.setdefault("idle", {})[d] = [notes[0]["hand"]]
                    dest = out / folder / d
                    if dest.exists():
                        shutil.rmtree(dest)
                    dest.mkdir(parents=True)
                    for i, p in enumerate(pics):
                        shutil.copy(p, dest / f"{i}.png")
                    hands.setdefault("breath", {})[d] = [n["hand"] for n in notes]
                else:
                    dest = out / folder / d
                    if dest.exists():
                        shutil.rmtree(dest)
                    dest.mkdir(parents=True)
                    keep = sorted(CHOP_KEYS.values()) if action == "chop" else range(frames)
                    for i in keep:
                        shutil.copy(pics[i], dest / f"{i}.png")
                    if action in ("aim", "aim_step"):
                        key = folder.lower()
                        hands.setdefault(key, {})[d] = [n["hand"] for n in notes]
                        keys.setdefault("held_angles", {}).setdefault(key, {})[d] = [n["weapon"] for n in notes]
                    elif action == "walk":
                        hands.setdefault("walk", {})[d] = [n["hand"] for n in notes]
                    elif action.startswith("v_"):
                        name = action[2:]
                        keys.setdefault("variants", {}).setdefault(name, {})[d] = {
                            "anim": folder.lower(),
                            **{k: {"frame": i, "hand": notes[i]["hand"], "weapon": notes[i]["weapon"]}
                               for k, i in VARIANTS[name][1].items()},
                            "all": [{"frame": i, "hand": n["hand"], "weapon": n["weapon"]} for i, n in enumerate(notes)],
                            "made_by": f"MPFB hero + Mixamo {fbx} (tools/sprites/build_hero3d.py)"}
                    else:
                        keys.setdefault("chop", {})[d] = {
                            "anim": folder.lower(),
                            **{k: {"frame": i, "hand": notes[i]["hand"], "weapon": notes[i]["weapon"]}
                               for k, i in CHOP_KEYS.items()},
                            "made_by": f"MPFB hero + Mixamo {fbx} (tools/sprites/build_hero3d.py)"}
            print("built", action, dirs)
    for name, parts in MIXED.items():        # from variants already built (their pictures and notes)
        made = keys.get("variants", {})
        if not all(v in made for v, _ in parts.values()):
            continue
        mixed = {}
        for d in CHOP_DIRS:
            def step(v, i):
                note = made[v][d]["all"][i]
                return {"anim": made[v][d]["anim"], "frame": i, "hand": note["hand"], "weapon": note["weapon"]}
            spec = {k: step(v, i) for k, (v, i) in parts.items()}
            wv, wi = parts["windup"]
            hv, hi = parts["hit"]
            seq = [step(wv, i) for i in range(wi + 1)] + [step(hv, i) for i in range(hi, 10)]
            mixed[d] = {"anim": spec["windup"]["anim"], **spec, "all": seq, "all_hit": wi + 1,
                        "made_by": f"key poses mixed from {sorted({v for v, _ in parts.values()})}"}
        keys["variants"][name] = mixed
    keys["default_variant"] = "samurai"      # bat aim, sword lunge and held blade (2026-11-20)
    keys["aim_styles"] = ["chop"]            # the bat aim is for swung weapons; knife and pistol keep their own
    keys["note"] = ("Key-pose attacks for the 3D hero (build_hero3d.py): wind-up and hit picture per direction, "
                    "hand (picture px) and weapon direction (degrees, y up) measured in Blender.")
    out.mkdir(parents=True, exist_ok=True)
    hands_file.write_text(json.dumps(hands, indent=1), encoding="utf-8")
    keys_file.write_text(json.dumps(keys, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
