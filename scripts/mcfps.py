"""Minecraft's frame export rate: publish counter over N seconds (shared memory Local\MCPassthroughFrame)."""
import mmap, struct, sys, time
m = mmap.mmap(-1, 4096, tagname="Local\MCPassthroughFrame", access=mmap.ACCESS_READ)
n = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
a = struct.unpack_from("<q", m, 32)[0]; time.sleep(n); b = struct.unpack_from("<q", m, 32)[0]
print(f"Minecraft exports {(b - a) / n:.1f} frames/s")
