"""Trepang2 crash watch: is the game alive, did it crash since a mark, and what does the crash say.

  python scripts/crash_check.py            newest crash report: time, error, stack (our main.dll frames symbolized)
  python scripts/crash_check.py mark       prints a mark (newest crash folder) to compare against later
  python scripts/crash_check.py since MARK exit 3 + the report if a crash newer than MARK exists, else "ok"
  python scripts/crash_check.py alive      exit 0 if the game runs, 3 (+ report) if it crashed, 1 if simply not running
  python scripts/crash_check.py watch      runs until stopped; prints a report the moment Trepang2 or Minecraft crashes,
                                           exits without a report, or hangs (window not responding for 15 s); also
                                           a JVM crash of Minecraft (hs_err_pid*.log). For a background monitor.
  python scripts/crash_check.py mc         Minecraft: running?, newest crash report

A Trepang2 report also shows the mod's flight recorder (crash_breadcrumbs.log next to the mod DLL): what the mod was doing
on each thread and its last operations when the exception happened.

Every automated step that drives Trepang2 calls `since`/`alive`, so a crash is caught at once instead of the scripts
clicking into the crash reporter's window.
"""
import re
import subprocess
import sys
from pathlib import Path

CRASHES = Path.home() / "AppData" / "Local" / "CPPFPS" / "Saved" / "Crashes"
MAIN_DLL = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Trepang2\CPPFPS\Binaries\Win64\ue4ss\Mods\T2Passthrough\dlls\main.dll")
SYMBOLIZER = Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\llvm-symbolizer.exe")


def newest():
    dirs = [d for d in CRASHES.iterdir() if d.is_dir()] if CRASHES.exists() else []
    return max(dirs, key=lambda d: d.stat().st_mtime) if dirs else None


def running(name):
    out = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {name}"], capture_output=True, text=True).stdout
    return name.lower()[:20] in out.lower()


ROOT_DIR = Path(__file__).resolve().parent.parent
BUILDS = ROOT_DIR / "lab" / "builds"
BREADCRUMBS = MAIN_DLL.parent.parent / "crash_breadcrumbs.log"
# both Minecraft game dirs: the dev client (src/mc/run) and the installed DeadPixel one; the newest crash folder counts
MC_DIRS = [Path(__file__).resolve().parent.parent / "src" / "mc" / "run", Path.home() / "AppData" / "Local" / "DeadPixel" / "minecraft"]
MC_CRASHES = max((d / "crash-reports" for d in MC_DIRS), key=lambda f: f.stat().st_mtime if f.exists() else 0)


def breadcrumbs(crash_time, window=20.0):
    """The mod's exception records from up to `window` seconds before the crash report was written."""
    import datetime
    if not BREADCRUMBS.exists():
        return []
    out, keep = [], False
    for line in BREADCRUMBS.read_text(errors="replace").splitlines():
        if line.startswith("    "):
            if keep:
                out.append(line)
            continue
        keep = False
        try:
            t = datetime.datetime.strptime(line[:23], "%Y-%m-%d %H:%M:%S.%f").timestamp()
        except ValueError:
            continue
        if " EXCEPTION " in line and crash_time - window <= t <= crash_time + 2:
            out.append(line)
            keep = True
    return out


def hung_seconds(exe, since={}):
    """How long the process's main window has not been responding (IsHungAppWindow), 0 if it responds or has none."""
    import ctypes
    import time
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    out = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {exe}", "/FO", "CSV", "/NH"], capture_output=True, text=True).stdout
    pids = {int(l.split('","')[1]) for l in out.splitlines() if l.startswith('"')}
    hung = [False]

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def each(hwnd, _):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in pids and user32.IsWindowVisible(hwnd) and user32.GetWindow(hwnd, 4) == 0 and user32.IsHungAppWindow(hwnd):
            hung[0] = True
        return True

    user32.EnumWindows(each, 0)
    now = time.time()
    if not hung[0]:
        since.pop(exe, None)
        return 0
    return now - since.setdefault(exe, now)


HISTORY = MAIN_DLL.parent.parent / "history.log"


def history_before(crash_time, window=30.0, most=12):
    """The mod's own log lines (history.log, kept across launches) from the `window` seconds before the crash."""
    import datetime
    if not HISTORY.exists():
        return []
    day, out = None, []
    for line in HISTORY.read_text(errors="replace").splitlines():
        if line.startswith("===== session "):
            day = line[14:24]
            continue
        if day is None or len(line) < 13 or line[2] != ":":
            continue
        try:
            t = datetime.datetime.strptime(f"{day} {line[:12]}", "%Y-%m-%d %H:%M:%S.%f").timestamp()
        except ValueError:
            continue
        if crash_time - window <= t <= crash_time + 2:
            out.append(line)
    return out[-most:]


def mc_report():
    alive = (running("javaw.exe") or running("java.exe"))
    print(f"Minecraft: {'running' if alive else 'NOT running'}")
    reports = sorted(MC_CRASHES.glob("*.txt"), key=lambda f: f.stat().st_mtime) if MC_CRASHES.exists() else []
    if reports:
        r = reports[-1]
        text = r.read_text(errors="replace").splitlines()
        desc = next((l for l in text if l.startswith("Description:")), "")
        print(f"  newest crash report: {r.name}  {desc}")
        for l in text[text.index("") + 1 if "" in text else 0:][:12]:
            print("   " + l)
    return alive


