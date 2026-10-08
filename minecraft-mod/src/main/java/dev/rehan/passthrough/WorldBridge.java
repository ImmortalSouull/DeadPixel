package dev.rehan.passthrough;

import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.sounds.SoundSource;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.FireworkRocketEntity;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.entity.projectile.arrow.AbstractArrow;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.TntBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/** Server-side half: the host's collision as invisible barrier blocks, commands, and events back to the host. */
public final class WorldBridge {
	private static volatile MinecraftServer server;
	/** Barriers we placed (so a reset only removes ours, never the player's builds). */
	private static final Set<BlockPos> barriers = ConcurrentHashMap.newKeySet();
	/** Block changes this tick (server thread only): true = now solid, false = gone. Sent at the end of the tick. */
	private static final Map<BlockPos, Boolean> changes = new LinkedHashMap<>();
	/** While placing or removing the host's own ground: those changes aren't news to the host (server thread only). */
	private static boolean placingGround;

	private WorldBridge() {
	}

	static void attach(final MinecraftServer s) {
		server = s;
	}

	static void detach() {
		server = null;
		barriers.clear();
	}

	public static boolean ready() {
		return server != null;
	}

	static MinecraftServer server() {
		return server;
	}

	/** Columns of solid ground from the host: {x, z, yBottom, yTop, ...} in block coordinates (inclusive). Only air is replaced. */
	public static void solid(final int[] columns) {
		MinecraftServer s = server;
		if (s == null) {
			return;
		}

		s.execute(() -> {
			ServerLevel level = s.overworld();
			BlockState barrier = Blocks.BARRIER.defaultBlockState();
			BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
			placingGround = true;
			for (int i = 0; i + 3 < columns.length; i += 4) {
				for (int y = columns[i + 2]; y <= columns[i + 3]; y++) {
					pos.set(columns[i], y, columns[i + 1]);
					if (level.isInWorldBounds(pos) && level.getBlockState(pos).isAir()) {
						level.setBlock(pos, barrier, Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE);
						barriers.add(pos.immutable());
					}
				}
			}

			placingGround = false;
		});
	}

	/**
	 * Columns the host found passable after all ({x, z, yBottom, yTop, ...}, inclusive): its player or AI walked there,
	 * so a "wall" there was a false one (a doorway the coarse 1 m test caught). Only our own barriers go.
	 */
	public static void open(final int[] columns) {
		MinecraftServer s = server;
		if (s == null) {
			return;
		}

		s.execute(() -> {
			ServerLevel level = s.overworld();
			BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
			placingGround = true;
			for (int i = 0; i + 3 < columns.length; i += 4) {
				for (int y = columns[i + 2]; y <= columns[i + 3]; y++) {
					pos.set(columns[i], y, columns[i + 1]);
					if (barriers.remove(pos) && level.getBlockState(pos).is(Blocks.BARRIER)) {
						level.setBlock(pos, Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE);
					}
				}
			}

			placingGround = false;
		});
	}

