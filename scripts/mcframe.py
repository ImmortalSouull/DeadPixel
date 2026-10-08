"""Dumps Minecraft's latest exported frame (shared memory Local\MCPassthroughFrame) to PNGs: world colour, overlay,
and the world depth as greys, plus the slot's camera. For checking what Minecraft draws without looking at its window.
  python scripts/mcframe.py [out_prefix]
"""
import mmap
import struct
import sys

import numpy as np
from PIL import Image

out = sys.argv[1] if len(sys.argv) > 1 else "lab/shots/mcframe"
HEADER, MAXW, MAXH = 4096, 3840, 2160
LAYER = MAXW * MAXH * 4
m = mmap.mmap(-1, HEADER + 3 * LAYER * 3, tagname=r"Local\MCPassthroughFrame", access=mmap.ACCESS_READ)
magic, ver, hdr, slots = struct.unpack_from("<4i", m, 0)
stride, = struct.unpack_from("<q", m, 16)
pub, latest = struct.unpack_from("<qi", m, 32)
print(f"magic {magic:#x} slots {slots} published {pub} latest {latest}")
d = 256 + 128 * latest
seq, mcf, hostf, w, h, near, far, fov, flags = struct.unpack_from("<qqqiifffi", m, d)
x, y, z = struct.unpack_from("<3d", m, d + 48)
yaw, pitch, roll = struct.unpack_from("<3f", m, d + 72)
bx0, by0, bx1, by1 = struct.unpack_from("<4i", m, d + 104)
print(f"slot {latest}: {w}x{h} near {near} far {far} fov {fov:.1f} flags {flags} (overlay empty {bool(flags & 8)}, world empty {bool(flags & 16)}) "
      f"box x {bx0}..{bx1} y {by0}..{by1} cam ({x:.2f}, {y:.2f}, {z:.2f}) yaw {yaw:.1f} pitch {pitch:.1f}")
base = HEADER + latest * stride
n = w * h * 4
col = np.frombuffer(m[base:base + n], np.uint8).reshape(h, w, 4)
dep = np.frombuffer(m[base + n:base + 2 * n], np.float32).reshape(h, w)
ov = np.frombuffer(m[base + 2 * n:base + 3 * n], np.uint8).reshape(h, w, 4)
flip = (lambda a: a[::-1]) if flags & 2 else (lambda a: a)
Image.fromarray(flip(col)).save(out + "_color.png")
Image.fromarray(flip(ov)).save(out + "_overlay.png")
print(f"alpha>0 pixels: {(col[..., 3] > 0).mean() * 100:.1f}%  depth min {dep.min():.4f} max {dep.max():.4f}")
g = (np.clip(dep, 0, 1) * 255).astype(np.uint8)
Image.fromarray(flip(g)).save(out + "_depth.png")
