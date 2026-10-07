"""TikTok (1080x1920, 30 fps): Blocktime, Trepang2 x Minecraft - the takes, the installer, an end card.

  uv run --project <universal-modder> python video/make_tiktok.py [out.mp4]

Look: Trepang2's own (black cards, stark white condensed type, a mono tag with a red chip), the takes in a 3:4-ish
window over a blurred copy of themselves; the installer clip is shown whole. Audio: each take's game sound
(Trepang2 + Minecraft); under the installer and the end card, music.wav (synthesised, video/gen_music.py).
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
TAKES = HERE / "takes"
WORK = HERE / "work"
ASSETS = HERE.parent / "installer" / "assets"
HEAD, MONO, BODY = ASSETS / "Oswald-Bold.ttf", ASSETS / "JetBrainsMono-Bold.ttf", ASSETS / "RobotoCond-SemiBold.ttf"
W, H, FPS = 1080, 1920, 30
BLUE = (226, 58, 62)  # the accent: Trepang2 red (the name is from BlockBreach)
RED = (214, 56, 48)
WHITE = (236, 238, 242)
DIM = (150, 155, 165)

# (kind, clip, in, seconds of source, speed, crop centre x, crop width, caption, tag)
SEGMENTS = [
    ("game", "bt_tnt_focus.mp4", 9.5, 6.5, 1.0, 960, 1000, "Bullet time|slows Minecraft too", "BLOCKTIME"),
    ("game", "bt_wall.mp4", 8.0, 30.0, 3.0, 960, 1000, "Bullets chew|through blocks", "COVER"),
    ("game", "bt_kick.mp4", 3.0, 6.0, 1.0, 960, 1000, "Kick the zombie", "MELEE"),
    ("game", "bt_nade.mp4", 8.0, 5.0, 1.0, 960, 1000, "Frag vs|brick wall", "BOOM"),
    ("game", "bt_fight.mp4", 3.0, 4.6, 1.0, 960, 1000, "Zombies vs|Trepang2's soldiers", "FIGHT"),
    ("installer", "installer.mkv", 0.0, 5.5, 1.0, 0, 0, "One-click installer|and launcher", "SETUP"),
]


def run(*args):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *map(str, args)], check=True)


def font(path, size):
    return ImageFont.truetype(str(path), size)


def spaced(dr, xy, text, f, fill, spacing):
    x, y = xy
    for ch in text:
        dr.text((x, y), ch, font=f, fill=fill)
        x += dr.textlength(ch, font=f) + spacing
    return x - xy[0] - spacing


def caption_png(text, tag, out):
    """Trepang2's style: a black card with a white bar on its left, white condensed caps, a mono tag above."""
    img = Image.new("RGBA", (W, H))
    dr = ImageDraw.Draw(img)
    f, ft = font(HEAD, 74), font(MONO, 28)
    lines = text.upper().replace("|", "\n").split("\n")  # "|" breaks a caption's line
    lh = 88
    x0, y0 = 60, 250
    width = max(dr.textlength(l, font=f) + 4 * len(l) for l in lines)
    box = (x0, y0, x0 + width + 96, y0 + 52 + lh * len(lines))
    shadow = Image.new("RGBA", (W, H))
    ImageDraw.Draw(shadow).rectangle((box[0] + 8, box[1] + 12, box[2] + 8, box[3] + 12), fill=(0, 0, 0, 140))
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(16)))
    dr.rectangle(box, fill=(8, 9, 11, 232))
    dr.rectangle((box[0], box[1], box[0] + 8, box[3]), fill=WHITE + (255,))
    # the tag chip above the card: blue square + mono caps
    tw = spaced(dr, (0, -100), tag, ft, (0, 0, 0, 0), 3)
    dr.rectangle((x0, y0 - 56, x0 + tw + 56, y0 - 12), fill=(8, 9, 11, 232))
    dr.rectangle((x0 + 14, y0 - 41, x0 + 28, y0 - 27), fill=BLUE + (255,))
    spaced(dr, (x0 + 40, y0 - 50), tag, ft, WHITE + (255,), 3)
    y = y0 + 24
    for line in lines:
        spaced(dr, (x0 + 50, y), line, f, WHITE + (255,), 4)
        y += lh
    img.save(out)


