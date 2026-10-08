//! DeadPixel's look: a dark monitor seen up close. A faint pixel structure over everything, panels like steel bezels with
//! a lit top edge, signal red for the one thing that matters on each screen, status LEDs instead of check marks, an
//! oscilloscope trace for Focus, and every shape pixel-stepped at the corners (Trepang2's cold lab, Minecraft's grid).
//! One pixel of the wordmark is dead - and one next to it is stuck on red.

use eframe::egui::{self, pos2, vec2, Align2, Color32, CornerRadius, FontFamily, FontId, Painter, Pos2, Rect, Response, Sense, Shape, Stroke, StrokeKind, Ui};

thread_local! {
    /// Demo mode's fake pointer (window coordinates) and whether it is pressed: buttons react to it as to the mouse.
    pub static VIRTUAL: std::cell::Cell<Option<(Pos2, bool)>> = const { std::cell::Cell::new(None) };
}

fn virtual_on(rect: Rect) -> (bool, bool) {
    VIRTUAL.with(|v| match v.get() {
        Some((p, down)) if rect.contains(p) => (true, down),
        _ => (false, false),
    })
}

pub const BG: Color32 = Color32::from_rgb(6, 8, 10);
pub const PANEL: Color32 = Color32::from_rgba_premultiplied(12, 15, 18, 225);
pub const LINE: Color32 = Color32::from_rgba_premultiplied(60, 75, 85, 60);
pub const TEXT: Color32 = Color32::from_rgb(228, 236, 240);
pub const DIM: Color32 = Color32::from_rgb(138, 154, 166);
pub const FAINT: Color32 = Color32::from_rgb(70, 82, 92);
/// the stuck pixel: signal red, the accent everywhere
pub const RED: Color32 = Color32::from_rgb(255, 43, 58);
/// kept for the shared code: the accent
pub const ACCENT: Color32 = RED;
pub const BLUE: Color32 = Color32::from_rgb(92, 225, 255); // the phosphor's cold side: readouts, secondary marks
pub const CYAN: Color32 = BLUE;
pub const GREEN: Color32 = Color32::from_rgb(70, 224, 122);
pub const AMBER: Color32 = Color32::from_rgb(255, 179, 71);
/// one screen "pixel" of the UI's pixel-stepped shapes
pub const PX: f32 = 3.0;

pub fn head(size: f32) -> FontId {
    FontId::new(size, FontFamily::Name("head".into()))
}
pub fn head_m(size: f32) -> FontId {
    FontId::new(size, FontFamily::Name("headm".into()))
}
pub fn body(size: f32) -> FontId {
    FontId::new(size, FontFamily::Name("body".into()))
}
pub fn body_b(size: f32) -> FontId {
    FontId::new(size, FontFamily::Name("bodyb".into()))
}
pub fn mono(size: f32) -> FontId {
    FontId::new(size, FontFamily::Name("mono".into()))
}
pub fn pixel(size: f32) -> FontId {
    FontId::new(size, FontFamily::Name("pixel".into()))
}

pub fn with_alpha(c: Color32, a: f32) -> Color32 {
    Color32::from_rgba_unmultiplied(c.r(), c.g(), c.b(), (a.clamp(0.0, 1.0) * 255.0) as u8)
}

/// Text with letter spacing. Returns its width.
pub fn spaced(p: &Painter, pos: Pos2, align: Align2, text: &str, font: FontId, color: Color32, spacing: f32) -> f32 {
    let glyphs: Vec<_> = text.chars().map(|c| p.layout_no_wrap(c.to_string(), font.clone(), color)).collect();
    let width: f32 = glyphs.iter().map(|g| g.size().x).sum::<f32>() + spacing * (glyphs.len().saturating_sub(1)) as f32;
    let height = glyphs.iter().map(|g| g.size().y).fold(0.0, f32::max);
    let mut x = match align.x() {
        egui::Align::Min => pos.x,
        egui::Align::Center => pos.x - width / 2.0,
        egui::Align::Max => pos.x - width,
    };
    let y = match align.y() {
        egui::Align::Min => pos.y,
        egui::Align::Center => pos.y - height / 2.0,
        egui::Align::Max => pos.y - height,
    };
    for g in glyphs {
        let w = g.size().x;
        p.galley(pos2(x, y), g, color);
        x += w + spacing;
    }
    width
}

