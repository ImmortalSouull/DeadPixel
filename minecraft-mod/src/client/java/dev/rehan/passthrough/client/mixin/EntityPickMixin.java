package dev.rehan.passthrough.client.mixin;

import dev.rehan.passthrough.client.HostState;
import net.minecraft.client.Camera;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.VoxelShape;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * In third person the host camera sits behind and beside the player, so aim along the camera's ray (what is under
 * the crosshair) instead of from the player's eyes. The ray starts level with the player and reaches `range` past.
 * In first person a ray that misses is tried again against collision shapes: the host's ground is barriers.
 */
@Mixin(Entity.class)
abstract class EntityPickMixin {
	/**
	 * Minecraft's own blocks along the ray, by their outlines - the host's barriers skipped: they only stand in for the
	 * host's level (approximately), and the host says itself where its surfaces are.
	 */
	private static BlockHitResult passthrough$clipBlocksOnly(final Level level, final Vec3 from, final Vec3 to, final Entity self) {
		ClipContext ctx = new ClipContext(from, to, ClipContext.Block.OUTLINE, ClipContext.Fluid.NONE, self);
		return BlockGetter.traverseBlocks(from, to, ctx, (c, pos) -> {
			BlockState state = level.getBlockState(pos);
			if (state.isAir() || state.is(Blocks.BARRIER)) {
				return null;
			}

			VoxelShape shape = c.getBlockShape(state, level, pos);
			return level.clipWithInteractionOverride(from, to, pos, shape, state);
		}, c -> {
			Vec3 d = from.subtract(to);
			return BlockHitResult.miss(to, Direction.getApproximateNearest(d.x, d.y, d.z), BlockPos.containing(to));
		});
	}
	@Inject(method = "pick(DFZ)Lnet/minecraft/world/phys/HitResult;", at = @At("HEAD"), cancellable = true)
	private void passthrough$cameraRay(final double range, final float a, final boolean withLiquids, final CallbackInfoReturnable<HitResult> cir) {
		HostState.Pose p = HostState.frame();
		if (p == null || !((Object) this instanceof LocalPlayer self)) {
			return;
		}

		if (p.firstPerson()) {
			// Minecraft's own blocks first (their outlines)
			Vec3 eye = self.getEyePosition(a);
			Vec3 end = eye.add(self.getViewVector(a).scale(range));
			ClipContext.Fluid fluid = withLiquids ? ClipContext.Fluid.ANY : ClipContext.Fluid.NONE;
			HitResult outline = passthrough$clipBlocksOnly(self.level(), eye, end, self);
			// then the host's own geometry, where its camera ray meets it (build mode): the block goes into the cell on the
			// seen side of that surface, nearest to it. The barrier grid is only an approximation of the host's level
			// (floors rounded to whole blocks, desks as whole blocks, a few false walls), and aiming at it put blocks in
			// the air.
			double[] aim = p.aim();
			if (aim != null) {
				Vec3 hit = new Vec3(aim[0], aim[1], aim[2]);
				Vec3 n = new Vec3(aim[3], aim[4], aim[5]);
				double hostDist = hit.distanceToSqr(eye);
				if (hostDist <= range * range && (outline.getType() == HitResult.Type.MISS || hostDist < outline.getLocation().distanceToSqr(eye) + 1.0e-3)) {
					Direction face = Direction.getApproximateNearest(n.x, n.y, n.z);
					// the cell on the seen side of the surface, nearest to it; a barrier there (the grid's whole-block desk,
					// a false wall) gives way to the block (BarrierReplaceMixin)
					BlockPos cell = BlockPos.containing(hit.add(n.scale(0.5)));

					// the hit names the target cell itself: air there is "replaceable", so the block goes exactly into it
					// (naming the solid cell behind the surface put the block inside the host's wall - that cell is air to
					// Minecraft too, and air is what gets replaced)
					cir.setReturnValue(new BlockHitResult(hit, face, cell, false));
					return;
				}
			}

			if (p.aiming()) {
				// build mode with nothing of the host's in reach: Minecraft's own blocks or nothing (never the barrier grid)
				cir.setReturnValue(outline);
				return;
			}

			// outside build mode the barriers still count (what is aimed at the host's floor): a ray that finds no block
			// is tried again against collision shapes
			cir.setReturnValue(outline.getType() != HitResult.Type.MISS ? outline
				: self.level().clip(new ClipContext(eye, end, ClipContext.Block.COLLIDER, fluid, self)));
			return;
		}

		Camera camera = Minecraft.getInstance().gameRenderer.mainCamera();
		Vec3 from = camera.position();
		Vec3 dir = new Vec3(camera.forwardVector()).normalize();
		double along = Math.max(0.0, self.getEyePosition(a).subtract(from).dot(dir));
		Vec3 start = from.add(dir.scale(Math.max(0.0, along - 0.4)));
		Vec3 end = from.add(dir.scale(along + range));
		ClipContext.Fluid fluid = withLiquids ? ClipContext.Fluid.ANY : ClipContext.Fluid.NONE;
		cir.setReturnValue(self.level().clip(new ClipContext(start, end, ClipContext.Block.OUTLINE, fluid, self)));
	}
}
