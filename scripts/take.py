"""Records one take of the Trepang2 x Minecraft passthrough: Trepang2's window, its audio and Minecraft's audio (each its
own process loopback), while a shot list drives the games. Then muxes everything to <out>.mp4.

  uv run --project <universal-modder> python scripts/take.py video/shots/build.json video/takes/build

Shot list: {"lead": 1.0, "tail": 1.5, "steps": [...]} where a step is one of
  {"op": ["mobs", "3"]}                      scripts/op.py arguments (host test ops, or "--raw" + JSON)
  {"drive": ["key 0x60", "click 960 600 right"]}  WinDrive commands on RoN's window
  {"turn": [dx, steps, ms]}  {"look": [dx, dy]}   relative mouse (smooth turn / one move)
  {"hold": ["0x57", 1500]}                   hold a key (ms)
  {"wait": 1.2}                              seconds
  {"mark": "tnt"}                            prints the take time, to find moments when cutting
  {"ahead": [6, 0, "summon minecraft:tnt {x} {y} {z} {{fuse:50}}"]}   a Minecraft command at d m ahead of the camera,
                                             s m to the right, on the floor under it ({x} {y} {z}: block centre)
  {"fire": [count, ms]}                      the player's gun: count trigger pulls (host op fire, no focus needed)
  {"yaw": [degrees, steps, ms]}              a smooth turn of the view (host op look), no focus needed
  {"pitch": degrees}                         the view's pitch, absolute
  {"move": [forward, right, frames]}         walk (host op move)
  {"near": [metres, seconds]}               wait until the nearest Minecraft mob is that close (host op mobdist)
Shot lists that use only ops, yaw, pitch, move, fire, ahead and waits never take the focus (someone may be working).
"""
import ctypes
import json
import subprocess
import sys
import time
from pathlib import Path

from um.win import Drive, Recorder, pid_of, ps_exe, tool_path

ROOT = Path(__file__).resolve().parent.parent
RON = "CPPFPS-Win64-Shipping.exe"
HISTORY = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Trepang2\CPPFPS\Binaries\Win64\ue4ss\Mods\T2Passthrough\history.log")


def pose():
    """The camera now: (MC x, y, z, UE yaw in degrees), from the host's answer to op pose."""
    import re
    subprocess.run([sys.executable, str(ROOT / "scripts" / "op.py"), "pose"], capture_output=True)
    time.sleep(0.25)
    for line in reversed(HISTORY.read_text(errors="replace").splitlines()[-400:]):
        m = re.search(r"pose: cam UE \([^)]*\) yaw (-?[\d.]+) pitch (-?[\d.]+) -> MC \((-?[\d.]+), (-?[\d.]+), (-?[\d.]+)\)", line)
        if m:
            return float(m[3]), float(m[4]), float(m[5]), float(m[1])
    raise RuntimeError("no pose in history.log")


_pose = None


def ahead(d, side, template, dy=0):
    """Uses the pose taken by the last {"pose": 1} step (one pose for a whole wall of blocks), else asks now."""
    import math
    x, y, z, yaw = _pose or pose()
    r = math.radians(yaw)
    fx, fz = math.cos(r), math.sin(r)
    bx = math.floor(x + fx * d - fz * side) + 0.5
    bz = math.floor(z + fz * d + fx * side) + 0.5
    by = round(y - 1.6) + dy  # the feet: Trepang2's eyes are 1.6 m above them
    cmd = template.format(x=bx, y=by, z=bz, ix=int(bx - 0.5), iy=by, iz=int(bz - 0.5), iy1=by + 1, iy2=by + 2, iy3=by + 3, iy4=by + 4)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "op.py"), "--raw", json.dumps({"t": "cmd", "c": cmd})], capture_output=True)
user32 = ctypes.windll.user32


def op_raw(message):
    """One message on the link, as JSON without spaces (the host matches "op":"name" literally)."""
    subprocess.run([sys.executable, str(ROOT / "scripts" / "op.py"), "--raw", json.dumps(message, separators=(",", ":"))], capture_output=True)


def mouse(dx, dy):
    user32.mouse_event(1, int(dx), int(dy), 0, 0)


