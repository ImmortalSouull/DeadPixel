"""Art for Blocktime, Trepang2 first with a drop of Minecraft: the app icon is a black badge fading to crimson (Focus),
Trepang2's crosshair arcs (white Focus meter, red Cloak meter), white ticks and a small pixel grass block in its centre.
Writes assets/blocktime.ico, icon_256.png, icon_64.png + .rgba (window icon), logo_128.rgba (the UI's badge) and
profile_icon.txt (the Minecraft Launcher profile's icon, a data URI).
Run: uv run --with pillow python installer/make_art.py
"""
import base64
import pathlib
import random

from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).resolve().parent / "assets"
rnd = random.Random(7)


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
    """The icon at 1024 px (scaled down with antialiasing later)."""
    k = size / 256.0
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # the badge: dark, near-square, a thin light rim
    r = int(46 * k)
    box = (int(8 * k), int(8 * k), size - int(8 * k), size - int(8 * k))
    grad = Image.new("RGBA", (size, size))
    gd = ImageDraw.Draw(grad)
    for y in range(size):
        t = y / size
        c = (int(10 + 70 * t * t), int(8 + 4 * t), int(10 + 6 * t), 255)
        gd.line([(0, y), (size, y)], fill=c)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(box, r, fill=255)
    img.paste(grad, (0, 0), mask)
    d.rounded_rectangle(box, r, outline=(255, 255, 255, 46), width=int(3 * k))
    # Trepang2's crosshair: two meters around it, Focus (white, left) and Cloak (red, right)
    c = size // 2
    R, wdt = int(84 * k), int(12 * k)
    white = (240, 240, 242, 255)
    d.arc((c - R, c - R, c + R, c + R), 112, 248, fill=white, width=wdt)
    d.arc((c - R, c - R, c + R, c + R), 292, 428, fill=(220, 40, 44, 255), width=wdt)
    t0, t1 = int(98 * k), int(116 * k)
    tw = int(7 * k)
    d.rectangle((c - tw // 2, c - t1, c + tw // 2, c - t0), fill=white)
    d.rectangle((c - tw // 2, c + t0, c + tw // 2, c + t1), fill=white)
    return img, c


def compose(size):
    big, c = badge(1024)
    img = big.resize((size, size), Image.LANCZOS)
    # the pixel block goes in at its final size with hard edges (nearest), centred in the reticle
    cube_px = max(8, round(size * 0.40))
    cube = pixel_cube(32).resize((cube_px, cube_px), Image.NEAREST)
    cc = round(c / 1024 * size)
    img.alpha_composite(cube, (size // 2 - cube_px // 2, cc - cube_px // 2))
    return img


def main():
    HERE.mkdir(exist_ok=True)
    sizes = [16, 24, 32, 48, 64, 128, 256]
    imgs = {s: compose(s) for s in sizes}
    imgs[256].save(HERE / "icon_256.png")
    imgs[64].save(HERE / "icon_64.png")
    (HERE / "icon_64.rgba").write_bytes(imgs[64].tobytes())
    (HERE / "logo_128.rgba").write_bytes(imgs[128].tobytes())
    imgs[256].save(HERE / "blocktime.ico", sizes=[(s, s) for s in sizes], append_images=[imgs[s] for s in sizes[:-1]])
    (HERE / "profile_icon.txt").write_text("data:image/png;base64," + base64.b64encode((HERE / "icon_64.png").read_bytes()).decode())
    # the grass block alone, for the UI's small Minecraft touches
    (HERE / "cube_32.rgba").write_bytes(pixel_cube(32).tobytes())
    print("art written to", HERE)


if __name__ == "__main__":
    main()