/// A rectangle with its corners stepped by one screen pixel (the 8-bit "round" corner): as a polygon.
fn stepped(r: Rect, step: f32) -> Vec<Pos2> {
    let s = step.min(r.width() / 2.0).min(r.height() / 2.0);
    vec![
        pos2(r.min.x + s, r.min.y),
        pos2(r.max.x - s, r.min.y),
        pos2(r.max.x, r.min.y + s),
        pos2(r.max.x, r.max.y - s),
        pos2(r.max.x - s, r.max.y),
        pos2(r.min.x + s, r.max.y),
        pos2(r.min.x, r.max.y - s),
        pos2(r.min.x, r.min.y + s),
    ]
}

pub fn pixel_rect(p: &Painter, r: Rect, fill: Color32, stroke: Option<Color32>) {
    let pts = stepped(r, PX);
    if fill.a() > 0 {
        p.add(Shape::convex_polygon(pts.clone(), fill, Stroke::NONE));
    }
    if let Some(c) = stroke {
        p.add(Shape::closed_line(pts, Stroke::new(1.0, c)));
    }
}

/// A status LED: a lit pixel square with a glow, or a dark socket.
pub fn led(p: &Painter, c: Pos2, color: Color32, lit: bool) {
    if lit {
        p.rect_filled(Rect::from_center_size(c, vec2(16.0, 16.0)), CornerRadius::ZERO, with_alpha(color, 0.10));
        p.rect_filled(Rect::from_center_size(c, vec2(10.0, 10.0)), CornerRadius::ZERO, with_alpha(color, 0.30));
        p.rect_filled(Rect::from_center_size(c, vec2(6.0, 6.0)), CornerRadius::ZERO, color);
    } else {
        p.rect_filled(Rect::from_center_size(c, vec2(6.0, 6.0)), CornerRadius::ZERO, with_alpha(Color32::WHITE, 0.08));
        p.rect_stroke(Rect::from_center_size(c, vec2(8.0, 8.0)), CornerRadius::ZERO, Stroke::new(1.0, FAINT), StrokeKind::Inside);
    }
}

/// kept for the shared code
pub fn lamp(p: &Painter, c: Pos2, color: Color32, lit: bool) {
    led(p, c, color, lit);
}

/// A section label: a red LED pixel, then "LABEL" in terminal mono.
pub fn tag(p: &Painter, pos: Pos2, text: &str, color: Color32) -> f32 {
    p.rect_filled(Rect::from_center_size(pos + vec2(3.0, 0.0), vec2(6.0, 6.0)), CornerRadius::ZERO, RED);
    spaced(p, pos + vec2(14.0, 0.0), Align2::LEFT_CENTER, text, mono(13.0), color, 1.5) + 14.0
}

/// The wordmark: "DEADPIXEL" in the pixel font, one pixel of its I gone dark and the one beside it stuck on red.
/// Returns its width.
pub fn wordmark(p: &Painter, at: Pos2, size: f32, color: Color32) -> f32 {
    let gap = (size * 0.1).round();
    let w = spaced(p, at, Align2::LEFT_CENTER, "DEADPIXEL", pixel(size), color, gap);
    let cell = size / 8.0;
    let adv = size + gap;
    // the I is the sixth letter; its bar is the middle two columns of its 8x8 cell
    let ix = at.x + 5.0 * adv + 3.0 * cell;
    let top = at.y - size / 2.0;
    p.rect_filled(Rect::from_min_size(pos2(ix, top + 3.0 * cell), vec2(2.0 * cell, cell)), CornerRadius::ZERO, BG);
    p.rect_filled(Rect::from_min_size(pos2(ix, top + 3.0 * cell), vec2(cell, cell)), CornerRadius::ZERO, RED);
    p.rect_filled(Rect::from_min_size(pos2(ix - cell * 0.5, top + 2.5 * cell), vec2(2.0 * cell, 2.0 * cell)), CornerRadius::ZERO, with_alpha(RED, 0.18));
    w
}