	/**
	 * Remove the barriers we placed (the host re-levels: a new map, or its floor moved). Only in loaded chunks: the
	 * others belong to another map's region (every map has its own), and reading them loaded each chunk from disk
	 * inside the server tick - a 4 s freeze on every map change (2026-10-04). Those barriers stay for that map's
	 * next visit, which puts the same floors there again.
	 */
	public static void clearSolid() {
		MinecraftServer s = server;
		if (s == null) {
			return;
		}

		s.execute(() -> {
			ServerLevel level = s.overworld();
			placingGround = true;
			for (BlockPos pos : barriers) {
				if (level.isLoaded(pos) && level.getBlockState(pos).is(Blocks.BARRIER)) {
					level.setBlock(pos, Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE);
				}
			}

			// and the ones earlier sessions left in the saved world (the host's probe has changed since, and stale
			// barriers over the new ones put blocks and mobs in the air): every loaded chunk around the players
			int swept = 0;
			BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
			for (ServerPlayer player : level.players()) {
				int ccx = player.getBlockX() >> 4, ccz = player.getBlockZ() >> 4;
				for (int cx = ccx - 8; cx <= ccx + 8; cx++) {
					for (int cz = ccz - 8; cz <= ccz + 8; cz++) {
						net.minecraft.world.level.chunk.LevelChunk chunk = level.getChunkSource().getChunkNow(cx, cz);
						if (chunk == null) {
							continue;
						}

						net.minecraft.world.level.chunk.LevelChunkSection[] sections = chunk.getSections();
						for (int i = 0; i < sections.length; i++) {
							if (sections[i].hasOnlyAir() || !sections[i].maybeHas(state -> state.is(Blocks.BARRIER))) {
								continue;
							}

							int y0 = chunk.getSectionYFromSectionIndex(i) << 4;
							for (int y = 0; y < 16; y++) {
								for (int z = 0; z < 16; z++) {
									for (int x = 0; x < 16; x++) {
										if (sections[i].getBlockState(x, y, z).is(Blocks.BARRIER)) {
											p.set((cx << 4) + x, y0 + y, (cz << 4) + z);
											level.setBlock(p, Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE);
											swept++;
										}
									}
								}
							}
						}
					}
				}
			}

			if (swept > 0) {
				Passthrough.LOG.info("swept {} stale barriers from earlier sessions", swept);
			}

			placingGround = false;
			barriers.clear();
		});
	}

	/** Run a command as the server (op). Results go to the log, not to chat (send_command_feedback is off). */
	public static void command(final String command) {
		MinecraftServer s = server;
		if (s == null) {
			return;
		}

		s.execute(() -> {
			Passthrough.LOG.info("command: {}", command);
			loadChunksOf(s.overworld(), command);
			s.getCommands().performPrefixedCommand(s.createCommandSourceStack(), command);
		});
	}

	/** Coordinates in a command ("setblock x y z ...", "fill x1 y1 z1 x2 y2 z2 ...", "summon kind x y z"). */
	private static final java.util.regex.Pattern XYZ = java.util.regex.Pattern.compile("(-?\\d+(?:\\.\\d+)?) (-?\\d+(?:\\.\\d+)?) (-?\\d+(?:\\.\\d+)?)");

	/**
	 * The chunks a command's coordinates fall in, loaded (generated) first: on a map's first visit the region around
	 * the host's camera isn't loaded yet, and setblock / fill / summon there failed ("That position is not loaded").
	 */
	private static void loadChunksOf(final ServerLevel level, final String command) {
		java.util.regex.Matcher m = XYZ.matcher(command);
		while (m.find()) {
			int x = (int) Math.floor(Double.parseDouble(m.group(1)));
			int z = (int) Math.floor(Double.parseDouble(m.group(3)));
			level.getChunk(x >> 4, z >> 4);
		}
	}

	private static boolean solidForHost(final ServerLevel level, final BlockPos pos, final BlockState state) {
		// the Nether's ground is the host's own ground turned: nothing to collide with that isn't there already
		return !state.isAir() && !state.is(Blocks.BARRIER) && !state.getCollisionShape(level, pos).isEmpty() && !Nether.isGround(pos);
	}

	/** Arrows the host already hit something with (they stay where they hit and aren't reported again). */
	private static final String HIT_TAG = "passthrough_hit";
	/** A stuck arrow goes after this many ticks, like one in the ground in vanilla (60 s). */
	private static final int STUCK_LIFE = 1200;
	/** Server tick each stuck arrow was first seen at (by entity id; arrows loaded from the save count from then). */
	private static final Map<Integer, Integer> stuckSince = new java.util.HashMap<>();

	/**
	 * Whether the host traces this projectile through its own world (Steve's arrows and crossbow fireworks, see
	 * reportProjectiles): those fly through the barriers that stand for the host's floors and walls, the host says
	 * where they really hit. Everything else (ender pearls, snowballs, potions, mobs' arrows, fireballs) isn't traced
	 * and keeps colliding with the barriers, so it lands on the host's floors and stops at its walls.
	 */
	public static boolean hostTraced(final Entity e) {
		return (e instanceof AbstractArrow || e instanceof FireworkRocketEntity rocket && rocket.isShotAtAngle())
			&& ((Projectile) e).getOwner() instanceof Player;
	}

