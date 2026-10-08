package dev.rehan.passthrough.client.mixin;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.rehan.passthrough.Passthrough;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.LivingEntityRenderer;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.world.phys.Vec3;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Constant;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.ModifyConstant;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * A mob right at the host's camera (a zombie hunting the player stands in its face) is drawn see-through by Minecraft
 * itself, the way it draws a spectator's view of invisible mobs: what is behind it (blocks) stays in the frame. Fading
 * it in the host's compositor instead would show the host's scene through it and lose the blocks it covers.
 */
@Mixin(LivingEntityRenderer.class)
abstract class LivingEntityRendererMixin {
	/** Closer than this (metres from the camera to the mob's box) the mob starts to fade. */
	@Unique private static final double FADE_FROM = 1.1;
	@Unique private static final double FADE_TO = 0.25;
	/** The faintest it gets (Minecraft discards fragments under 0.1 alpha in this pipeline). */
	@Unique private static final float FAINTEST = 0.16F;

	@Unique private float passthrough$alpha = 1.0F;

	@Inject(
		method = "submit(Lnet/minecraft/client/renderer/entity/state/LivingEntityRenderState;Lcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/SubmitNodeCollector;Lnet/minecraft/client/renderer/state/level/CameraRenderState;)V",
		at = @At("HEAD")
	)
	private void passthrough$nearness(final LivingEntityRenderState state, final PoseStack pose, final SubmitNodeCollector collector,
			final CameraRenderState camera, final CallbackInfo ci) {
		this.passthrough$alpha = 1.0F;
		if (!Passthrough.active || camera == null || camera.pos == null || !camera.isFirstPerson) {
			return;
		}

		Vec3 c = camera.pos;
		double half = state.boundingBoxWidth * 0.5;
		double dx = Math.max(Math.abs(c.x - state.x) - half, 0.0);
		double dz = Math.max(Math.abs(c.z - state.z) - half, 0.0);
		double dy = c.y < state.y ? state.y - c.y : Math.max(c.y - (state.y + state.boundingBoxHeight), 0.0);
		double d = Math.sqrt(dx * dx + dy * dy + dz * dz);
		if (d >= FADE_FROM) {
			return;
		}

		double t = Math.clamp((d - FADE_TO) / (FADE_FROM - FADE_TO), 0.0, 1.0);
		t = t * t * (3.0 - 2.0 * t);
		this.passthrough$alpha = (float)(FAINTEST + (1.0 - FAINTEST) * t);
	}

	/** A near mob takes Minecraft's see-through path (translucent render type). */
	@Redirect(
		method = "submit(Lnet/minecraft/client/renderer/entity/state/LivingEntityRenderState;Lcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/SubmitNodeCollector;Lnet/minecraft/client/renderer/state/level/CameraRenderState;)V",
		at = @At(value = "INVOKE", target = "Lnet/minecraft/client/renderer/entity/LivingEntityRenderer;isBodyVisible(Lnet/minecraft/client/renderer/entity/state/LivingEntityRenderState;)Z")
	)
	private boolean passthrough$seeThrough(final LivingEntityRenderer<?, ?, ?> self, final LivingEntityRenderState state) {
		boolean visible = ((LivingEntityRendererInvoker)self).passthrough$isBodyVisible(state);
		return visible && this.passthrough$alpha >= 1.0F;
	}

	/** ...with its alpha set by how close it is (vanilla's spectator alpha stays for everything else). */
	@ModifyConstant(
		method = "submit(Lnet/minecraft/client/renderer/entity/state/LivingEntityRenderState;Lcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/SubmitNodeCollector;Lnet/minecraft/client/renderer/state/level/CameraRenderState;)V",
		constant = @Constant(intValue = 654311423)
	)
	private int passthrough$alphaTint(final int spectatorTint) {
		if (this.passthrough$alpha >= 1.0F) {
			return spectatorTint;
		}

		return Math.round(this.passthrough$alpha * 255.0F) << 24 | 0xFFFFFF;
	}

	/** Armour, held items and the like are opaque: left out while the mob is see-through. */
	@Redirect(
		method = "submit(Lnet/minecraft/client/renderer/entity/state/LivingEntityRenderState;Lcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/SubmitNodeCollector;Lnet/minecraft/client/renderer/state/level/CameraRenderState;)V",
		at = @At(value = "INVOKE", target = "Lnet/minecraft/client/renderer/entity/LivingEntityRenderer;shouldRenderLayers(Lnet/minecraft/client/renderer/entity/state/LivingEntityRenderState;)Z")
	)
	private boolean passthrough$layers(final LivingEntityRenderer<?, ?, ?> self, final LivingEntityRenderState state) {
		return this.passthrough$alpha >= 0.85F && ((LivingEntityRendererInvoker)self).passthrough$shouldRenderLayers(state);
	}
}