/// A pixel-stepped scope: a sine trace that runs at `scale` of real time (1.0: Trepang2's real time, 0.25: deep
/// Focus), drawn as the phosphor would hold it, a bright sweep dot at its head; the readouts in the corners.
pub fn scope(p: &Painter, rect: Rect, scale: f32, t: f32) {
    p.rect_filled(rect, CornerRadius::ZERO, with_alpha(Color32::BLACK, 0.45));
    let grid = Stroke::new(1.0, with_alpha(CYAN, 0.08));
    let cols = 8;
    for i in 1..cols {
        let x = rect.min.x + rect.width() * i as f32 / cols as f32;
        p.line_segment([pos2(x, rect.min.y), pos2(x, rect.max.y)], grid);
    }
    for j in 1..4 {
        let y = rect.min.y + rect.height() * j as f32 / 4.0;
        p.line_segment([pos2(rect.min.x, y), pos2(rect.max.x, y)], grid);
    }
    p.line_segment([pos2(rect.min.x, rect.center().y), pos2(rect.max.x, rect.center().y)], Stroke::new(1.0, with_alpha(CYAN, 0.18)));
    // the trace: a wave whose frequency is the time scale; the sweep's phase runs with t
    let amp = rect.height() * 0.30;
    let n = (rect.width() / PX).floor() as usize;
    let sweep = (t * 0.45).fract();
    let wave = |u: f32| -> f32 {
        let phase = u * std::f32::consts::TAU * (1.5 + 6.5 * scale) - t * 2.2;
        rect.center().y - phase.sin() * amp * (0.55 + 0.45 * scale)
    };
    let mut prev: Option<Pos2> = None;
    for i in 0..=n {
        let u = i as f32 / n as f32;
        let at = pos2(rect.min.x + u * rect.width(), (wave(u) / PX).round() * PX);
        let age = (sweep - u).rem_euclid(1.0); // how long ago the sweep passed here
        let a = (1.0 - age * 1.1).clamp(0.12, 1.0);
        if let Some(q) = prev {
            p.line_segment([q, at], Stroke::new(2.0, with_alpha(RED, a)));
        }
        prev = Some(at);
    }
    let head_at = pos2(rect.min.x + sweep * rect.width(), wave(sweep));
    p.rect_filled(Rect::from_center_size(head_at, vec2(11.0, 11.0)), CornerRadius::ZERO, with_alpha(RED, 0.25));
    p.rect_filled(Rect::from_center_size(head_at, vec2(5.0, 5.0)), CornerRadius::ZERO, Color32::WHITE);
    spaced(p, rect.min + vec2(10.0, 14.0), Align2::LEFT_CENTER, &format!("{scale:.2}x"), head(22.0), TEXT, 1.0);
    spaced(p, pos2(rect.max.x - 10.0, rect.min.y + 14.0), Align2::RIGHT_CENTER, &format!("MC {:.0} TICKS/S", 20.0 * scale.max(0.25)), mono(12.0), CYAN, 1.0);
    let focus = scale < 0.6;
    spaced(p, pos2(rect.max.x - 10.0, rect.max.y - 12.0), Align2::RIGHT_CENTER, if focus { "FOCUS" } else { "REAL TIME" }, pixel(9.0), if focus { RED } else { DIM }, 1.0);
}

#[derive(Clone, Copy, PartialEq)]
pub enum Btn {
    /// signal red, dark text: the call to action
    Primary,
    /// a thin outline
    Ghost,
    Danger,
}

