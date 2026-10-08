"""One Trepang2 map's full check without taking the focus (console map loads, host test ops, posted keys):

  python scripts/t2_tour.py <map> [<map> ...]      e.g.  python scripts/t2_tour.py Horde_Cafe KillCultists_Persistent

Per map: 1. open it (scripts/t2_open.py), god mode, test blocks + far pillars; 2. the player's gun at the gold block
(op pfire) until it breaks; 3. a frag at the pillars (op nade): Minecraft's crater; 4. zombies around the player and at
an NPC, 15 s of fighting; 5. Focus (Q): Minecraft's tick rate; 6. a kick (right mouse); 7. build mode: grass blocks;
8. FPS, host warnings, Trepang2 and Minecraft alive. Writes lab/tour/<map>.txt + screenshots and a row in
lab/tour/summary.md. Minecraft must be in its world (scripts/mc_dev.py).
"""
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIN64 = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Trepang2\CPPFPS\Binaries\Win64")
LOG = WIN64 / "ue4ss" / "UE4SS.log"
MC_LOG = ROOT / "src" / "mc" / "run" / "logs" / "latest.log"
TOUR = ROOT / "lab" / "tour"
sys.path.insert(0, str(ROOT / "scripts"))
import op  # noqa: E402


def text(path):
    try:
        return path.read_text(errors="replace")
    except OSError:
        return ""


def ps(script):
    return subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script], capture_output=True, text=True)


def send(*messages):
    op.send(list(messages))


def gta(name, **kw):
    parts = ['"t":"gta"', f'"op":"{name}"'] + [f'"{k}":{v}' for k, v in kw.items()]
    send("{" + ",".join(parts) + "}")


def key(vk):
    ps(f"& '{ROOT / 'scripts' / 't2-postkey.ps1'}' {vk}")


def click(button):
    ps(f"& '{ROOT / 'scripts' / 't2-postmouse.ps1'}' {button}")


def shot(path):
    subprocess.run(["bash", "-lc", f"um win shot --exe CPPFPS-Win64-Shipping.exe '{path}' --scale 0.5"], capture_output=True)


def alive():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "crash_check.py"), "alive"], capture_output=True, text=True)
    return r.returncode == 0


def host_since(mark):
    return [l for l in text(LOG)[mark:].splitlines() if "[T2Passthrough]" in l]


def fps_from(lines):
    """Frames per second from the host's stats lines (every 300 frames, with the log's timestamps)."""
    stamps = []
    for l in lines:
        if "] cam UE" in l and "frames " in l:
            m = re.match(r"\[\d+-\d+-\d+ (\d+):(\d+):([\d.]+)\]", l)
            if m:
                stamps.append(int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)))
    if len(stamps) < 2:
        return None
    return 300.0 * (len(stamps) - 1) / (stamps[-1] - stamps[0])


