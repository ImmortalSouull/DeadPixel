"""Starts the Minecraft dev client (gradlew runClient: our mod from source, world "passthrough") and waits until it is
in the world, giving the focus back to the window that had it (the user may be working).
  python scripts/mc_dev.py          exit 0 in the world, 2 not in time
The Gradle run keeps going in the background (its output: lab/mc-client.log). Close Minecraft with its window's X
(CloseMainWindow), never by PID: that left Windows' focus stuck on GameInputServiceWindow once.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "src" / "mc" / "run" / "logs" / "latest.log"


def ps(script):
    return subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script], capture_output=True, text=True)


def mc_title():
    r = ps("(Get-Process java -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like 'Minecraft*' } | Select-Object -First 1).MainWindowTitle")
    return r.stdout.strip()


def main():
    if " - " in mc_title():
        print("Minecraft is already in its world")
        return 0
    fg = ps(f"& '{ROOT / 'scripts' / 'fg.ps1'}' save").stdout.strip()
    env = dict(os.environ, JAVA_HOME=r"C:\Program Files\Eclipse Adoptium\jdk-25.0.4.101-hotspot")
    out = open(ROOT / "lab" / "mc-client.log", "w")
    subprocess.Popen(["cmd", "/c", str(ROOT / "src" / "mc" / "gradlew.bat"), "runClient", "--console=plain"], cwd=str(ROOT / "src" / "mc"), env=env, stdout=out,
                     stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS)
    started = time.time()
    restored = 0
    while time.time() - started < 400:
        time.sleep(3)
        title = mc_title()
        if title and fg.isdigit() and restored < 6:
            restored += 1
            ps(f"& '{ROOT / 'scripts' / 'fg.ps1'}' restore {fg}")
        if " - " in title:
            time.sleep(2)
            if fg.isdigit():
                ps(f"& '{ROOT / 'scripts' / 'fg.ps1'}' restore {fg}")
            print(f"Minecraft in its world after {time.time() - started:.0f} s")
            return 0
    print("Minecraft not in its world in time")
    return 2


if __name__ == "__main__":
    sys.exit(main())
