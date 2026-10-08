"""TikTok (1080x1920, 60 fps, near-lossless): DeadPixel, Trepang2 x Minecraft - the takes, the installer, an end card.

  python video/make_tiktok.py [out.mp4]      (ffmpeg + Pillow)

Look: DeadPixel's (a dark monitor: pixel-stepped black cards, squared techno type, a pixel-font tag with a signal-red
"stuck pixel" chip), the takes in a 3:4-ish window over a blurred copy of themselves; the installer clip is shown whole.
Audio: each take's game sound (Trepang2 + Minecraft); under the installer and the end card, music.wav (synthesised,
video/gen_music.py). The encode is near-lossless (crf 12, 60 fps, 320 kb/s AAC); TikTok re-encodes once on upload, so
nothing is lost twice.
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
TAKES = HERE / "takes"
WORK = HERE / "work"
ASSETS = HERE.parent / "installer" / "assets"
HEAD, MONO, BODY, PIXEL = ASSETS / "ChakraPetch-Bold.ttf", ASSETS / "ShareTechMono-Regular.ttf", ASSETS / "ChakraPetch-SemiBold.ttf", ASSETS / "PressStart2P-Regular.ttf"
W, H, FPS = 1080, 1920, 60
CRF = 12
BLUE = (255, 43, 58)  # the accent: the stuck pixel's signal red (the name is from BlockBreach)
RED = (255, 43, 58)
CYAN = (92, 225, 255)
WHITE = (228, 236, 240)
DIM = (138, 154, 166)

# (kind, clip, in, seconds of source, speed, crop centre x, crop width, caption, tag)
SEGMENTS = [
    ("game", "bt_tnt_focus.mp4", 9.5, 6.5, 1.0, 960, 1000, "Bullet time|slows Minecraft too", "DEADPIXEL"),
    ("game", "bt_wall.mp4", 8.0, 30.0, 3.0, 960, 1000, "Bullets chew|through blocks", "COVER"),
    ("game", "dp_room.mp4", 12.3, 6.7, 1.0, 960, 1000, "Minecraft's TNT|wrecks the room", "WRECK"),
    ("game", "bt_kick.mp4", 3.0, 6.0, 1.0, 960, 1000, "Kick the zombie", "MELEE"),
    ("game", "bt_nade.mp4", 8.0, 5.0, 1.0, 960, 1000, "Frag vs|brick wall", "BOOM"),
    ("game", "dp_cloak.mp4", 5.5, 8.0, 1.0, 960, 1000, "Cloak: zombies|lose track of you", "GHOST"),
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


def stepped(dr, box, fill, step=6):
    """A rectangle with its corners stepped by one screen pixel (DeadPixel's 8-bit corner)."""
    x0, y0, x1, y1 = box
    dr.polygon([(x0 + step, y0), (x1 - step, y0), (x1, y0 + step), (x1, y1 - step), (x1 - step, y1), (x0 + step, y1), (x0, y1 - step), (x0, y0 + step)], fill=fill)


def caption_png(text, tag, out):
    """DeadPixel's style: a pixel-stepped near-black card with a cyan hairline on its left, white squared caps, a tag in the
    pixel font above it with the stuck pixel as its chip."""
    img = Image.new("RGBA", (W, H))
    dr = ImageDraw.Draw(img)
    f, ft = font(HEAD, 78), font(PIXEL, 24)
    lines = text.upper().replace("|", "\n").split("\n")  # "|" breaks a caption's line
    lh = 92
    x0, y0 = 60, 250
    width = max(dr.textlength(l, font=f) + 4 * len(l) for l in lines)
    box = (x0, y0, x0 + width + 96, y0 + 52 + lh * len(lines))
    shadow = Image.new("RGBA", (W, H))
    ImageDraw.Draw(shadow).rectangle((box[0] + 8, box[1] + 12, box[2] + 8, box[3] + 12), fill=(0, 0, 0, 150))
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(16)))
    stepped(dr, box, (6, 8, 10, 236))
    dr.rectangle((box[0] + 6, box[1] + 1, box[2] - 6, box[1] + 2), fill=(255, 255, 255, 40))  # the bezel's lit edge
    dr.rectangle((box[0] + 14, box[1] + 18, box[0] + 18, box[3] - 18), fill=CYAN + (255,))
    # the tag above the card: the stuck pixel (with its glow) + pixel caps
    tw = spaced(dr, (0, -100), tag, ft, (0, 0, 0, 0), 4)
    stepped(dr, (x0, y0 - 60, x0 + tw + 70, y0 - 12), (6, 8, 10, 236))
    glow = Image.new("RGBA", (W, H))
    ImageDraw.Draw(glow).rectangle((x0 + 10, y0 - 48, x0 + 34, y0 - 24), fill=RED + (150,))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(8)))
    dr = ImageDraw.Draw(img)
    dr.rectangle((x0 + 16, y0 - 42, x0 + 28, y0 - 30), fill=RED + (255,))
    spaced(dr, (x0 + 44, y0 - 48), tag, ft, WHITE + (255,), 4)
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
          f"[1:v]format=rgba,fade=t=in:st=0.05:d=0.2:alpha=1[cap];[base][cap]overlay=0:0:shortest=1,setsar=1,format=yuv420p[v];"
          f"[0:a]asetpts=PTS-STARTPTS,atempo={speed},aresample=48000,volume=0.9[a0]")
    run("-ss", f"{t_in:.3f}", "-t", f"{src_len + 0.05:.3f}", "-i", TAKES / clip, "-loop", "1", "-framerate", FPS, "-t", f"{dur:.3f}", "-i", png,
        "-filter_complex", vf, "-map", "[v]", "-map", "[a0]", "-t", f"{dur:.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", str(CRF), "-r", FPS, "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-ac", "2", out)
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
          f"[1:v]format=rgba,fade=t=in:st=0.05:d=0.2:alpha=1[cap];[base][cap]overlay=0:0:shortest=1,setsar=1,format=yuv420p[v];"
          f"[2:a]aresample=48000,volume=0.7,afade=t=in:d=0.4,afade=t=out:st={max(0.0, dur - 0.5):.3f}:d=0.5[a0]")
    run("-ss", f"{t_in:.3f}", "-t", f"{src_len + 0.05:.3f}", "-i", TAKES / clip, "-loop", "1", "-framerate", FPS, "-t", f"{dur:.3f}", "-i", png,
        *audio_in, "-filter_complex", vf, "-map", "[v]", "-map", "[a0]", "-t", f"{dur:.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", str(CRF), "-r", FPS, "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-ac", "2", out)
    return out


