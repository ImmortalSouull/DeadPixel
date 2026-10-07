"""Loads a Trepang2 map without a single click (no menus, works while Windows' focus is elsewhere):

  python scripts/t2_open.py <map> [--restart] [--deploy]
  e.g.  python scripts/t2_open.py Horde_Cafe       (maps: lab/maps.txt, e.g. Horde_*, SafeHouse_Persistent)

  --restart  close Trepang2 first (like its window's X; killed by PID only if it hangs)
  --deploy   with --restart: scripts/deploy-host.ps1 while Trepang2 is closed
Trepang2 is started if it isn't running (its window moved to the laptop screen at 1920x1200 like
ron-to-station.ps1 -Laptop), Minecraft must be listening (the dev client or the real one). The map is opened with the
console command "open <map>" through the host mod's console op, from the main menu or from another map, and the
script waits for the host's "in game" line. Map names: the levels' *_BarricadedSuspects_Core (see MAPS in
release_tour.py). Exit 0 in game, 2 not in game in time, 3 Trepang2 gone.
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIN64 = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Trepang2\CPPFPS\Binaries\Win64")
EXE = WIN64 / "CPPFPS-Win64-Shipping.exe"
LOG = WIN64 / "ue4ss" / "UE4SS.log"
sys.path.insert(0, str(ROOT / "scripts"))
import op  # noqa: E402


def ps(script):
    return subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script], capture_output=True, text=True)


def pid():
    r = ps("(Get-Process CPPFPS-Win64-Shipping -ErrorAction SilentlyContinue | Select-Object -First 1).Id")
    return int(r.stdout.strip()) if r.stdout.strip().isdigit() else None


def log_text():
    try:
        return LOG.read_text(errors="replace")
    except OSError:
        return ""


def close():
    p = pid()
    if p is None:
        return
    ps(f"(Get-Process -Id {p}).CloseMainWindow() | Out-Null")
    for _ in range(40):
        time.sleep(1)
        if pid() is None:
            time.sleep(2)
            return
    subprocess.run(["taskkill", "/PID", str(p), "/F"], capture_output=True)
    time.sleep(4)


def start():
    started = time.time()
    # through Steam: the exe is wrapped by Steam's DRM and started directly it quietly does nothing. The user may be
    # working meanwhile: the window they had in front gets the focus back each time the game's window takes it.
    fg = ps(f"& '{ROOT / 'scripts' / 'fg.ps1'}' save").stdout.strip()
    subprocess.Popen(["cmd", "/c", "start", "", "steam://rungameid/1164940"])
    for _ in range(60):
        time.sleep(2)
        if pid() is not None:
            break
    else:
        print("Trepang2 did not start")
        sys.exit(3)
    if fg.isdigit():
        for _ in range(12):
            time.sleep(1.5)
            ps(f"& '{ROOT / 'scripts' / 'fg.ps1'}' restore {fg}")
    # the title screen ("PRESS ANY KEY") has no player yet: Enter is posted to the window (no focus needed) until the
    # host logs its camera (and Minecraft connects)
    moved = False
    for i in range(150):
        time.sleep(2)
        if pid() is None:
            print("Trepang2 is gone")
            sys.exit(3)
        if i > 3 and i % 2 == 0:
            # the laptop screen, 1920x1200, without activating it; again and again while starting (the game sizes its
            # window to the main screen once more while it comes up)
            laptop()
        if LOG.exists() and LOG.stat().st_mtime > started and "camera manager found" in log_text():
            break
        if i > 8 and i % 3 == 0:
            ps(f"& '{ROOT / 'scripts' / 't2-postkey.ps1'}' 13")
    time.sleep(4)


def laptop():
    ps(f"& '{ROOT / 'scripts' / 't2-laptop.ps1'}'")


def open_map(name, timeout=180):
    mark = len(log_text())
    op.send(['{"t":"gta","op":"console","c":"open %s"}' % name])
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(2)
        if pid() is None:
            print("Trepang2 is gone")
            return 3
        new = log_text()[mark:]
        if name.lower() in new.lower() and "] in game" not in new and int(time.time()) % 4 < 2:
            # the level is loaded but waits on its "PRESS ANY KEY" screen: the game instance's own handler, and a posted
            # Enter for older host builds
            op.send(['{"t":"gta","op":"anykey"}'])
            ps(f"& '{ROOT / 'scripts' / 't2-postkey.ps1'}' 13")
        if "] in game" in new and name.lower() in new.lower():
            laptop()
            time.sleep(3)
            print(f"in game: {name}")
            return 0
    print(f"not in game after {timeout} s: {name}")
    return 2


def main(args):
    name = args[0]
    if "--restart" in args:
        close()
        if "--deploy" in args:
            r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "scripts" / "deploy-host.ps1")],
                               capture_output=True, text=True)
            print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr.strip())
    if pid() is None:
        start()
    code = open_map(name, timeout=90)
    if code == 2:
        # map-to-map travel sometimes never gets the player in (seen on DLC maps after another mission): a fresh start
        print("retrying from a fresh start")
        close()
        start()
        code = open_map(name)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
