# Changelog / История изменений

**Русский** · [English](#english)

## 1.1.1 — 2026-10-08
Обновитесь с 1.1.0: там Trepang2 мог вылететь при загрузке уровня.

**Исправлено (относительно 1.1.0)**
- Вылет Trepang2 в первом кадре уровня (ошибка доступа в d3d11): мод обращался к буферу глубины прошлого уровня,
  уже уничтоженного. Проверено: 14 загрузок карт подряд и 3 холодных запуска — без вылетов.
- Пинок промахивался по зомби, стоящему вплотную: теперь моб ближе 60 см отлетает при любом угле.
- Тестовые блоки (F6) вставали на столы, полки и нижние ярусы под решётками.
- Лишние записи в журнале мода в режиме стройки.

**Известные баги**
- Охотящийся зомби подходит вплотную и стоит «в» игроке (рисуется полупрозрачным, пинок отбрасывает).
- Дым большого взрыва Minecraft закрывает обзор на 2–3 секунды.
- Запуск через официальный Minecraft Launcher (кнопка PLAY) не проверен живым нажатием.

## 1.1.0 — 2026-10-08
Новое имя DeadPixel (было Blocktime), новый лаунчер и иконка.

**Новое**
- До +40 % FPS с модом при той же картинке (105 → 148 к/с на одной сцене, RTX 4050).
- TNT из Minecraft немного крушит комнаты Trepang2: мебель разлетается, выбивается одна тонкая стеновая панель,
  остаётся гарь; колонны, двери, полы и сюжетные объекты не трогаются. Выключается в НАСТРОЙКАХ.
- Стройка по взгляду: блок встаёт на ту поверхность Trepang2, куда вы смотрите.
- Камуфляж прячет от мобов Minecraft: зомби останавливаются, как только вы исчезаете.

**Исправлено (относительно 1.0.0)**
- Граната на полу не ломала постройки; блоки при стройке вставали в воздухе; зомби у лица исчезал вместе с
  блоками за ним; тонкие предметы пропускали блоки; дыры в невидимом полу под столами; блоки утопали в полу до
  0,4 м на некоторых картах; зомби у людей Trepang2 не находили места на щебне; старые барьеры прошлых сессий;
  зависания Minecraft на 40–60 с при смене уровня; постройки без коллизии при повторном заходе; вылет от TNT над
  разорванными солдатами.

**Известные баги** (→ где исправлены)
- Вылет в первом кадре уровня → 1.1.1
- Пинок промахивался по зомби вплотную → 1.1.1
- Тестовые блоки вставали на столы и полки → 1.1.1

## 1.0.0 — 2026-10-07 (Blocktime)
Первый релиз: Minecraft внутри Trepang2 — замедление на двоих, блоки как укрытие, воронки от гранат, бой зомби с
солдатами, режим стройки, установщик.

**Известные баги** (→ где исправлены)
- Граната на полу не ломала постройки → 1.1.0
- Камуфляж не прятал от мобов → 1.1.0
- Блоки при стройке вставали в воздухе на некоторых картах → 1.1.0
- Зомби у лица исчезал вместе с блоками за ним → 1.1.0
- Тонкие предметы пропускали блоки за ними → 1.1.0
- Дыры в невидимом полу под столами → 1.1.0
- Блоки утопали в полу до 0,4 м на некоторых картах → 1.1.0
- Зависания Minecraft на 40–60 с при смене уровня; постройки без коллизии при повторном заходе → 1.1.0
- Вылет от TNT над убитыми и разорванными солдатами → 1.1.0
- FPS ниже, чем мог бы быть → 1.1.0
- Пинок промахивался по зомби вплотную → 1.1.1

---

<a name="english"></a>
## English

### 1.1.1 — 2026-10-08
A fix release: please update from 1.1.0.
- **Crash fixed**: Trepang2 could crash (an access violation in d3d11) on the first frame of a level, right after it
  loaded: the compositor asked about the previous level's depth buffer, already destroyed. It now only looks at the
  depth buffer the current frame drew into. Checked: 14 level loads in a row and 3 cold starts, no crash.
- **Kick**: a zombie pressed right against you (a hunting zombie stands in you) is now kicked whatever the angle; the
  kick used to miss it.
- Test blocks (F6) stand on the floor under them, traced from knee height: they no longer end up on shelves.
- Quieter log in build mode.

**Known bugs**
- A hunting zombie walks right up and stands "in" the player (drawn see-through; a kick throws it off).
- The smoke of a big Minecraft explosion covers the view for 2–3 seconds.
- Starting through the official Minecraft Launcher (the PLAY button) wasn't tested with a real click.

### 1.1.0 — 2026-10-08
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

**Known bugs** (→ fixed in)
- A crash on the first frame of a level → 1.1.1
- The kick missed a zombie pressed against you → 1.1.1
- Test blocks stood on desks and shelves → 1.1.1

### 1.0.0 — 2026-10-07 (as Blocktime)
First release: Trepang2 × Minecraft — bullet time for both games, blocks as cover, grenade craters, zombies vs
soldiers, build mode, an installer.

**Known bugs** (→ fixed in)
- A frag on the floor broke nothing in builds → 1.1.0
- Cloak didn't hide you from mobs → 1.1.0
- Blocks landed in the air in build mode on some maps → 1.1.0
- A zombie in your face faded out with the blocks behind it → 1.1.0
- Thin things let blocks behind them show through → 1.1.0
- Holes in the invisible floor under desks → 1.1.0
- Blocks sat up to 0.4 m deep in the floor on some maps → 1.1.0
- 40–60 s Minecraft freezes on level changes; builds without collision on a second visit → 1.1.0
- A crash from TNT over killed and torn-apart soldiers → 1.1.0
- Lower FPS than necessary → 1.1.0
- The kick missed a zombie pressed against you → 1.1.1
