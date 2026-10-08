"""Art for DeadPixel: the app icon is a dark monitor seen up close - a steel bezel, the screen's 16 x 16 pixel structure,
one pixel stuck on signal red with its glow, and Trepang2's reticle closed on it.
Writes assets/deadpixel.ico, icon_256.png, icon_64.png + .rgba (window icon), logo_128.rgba (the UI's badge) and
profile_icon.txt (the Minecraft Launcher profile's icon, a data URI).
Run: uv run --with pillow python installer/make_art.py
"""
import base64
import pathlib
import random

from PIL import Image, ImageDraw, ImageFilter

HERE = pathlib.Path(__file__).resolve().parent / "assets"
rnd = random.Random(7)

RED = (255, 43, 58, 255)
BEZEL = (58, 70, 80, 255)
BEZEL_DARK = (28, 34, 40, 255)
SCREEN = (8, 11, 14, 255)


def tex_grass_top():
    base = [(93, 160, 52), (106, 176, 60), (84, 146, 46), (118, 186, 70)]
    return [[rnd.choice(base) for _ in range(16)] for _ in range(16)]


def tex_grass_side():
    dirt = [(134, 96, 67), (121, 85, 58), (150, 108, 74), (108, 76, 52)]
    grass = [(93, 160, 52), (106, 176, 60), (84, 146, 46)]
    t = [[rnd.choice(dirt) for _ in range(16)] for _ in range(16)]
    for x in range(16):
        for y in range(3 + rnd.choice([0, 0, 1, 1, 2])):
            t[y][x] = rnd.choice(grass)
    return t


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def pixel_cube(size=32):
    """An isometric grass block in a size x size frame, sampled per pixel (hard pixel edges)."""
    top, side = tex_grass_top(), tex_grass_side()
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = img.load()
    s = size / 32.0
    cx, ty, w, h, edge = 16 * s, 1.5 * s, 14.5 * s, 7.25 * s, 15.5 * s
    for y in range(size):
        for x in range(size):
            fx, fy = x + 0.5, y + 0.5
            dx = (fx - cx) / w
            tcy = ty + h
            dy = (fy - tcy) / h
            if abs(dx) + abs(dy) <= 1.0:
                u, v = (dx + dy + 1) / 2 * 16, (dy - dx + 1) / 2 * 16
                px[x, y] = (*top[min(15, int(v))][min(15, int(u))], 255)
            elif -1.0 <= dx < 0:
                y0 = tcy + h * (1 + dx)
                if y0 <= fy <= y0 + edge:
                    px[x, y] = (*shade(side[min(15, int((fy - y0) / edge * 16))][min(15, int((dx + 1) * 16))], 0.92), 255)
            elif 0 <= dx <= 1.0:
                y0 = tcy + h * (1 - dx)
                if y0 <= fy <= y0 + edge:
                    px[x, y] = (*shade(side[min(15, int((fy - y0) / edge * 16))][min(15, int(dx * 16))], 0.68), 255)
    return img


def badge(size=1024):
    """The icon at 1024 px: the bezel, the screen with its pixel structure, the stuck pixel's glow, the reticle."""
    k = size / 256.0
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = int(44 * k)
    box = (int(8 * k), int(8 * k), size - int(8 * k), size - int(8 * k))
    # the bezel: steel, a lighter top edge
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(box, r, fill=255)
    bezel = Image.new("RGBA", (size, size), BEZEL)
    bd = ImageDraw.Draw(bezel)
    for y in range(size):
        f = 1.0 - 0.45 * y / size
        bd.line([(0, y), (size, y)], fill=tuple(int(c * f) for c in BEZEL[:3]) + (255,))
    img.paste(bezel, (0, 0), mask)
    # the screen, inset
    inset = int(26 * k)
    sr = int(26 * k)
    screen_box = (box[0] + inset, box[1] + inset, box[2] - inset, box[3] - inset)
    d.rounded_rectangle(screen_box, sr, fill=SCREEN)
    d.rounded_rectangle(screen_box, sr, outline=BEZEL_DARK, width=int(3 * k))
    # the pixel structure: a 16 x 16 grid of cells, each a little lighter than the gap
    sx0, sy0, sx1, sy1 = screen_box
    cells = 16
    cw = (sx1 - sx0) / cells
    grid = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    gap = max(1, int(cw * 0.14))
    for j in range(cells):
        for i in range(cells):
            x0 = sx0 + i * cw
            y0 = sy0 + j * cw
            n = rnd.random()
            tone = 14 + int(6 * n)
            gd.rectangle((x0 + gap, y0 + gap, x0 + cw - gap, y0 + cw - gap), fill=(tone, tone + 4, tone + 8, 255))
    smask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(smask).rounded_rectangle(screen_box, sr, fill=255)
    img.paste(grid, (0, 0), smask)
    # the stuck pixel: one cell (a little right of centre, a little up) lit red, its glow bleeding into the neighbours
    ci, cj = 9, 6
    px0 = sx0 + ci * cw
    py0 = sy0 + cj * cw
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(glow).rectangle((px0 - cw * 1.2, py0 - cw * 1.2, px0 + cw * 2.2, py0 + cw * 2.2), fill=(255, 43, 58, 170))
    glow = glow.filter(ImageFilter.GaussianBlur(cw * 0.9))
    glow_masked = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_masked.paste(glow, (0, 0), smask)
    img.alpha_composite(glow_masked)
    d = ImageDraw.Draw(img)
    d.rectangle((px0 + gap, py0 + gap, px0 + cw - gap, py0 + cw - gap), fill=RED)
    # Trepang2's reticle on it: four ticks with a gap in the middle, white
    cx, cy = px0 + cw / 2, py0 + cw / 2
    inner, outer, w = cw * 1.1, cw * 3.0, max(2, int(5 * k))
    white = (236, 242, 246, 255)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        d.line([(cx + dx * inner, cy + dy * inner), (cx + dx * outer, cy + dy * outer)], fill=white, width=w)
    # a thin frame of the reticle's corners, further out
    far, arm = cw * 4.6, cw * 1.0
    for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        d.line([(cx + sx * far, cy + sy * far), (cx + sx * (far - arm), cy + sy * far)], fill=white, width=max(1, int(3 * k)))
        d.line([(cx + sx * far, cy + sy * far), (cx + sx * far, cy + sy * (far - arm))], fill=white, width=max(1, int(3 * k)))
    return img


def compose(size):
    return badge(1024).resize((size, size), Image.LANCZOS)


def main():
    HERE.mkdir(exist_ok=True)
    sizes = [16, 24, 32, 48, 64, 128, 256]
    imgs = {s: compose(s) for s in sizes}
    imgs[256].save(HERE / "icon_256.png")
    imgs[64].save(HERE / "icon_64.png")
    (HERE / "icon_64.rgba").write_bytes(imgs[64].tobytes())
    (HERE / "logo_128.rgba").write_bytes(imgs[128].tobytes())
    imgs[256].save(HERE / "deadpixel.ico", sizes=[(s, s) for s in sizes], append_images=[imgs[s] for s in sizes[:-1]])
    (HERE / "profile_icon.txt").write_text("data:image/png;base64," + base64.b64encode((HERE / "icon_64.png").read_bytes()).decode())
    # the grass block alone, for the UI's small Minecraft touches
    (HERE / "cube_32.rgba").write_bytes(pixel_cube(32).tobytes())
    print("art written to", HERE)


if __name__ == "__main__":
    main()