	/** Every server tick: block changes, and projectiles in flight for the host to trace through its own world. */
	static void tick(final MinecraftServer s) {
		flush(s);
		if (Passthrough.active) {
			reportProjectiles(s.overworld());
		}

		if (s.getTickCount() % 20 == 0) {
			expireStuckArrows(s.overworld(), s.getTickCount());
		}

		MobWar.tick(s);
		Nether.tick(s);
	}

	/**
	 * Steve's arrows (bow, crossbow) and crossbow fireworks in flight: {"t":"proj","p":[[id,kind,x,y,z],...]}. Mobs'
	 * arrows aren't traced by the host: they hit its people's proxies here.
	 */
	private static void reportProjectiles(final ServerLevel level) {
		StringBuilder b = null;
		for (Entity e : level.getAllEntities()) {
			String kind = null;
			if (!(e instanceof Projectile projectile) || !(projectile.getOwner() instanceof Player)) {
				continue;
			}

			if (e instanceof AbstractArrow arrow && !arrow.entityTags().contains(HIT_TAG) && arrow.getDeltaMovement().lengthSqr() > 1.0E-4) {
				kind = "arrow";
			} else if (e instanceof FireworkRocketEntity rocket && rocket.isShotAtAngle()) {
				kind = "firework"; // not the ones boosting an elytra flight
			}

			if (kind != null) {
				b = b == null ? new StringBuilder("{\"t\":\"proj\",\"p\":[") : b.append(',');
				b.append(String.format(Locale.ROOT, "[%d,\"%s\",%.3f,%.3f,%.3f]", e.getId(), kind, e.getX(), e.getY(), e.getZ()));
			}
		}

		if (b != null) {
			Passthrough.events.accept(b.append("]}").toString());
		}
	}

	/**
	 * Arrows stuck in the host's walls hang in the air on Minecraft's side (no block holds them, vanilla's "in ground"
	 * despawn never starts): they go after STUCK_LIFE ticks, also the ones left in the save by an earlier session.
	 */
	private static void expireStuckArrows(final ServerLevel level, final int now) {
		java.util.Set<Integer> alive = new java.util.HashSet<>();
		for (Entity e : level.getAllEntities()) {
			if (e instanceof AbstractArrow && e.entityTags().contains(HIT_TAG)) {
				alive.add(e.getId());
				if (now - stuckSince.computeIfAbsent(e.getId(), id -> now) >= STUCK_LIFE) {
					e.discard();
				}
			}
		}

		stuckSince.keySet().retainAll(alive);
	}

	/**
	 * The host traced a projectile into something of its own: a firework bursts there; an arrow goes into a person
	 * or car (gone) or sticks where it hit a wall.
	 */
	public static void projectileHit(final int id, final double x, final double y, final double z, final boolean stick) {
		MinecraftServer s = server;
		if (s == null) {
			return;
		}

		s.execute(() -> {
			ServerLevel level = s.overworld();
			Entity e = level.getEntity(id);
			if (e instanceof FireworkRocketEntity) {
				e.setPos(x, y, z);
				level.broadcastEntityEvent(e, (byte) 17);
				e.discard();
			} else if (e instanceof AbstractArrow) {
				if (stick) {
					e.setPos(x, y, z);
					e.setDeltaMovement(Vec3.ZERO);
					e.setNoGravity(true);
					e.addTag(HIT_TAG);
				} else {
					e.discard();
				}
			}
		});
	}

	/** Server thread, from Level.setBlock: remember the change; flushed once per tick. */
	public static void onBlockChanged(final ServerLevel level, final BlockPos pos, final BlockState state) {
		if (!Passthrough.active || level != level.getServer().overworld()) {
			return;
		}

		Nether.onBlockChanged(pos, state);
		if (!placingGround) {
			changes.put(pos.immutable(), solidForHost(level, pos, state));
		}
	}

	/** While on, block changes are the host's own ground being edited (not reported as blocks to collide with). */
	static void quietGround(final boolean on) {
		placingGround = on;
	}

