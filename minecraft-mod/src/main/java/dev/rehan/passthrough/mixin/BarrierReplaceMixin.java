package dev.rehan.passthrough.mixin;

import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * The host's barriers only stand in for its level, a block at a time (a desk with a monitor on it is a 4-block pillar):
 * a block the player places goes where the host's own geometry says the surface is, barrier or not - the barrier there
 * was the approximation, the host's real collision still holds, and a block set into the host's wall is hidden by its
 * depth. Players have no barrier items, so every barrier is the host's.
 */
@Mixin(BlockBehaviour.class)
abstract class BarrierReplaceMixin {
	@Inject(method = "canBeReplaced(Lnet/minecraft/world/level/block/state/BlockState;Lnet/minecraft/world/item/context/BlockPlaceContext;)Z", at = @At("HEAD"), cancellable = true)
	private void passthrough$barriersGiveWay(final BlockState state, final BlockPlaceContext context, final CallbackInfoReturnable<Boolean> cir) {
		if (state.is(Blocks.BARRIER)) {
			cir.setReturnValue(true);
		}
	}
}
