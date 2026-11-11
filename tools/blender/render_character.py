"""Render every action sheet of one character from its costume, with the shared settings.

    .venv\\Scripts\\python.exe tools/blender/render_character.py hero [nurse worker ...]

For each name it reads assets/characters/costumes/<name>.json and writes the sheets the game
uses into assets/characters/<name>/ (idle, sneak_idle, walk, sneak, swing, hurt, down,
pickup) plus look.json (strides and the impact frame, copied from base/ because every
character shares the base body's actions). The action list and render settings live here
once, so all characters are made the same way (CHARACTER_WORKFLOW.md section 4).
"""

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
      "sneak=Walk_Loop+Crouch_Idle_Loop*0.3", "hurt=Hit_Chest", "down=Death01",
      "pickup=Fixing_Kneeling@0-20"],
     ["idle=4", "sneak_idle=4", "walk=12", "sneak=12", "hurt=3", "down=5", "pickup=4"],
     ["--shift-for", "down=16"]),
    (LIB2,
     ["swing=Sword_Regular_A,Sword_Regular_A_Rec@7-23"],
     ["swing=6,3"],
     []),
]


def render(name):
    costume = ROOT / "assets" / "characters" / "costumes" / f"{name}.json"
    out = ROOT / "assets" / "characters" / name
    out.mkdir(parents=True, exist_ok=True)
    for anim, mapping, counts, extra in PASSES:
        cmd = [BLENDER, "-b", "-P", str(SCRIPT), "--", "--costume", str(costume),
               "--anim-file", str(anim), "--out", str(out),
               "--map", *mapping, "--frames-for", *counts, *SETTINGS, *extra]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        saved = [line for line in result.stdout.splitlines() if line.startswith("saved")]
        for line in saved:
            print(f"[{name}] {line}")
        if result.returncode or len(saved) != len(mapping):
            print(result.stdout[-2000:], result.stderr[-2000:])
            raise SystemExit(f"[{name}] render failed")
    shutil.copyfile(ROOT / "assets" / "characters" / "base" / "look.json", out / "look.json")


if __name__ == "__main__":
    for character in sys.argv[1:] or ["hero"]:
        render(character)