	/** End of each server tick: {"t":"blocks","set":[x,y,z,...],"clear":[x,y,z,...]}. */
	static void flush(final MinecraftServer s) {
		if (changes.isEmpty()) {
			return;
		}

		StringBuilder set = new StringBuilder();
		StringBuilder clear = new StringBuilder();
		for (Map.Entry<BlockPos, Boolean> e : changes.entrySet()) {
			StringBuilder b = e.getValue() ? set : clear;
			BlockPos p = e.getKey();
			b.append(b.isEmpty() ? "" : ",").append(p.getX()).append(',').append(p.getY()).append(',').append(p.getZ());
		}

		changes.clear();
		Passthrough.events.accept("{\"t\":\"blocks\",\"set\":[" + set + "],\"clear\":[" + clear + "]}");
	}

	/**
	 * Every solid block within `radius` of `center` (the host's camera; null: the player), as one "blocks" message.
	 * Around the host's camera: right after a level change the player may still be in the last map's region.
	 */
	public static void sync(final int radius, final BlockPos center) {
		MinecraftServer s = server;
		if (s == null) {
			return;
		}

		s.execute(() -> {
			ServerLevel level = s.overworld();
			ServerPlayer player = s.getPlayerList().getPlayers().isEmpty() ? null : s.getPlayerList().getPlayers().get(0);
			if (player == null) {
				return;
			}

			BlockPos c = center != null ? center : player.blockPosition();
			for (int cx = (c.getX() - radius) >> 4; cx <= (c.getX() + radius) >> 4; cx++) {
				for (int cz = (c.getZ() - radius) >> 4; cz <= (c.getZ() + radius) >> 4; cz++) {
					level.getChunk(cx, cz); // a map's first frames: its region may not be loaded yet
				}
			}
			BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
			int found = 0;
			for (int x = -radius; x <= radius && found < 3000; x++) {
				for (int z = -radius; z <= radius && found < 3000; z++) {
					for (int y = -24; y <= 40; y++) {
						p.set(c.getX() + x, c.getY() + y, c.getZ() + z);
						if (!level.isInWorldBounds(p) || !level.isLoaded(p)) {
							continue;
						}

						BlockState state = level.getBlockState(p);
						if (solidForHost(level, p, state)) {
							changes.put(p.immutable(), true);
							found++;
						}
					}
				}
			}

			flush(s);
		});
	}

	/** Elytra on and gliding (creative flight off), launched forward along the look; or back to creative flight. */
	public static void glide(final boolean start, final double speed) {
		MinecraftServer s = server;
		if (s == null) {
			return;
		}

		s.execute(() -> {
			if (s.getPlayerList().getPlayers().isEmpty()) {
				return;
			}

			ServerPlayer player = s.getPlayerList().getPlayers().get(0);
			if (start) {
				player.setItemSlot(EquipmentSlot.CHEST, new ItemStack(Items.ELYTRA));
				player.getAbilities().flying = false;
				player.onUpdateAbilities();
				player.setOnGround(false);
				player.startFallFlying();
				player.setDeltaMovement(player.getLookAngle().scale(speed));
				player.needsSync = true;
			} else {
				player.stopFallFlying();
				player.setItemSlot(EquipmentSlot.CHEST, ItemStack.EMPTY);
				player.getAbilities().flying = true;
				player.onUpdateAbilities();
			}
		});
	}

	/** While Minecraft acts out one of the host's own explosions (reported back as "host": the host ignores those). */
	private static boolean hostBlast;

	/** The host's explosive went off (a grenade, a rocket): the same blast here, craters in what was built. */
	public static void hostExplosion(final double x, final double y, final double z, final float power) {
		MinecraftServer s = server;
		if (s == null) {
			return;
		}

		s.execute(() -> {
			hostBlast = true;
			try {
				// never centred inside a blast-proof barrier (the host's floor): its rays would all die at once
				double cy = y;
				for (int i = 0; i < 3 && s.overworld().getBlockState(BlockPos.containing(x, cy, z)).is(Blocks.BARRIER); i++) {
					cy = Math.floor(cy) + 1.2;
				}
				s.overworld().explode(null, x, cy, z, power, net.minecraft.world.level.Level.ExplosionInteraction.TNT);
			} finally {
				hostBlast = false;
			}
		});
	}