/// A button: a pixel-stepped plate. Hover brightens and splits the label's colour a pixel (a glitch); pressed sinks.
pub fn button(ui: &mut Ui, rect: Rect, label: &str, font: FontId, kind: Btn, enabled: bool) -> Response {
    let id = ui.id().with(("btn", label, rect.min.x as i32, rect.min.y as i32));
    let resp = ui.interact(rect, id, if enabled { Sense::click() } else { Sense::hover() });
    let p = ui.painter();
    let (vh, vd) = virtual_on(rect);
    let hovered = enabled && (resp.hovered() || vh);
    let pressed = enabled && (resp.is_pointer_button_down_on() || vd);
    let r = if pressed { rect.translate(vec2(0.0, 1.0)) } else { rect };
    let (fill, stroke, text) = match (kind, enabled, hovered) {
        (_, false, _) => (with_alpha(Color32::WHITE, 0.04), with_alpha(Color32::WHITE, 0.10), FAINT),
        (Btn::Primary, true, false) => (RED, RED, Color32::from_rgb(14, 6, 8)),
        (Btn::Primary, true, true) => (Color32::from_rgb(255, 92, 104), Color32::WHITE, Color32::BLACK),
        (Btn::Ghost, true, false) => (with_alpha(Color32::BLACK, 0.45), with_alpha(Color32::WHITE, 0.30), TEXT),
        (Btn::Ghost, true, true) => (with_alpha(CYAN, 0.10), CYAN, Color32::WHITE),
        (Btn::Danger, true, false) => (with_alpha(Color32::BLACK, 0.45), with_alpha(RED, 0.7), RED),
        (Btn::Danger, true, true) => (RED, RED, Color32::WHITE),
    };
    pixel_rect(p, r, fill, Some(stroke));
    if kind == Btn::Primary && enabled {
        // the top edge lit, as a bezel catches light; a lit pixel in the corner
        p.line_segment([pos2(r.min.x + PX, r.min.y + 1.0), pos2(r.max.x - PX, r.min.y + 1.0)], Stroke::new(1.0, with_alpha(Color32::WHITE, 0.45)));
        p.rect_filled(Rect::from_min_size(r.min + vec2(8.0, 8.0), vec2(4.0, 4.0)), CornerRadius::ZERO, with_alpha(Color32::WHITE, 0.9));
    }
    if hovered {
        // chromatic split under the label
        spaced(p, r.center() + vec2(-1.0, 0.0), Align2::CENTER_CENTER, label, font.clone(), with_alpha(CYAN, 0.55), 2.0);
        spaced(p, r.center() + vec2(1.0, 0.0), Align2::CENTER_CENTER, label, font.clone(), with_alpha(RED, 0.55), 2.0);
    }
    spaced(p, r.center(), Align2::CENTER_CENTER, label, font, text, 2.0);
    if hovered {
        ui.ctx().set_cursor_icon(egui::CursorIcon::PointingHand);
    }
    resp
}

/// A tab along the top: "01 PLAY", the active one white with a row of red pixels under it.
pub fn menu_item(ui: &mut Ui, rect: Rect, index: usize, label: &str, selected: bool) -> Response {
    let id = ui.id().with(("menu", index));
    let resp = ui.interact(rect, id, Sense::click());
    let p = ui.painter();
    let (vh, _) = virtual_on(rect);
    let hovered = resp.hovered() || vh;
    let color = if selected { TEXT } else if hovered { Color32::from_rgb(200, 212, 220) } else { DIM };
    let w = spaced(p, pos2(0.0, -500.0), Align2::LEFT_CENTER, label, head_m(17.0), color, 1.5);
    let x0 = rect.center().x - (w + 26.0) / 2.0;
    if selected {
        p.rect_filled(rect, CornerRadius::ZERO, with_alpha(Color32::WHITE, 0.04));
        // the underline: pixels, one gap between
        let mut x = x0;
        while x < x0 + w + 26.0 {
            p.rect_filled(Rect::from_min_size(pos2(x, rect.max.y - 4.0), vec2(PX, PX)), CornerRadius::ZERO, RED);
            x += PX * 2.0;
        }
    } else if hovered {
        p.rect_filled(Rect::from_min_max(pos2(rect.min.x, rect.max.y - 1.0), rect.max), CornerRadius::ZERO, with_alpha(CYAN, 0.45));
    }
    p.text(pos2(x0, rect.center().y), Align2::LEFT_CENTER, format!("{:02}", index), pixel(9.0), if selected { RED } else { FAINT });
    spaced(p, pos2(x0 + 26.0, rect.center().y), Align2::LEFT_CENTER, label, head_m(17.0), color, 1.5);
    if hovered {
        ui.ctx().set_cursor_icon(egui::CursorIcon::PointingHand);
    }
    resp
}

