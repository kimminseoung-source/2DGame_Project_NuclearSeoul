"""Render every action sheet of one character from its costume, with the shared settings.

    .venv\\Scripts\\python.exe tools/blender/render_character.py hero [nurse worker ...]

For each name it reads assets/characters/costumes/<name>.json and writes the sheets the game
uses into assets/characters/<name>/ (idle, sneak_idle, walk, sneak, swing, hurt, down,
pickup) plus look.json (strides and the impact frame, copied from base/ because every
character shares the base body's actions). The action list and render settings live here
once, so all characters are made the same way (CHARACTER_WORKFLOW.md section 4).
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
SCRIPT = ROOT / "tools" / "blender" / "render_sprites.py"
LIB1 = ROOT / "assets/source3d/quaternius_animation_library/Unreal-Godot/UAL1_Standard.glb"
LIB2 = ROOT / "assets/source3d/quaternius_animation_library_2/Unreal-Godot/UAL2_Standard.glb"
SETTINGS = ["--tilt", "20", "--bands", "4", "--outline"]

# (animation file, sheet=action list, sheet=frame count list, extra arguments)
PASSES = [
    (LIB1,
     ["idle=Idle_Loop", "sneak_idle=Idle_Loop+Crouch_Idle_Loop*0.3", "walk=Walk_Loop",
      "sneak=Walk_Loop+Crouch_Idle_Loop*0.3", "run=Jog_Fwd_Loop", "hurt=Hit_Chest", "down=Death01",
      "pickup=Fixing_Kneeling@0-20"],
     ["idle=4", "sneak_idle=4", "walk=12", "sneak=12", "run=12", "hurt=3", "down=5", "pickup=4"],
     ["--shift-for", "down=16"]),
    (LIB2,
     # Machete combo (2026-11-13, the user's pick from the sheets: "back to this one"):
     # 1st a quick sweep (B, wind-up cut off), 2nd a short rising cut (A from its crouch on,
     # fewer frames), 3rd the overhead chop - the finisher of the pack's own
     # Sword_Regular_Combo, so all three come from one animated combo. The time-warp
     # release swings the 3rd hit too.
     ["swing=Sword_Regular_B@2-13,Sword_Regular_B_Rec", "swing2=Sword_Regular_A@4-,Sword_Regular_A_Rec@7-23",
      "swing3=Sword_Regular_Combo@31.5-34.5,Sword_Regular_Combo@37.6-41,Sword_Regular_Combo@51-72"],
     ["swing=4,3", "swing2=4,3", "swing3=2,2,3"],
     []),
]


# Infected (people who died past the radiation limit and turned, PRD 12): the same base body
# with the pack's zombie motions. Sheet names are what zombie.py asks the look for.
INFECTED_PASSES = [
    (LIB2,
     ["idle=Zombie_Idle_Loop", "walk=Zombie_Walk_Fwd_Loop", "attack=Zombie_Scratch"],
     ["idle=4", "walk=12", "attack=8"],
     []),
    (LIB1,
     ["hurt=Hit_Chest", "down=Death01"],
     ["hurt=3", "down=5"],
     ["--shift-for", "down=16"]),
]
ACTION_SETS = {"hero": PASSES, "infected": INFECTED_PASSES}


def passes_of(costume):
    data = json.loads(Path(costume).read_text(encoding="utf-8"))
    return ACTION_SETS[data.get("actions", "hero")]


def blender_pass(costume, out, render_pass, name):
    """All sheets of one character for one render pass (color, or id/light/tex for repaint)."""
    out.mkdir(parents=True, exist_ok=True)
    for anim, mapping, counts, extra in passes_of(costume):
        settings = SETTINGS if render_pass == "color" else ["--tilt", "20", "--pass", render_pass]
        cmd = [BLENDER, "-b", "-P", str(SCRIPT), "--", "--costume", str(costume),
               "--anim-file", str(anim), "--out", str(out),
               "--map", *mapping, "--frames-for", *counts, *settings, *extra]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        saved = [line for line in result.stdout.splitlines() if line.startswith("saved")]
        print(f"[{name}:{render_pass}] {len(saved)} sheets")
        if result.returncode or len(saved) != len(mapping):
            print(result.stdout[-2000:], result.stderr[-2000:])
            raise SystemExit(f"[{name}] render failed")


EXPORT = ROOT / "tools" / "blender" / "export_pose2d.py"


def export_poses(out, name, costume):
    """Screen joints of every frame of every sheet (same frames as the renders)."""
    files = []
    for index, (anim, mapping, counts, extra) in enumerate(passes_of(costume)):
        target = out / f"poses_{index}.json"
        cmd = [BLENDER, "-b", "-P", str(EXPORT), "--", "--anim-file", str(anim),
               "--map", *mapping, "--frames-for", *counts, "--out", str(target)]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode or not target.exists():
            print(result.stdout[-2000:], result.stderr[-2000:])
            raise SystemExit(f"[{name}] pose export failed")
        files.append(str(target))
    return files


def render(spec):
    """spec = "costume" or "costume:folder" (e.g. hero_q:hero writes assets/characters/hero/)."""
    name, _, folder = spec.partition(":")
    costume = ROOT / "assets" / "characters" / "costumes" / f"{name}.json"
    out = ROOT / "assets" / "characters" / (folder or name)
    data = json.loads(costume.read_text(encoding="utf-8"))
    if data.get("paint_clothes"):
        # Rotoscoping with 2D drawing: the base body's part map and light, then the clothes
        # are painted in pixels over every frame (tools/sprites/paint_clothes.py).
        passes = out / "_passes"
        for render_pass in ("id", "light"):
            blender_pass(costume, passes / render_pass, render_pass, name)
        poses = export_poses(passes, name, costume)
        subprocess.run([sys.executable, str(ROOT / "tools" / "sprites" / "paint_clothes.py"),
                        "--id", str(passes / "id"), "--light", str(passes / "light"),
                        "--poses", *poses, "--out", str(out), "--outfit", str(costume),
                        *([] if data.get("backpack", True) else ["--no-pack"]),
                        "--weapon", data.get("weapon", "machete")], check=True)
    elif "repaint" in data:
        # Rotoscoping: part IDs, light and the clothes' own texture, then repaint with the
        # concept colours (tools/sprites/repaint.py). The passes stay out of git (_passes/).
        passes = out / "_passes"
        for render_pass in ("id", "light", "tex"):
            blender_pass(costume, passes / render_pass, render_pass, name)
        subprocess.run([sys.executable, str(ROOT / "tools" / "sprites" / "repaint.py"), "--costume", str(costume),
                        "--id", str(passes / "id"), "--light", str(passes / "light"), "--tex", str(passes / "tex"),
                        "--out", str(out)], check=True)
    else:
        blender_pass(costume, out, "color", name)
    if data.get("actions", "hero") == "hero":
        shutil.copyfile(ROOT / "assets" / "characters" / "base" / "look.json", out / "look.json")


if __name__ == "__main__":
    for character in sys.argv[1:] or ["hero"]:
        render(character)