	/** `source`: what exploded or was blown up, e.g. "tnt", "creeper", "fireball" (a ghast's). */
	public static void onExplosion(final Vec3 center, final float radius, final String reported) {
		final String source = hostBlast ? "host" : reported;
		if (Passthrough.active) {
			Passthrough.events.accept(String.format(Locale.ROOT, "{\"t\":\"explosion\",\"pos\":[%.3f,%.3f,%.3f],\"r\":%.2f,\"src\":\"%s\"}",
				center.x, center.y, center.z, radius, source));
		}
	}

	/** Damage each block has taken from the host's bullets (server thread only), and when it was last hit (ticks). */
	private static final Map<BlockPos, float[]> blockDamage = new java.util.HashMap<>();
	/** Crack overlay ids, one per damaged block (any id not used by a player breaking blocks). */
	private static int crackIds = 0x7B10_0000;

	/**
	 * The host shot a block (its collision box in the host's world): {"t":"blockdmg","pos":[x,y,z],"d":damage,"n":pellets,
	 * "hit":[x,y,z]}. Blocks have hit points from their hardness: glass, dirt, wood go in a shot or two, stone in a few,
	 * iron blocks take a magazine, obsidian and bedrock don't break. TNT shot is primed. Cracks show the damage so far.
	 */
	public static void blockDamage(final int x, final int y, final int z, final double damage, final int pellets, final Vec3 hit) {
		MinecraftServer s = server;
		if (s == null) {
			return;
		}

		s.execute(() -> {
			ServerLevel level = s.overworld();
			BlockPos pos = new BlockPos(x, y, z);
			BlockState state = level.getBlockState(pos);
			if (state.isAir() || state.is(Blocks.BARRIER)) {
				return;
			}

			BlockParticleOption dust = new BlockParticleOption(ParticleTypes.BLOCK, state);
			level.sendParticles(dust, hit.x, hit.y, hit.z, 6 * Math.max(1, Math.min(pellets, 3)), 0.08, 0.08, 0.08, 0.15);
			level.playSound(null, pos, state.getSoundType().getHitSound(), SoundSource.BLOCKS, 0.9F, 1.1F);
			if (state.is(Blocks.TNT)) {
				TntBlock.prime(level, pos);
				level.removeBlock(pos, false);
				return;
			}

			float hardness = state.getDestroySpeed(level, pos);
			if (hardness < 0.0F || hardness >= 40.0F) {
				return; // bedrock, obsidian, end portal frames: bullets only chip them
			}

			// hit points: 1 shot of ~25 damage per 1.25 hardness (dirt 0.5 -> 1, planks 2 -> 2, stone 1.5 -> 2, iron 5 -> 4)
			float hp = Math.max(1.0F, hardness * 20.0F);
			float per = (float) Math.max(10.0, Math.min(damage, 80.0)) * Math.max(1, pellets) * (pellets > 1 ? 0.5F : 1.0F);
			float[] d = blockDamage.computeIfAbsent(pos, k -> new float[] {0.0F, crackIds++});
			d[0] += per;
			if (d[0] >= hp) {
				blockDamage.remove(pos);
				level.destroyBlockProgress((int) d[1], pos, -1);
				level.destroyBlock(pos, false, null, 512);
				Passthrough.LOG.info("host shot block {} ({}) apart", pos, state.getBlock().getName().getString());
			} else {
				level.destroyBlockProgress((int) d[1], pos, Math.min(9, (int) (d[0] / hp * 10.0F)));
			}
		});
	}

	/** The host's time dilation (its slow motion): Minecraft's tick rate follows, 20 x scale (clients get it too). */
	public static void tickRate(final float scale) {
		MinecraftServer s = server;
		if (s == null) {
			return;
		}

		s.execute(() -> {
			// never below 5 ticks/s: the server works through the host's floors and blocks one task per tick
			float rate = Math.max(5.0F, Math.min(20.0F, 20.0F * scale));
			s.tickRateManager().setTickRate(rate);
			Passthrough.LOG.info("tick rate {} (host time x{})", rate, scale);
		});
	}
}
