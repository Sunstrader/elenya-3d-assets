#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw
import json

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "game-v54" / "sprites" / "elenya.webp"
OUT = ROOT / "build" / "modular-preview" / "elenya"
LAYERS = OUT / "layers"

def mask_rect(size, box):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rectangle(box, fill=255)
    return m

def masked_layer(src, mask):
    rgba = src.copy()
    alpha = ImageChops.multiply(src.getchannel("A"), mask)
    rgba.putalpha(alpha)
    return rgba

def composite(layers):
    canvas = Image.new("RGBA", layers[0].size, (0,0,0,0))
    for layer in layers:
        canvas.alpha_composite(layer)
    return canvas

def transformed_preview(parts):
    w,h = parts["torso"].size
    canvas = Image.new("RGBA", (w,h), (0,0,0,0))
    canvas.alpha_composite(parts["lower"])

    torso = parts["torso"].resize((w, int(h*1.006)), Image.Resampling.BICUBIC).crop((0,0,w,h))
    canvas.alpha_composite(torso)

    la = parts["left_arm"].rotate(1.6, resample=Image.Resampling.BICUBIC, center=(int(w*.30), int(h*.45)))
    ra = parts["right_arm"].rotate(-1.6, resample=Image.Resampling.BICUBIC, center=(int(w*.70), int(h*.45)))
    canvas.alpha_composite(la)
    canvas.alpha_composite(ra)

    head = Image.new("RGBA", (w,h), (0,0,0,0))
    head.alpha_composite(parts["head"], (0,-3))
    canvas.alpha_composite(head)
    return canvas

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    LAYERS.mkdir(parents=True, exist_ok=True)

    src = Image.open(SOURCE).convert("RGBA")
    w,h = src.size
    if (w,h) != (1024,1536):
        raise SystemExit(f"Unexpected Elenya sprite size: {w}x{h}")

    y_head = round(h*.39)
    y_lower = round(h*.70)
    x_left = round(w*.38)
    x_right = round(w*.62)

    masks = {
        "head": mask_rect((w,h), (0,0,w-1,y_head-1)),
        "left_arm": mask_rect((w,h), (0,y_head,x_left-1,y_lower-1)),
        "right_arm": mask_rect((w,h), (x_right,y_head,w-1,y_lower-1)),
        "lower": mask_rect((w,h), (0,y_lower,w-1,h-1)),
    }
    used = Image.new("L", (w,h), 0)
    for m in masks.values():
        used = ImageChops.lighter(used, m)
    masks["torso"] = ImageChops.invert(used)

    order = ["lower","torso","left_arm","right_arm","head"]
    parts = {}
    for name in order:
        layer = masked_layer(src, masks[name])
        parts[name] = layer
        layer.save(LAYERS / f"{name}.webp", "WEBP", lossless=True, method=6)

    rebuilt = composite([parts[n] for n in order])
    diff = ImageChops.difference(src, rebuilt)
    exact = diff.getbbox() is None
    rebuilt.save(OUT / "reconstructed.webp", "WEBP", lossless=True, method=6)

    animated = transformed_preview(parts)

    thumbs = []
    for image, label in [(src,"SOURCE"),(rebuilt,"REBUILT"),(animated,"RIG TEST")]:
        thumb = image.copy()
        thumb.thumbnail((512,768), Image.Resampling.LANCZOS)
        card = Image.new("RGBA", (540,820), (20,22,29,255))
        card.alpha_composite(thumb, ((540-thumb.width)//2, 42))
        d = ImageDraw.Draw(card)
        d.text((16,12), label, fill=(240,240,245,255))
        thumbs.append(card)
    sheet = Image.new("RGBA", (540*3,820), (10,11,16,255))
    for i,card in enumerate(thumbs):
        sheet.alpha_composite(card, (540*i,0))
    sheet.save(OUT / "preview.png", "PNG", optimize=True)

    report = {
        "character":"elenya",
        "source":str(SOURCE.relative_to(ROOT)),
        "size":[w,h],
        "partition":{"head_end_y":y_head,"lower_start_y":y_lower,"left_arm_end_x":x_left,"right_arm_start_x":x_right},
        "layers":[f"layers/{n}.webp" for n in order],
        "reconstruction_exact_in_memory":exact
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not exact:
        raise SystemExit("Layer reconstruction is not pixel-exact")

if __name__ == "__main__":
    main()
