"""Refreshes repo/ (the public GitHub tree) from the project's sources: the same files in the same places, stale files
removed. Build outputs, logs, takes and the lab never go in (see repo/.gitignore).

  python release/stage_repo.py
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT / "repo"

# repo path -> source path (a file, or a directory copied whole)
TREE = {
    "README.md": "release/README.md",
    "BUILDING.md": "release/BUILDING.md",
    "LICENSE": "release/LICENSE",
    "t2-host/dllmain.cpp": "src/t2-host/dllmain.cpp",
    "t2-host/compositor.cpp": "src/t2-host/compositor.cpp",
    "t2-host/compositor.h": "src/t2-host/compositor.h",
    "t2-host/crash_guard.cpp": "src/t2-host/crash_guard.cpp",
    "t2-host/crash_guard.h": "src/t2-host/crash_guard.h",
    "t2-host/ue_call.h": "src/t2-host/ue_call.h",
    "t2-host/ws.cpp": "src/t2-host/ws.cpp",
    "t2-host/ws.h": "src/t2-host/ws.h",
    "t2-host/CMakeLists.txt": "src/t2-host/CMakeLists.txt",
    "t2-host/CMakeLists.root.txt": "src/CMakeLists.txt",
    "t2-host/build-host.bat": "scripts/build-host.bat",
    "t2-host/shaders": "src/t2-host/shaders",
    "minecraft-mod/build.gradle": "src/mc/build.gradle",
    "minecraft-mod/gradle.properties": "src/mc/gradle.properties",
    "minecraft-mod/settings.gradle": "src/mc/settings.gradle",
    "minecraft-mod/gradlew": "src/mc/gradlew",
    "minecraft-mod/gradlew.bat": "src/mc/gradlew.bat",
    "minecraft-mod/gradle": "src/mc/gradle",
    "minecraft-mod/src": "src/mc/src",
    "installer/Cargo.toml": "installer/Cargo.toml",
    "installer/Cargo.lock": "installer/Cargo.lock",
    "installer/build.rs": "installer/build.rs",
    "installer/make_art.py": "installer/make_art.py",
    "installer/make_payload.py": "installer/make_payload.py",
    "installer/src": "installer/src",
    "installer/assets": "installer/assets",
    "release": "release",
    "video/make_tiktok.py": "video/make_tiktok.py",
    "video/gen_music.py": "video/gen_music.py",
    "video/shots": "video/shots",
}
SCRIPTS = ["crash_check.py", "deploy-host.ps1", "fg.ps1", "fps.py", "mc_dev.py", "mcfps.py", "mcframe.py", "op.py", "scene.py", "t2-laptop.ps1",
           "t2-postkey.ps1", "t2-postmouse.ps1", "t2_open.py", "t2_tour.py", "take.py"]
SKIP_NAMES = {"__pycache__", "selftest.txt"}


def copy_tree(src: Path, dst: Path):
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=lambda d, names: [n for n in names if n in SKIP_NAMES or n.endswith(".pyc")])


def main() -> int:
    tree = dict(TREE)
    for s in SCRIPTS:
        tree[f"scripts/{s}"] = f"scripts/{s}"
    # stale files in the repo's folders (not .git, not the tree)
    wanted = {REPO / k for k in tree}
    for top in ("t2-host", "minecraft-mod", "installer", "release", "scripts", "video"):
        d = REPO / top
        if not d.exists():
            continue
        for f in d.rglob("*"):
            if f.is_file() and not any(f == w or w in f.parents for w in wanted):
                print("removed", f.relative_to(REPO))
                f.unlink()
    for rel, src in tree.items():
        s = ROOT / src
        d = REPO / rel
        if not s.exists():
            sys.exit(f"missing source: {s}")
        d.parent.mkdir(parents=True, exist_ok=True)
        if s.is_dir():
            copy_tree(s, d)
        else:
            shutil.copy2(s, d)
    # empty folders left behind
    for d in sorted((p for p in REPO.rglob("*") if p.is_dir() and ".git" not in p.parts), reverse=True):
        if not any(d.iterdir()):
            d.rmdir()
    print("repo/ refreshed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
