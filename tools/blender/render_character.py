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
      "pickup=Fixing_Kneeling@0-20",
      # push: a light two-handed shove, the legs held still in the idle stance (2026-11-16: "벽을
      #미는 것 같다" -> cross punch + Push_Loop for both hands; then "하체는 거의 가만히, 상체만
      #가볍게" -> '~Idle_Loop' keeps hips and legs in Idle_Loop's first pose, render_sprites.get_action)
      "push=Punch_Cross~Idle_Loop@0-14+Push_Loop~Idle_Loop*0.45",
      # (a takedown sheet - take hold, short stab - was tried and dropped 2026-11-16 "기습 성공하는 건 빼죠")
      # stomp: on a crawling infected (made from the idle pose, tools/blender/made_actions.py)
      "stomp=Stomp",
      # The plain attacks, one per weapon style (2026-11-16 "애니메이션 동작이 일반적이어야", "다른 무기들을
      # 했을 때도 문제가 없게"): feet planted, the arm does the work. Any weapon of a style uses its
      # sheet; the weapon is painted into the hand. stab = a straight thrust, swingh = across the
      # front, chop = overhead and down (made_actions.py).
      "stab=Punch_Cross~Idle_Loop", "swingh=Swing", "chop=Chop"],
     ["idle=4", "sneak_idle=4", "walk=12", "sneak=12", "run=12", "hurt=3", "down=5", "pickup=4", "push=4",
      "stomp=6", "stab=7", "swingh=7", "chop=7"],
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
     # crawl: an infected that drags itself along (2026-11-16 "기어서도 오는 요소", now a kind of
     # infected from the start); the front crawl stroke seen from the side reads as pulling along
     ["hurt=Hit_Chest", "down=Death01", "crawl=Swim_Fwd_Loop"],
     ["hurt=3", "down=5", "crawl=8"],
     ["--shift-for", "down=16"]),
]
ACTION_SETS = {"hero": PASSES, "infected": INFECTED_PASSES}


def passes_of(costume):
    data = json.loads(Path(costume).read_text(encoding="utf-8"))
    return ACTION_SETS[data.get("actions", "hero")]


# Sprite sizes (2026-11-16 "도트 형식으로"): "full" is the original 54 px person in 96 x 64 cells,
# "dot" a 32 px person in 64 x 48 cells drawn as pixel art (the game shows it on a pixel canvas).
SIZES = {"full": {"cell": (96, 64), "person_px": 54, "feet": 4},
         "dot": {"cell": (64, 48), "person_px": 32, "feet": 3, "empty_handed": True}}
# empty_handed: the sheets show no weapon, only the hand's line per frame (blade.json); the game
# draws whatever weapon is held on that line, so a new weapon needs no new sheets.
SIZE = SIZES["full"]


def size_args(extra):
    """The size flags for render_sprites, and `extra` with its --shift-for px scaled to the size."""
    k = SIZE["person_px"] / 54
    scaled, shifting = [], False
    for arg in extra:
        if arg.startswith("--"):
            shifting = arg == "--shift-for"
            scaled.append(arg)
        elif shifting and "=" in arg:
            sheet, px = arg.split("=")
            scaled.append(f"{sheet}={round(float(px) * k)}")
        else:
            scaled.append(arg)
    w, h = SIZE["cell"]
    return ["--cell", str(w), str(h), "--person-px", str(SIZE["person_px"]), "--feet", str(SIZE["feet"])], scaled


def blender_pass(costume, out, render_pass, name):
    """All sheets of one character for one render pass (color, or id/light/tex for repaint)."""
    out.mkdir(parents=True, exist_ok=True)
    for anim, mapping, counts, extra in passes_of(costume):
        settings = SETTINGS if render_pass == "color" else ["--tilt", "20", "--pass", render_pass]
        sizing, extra = size_args(extra)
        cmd = [BLENDER, "-b", "-P", str(SCRIPT), "--", "--costume", str(costume),
               "--anim-file", str(anim), "--out", str(out),
               "--map", *mapping, "--frames-for", *counts, *settings, *sizing, *extra]
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
                        "--weapon", "none" if SIZE.get("empty_handed") else data.get("weapon", "machete"),
                        "--cell", *map(str, SIZE["cell"]), "--person-px", str(SIZE["person_px"])], check=True)
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
    # The game reads the cell size from look.json (character_look.SheetLook).
    look = out / "look.json"
    meta = json.loads(look.read_text(encoding="utf-8")) if look.exists() else {}
    if SIZE is SIZES["full"]:
        meta.pop("_size", None)
    else:
        meta["_size"] = {"cell": list(SIZE["cell"]), "person_px": SIZE["person_px"], "feet": SIZE["feet"]}
    look.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--size"]:                    # render_character.py --size dot hero_2d:hero
        SIZE = SIZES[args[1]]
        args = args[2:]
    for character in args or ["hero"]:
        render(character)