def game(i, clip, t_in, src_len, speed, cx, cw, text, tag):
    out = WORK / f"seg{i:02d}.mp4"
    png = WORK / f"cap{i:02d}.png"
    caption_png(text, tag, png)
    dur = src_len / speed
    x = max(0, min(1920 - cw, cx - cw // 2))
    fh = round(W * 1200 / cw / 2) * 2
    top = (H - fh) // 2 + 80
    vf = (f"[0:v]setpts=(PTS-STARTPTS)/{speed},fps={FPS},crop={cw}:1200:{x}:0,split[a][b];"
          f"[a]scale=270:480,boxblur=10:2,eq=brightness=-0.22:saturation=0.8,scale={W}:{H}[bg];"
          f"[b]scale={W}:{fh}:flags=lanczos[fg];[bg][fg]overlay=0:{top}[base];"
          f"[1:v]format=rgba,fade=t=in:st=0.05:d=0.2:alpha=1[cap];[base][cap]overlay=0:0:shortest=1,format=yuv420p[v];"
          f"[0:a]asetpts=PTS-STARTPTS,atempo={speed},aresample=48000,volume=0.9[a0]")
    run("-ss", f"{t_in:.3f}", "-t", f"{src_len + 0.05:.3f}", "-i", TAKES / clip, "-loop", "1", "-framerate", FPS, "-t", f"{dur:.3f}", "-i", png,
        "-filter_complex", vf, "-map", "[v]", "-map", "[a0]", "-t", f"{dur:.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-r", FPS, "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", out)
    return out


def installer(i, clip, t_in, src_len, speed, _cx, _cw, text, tag):
    """The installer's window whole (1080x700 -> 1040 wide), over a blurred, darkened copy; music under it if any."""
    out = WORK / f"seg{i:02d}.mp4"
    png = WORK / f"cap{i:02d}.png"
    caption_png(text, tag, png)
    dur = src_len / speed
    # the left 900 px of the 1080-wide window (menu, objectives, READY): bigger on a phone
    cw = 900
    fw = 1040
    fh = round(fw * 700 / cw / 2) * 2
    top = (H - fh) // 2 + 140
    music = HERE / "music.wav"
    audio_in = ["-ss", "0", "-t", f"{dur:.3f}", "-i", music] if music.exists() else ["-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
    vf = (f"[0:v]setpts=(PTS-STARTPTS)/{speed},fps={FPS},split[a][b];"
          f"[a]scale=270:480,boxblur=12:3,eq=brightness=-0.3:saturation=0.7,scale={W}:{H}[bg];"
          f"[b]crop={cw}:700:0:0,scale={fw}:{fh}:flags=lanczos,pad={fw + 4}:{fh + 4}:2:2:color=0x3a3f48[fg];[bg][fg]overlay={(W - fw - 4) // 2}:{top}[base];"
          f"[1:v]format=rgba,fade=t=in:st=0.05:d=0.2:alpha=1[cap];[base][cap]overlay=0:0:shortest=1,format=yuv420p[v];"
          f"[2:a]aresample=48000,volume=0.7,afade=t=in:d=0.4,afade=t=out:st={max(0.0, dur - 0.5):.3f}:d=0.5[a0]")
    run("-ss", f"{t_in:.3f}", "-t", f"{src_len + 0.05:.3f}", "-i", TAKES / clip, "-loop", "1", "-framerate", FPS, "-t", f"{dur:.3f}", "-i", png,
        *audio_in, "-filter_complex", vf, "-map", "[v]", "-map", "[a0]", "-t", f"{dur:.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-r", FPS, "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", out)
    return out


def end_png(frame_png, out):
    """The badge, the name and the line under it, over a dark blurred frame of the game."""
    im = Image.open(frame_png).convert("RGB")
    r = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)))
    im = im.crop(((im.width - W) // 2, (im.height - H) // 2, (im.width - W) // 2 + W, (im.height - H) // 2 + H))
    im = im.filter(ImageFilter.GaussianBlur(20)).convert("RGBA")
    im.alpha_composite(Image.new("RGBA", (W, H), (7, 8, 10, 215)))
    badge = Image.open(ASSETS / "icon_256.png").convert("RGBA").resize((360, 360), Image.LANCZOS)
    im.alpha_composite(badge, ((W - 360) // 2, 560))
    dr = ImageDraw.Draw(im)
    f1, f2, f3 = font(HEAD, 120), font(MONO, 34), font(BODY, 42)
    w = spaced(dr, (0, -500), "BLOCKTIME", f1, (0, 0, 0, 0), 10)
    spaced(dr, ((W - w) / 2, 960), "BLOCKTIME", f1, WHITE, 10)
    w = spaced(dr, (0, -500), "TREPANG2  x  MINECRAFT", f2, (0, 0, 0, 0), 6)
    spaced(dr, ((W - w) / 2, 1130), "TREPANG2  x  MINECRAFT", f2, DIM, 6)
    dr.rectangle(((W - 120) / 2, 1200, (W + 120) / 2, 1206), fill=WHITE)
    sub = "installer + mod  -  single player"
    dr.text(((W - dr.textlength(sub, font=f3)) / 2, 1240), sub, font=f3, fill=(200, 204, 210))
    # the release: a white chip like the installer's READY button, and the GitHub link under it
    fr, fg = font(HEAD, 64), font(MONO, 34)
    label = "RELEASE  1.0.0"
    lw = spaced(dr, (0, -500), label, fr, (0, 0, 0, 0), 6)
    x0, y0 = (W - lw) / 2 - 48, 1340
    dr.rectangle((x0, y0, x0 + lw + 96, y0 + 104), fill=WHITE)
    dr.rectangle((x0 + lw + 96 - 22, y0, x0 + lw + 96, y0 + 6), fill=BLUE)
    spaced(dr, (x0 + 48, y0 + 14), label, fr, (10, 11, 13), 6)
    link = LINK
    # a small GitHub-style mark: a dark circle with a white ring, before the link
    lt = dr.textlength(link, font=fg)
    gx = (W - lt - 56) / 2
    gy = y0 + 150
    dr.ellipse((gx, gy, gx + 40, gy + 40), fill=WHITE)
    dr.ellipse((gx + 6, gy + 6, gx + 34, gy + 34), fill=(24, 26, 30))
    dr.text((gx + 56, gy - 2), link, font=fg, fill=WHITE)
    # Trepang2's crosshair meters above the badge: a white Focus arc and a red Cloak arc
    dr.arc((W // 2 - 230, 520, W // 2 + 230, 980), 120, 240, fill=WHITE, width=10)
    dr.arc((W // 2 - 230, 520, W // 2 + 230, 980), 300, 420, fill=RED, width=10)
    im.convert("RGB").save(out)


def still(i, png, dur, push=0.03):
    out = WORK / f"seg{i:02d}.mp4"
    frames = round(dur * FPS)
    vf = (f"scale={W * 2}:{H * 2},zoompan=z='1+{push}*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},"
          f"fade=t=in:st=0:d=0.3,fade=t=out:st={dur - 0.4:.3f}:d=0.4,format=yuv420p")
    music = HERE / "music.wav"
    audio_in = ["-ss", "8", "-t", f"{dur:.3f}", "-i", music] if music.exists() else ["-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
    af = f"[1:a]aresample=48000,volume=0.6,afade=t=in:d=0.3,afade=t=out:st={max(0.0, dur - 0.8):.3f}:d=0.8[a]"
    run("-loop", "1", "-framerate", FPS, "-t", f"{dur:.3f}", "-i", png, *audio_in,
        "-filter_complex", f"[0:v]{vf}[v];{af}", "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-r", FPS, "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", out)
    return out


LINK = "github.com/ImmortalSouull/Blocktime"


def main(out):
    WORK.mkdir(exist_ok=True)
    parts = []
    for i, (kind, *seg) in enumerate(SEGMENTS):
        if not (TAKES / seg[0]).exists():
            print("missing take, skipped:", seg[0])
            continue
        parts.append((installer if kind == "installer" else game)(i, *seg))
    frame = WORK / "endframe.png"
    first = next((s for s in SEGMENTS if s[0] == "game" and (TAKES / s[1]).exists()), None)
    src = TAKES / (first[1] if first else "bt_fight.mp4")
    run("-ss", "2.0", "-i", src, "-frames:v", "1", frame)
    end_png(frame, WORK / "end.png")
    parts.append(still(len(SEGMENTS), WORK / "end.png", 4.0, 0.03))
    lst = WORK / "list.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts))
    joined = WORK / "joined.mp4"
    run("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined)
    # one loudness for the whole thing, and a short fade at the very end
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(joined)], capture_output=True, text=True).stdout)
    run("-i", joined, "-af", f"loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=out:st={dur - 0.6:.3f}:d=0.6", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", out)
    print("->", out, f"{dur:.1f} s")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(HERE / "blocktime_tiktok.mp4"))
