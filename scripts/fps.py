"""RoN's frame rate from the host mod's log: its stats line ("cam UE ... frames N") comes every 300 game ticks, with a
timestamp, so fps = 300 / (time between two lines). Needs RoN in the game proper, in front, not paused.

  python scripts/fps.py                    fps over the last 20 s
  python scripts/fps.py sweep              composite off, then Minecraft at 100 / 75 / 50 % render size (op mcscale),
                                           ~20 s each; prints a table (the player stands still, same view)
"""
import datetime
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import op  # noqa: E402

LOG = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Trepang2\CPPFPS\Binaries\Win64\ue4ss\UE4SS.log")


def stamps(since):
    out = []
    for line in LOG.read_text(errors="replace").splitlines():
        if "[T2Passthrough] cam UE" not in line:
            continue
        m = re.match(r"\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+)", line)
        if m:
            t = datetime.datetime.strptime(m.group(1)[:26], "%Y-%m-%d %H:%M:%S.%f").timestamp()
            if t >= since:
                out.append(t)
    return out


def fps_since(since):
    t = stamps(since)
    if len(t) < 2:
        return None
    return 300.0 * (len(t) - 1) / (t[-1] - t[0])


def measure(seconds=20.0, settle=4.0):
    time.sleep(settle)
    start = time.time()
    time.sleep(seconds)
    return fps_since(start)


def main(args):
    if args and args[0] == "sweep":
        rows = []
        op.send(['{"t":"gta","op":"toggle"}'])
        rows.append(("composite off", measure()))
        op.send(['{"t":"gta","op":"toggle"}'])
        for scale in (100, 75, 50):
            op.send([f'{{"t":"gta","op":"mcscale","v":{scale}}}'])
            rows.append((f"Minecraft at {scale} %", measure()))
        op.send(['{"t":"gta","op":"mcscale","v":75}'])  # the default
        for name, fps in rows:
            print(f"  {name:22s} {fps:6.1f} fps" if fps else f"  {name:22s}   n/a")
    else:
        fps = fps_since(time.time() - 20.0)
        print(f"{fps:.1f} fps over the last 20 s" if fps else "no stats lines in the last 20 s")


if __name__ == "__main__":
    main(sys.argv[1:])