/// A panel: a dark plate with its top edge lit (a bezel), a header strip with an LED and "TITLE" in mono, and a channel
/// number on the right.
pub fn panel(p: &Painter, rect: Rect, title: Option<&str>) {
    pixel_rect(p, rect, PANEL, Some(LINE));
    p.line_segment([pos2(rect.min.x + PX, rect.min.y + 1.0), pos2(rect.max.x - PX, rect.min.y + 1.0)], Stroke::new(1.0, with_alpha(Color32::WHITE, 0.10)));
    if let Some(t) = title {
        let strip = Rect::from_min_size(rect.min + vec2(1.0, 2.0), vec2(rect.width() - 2.0, 26.0));
        p.rect_filled(strip, CornerRadius::ZERO, with_alpha(Color32::WHITE, 0.035));
        p.rect_filled(Rect::from_center_size(rect.min + vec2(16.0, 15.0), vec2(6.0, 6.0)), CornerRadius::ZERO, RED);
        spaced(p, rect.min + vec2(28.0, 15.0), Align2::LEFT_CENTER, t, mono(13.0), TEXT, 2.0);
        let n = hash(t.len() as u32 * 977 + t.chars().next().map(|c| c as u32).unwrap_or(0)) % 16 + 1;
        spaced(p, pos2(rect.max.x - 12.0, rect.min.y + 15.0), Align2::RIGHT_CENTER, &format!("CH {n:02}"), pixel(8.0), FAINT, 1.0);
    }
}

/// A readout line: an LED, the text, the detail under it, and the status word in the pixel font on the right.
pub fn objective(p: &Painter, at: Pos2, width: f32, done: Option<bool>, text: &str, detail: &str, state: &str) {
    let c = match done {
        Some(true) => GREEN,
        Some(false) => RED,
        None => AMBER,
    };
    led(p, at + vec2(8.0, 12.0), c, true);
    p.text(at + vec2(26.0, 10.0), Align2::LEFT_CENTER, text, body_b(18.0), TEXT);
    p.text(at + vec2(26.0, 31.0), Align2::LEFT_CENTER, detail, mono(13.0), DIM);
    let g = p.layout_no_wrap(state.to_owned(), pixel(10.0), c);
    let box_ = Rect::from_center_size(at + vec2(width - 56.0, 12.0), g.size() + vec2(16.0, 10.0));
    pixel_rect(p, box_, with_alpha(c, 0.10), Some(with_alpha(c, 0.7)));
    p.galley(box_.center() - g.size() / 2.0, g, c);
}

/// An on/off option: a pixel switch and a label with a dim hint. Returns true when clicked.
pub fn toggle(ui: &mut Ui, at: Pos2, width: f32, on: &mut bool, label: &str, hint: Option<&str>) -> bool {
    let h = if hint.is_some() { 44.0 } else { 26.0 };
    let rect = Rect::from_min_size(at, vec2(width, h));
    let resp = ui.interact(rect, ui.id().with(("toggle", label)), Sense::click());
    let p = ui.painter();
    let track = Rect::from_min_size(at + vec2(0.0, 4.0), vec2(34.0, 16.0));
    pixel_rect(p, track, if *on { with_alpha(RED, 0.85) } else { with_alpha(Color32::WHITE, 0.10) }, Some(if resp.hovered() { Color32::WHITE } else { with_alpha(Color32::WHITE, 0.35) }));
    let knob = Rect::from_min_size(track.min + vec2(if *on { 20.0 } else { 2.0 }, 2.0), vec2(12.0, 12.0));
    p.rect_filled(knob, CornerRadius::ZERO, if *on { Color32::from_rgb(20, 8, 10) } else { DIM });
    p.text(at + vec2(46.0, 12.0), Align2::LEFT_CENTER, label, body_b(17.0), if resp.hovered() { Color32::WHITE } else { TEXT });
    if let Some(hint) = hint {
        p.text(at + vec2(46.0, 32.0), Align2::LEFT_CENTER, hint, body(14.5), DIM);
    }
    if resp.hovered() {
        ui.ctx().set_cursor_icon(egui::CursorIcon::PointingHand);
    }
    if resp.clicked() {
        *on = !*on;
        return true;
    }
    false
}

