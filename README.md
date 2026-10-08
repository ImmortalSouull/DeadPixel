# DeadPixel — Trepang2 × Minecraft

**Minecraft Java runs alongside Trepang2, and its blocks, mobs and explosions appear inside Trepang2's picture** — at
the right depth, under the HUD, lit to match the scene. Build cover and watch it get chewed apart by gunfire, slow
time with Focus and Minecraft slows down with you, frag a brick house into a crater, kick a zombie across the room.

*(Русская версия ниже.)*

## What it does
- **Minecraft in the picture.** Trepang2's camera drives Minecraft's; Minecraft's frame is composited into Trepang2's
  against its depth buffer (ReShade add-on), relit by the scene around it.
- **Bullet time, block time.** Focus (Q) slows Trepang2 down — and Minecraft's world with it: mobs, TNT fuses,
  arrows and particles run at Trepang2's time scale.
- **Blocks are cover — and they break.** Every Minecraft block is solid in Trepang2 (you and the AI bump into it,
  bullets stop). Your bullets crack and break blocks by their hardness: dirt and glass go in a shot, planks and stone in
  a few, iron takes a magazine, obsidian never breaks. Shooting TNT lights it.
- **Grenades leave craters.** Frags, grenade launcher rounds, rockets and mines blow the same blast into Minecraft.
- **Minecraft's TNT wrecks Trepang2's rooms — a little.** Blasts throw furniture and loose props, knock out a thin wall
  panel next to them (only where there is floor behind it) and leave a scorch mark. Floors, doors and scripted pieces
  stay. Switch it off in SETTINGS.
- **The two games fight.** Zombies and creepers attack Trepang2's soldiers and cultists; they shoot back with real
  bursts. TNT, creepers, arrows and fireworks hurt Trepang2's people. Your kick sends a mob flying; your gun kills mobs.
- **Cloak (E)** hides you from Minecraft's mobs too: walk right past them. A mob right in your face is drawn see-through.
- **Build mode (NumPad 0).** The mouse, wheel and 1–9 go to Minecraft: place blocks where you look — on Trepang2's floors,
  desks, walls and chairs — use any item; **E** opens Minecraft's creative inventory.
- **Trepang2's level in Minecraft.** Floors, stairs and walls become invisible barriers, so mobs walk every level.
  Every level gets its own part of the Minecraft world.

## Requirements
- Windows 10/11, a GPU that runs both games (tested: RTX 4050 laptop, 60 fps capped at 1920×1200).
- **Trepang2** (Steam), tested on build 2484 (30 Jul 2024). Single-player.
- **Minecraft: Java Edition** with the official Minecraft Launcher. DeadPixel uses Minecraft 26.3 with Fabric Loader
  0.19.5 in its own game folder; the launcher downloads the game itself on first start.

## Install
1. Run **DeadPixel.exe**. It finds Trepang2 (through Steam) and the Minecraft Launcher by itself.
2. **INSTALL** — installs everything (≈30 MB). Files that were already in Trepang2's folder are backed up.
3. **DEPLOY** — opens the Minecraft Launcher with the *DeadPixel* profile selected: press **PLAY** there. Once
   Minecraft has opened its world, DeadPixel starts Trepang2 through Steam.
4. Play a mission or a combat sim. Minecraft appears in it.

Windows SmartScreen may warn about an unknown publisher (the exe is not code-signed): *More info → Run anyway*.
Some antivirus programs flag `dwmapi.dll` / `dxgi.dll` (UE4SS and ReShade load through them): that is how both work.

## Controls
| Key | |
|---|---|
| Fire | Bullets break Minecraft blocks and hit Minecraft's mobs |
| Q (Focus) | Minecraft slows down with you |
| E (Cloak) | Minecraft's mobs lose track of you |
| RMB (Kick) | The mob in front of you flies off |
| NumPad 0 | Build mode on/off (mouse, wheel and 1–9 go to Minecraft) |
| LMB / RMB | Build mode: break, attack, shoot the bow / place a block, use the item |
| 1–9, wheel | Build mode: hotbar slot |
| E | Build mode: Minecraft's inventory (E or Esc closes it) |
| F5 | Minecraft in the picture on/off |
| F6 | Re-level the ground + test blocks in front of you |

Hotbar: zombie egg, diamond sword, crossbow (+ fireworks in the off hand), bow, TNT, flint and steel, creeper egg,
grass block, fireworks.

## Settings
DeadPixel → **SETTINGS**: Minecraft's render resolution (75 % by default), whether mobs hunt you, whether allies fight
mobs too. Applied the next time Trepang2 starts.

## Uninstall
DeadPixel → **INSTALL → UNINSTALL** (or Windows *Apps & features → DeadPixel*). Everything goes, the backed-up files go
back, the Minecraft profile is removed; your Minecraft world is kept if you ask it to.

## Troubleshooting
- Nothing of Minecraft in Trepang2: Minecraft must be in its world before you start a level; F5 toggles the picture.
  Trepang2 must run in DirectX 11 (its default; DEPLOY passes `-dx11`).
- Focus does nothing at a combat sim's very start: its meter starts empty in Trepang2 itself (kills charge it).
- Logs: `…\Trepang2\CPPFPS\Binaries\Win64\ue4ss\UE4SS.log`, `…\ue4ss\Mods\T2Passthrough\history.log`,
  `…\Win64\ReShade.log`; Minecraft: `%LOCALAPPDATA%\DeadPixel\minecraft\logs\latest.log`.
