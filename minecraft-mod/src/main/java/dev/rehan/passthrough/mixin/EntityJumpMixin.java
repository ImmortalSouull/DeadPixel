package dev.rehan.passthrough.mixin;

import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * A player moved more than 32 blocks in one step is the host changing levels (every level has its own region, 100k+
 * blocks apart): the player is put there directly. Swept with collisions block by block along the way, that one move
 * held the server for 40-60 s on every level change (2026-10-08: "Can't keep up! ... 53121ms behind"); the host's
 * pose had paused during the load, so the player wasn't a ghost (noPhysics) for that first move.
 */
@Mixin(Entity.class)
abstract class EntityJumpMixin {
	@Inject(method = "move", at = @At("HEAD"), cancellable = true)
	private void passthrough$jump(final MoverType type, final Vec3 movement, final CallbackInfo ci) {
		Entity self = (Entity) (Object) this;
		if (self instanceof Player && movement.horizontalDistanceSqr() > 32.0 * 32.0) {
			self.setPos(self.getX() + movement.x, self.getY() + movement.y, self.getZ() + movement.z);
			ci.cancel();
		}
	}
}