/// A track of pixel segments with a block handle; the value in mono on the right.
pub fn slider(ui: &mut Ui, rect: Rect, value: &mut u32, min: u32, max: u32, step: u32, label: &str) -> bool {
    let resp = ui.interact(rect, ui.id().with(("slider", label)), Sense::click_and_drag());
    let p = ui.painter();
    p.text(pos2(rect.min.x, rect.min.y + 8.0), Align2::LEFT_CENTER, label, body_b(17.0), TEXT);
    spaced(p, pos2(rect.max.x, rect.min.y + 8.0), Align2::RIGHT_CENTER, &format!("{value}%"), mono(15.0), CYAN, 1.0);
    let ty = rect.max.y - 10.0;
    let (x0, x1) = (rect.min.x, rect.max.x);
    let t = (*value - min) as f32 / (max - min) as f32;
    let hx = x0 + t * (x1 - x0);
    let segs = ((max - min) / step) as usize;
    for k in 0..segs {
        let a = x0 + k as f32 / segs as f32 * (x1 - x0);
        let b = x0 + (k + 1) as f32 / segs as f32 * (x1 - x0) - 3.0;
        p.rect_filled(Rect::from_min_max(pos2(a, ty - 3.0), pos2(b, ty + 3.0)), CornerRadius::ZERO, if b <= hx + 1.0 { RED } else { with_alpha(Color32::WHITE, 0.14) });
    }
    let knob = Rect::from_center_size(pos2(hx, ty), vec2(10.0, 20.0));
    pixel_rect(p, knob, if resp.hovered() || resp.dragged() { Color32::WHITE } else { TEXT }, None);
    let mut changed = false;
    if resp.dragged() || resp.clicked() {
        if let Some(pos) = resp.interact_pointer_pos() {
            let t = ((pos.x - x0) / (x1 - x0)).clamp(0.0, 1.0);
            let v = (((min as f32 + t * (max - min) as f32) / step as f32).round() as u32 * step).clamp(min, max);
            if v != *value {
                *value = v;
                changed = true;
            }
        }
    }
    changed
}

/// The install progress: a row of pixels lighting up red, the next one blinking.
pub fn progress_bar(p: &Painter, rect: Rect, fraction: f32, failed: bool) {
    pixel_rect(p, rect, with_alpha(Color32::BLACK, 0.6), Some(with_alpha(Color32::WHITE, 0.2)));
    let inner = rect.shrink(3.0);
    let n = (inner.width() / 10.0).floor() as usize;
    let lit = (n as f32 * fraction.clamp(0.0, 1.0)).floor() as usize;
    let blink = (p.ctx().input(|i| i.time) * 6.0).fract() < 0.5;
    for i in 0..n {
        let r = Rect::from_min_size(pos2(inner.min.x + i as f32 * 10.0, inner.min.y), vec2(7.0, inner.height()));
        let c = if i < lit {
            if failed { AMBER } else { RED }
        } else if i == lit && blink && fraction < 1.0 && !failed {
            with_alpha(RED, 0.5)
        } else {
            with_alpha(Color32::WHITE, 0.06)
        };
        p.rect_filled(r, CornerRadius::ZERO, c);
    }
}

/// A key cap: dark, thin border, mono label, a red underline.
pub fn keycap(p: &Painter, at: Pos2, label: &str) -> f32 {
    let w = (label.chars().count() as f32 * 9.5 + 22.0).max(46.0);
    let r = Rect::from_min_size(at, vec2(w, 28.0));
    pixel_rect(p, r, with_alpha(Color32::WHITE, 0.06), Some(with_alpha(Color32::WHITE, 0.35)));
    p.line_segment([pos2(r.min.x + PX, r.max.y - 1.0), pos2(r.max.x - PX, r.max.y - 1.0)], Stroke::new(2.0, RED));
    p.text(r.center(), Align2::CENTER_CENTER, label, mono(13.0), TEXT);
    w
}