def dll_for(crash_time):
    """The archived build that was deployed last before the crash (lab/builds/<yyyymmdd-hhmmss>), else the live one."""
    import datetime
    best = None
    for b in sorted(BUILDS.iterdir()) if BUILDS.exists() else []:
        try:
            t = datetime.datetime.strptime(b.name, "%Y%m%d-%H%M%S").timestamp()
        except ValueError:
            continue
        if t <= crash_time and (b / "T2Passthrough.dll").exists():
            best = b / "T2Passthrough.dll"
    return best


def report(d):
    import datetime
    dll = dll_for(d.stat().st_mtime)
    exact = dll is not None
    dll = dll or MAIN_DLL
    xml = (d / "CrashContext.runtime-xml").read_text(errors="replace")
    err = re.search(r"<ErrorMessage>([^<]*)", xml)
    stack = re.search(r"<PCallStack>(.*?)</PCallStack>", xml, re.S)
    print(f"CRASH {d.name}  at {datetime.datetime.fromtimestamp(d.stat().st_mtime):%Y-%m-%d %H:%M:%S}")
    print("  " + (err.group(1).strip() if err else "?"))
    print(f"  (main.dll symbols from {dll})" if exact else
          f"  (no archived build from before this crash: main.dll frames symbolized with the live DLL, may be WRONG)")
    for line in (stack.group(1).strip().splitlines() if stack else [])[:14]:
        parts = line.split()
        if len(parts) >= 4 and parts[0] == "main" and SYMBOLIZER.exists():
            sym = subprocess.run([str(SYMBOLIZER), f"--obj={dll}", "--relative-address", "0x" + parts[3]],
                                 capture_output=True, text=True).stdout.split("\n")
            print(f"  main+{parts[3]}  {sym[0]}  {sym[1] if len(sym) > 1 else ''}")
        else:
            print("  " + " ".join(parts))
    hist = history_before(d.stat().st_mtime)
    if hist:
        print("  the mod's last lines (history.log):")
        for line in hist:
            print("   " + line[:200])
    crumbs = breadcrumbs(d.stat().st_mtime)
    print("  mod flight recorder:" if crumbs else "  mod flight recorder: nothing recorded near the crash (the mod wasn't at work)")
    for line in crumbs:
        print("   " + line)


def main(args):
    cmd = args[0] if args else "show"
    d = newest()
    if cmd == "mark":
        print(d.name if d else "none")
    elif cmd == "since":
        mark = args[1] if len(args) > 1 else "none"
        if d and d.name != mark and not running("CPPFPS-Win64-Shipping.exe"):
            report(d)
            sys.exit(3)
        print("ok")
    elif cmd == "alive":
        if running("CPPFPS-Win64-Shipping.exe"):
            print("alive")
        elif running("CrashReporter.exe"):
            report(d)
            sys.exit(3)
        else:
            print("not running")
            sys.exit(1)
    elif cmd == "mc":
        mc_report()
    elif cmd == "watch":
        import time
        seen = d.name if d else None
        mc_seen = max((f.name for f in MC_CRASHES.glob("*.txt")), default=None) if MC_CRASHES.exists() else None
        jvm_seen = {f.name for d in MC_DIRS for f in d.glob("hs_err_pid*.log")}
        hung_told = set()
        print("watching for crashes", flush=True)
        ron_up = running("CPPFPS-Win64-Shipping.exe")
        mc_up = (running("javaw.exe") or running("java.exe"))
        while True:
            time.sleep(2)
            # a game that vanishes without a crash report (hard kill, driver reset, plain exit) is news too
            ron_now, mc_now = running("CPPFPS-Win64-Shipping.exe"), (running("javaw.exe") or running("java.exe"))
            if ron_up and not ron_now:
                time.sleep(4)
                n = newest()
                # a crash report (just printed, or about to be) explains it already
                recent = n is not None and time.time() - n.stat().st_mtime < 120
                if not recent:
                    print("=== Trepang2 process gone (no crash report: closed, killed or driver reset) ===", flush=True)
            if mc_up and not mc_now:
                print("=== Minecraft process gone ===", flush=True)
            if not ron_up and ron_now:
                print("Trepang2 started", flush=True)
            if not mc_up and mc_now:
                print("Minecraft started", flush=True)
            ron_up, mc_up = ron_now, mc_now
            for exe, name in (("CPPFPS-Win64-Shipping.exe", "Trepang2"), ("javaw.exe", "Minecraft")):
                h = hung_seconds(exe)
                if h >= 15 and exe not in hung_told:
                    hung_told.add(exe)
                    print(f"=== {name} NOT RESPONDING for {h:.0f} s (hung: kill it by PID if it doesn't recover) ===", flush=True)
                elif h == 0 and exe in hung_told:
                    hung_told.discard(exe)
                    print(f"{name} responds again", flush=True)
            for f in (f for d in MC_DIRS for f in d.glob("hs_err_pid*.log")):
                if f.name not in jvm_seen:
                    jvm_seen.add(f.name)
                    head = f.read_text(errors="replace").splitlines()[:12]
                    print(f"=== Minecraft's JVM CRASHED ({f.name}) ===", flush=True)
                    for l in head:
                        if l.startswith("#") and l.strip("# "):
                            print("   " + l, flush=True)
            n = newest()
            if n and n.name != seen:
                time.sleep(3)  # let the reporter finish writing
                seen = n.name
                print("=== Trepang2 CRASHED ===", flush=True)
                report(n)
                sys.stdout.flush()
            m = max((f.name for f in MC_CRASHES.glob("*.txt")), default=None) if MC_CRASHES.exists() else None
            if m and m != mc_seen:
                mc_seen = m
                print("=== Minecraft CRASHED ===", flush=True)
                mc_report()
                sys.stdout.flush()
    elif d:
        report(d)


if __name__ == "__main__":
    main(sys.argv[1:])
