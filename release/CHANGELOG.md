# Changelog

## 1.1.1 — 2026-10-08
A fix release: please update from 1.1.0.
- **Crash fixed**: Trepang2 could crash (an access violation in d3d11) on the first frame of a level, right after it
  loaded: the compositor asked about the previous level's depth buffer, already destroyed. It now only looks at the
  depth buffer the current frame drew into. Checked: 14 level loads in a row and 3 cold starts, no crash.
- **Kick**: a zombie pressed right against you (a hunting zombie stands in you) is now kicked whatever the angle; the
  kick used to miss it.
- Test blocks (F6) stand on the floor under them, traced from knee height: they no longer end up on shelves.
- Quieter log in build mode.

## 1.1.0 — 2026-10-08
DeadPixel (was Blocktime 1.0.0): a new name, icon and launcher of its own, a big speed-up, and a round of polish.
- **New look**: the launcher is a dark monitor seen up close — the screen's pixel structure, steel bezels, signal red for
  the one thing that matters, status LEDs, an oscilloscope trace for Focus, pixel-stepped corners everywhere, and a
  wordmark with one pixel dead and one stuck on. Its own fonts (with Cyrillic). New icon.
- **Up to 40 % more FPS in Trepang2 with the mod on** (105 → 148 fps standing in the same spot, RTX 4050 laptop):
  the mod no longer scans the whole object array every few frames for grenades and characters — it is told about
  them as they begin play. Minecraft's frame reaches Trepang2 with less copying (the hand/HUD layer only when it has
  something in it), and the compositor searches Minecraft's frame only where Minecraft drew anything. Minecraft
  renders 7 chunks (112 m) instead of 10 — everything that can matter is within 96 m anyway. The picture is the same.
- **A mob right in your face is see-through, and the blocks behind it stay** (it used to fade in the compositor, and
  everything behind it faded with it; now Minecraft itself draws a near mob translucent, blocks included).
- **Minecraft's TNT wrecks Trepang2's rooms** (a little): blasts throw furniture and loose props, knock out one thin
  wall panel next to them (only where there is floor behind it; never pillars, beams or frames), leave a scorch mark.
  Floors, doors, lights and scripted pieces are never touched. A switch in SETTINGS.
- **Grenades break builds for real**: a frag lying on the floor went off inside Minecraft's invisible floor and broke
  nothing; it now blasts from just above it, and a frag is a bit stronger than TNT.
- **Cloak**: Minecraft's mobs lose track of you the moment you go invisible — they stop where they are instead of
  walking on to where you stood — and find you again when it runs out.
- **No more 40–60 s freezes in Minecraft on every level change**; builds keep their collision on a second visit;
  blocks placed on a level's first visit appear right away.
- Zombies summoned next to Trepang2's people find their footing on rubble and steps too.
- A Minecraft block seen past a thin thing of Trepang2's (a bed rail, a chair leg) no longer shows through it: Trepang2
  renders its depth at half resolution, and the compositor now takes the nearest of the depth texels around each pixel.
- Test blocks (F6) stand on the floor under each of them, not at the player's feet height (on a sunken floor they hung
  in the air).
- **Build mode places blocks where you look.** Trepang2 traces the camera ray against its own geometry (exact, per
  triangle; props and people included) and Minecraft puts the block on that surface - on the desk, against the wall, on
  the chair. A barrier of the grid in that cell gives way to the block (the barrier was the approximation). Nothing
  within reach: nothing is placed, never on the invisible grid.
- Barriers left in the world by earlier sessions are swept when a level is (re)entered.
- Floor probes use exact collision (a wall piece's simple hull used to reach 13 m down over SafeHouse's desks).
- Floors line up better: the level's height reference is the floor under the player, not the capsule's bottom (on
  Horde_Nuke every block sat 0.4 m deep in the floor).
- A floor column whose centre sat inside a monitor stand or a chair leg got no barrier at all — a one-block hole that TNT
  and mobs fell through; the probe now tries again off-centre.
- **Crash fixed**: TNT over soldiers already killed and torn apart by an earlier blast.

## 1.0.0 — 2026-10-07 (as Blocktime)
First release: Trepang2 × Minecraft.
