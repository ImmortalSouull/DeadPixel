"""Plays a shot list against the running games without recording and without taking the focus (plain Python, no
dependencies): for spot checks and screenshots.

  python scripts/scene.py video/shots/bt_kick.json [--shot lab/shots/kick.png]

Steps (the same as take.py's focus-free ones): op, pose, ahead, wait, mark, fire, yaw, pitch, move, plus
  {"shot": "lab/shots/x.png"}   a screenshot of Trepang2's window (um win shot, half size)
  {"turn": [yaw_deg_per_s, pitch_deg_per_s, frames]}   a smooth turn through the host (op turn)
  {"press": ["jump"|"crouch"|"sprint"|"zoom", frames]}   a button held (op press)
  {"cmd": "time set noon"}      a Minecraft command as is
  {"clear": 8}                  air within 8 blocks of the camera and no mobs (leftovers of earlier tests)
  {"mouse": "right"}  {"key": "0x38"}   a mouse button / a key posted to Trepang2's window (build mode: to Minecraft)
"""
import json
import math
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# what the test scenes build with (and what explosions leave of it)
TEST_BLOCKS = ["bricks", "glowstone", "oak_planks", "iron_block", "glass", "dirt", "stone", "cobblestone", "grass_block", "tnt", "gold_block",
               "diamond_block", "emerald_block", "obsidian", "oak_log", "sand", "gravel", "fire"]
HISTORY = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Trepang2\CPPFPS\Binaries\Win64\ue4ss\Mods\T2Passthrough\history.log")
_pose = None


def op(*args):
    subprocess.run([sys.executable, str(ROOT / "scripts" / "op.py"), *args], capture_output=True)


def raw(obj):
    op("--raw", json.dumps(obj, separators=(",", ":")))


def pose():
    raw({"t": "gta", "op": "pose"})
    time.sleep(0.3)
    for line in reversed(HISTORY.read_text(errors="replace").splitlines()[-400:]):
        m = re.search(r"pose: cam UE \([^)]*\) yaw (-?[\d.]+) pitch (-?[\d.]+) -> MC \((-?[\d.]+), (-?[\d.]+), (-?[\d.]+)\)", line)
        if m:
            return float(m[3]), float(m[4]), float(m[5]), float(m[1])
    raise RuntimeError("no pose in history.log")


def ahead(d, side, template, dy=0):
    x, y, z, yaw = _pose or pose()
    r = math.radians(yaw)
    fx, fz = math.cos(r), math.sin(r)
    bx = math.floor(x + fx * d - fz * side) + 0.5
    bz = math.floor(z + fz * d + fx * side) + 0.5
    by = round(y - 1.6) + dy
    cmd = template.format(x=bx, y=by, z=bz, ix=int(bx - 0.5), iy=by, iz=int(bz - 0.5), iy1=by + 1, iy2=by + 2, iy3=by + 3, iy4=by + 4)
    raw({"t": "cmd", "c": cmd})


def shot(path):
    path = str(ROOT / path) if not Path(path).is_absolute() else path
    subprocess.run(["bash", "-lc", f"um win shot --exe CPPFPS-Win64-Shipping.exe '{Path(path).as_posix()}' --scale 0.5"], capture_output=True)
    print("shot", path)


def run(steps, t0=None):
    global _pose
    t0 = t0 or time.time()
    for s in steps:
        if "op" in s:
            op(*s["op"])
        elif "pose" in s:
            _pose = pose()
        elif "ahead" in s:
            ahead(*s["ahead"])
        elif "clear" in s:
            # the test blocks within this radius of the camera go (leftovers of earlier tests in this map's region), and
            # every mob. Only the kinds the tests place: a plain fill to air would take the host's barriers (its floors and
            # walls) with them, and then nothing can be placed or spawned there until the level is re-entered
            x, y, z, _ = _pose or pose()
            r = int(s["clear"])
            x0, y0, z0 = int(math.floor(x)) - r, int(round(y - 1.6)) - 1, int(math.floor(z)) - r
            x1, y1, z1 = int(math.floor(x)) + r, int(round(y - 1.6)) + 6, int(math.floor(z)) + r
            for kind in TEST_BLOCKS:
                raw({"t": "cmd", "c": f"fill {x0} {y0} {z0} {x1} {y1} {z1} minecraft:air replace minecraft:{kind}"})
            raw({"t": "cmd", "c": "kill @e[type=!player]"})
        elif "cmd" in s:
            raw({"t": "cmd", "c": s["cmd"]})
        elif "wait" in s:
            time.sleep(s["wait"])
        elif "mark" in s:
            print(f"{time.time() - t0:6.2f}  {s['mark']}", flush=True)
        elif "fire" in s:
            count, ms = s["fire"]
            for _ in range(count):
                raw({"t": "gta", "op": "fire", "v": 4})
                time.sleep(ms / 1000.0)
        elif "yaw" in s:
            deg, steps_, ms = s["yaw"]
            for _ in range(steps_):
                raw({"t": "gta", "op": "look", "yaw": deg / steps_, "pitch": 0})
                time.sleep(ms / 1000.0 / steps_)
        elif "pitch" in s:
            raw({"t": "gta", "op": "look", "yaw": 0, "pitch": s["pitch"], "abs": 1})
        elif "move" in s:
            f, r, frames = s["move"]
            raw({"t": "gta", "op": "move", "f": f, "r": r, "v": frames})
        elif "turn" in s:
            y, p, frames = s["turn"]
            raw({"t": "gta", "op": "turn", "yaw": y, "pitch": p, "v": frames})
        elif "press" in s:
            k, frames = s["press"]
            raw({"t": "gta", "op": "press", "k": k, "v": frames})
        elif "mouse" in s:
            # a mouse button posted to Trepang2's window (left|right); in build mode it goes to Minecraft
            subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "scripts" / "t2-postmouse.ps1"), s["mouse"]], capture_output=True)
        elif "key" in s:
            # a key posted to Trepang2's window (virtual-key code as hex text, e.g. "0x38" = 8)
            subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "scripts" / "t2-postkey.ps1"), s["key"]], capture_output=True)
        elif "shot" in s:
            shot(s["shot"])
        time.sleep(0.12)


if __name__ == "__main__":
    args = sys.argv[1:]
    spec = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    run(spec["steps"])
    if "--shot" in args:
        shot(args[args.index("--shot") + 1])