/// The scene behind everything: the backdrop drifting slowly, darkened, the screen's pixel structure over it, a slow
/// refresh band, and the dead pixel itself, stuck on red in the corner.
pub fn background(p: &Painter, rect: Rect, t: f32, image: Option<&egui::TextureHandle>) {
    p.rect_filled(rect, CornerRadius::ZERO, BG);
    if let Some(tex) = image {
        let size = tex.size_vec2();
        let over = size - rect.size();
        let k = (t * 0.03).sin() * 0.5 + 0.5;
        let off = vec2(over.x * k, over.y * (0.5 + 0.3 * (t * 0.021).cos()));
        let r = Rect::from_min_size(rect.min - off, size);
        p.image(tex.id(), r, Rect::from_min_max(pos2(0.0, 0.0), pos2(1.0, 1.0)), with_alpha(Color32::WHITE, 0.42));
    }
    // the pixel structure: fine lines every 4 px, barely there (a monitor seen up close)
    let grid = Stroke::new(1.0, with_alpha(Color32::BLACK, 0.22));
    let mut x = rect.min.x;
    while x < rect.max.x {
        p.line_segment([pos2(x, rect.min.y), pos2(x, rect.max.y)], grid);
        x += 4.0;
    }
    let mut y = rect.min.y;
    while y < rect.max.y {
        p.line_segment([pos2(rect.min.x, y), pos2(rect.max.x, y)], grid);
        y += 4.0;
    }
    // a cold glow from the top right, breathing
    let a = 0.06 + 0.04 * ((t * 0.7).sin() * 0.5 + 0.5);
    let mut mesh = egui::Mesh::default();
    mesh.colored_vertex(rect.right_top(), with_alpha(CYAN, a));
    mesh.colored_vertex(rect.right_top() - vec2(560.0, 0.0), with_alpha(CYAN, 0.0));
    mesh.colored_vertex(rect.right_top() + vec2(0.0, 420.0), with_alpha(CYAN, 0.0));
    mesh.add_triangle(0, 1, 2);
    p.add(Shape::mesh(mesh));
    // the refresh band
    let sy = rect.min.y + ((t * 28.0) % (rect.height() + 80.0)) - 40.0;
    for i in 0..8 {
        let yy = sy + i as f32 * 4.0;
        p.line_segment([pos2(rect.min.x, yy), pos2(rect.max.x, yy)], Stroke::new(2.0, with_alpha(Color32::WHITE, 0.012 * (8 - i) as f32)));
    }
    // the lower right darkened (the backdrop's own HUD sits there)
    let mut shade = egui::Mesh::default();
    shade.colored_vertex(rect.right_bottom(), with_alpha(Color32::BLACK, 0.85));
    shade.colored_vertex(rect.right_bottom() - vec2(420.0, 0.0), with_alpha(Color32::BLACK, 0.0));
    shade.colored_vertex(rect.right_bottom() - vec2(0.0, 260.0), with_alpha(Color32::BLACK, 0.0));
    shade.add_triangle(0, 1, 2);
    p.add(Shape::mesh(shade));
    // the dead pixel: stuck on, in the lower right, its glow pulsing
    let d = pos2(rect.max.x - 46.0, rect.max.y - 62.0);
    let pulse = 0.5 + 0.5 * (t * 2.6).sin();
    p.rect_filled(Rect::from_center_size(d, vec2(14.0, 14.0)), CornerRadius::ZERO, with_alpha(RED, 0.08 + 0.10 * pulse));
    p.rect_filled(Rect::from_center_size(d, vec2(4.0, 4.0)), CornerRadius::ZERO, RED);
}

