package dev.rehan.passthrough.client.mixin;

import net.minecraft.client.renderer.entity.LivingEntityRenderer;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Invoker;

@Mixin(LivingEntityRenderer.class)
public interface LivingEntityRendererInvoker {
	@Invoker("isBodyVisible")
	boolean passthrough$isBodyVisible(LivingEntityRenderState state);

	@Invoker("shouldRenderLayers")
	boolean passthrough$shouldRenderLayers(LivingEntityRenderState state);
}