def end_png(frame_png, out):
    """The badge, the name and the line under it, over a dark blurred frame of the game."""
    im = Image.open(frame_png).convert("RGB")
    r = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)))
    im = im.crop(((im.width - W) // 2, (im.height - H) // 2, (im.width - W) // 2 + W, (im.height - H) // 2 + H))
    im = im.filter(ImageFilter.GaussianBlur(20)).convert("RGBA")
    im.alpha_composite(Image.new("RGBA", (W, H), (7, 8, 10, 215)))
    # the screen's pixel structure over the blur
    grid = Image.new("RGBA", (W, H))
    gd = ImageDraw.Draw(grid)
    for x in range(0, W, 6):
        gd.line([(x, 0), (x, H)], fill=(0, 0, 0, 60))
    for y in range(0, H, 6):
        gd.line([(0, y), (W, y)], fill=(0, 0, 0, 60))
    im.alpha_composite(grid)
    badge = Image.open(ASSETS / "icon_256.png").convert("RGBA").resize((400, 400), Image.LANCZOS)
    im.alpha_composite(badge, ((W - 400) // 2, 520))
    dr = ImageDraw.Draw(im)
    f1, f2, f3 = font(PIXEL, 92), font(MONO, 36), font(BODY, 42)
    gap = 9
    w = spaced(dr, (0, -500), "DEADPIXEL", f1, (0, 0, 0, 0), gap)
    wx, wy = (W - w) / 2, 990
    spaced(dr, (wx, wy), "DEADPIXEL", f1, WHITE, gap)
    # the dead pixel in the I (the sixth letter): one cell dark, the one beside it stuck on red
    cell = 92 / 8
    adv = dr.textlength("D", font=f1) + gap
    ix = wx + 5 * adv + 3 * cell
    dr.rectangle((ix, wy + 3 * cell, ix + 2 * cell, wy + 4 * cell), fill=(7, 8, 10))
    glow = Image.new("RGBA", (W, H))
    ImageDraw.Draw(glow).rectangle((ix - cell, wy + 2 * cell, ix + 2 * cell, wy + 5 * cell), fill=RED + (160,))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10)))
    dr = ImageDraw.Draw(im)
    dr.rectangle((ix, wy + 3 * cell, ix + cell, wy + 4 * cell), fill=RED)
    w = spaced(dr, (0, -500), "TREPANG2  x  MINECRAFT", f2, (0, 0, 0, 0), 6)
    spaced(dr, ((W - w) / 2, 1130), "TREPANG2  x  MINECRAFT", f2, CYAN, 6)
    for i in range(9):
        dr.rectangle(((W - 102) / 2 + i * 12, 1200, (W - 102) / 2 + i * 12 + 6, 1206), fill=WHITE)
    sub = "installer + mod  -  single player"
    dr.text(((W - dr.textlength(sub, font=f3)) / 2, 1240), sub, font=f3, fill=(200, 208, 214))
    # the release: a red plate like the installer's INSTALL button, and the GitHub link under it
    fr, fg = font(HEAD, 64), font(MONO, 36)
    label = "RELEASE  1.1.0"
    lw = spaced(dr, (0, -500), label, fr, (0, 0, 0, 0), 6)
    x0, y0 = (W - lw) / 2 - 48, 1340
    stepped(dr, (x0, y0, x0 + lw + 96, y0 + 104), RED)
    dr.rectangle((x0 + 6, y0 + 2, x0 + lw + 90, y0 + 3), fill=(255, 255, 255, 110))
    dr.rectangle((x0 + 14, y0 + 14, x0 + 22, y0 + 22), fill=WHITE)
    spaced(dr, (x0 + 48, y0 + 14), label, fr, (14, 6, 8), 6)
    link = LINK
    # a small GitHub-style mark: a dark circle with a white ring, before the link
    lt = dr.textlength(link, font=fg)
    gx = (W - lt - 56) / 2
    gy = y0 + 150
    dr.ellipse((gx, gy, gx + 40, gy + 40), fill=WHITE)
    dr.ellipse((gx + 6, gy + 6, gx + 34, gy + 34), fill=(24, 26, 30))
    dr.text((gx + 56, gy - 2), link, font=fg, fill=WHITE)
    im.convert("RGB").save(out)


def still(i, png, dur, push=0.03):
    out = WORK / f"seg{i:02d}.mp4"
    frames = round(dur * FPS)
    vf = (f"scale={W * 2}:{H * 2},zoompan=z='1+{push}*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},"
          f"fade=t=in:st=0:d=0.3,fade=t=out:st={dur - 0.4:.3f}:d=0.4,setsar=1,format=yuv420p")
    music = HERE / "music.wav"
    audio_in = ["-ss", "8", "-t", f"{dur:.3f}", "-i", music] if music.exists() else ["-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
    af = f"[1:a]aresample=48000,volume=0.6,afade=t=in:d=0.3,afade=t=out:st={max(0.0, dur - 0.8):.3f}:d=0.8[a]"
    run("-loop", "1", "-framerate", FPS, "-t", f"{dur:.3f}", "-i", png, *audio_in,
        "-filter_complex", f"[0:v]{vf}[v];{af}", "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", str(CRF), "-r", FPS, "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-ac", "2", out)
    return out


LINK = "github.com/ImmortalSouull/DeadPixel"


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
    run("-i", joined, "-af", f"loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=out:st={dur - 0.6:.3f}:d=0.6", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k",
        "-movflags", "+faststart", out)
    print("->", out, f"{dur:.1f} s")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(HERE / "deadpixel_tiktok.mp4"))