def tour(name):
    out = []
    say = lambda s: (print(s, flush=True), out.append(s))
    shots = TOUR / name
    shots.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([sys.executable, "-u", str(ROOT / "scripts" / "t2_open.py"), name], capture_output=True, text=True)
    say(f"open: {r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr.strip()[-200:]}")
    if r.returncode != 0:
        return out, {"map": name, "ok": False, "why": "not in game"}
    mark = len(text(LOG))
    mc_mark = len(text(MC_LOG))
    res = {"map": name}
    gta("god", v=1)
    # a clean start: the blocks earlier runs left in this map's region (grass from build mode, broken pillars) out of
    # the way, so the zombies of steps 4 and 6 have room to stand in front of the player
    import scene
    x, y, z, _ = scene.pose()
    for kind in scene.TEST_BLOCKS:
        send('{"t":"cmd","c":"fill %d %d %d %d %d %d minecraft:air replace minecraft:%s"}' % (int(x) - 20, int(y) - 6, int(z) - 20, int(x) + 20, int(y) + 6, int(z) + 20, kind))
    time.sleep(1.0)
    gta("test", v=1)
    # on a first visit Minecraft generates this map's region first: wait for the test blocks (sent after "test blocks
    # placed") to come back as collision boxes here
    for _ in range(40):
        time.sleep(0.5)
        lines = host_since(mark)
        after = next((i for i, l in enumerate(lines) if "test blocks placed" in l), None)
        if after is not None and any(re.search(r"blocks: \+([3-9]|\d\d+) -\d+, [1-9]\d* boxes", l) for l in lines[after:]):
            break
    time.sleep(1.5)
    shot(shots / "1_blocks.png")
    # 2. the gold block, 3 m ahead on the floor: aim at its middle (where the host put it) and shoot until it breaks
    gta("look", yaw=0, pitch=-22, abs=1)
    time.sleep(0.6)
    gold = next((m for l in reversed(host_since(mark)) for m in [re.search(r"test gold block at \((-?\d+), (-?\d+), (-?\d+)\)", l)] if m), None)
    if gold:
        import math
        x, y, z, now = scene.pose()
        gx, gy, gz = int(gold[1]) + 0.5, int(gold[2]) + 0.5, int(gold[3]) + 0.5
        # UE's yaw is measured in Minecraft's x/z plane the same way; the op turns the yaw by this much, sets the pitch
        turn = (math.degrees(math.atan2(gz - z, gx - x)) - now + 540.0) % 360.0 - 180.0
        pitch = math.degrees(math.atan2(gy - y, math.hypot(gx - x, gz - z)))
        gta("look", yaw=round(turn, 2), pitch=round(pitch, 2), abs=1)
        time.sleep(0.6)
    for _ in range(6):
        gta("fire", v=4)  # the real trigger: the gun fires, the host counts it as the mouse button's shot
        time.sleep(0.6)
    time.sleep(1)
    shot(shots / "2_shot.png")
    lines = host_since(mark)
    res["block_hits"] = sum("player shot block" in l for l in lines)
    res["block_broken"] = "apart" in text(MC_LOG)[mc_mark:]
    # 3. a frag towards the pillars
    gta("look", yaw=0, pitch=-8, abs=1)
    time.sleep(0.5)
    gta("nade")
    time.sleep(5)
    shot(shots / "3_nade.png")
    lines = host_since(mark)
    res["explosions"] = sum("Trepang2 explosion at" in l for l in lines)
    removed = sum(int(m.group(1)) for l in lines for m in [re.search(r"blocks: \+\d+ -(\d+)", l)] if m)
    res["blocks_removed"] = removed
    # 4. zombies: around the player and at an NPC
    gta("mobs", v=3)
    gta("mobsat", v=3)
    time.sleep(15)
    shot(shots / "4_fight.png")
    lines = host_since(mark)
    res["npc_shots"] = sum(" shoots mob " in l for l in lines)
    res["mob_hits"] = sum("mob hit ped" in l for l in lines)
    gta("mobsclear")
    # 5. Focus
    gta("slowmo")
    time.sleep(1.5)
    shot(shots / "5_focus.png")
    gta("slowmo")
    time.sleep(1.5)
    lines = host_since(mark)
    res["slowmo"] = any("time dilation 0." in l for l in lines)
    # 6. a kick at a zombie in front
    gta("look", yaw=0, pitch=-5, abs=1)
    send('{"t":"spawnmobs","k":"zombie","n":1,"rmin":1.6,"rmax":2.2,"arc":10}')
    time.sleep(2.5)
    gta("kick")
    time.sleep(1)
    gta("mobsclear")
    lines = host_since(mark)
    res["kick"] = any("player kick" in l for l in lines)
    # 7. build mode: grass blocks on the floor in front
    gta("build")
    time.sleep(0.6)
    key("0x38")
    gta("look", yaw=-20, pitch=-40, abs=1)
    before = sum(1 for l in host_since(mark) if re.search(r"blocks: \+[1-9]\d* -0", l))
    for _ in range(4):
        click("right")
        time.sleep(0.35)
        gta("look", yaw=10, pitch=0)
        time.sleep(0.25)
    time.sleep(1)
    shot(shots / "7_build.png")
    gta("build")
    lines = host_since(mark)
    res["placed"] = sum(1 for l in lines if re.search(r"blocks: \+[1-9]\d* -0", l)) - before
    res["fps"] = fps_from(lines)
    warn = [l for l in lines if re.search(r"no UFunction|no parameter|NOT usable|could not|SAFE MODE", l)]
    res["warnings"] = len(warn)
    for w in warn[:5]:
        say("  warning: " + w[w.find("[T2Passthrough]"):][:200])
    res["alive"] = alive()
    res["ok"] = res["alive"] and res["block_hits"] > 0 and res["explosions"] > 0 and res["slowmo"]
    say(" | ".join(f"{k} {v:.0f}" if isinstance(v, float) else f"{k} {v}" for k, v in res.items()))
    return out, res


def main(maps):
    TOUR.mkdir(parents=True, exist_ok=True)
    summary = TOUR / "summary.md"
    if not summary.exists():
        summary.write_text("| time | map | ok | block hits | broken | explosions | removed | NPC shots | mob hits | focus | kick | placed | FPS | warnings | alive |\n"
                           "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n", encoding="utf-8")
    for name in maps:
        print(f"=== {name}", flush=True)
        out, r = tour(name)
        (TOUR / f"{name}.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
        g = lambda k: r.get(k, "-")
        fps = r.get("fps")
        with summary.open("a", encoding="utf-8") as f:
            f.write(f"| {time.strftime('%m-%d %H:%M')} | {name} | {'yes' if r.get('ok') else 'NO'} | {g('block_hits')} | {g('block_broken')} | {g('explosions')} | "
                    f"{g('removed') if 'removed' in r else g('blocks_removed')} | {g('npc_shots')} | {g('mob_hits')} | {g('slowmo')} | {g('kick')} | {g('placed')} | "
                    f"{f'{fps:.0f}' if fps else '-'} | {g('warnings')} | {g('alive')} |\n")
        if not r.get("alive", True):
            print("Trepang2 is not alive: stopping the tour", flush=True)
            return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