- After a Trepang2 update: DeadPixel → INSTALL → REPAIR.

## Credits
- [UE4SS](https://github.com/UE4SS-RE/RE-UE4SS) (MIT) — Unreal Engine scripting system.
- [ReShade](https://reshade.me) (BSD 3-Clause) by crosire — the add-on API the compositor runs in.
- [Fabric Loader and Fabric API](https://fabricmc.net) (Apache 2.0).
- The *mc-gta5-passthrough* example by rehan (MIT) — the Minecraft passthrough mod and compositor this builds on.
- Fonts: Chakra Petch, Share Tech Mono, Press Start 2P, Russo One, Play, PT Mono (SIL Open Font License).
- Built with Claude (Anthropic) in Claude Code: the code, the installer, the art (procedural) and the testing.
- Fan-made. Not affiliated with Trepang Studios, Team17, Mojang Studios or Microsoft. *Trepang2* and *Minecraft* are
  trademarks of their owners.

License: DeadPixel's own code is MIT (see LICENSE). Third-party parts keep their licenses (THIRD_PARTY_NOTICES.md).

---

# DeadPixel — Trepang2 × Minecraft (по-русски)

**Minecraft Java работает рядом с Trepang2, и его блоки, мобы и взрывы появляются прямо в кадре Trepang2** — на
правильной глубине, под интерфейсом, с подстроенным светом. Стройте укрытия и смотрите, как их крошат пули; включайте
фокус — и Minecraft замедляется вместе с вами; превращайте кирпичный дом в воронку гранатой; пинайте зомби.

## Возможности
- **Minecraft в кадре**: камера Trepang2 управляет камерой Minecraft, кадр встраивается по буферу глубины.
- **Замедление на двоих**: фокус (Q) замедляет и мир Minecraft — мобов, фитили TNT, стрелы, частицы.
- **Блоки — укрытие, и они ломаются**: каждый блок твёрдый в Trepang2 (пули тоже не проходят). Ваши пули ломают блоки по
  прочности: земля и стекло — с выстрела, доски и камень — с нескольких, железо — за магазин, обсидиан — никогда. TNT
  от выстрела поджигается.
- **Гранаты оставляют воронки**: осколочные, гранатомёт, ракеты и мины взрываются и в Minecraft.
- **TNT из Minecraft крушит комнаты Trepang2 — немного**: раскидывает мебель, выбивает тонкую стеновую панель рядом
  (только если за ней есть пол), оставляет гарь. Полы, двери и сюжетные объекты не трогаются. Выключается в НАСТРОЙКАХ.
- **Игры воюют**: зомби и криперы нападают на солдат и культистов, те отстреливаются настоящими очередями; TNT,
  криперы, стрелы и фейерверки ранят людей Trepang2; пинок отправляет моба в полёт; ваше оружие убивает мобов.
- **Камуфляж (E)** прячет вас и от мобов Minecraft: можно пройти мимо.
- **Режим стройки (NumPad 0)**: мышь, колесо и 1–9 идут в Minecraft; блок ставится туда, куда вы смотрите — на пол,
  стол, стену, стул Trepang2; **E** — творческий инвентарь.
- **Уровень Trepang2 в Minecraft**: полы и стены — невидимые барьеры; у каждого уровня своя часть мира Minecraft.

## Требования
Windows 10/11; Trepang2 (Steam, проверено на сборке 2484); Minecraft: Java Edition с официальным лаунчером. DeadPixel
использует Minecraft 26.3 + Fabric Loader 0.19.5 в своей папке игры.

## Установка
1. Запустите **DeadPixel.exe** — он сам найдёт Trepang2 и Minecraft Launcher.
2. **УСТАНОВИТЬ** — ставит всё (≈30 МБ), чужие файлы сохраняются в бэкап.
3. **В БОЙ** — открывает Minecraft Launcher с профилем *DeadPixel*: нажмите там **PLAY**. Когда мир откроется,
   DeadPixel запустит Trepang2 через Steam.
4. Играйте миссию или симуляцию боя.

SmartScreen может предупредить о неизвестном издателе: «Подробнее → Выполнить в любом случае».

## Управление
Огонь — пули ломают блоки и бьют мобов; Q — фокус замедляет и Minecraft; E — камуфляж от мобов; ПКМ — пинок;
NumPad 0 — режим стройки (ЛКМ/ПКМ — ломать/ставить, 1–9 и колесо — слот, E — инвентарь); F5 — Minecraft в кадре
вкл/выкл; F6 — выровнять пол.

## Удаление
DeadPixel → **УСТАНОВКА → УДАЛИТЬ** (или «Приложения» Windows). Всё убирается, сохранённые файлы возвращаются.

## Если не работает
Minecraft должен открыть мир до начала уровня; F5 включает картинку. Фокус в начале симуляции боя пуст в самой игре
(заряжается убийствами). Журналы: `…\Win64\ue4ss\UE4SS.log`, `…\ue4ss\Mods\T2Passthrough\history.log`,
`…\Win64\ReShade.log`, `%LOCALAPPDATA%\DeadPixel\minecraft\logs\latest.log`. После обновления Trepang2 — УСТАНОВКА →
ПОЧИНИТЬ.