def run_steps(steps, drive, t0):
    for step in steps:
        if "op" in step:
            subprocess.run([sys.executable, str(ROOT / "scripts" / "op.py"), *step["op"]], capture_output=True)
        elif "drive" in step:
            for cmd in step["drive"]:
                drive.cmd(cmd)
        elif "turn" in step:
            dx, n, ms = step["turn"]
            start = time.perf_counter()
            for i in range(1, n + 1):
                mouse(dx, 0)
                while time.perf_counter() - start < i * ms / 1000.0:
                    pass
        elif "look" in step:
            mouse(*step["look"])
        elif "hold" in step:
            drive.cmd(f"hold {step['hold'][0]} {step['hold'][1]}")
        elif "wait" in step:
            time.sleep(step["wait"])
        elif "pose" in step:
            global _pose
            _pose = pose()
        elif "ahead" in step:
            ahead(*step["ahead"])
        elif "fire" in step:
            n, ms = step["fire"]
            for _ in range(n):
                op_raw({"t": "gta", "op": "fire", "v": 4})
                time.sleep(ms / 1000.0)
        elif "yaw" in step:
            deg, n, ms = step["yaw"]
            for _ in range(n):
                op_raw({"t": "gta", "op": "look", "yaw": deg / n, "pitch": 0})
                time.sleep(ms / 1000.0)
        elif "pitch" in step:
            op_raw({"t": "gta", "op": "look", "yaw": 0, "pitch": step["pitch"], "abs": 1})
        elif "move" in step:
            f, r, frames = step["move"]
            op_raw({"t": "gta", "op": "move", "f": f, "r": r, "v": frames})
        elif "mark" in step:
            print(f"  {time.time() - t0:6.2f}s  {step['mark']}", flush=True)
        elif "near" in step:
            # wait until the nearest Minecraft mob is closer than d metres (host op mobdist), at most s seconds
            import re
            d, limit = step["near"]
            end = time.time() + limit
            while time.time() < end:
                subprocess.run([sys.executable, str(ROOT / "scripts" / "op.py"), "mobdist"], capture_output=True)
                time.sleep(0.15)
                line = next((l for l in reversed(HISTORY.read_text(errors="replace").splitlines()[-60:]) if "nearest" in l), "")
                m = re.search(r"nearest (\d+(?:\.\d+)?) m", line)
                if m and float(m[1]) < d:
                    print(f"  {time.time() - t0:6.2f}s  mob at {m[1]} m", flush=True)
                    break


def main(shots, out):
    shot = json.loads(Path(shots).read_text())
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    drive = Drive("CPPFPS-Win64-Shipping")
    # a shot list of ops only needs no input: leave the focus alone (someone may be using the PC)
    if any("drive" in st or "turn" in st or "look" in st or "hold" in st for st in shot["steps"]):
        drive.cmd("focus")
    # Minecraft's sound (blocks, TNT, mobs) from its own process
    mc_pid = pid_of("javaw.exe") or pid_of("java.exe")  # the Gradle dev client runs as java.exe
    mc = subprocess.Popen([ps_exe(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", tool_path("ProcLoopback.ps1"),
                           "-TargetPid", str(mc_pid), "-Out", out + ".mc.audio.raw"],
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    mc_header = json.loads(mc.stdout.readline() or "{}")
    rec = Recorder(exe=RON, out=out, fps=60).start()
    t0 = time.time()
    time.sleep(shot.get("lead", 1.0))
    try:
        run_steps(shot["steps"], drive, t0)
        time.sleep(shot.get("tail", 1.5))
    finally:
        meta = rec.stop()
        mc.stdin.write("\n")
        mc.stdin.flush()
        mc.wait(10)
    # the same instant in both audio files: video start = RoN audio position audio_offset_s
    t_video_hns = meta["start_hns"] + meta["audio_offset_s"] * 1e7
    mc_pos = (t_video_hns - mc_header["start_hns"]) / 1e7
    ff = "ffmpeg"
    cmd = [ff, "-hide_banner", "-loglevel", "error", "-y", "-i", out + ".mkv",
           "-f", "f32le", "-ar", "48000", "-ac", "2", "-ss", f"{max(0.0, meta['audio_offset_s']):.3f}", "-i", meta["audio"],
           "-f", "f32le", "-ar", "48000", "-ac", "2", "-ss", f"{max(0.0, mc_pos):.3f}", "-i", out + ".mc.audio.raw",
           "-filter_complex", "[1:a][2:a]amix=inputs=2:normalize=0:duration=first[a]",
           "-map", "0:v", "-map", "[a]", "-shortest", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out + ".mp4"]
    subprocess.run(cmd, check=True)
    print("take ->", out + ".mp4")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