pub fn spinner(p: &Painter, c: Pos2, t: f32, color: Color32) {
    // eight pixels around a ring, the lit one running
    let lit = ((t * 10.0) as usize) % 8;
    for i in 0..8 {
        let a = i as f32 / 8.0 * std::f32::consts::TAU;
        let d = vec2(a.cos(), a.sin()) * 7.0;
        let k = ((i + 8 - lit) % 8) as f32 / 8.0;
        p.rect_filled(Rect::from_center_size(c + d, vec2(3.0, 3.0)), CornerRadius::ZERO, with_alpha(color, (1.0 - k).max(0.15)));
    }
}

// ---------------------------------------------------------------------------------------------------------------
// Minecraft's pixel blocks (the hotbar, the loadout tiles)

#[derive(Clone, Copy)]
pub enum Block {
    Grass,
    Tnt,
    Brick,
}

fn rgb(c: u32) -> Color32 {
    Color32::from_rgb((c >> 16) as u8, (c >> 8) as u8, c as u8)
}

fn texture(b: Block, top: bool, x: usize, y: usize, salt: u32) -> Color32 {
    let n = hash(x as u32 * 7 + y as u32 * 13 + salt) % 4;
    match b {
        Block::Grass => {
            if top || y == 0 {
                rgb([0x5da034, 0x6ab03c, 0x54922e, 0x76ba46][n as usize])
            } else {
                rgb([0x866043, 0x79553a, 0x966c4a, 0x6c4c34][n as usize])
            }
        }
        Block::Tnt => {
            if top {
                if (x == 1 || x == 2) && (y == 1 || y == 2) { rgb(0x2a2a2a) } else { rgb(0xdb4a3c) }
            } else if y == 1 || y == 2 {
                if n == 0 { rgb(0x1e1e1e) } else { rgb(0xeeeeee) }
            } else {
                rgb([0xdb4a3c, 0xc23a2e, 0xe0584a, 0xb8352a][n as usize])
            }
        }
        Block::Brick => {
            if y % 2 == 1 && (x + y / 2) % 2 == 0 {
                rgb(0xb0a49a)
            } else {
                rgb([0x9a4a3a, 0x8c4234, 0xa65444, 0x84402f][n as usize])
            }
        }
    }
}

pub fn hash(mut x: u32) -> u32 {
    x ^= x >> 16;
    x = x.wrapping_mul(0x7feb352d);
    x ^= x >> 15;
    x = x.wrapping_mul(0x846ca68b);
    x ^ (x >> 16)
}

fn shade(c: Color32, f: f32, alpha: f32) -> Color32 {
    Color32::from_rgba_unmultiplied((c.r() as f32 * f) as u8, (c.g() as f32 * f) as u8, (c.b() as f32 * f) as u8, (alpha * 255.0) as u8)
}

/// An isometric cube centred at `c` (`size` = its width), each face a 4x4 grid of texture pixels.
pub fn cube(p: &Painter, c: Pos2, size: f32, b: Block, alpha: f32, salt: u32) {
    let w = size / 2.0;
    let h = size / 4.0;
    let e = size / 2.0;
    let top = c + vec2(0.0, -h - e / 2.0);
    let left = top + vec2(-w, h);
    let right = top + vec2(w, h);
    let front = top + vec2(0.0, 2.0 * h);
    let quad = |a: Pos2, u: egui::Vec2, v: egui::Vec2, i: usize, j: usize| -> Vec<Pos2> {
        let s = 0.25;
        let o = a + u * (i as f32 * s) + v * (j as f32 * s);
        vec![o, o + u * s, o + u * s + v * s, o + v * s]
    };
    let mut shapes = Vec::with_capacity(48);
    for j in 0..4 {
        for i in 0..4 {
            shapes.push(Shape::convex_polygon(quad(left, top - left, front - left, i, j), shade(texture(b, true, i, j, salt), 1.0, alpha), Stroke::NONE));
            shapes.push(Shape::convex_polygon(quad(left, front - left, vec2(0.0, e), i, j), shade(texture(b, false, i, j, salt + 1), 0.82, alpha), Stroke::NONE));
            shapes.push(Shape::convex_polygon(quad(front, right - front, vec2(0.0, e), i, j), shade(texture(b, false, i, j, salt + 2), 0.62, alpha), Stroke::NONE));
        }
    }
    p.extend(shapes);
}
