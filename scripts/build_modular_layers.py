#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "game-v54" / "sprites" / "elenya.webp"
PROD = ROOT / "game-v56" / "modular" / "elenya"
PREVIEW = ROOT / "build" / "modular-preview" / "elenya"
MANIFEST = ROOT / "game-v56" / "modular" / "manifest.json"

def polygon_mask(size, points, blur):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(blur)) if blur else mask

def rgba_with_alpha(src, alpha):
    rgb = np.asarray(src)[..., :3]
    out = np.dstack([rgb, np.clip(np.rint(alpha * 255), 0, 255).astype(np.uint8)])
    return Image.fromarray(out, "RGBA")

def make_card(image, label):
    thumb = image.copy()
    thumb.thumbnail((512, 768), Image.Resampling.LANCZOS)
    card = Image.new("RGBA", (540, 820), (20, 22, 29, 255))
    card.alpha_composite(thumb, ((540-thumb.width)//2, 42))
    ImageDraw.Draw(card).text((16, 12), label, fill=(240, 240, 245, 255))
    return card

def main():
    PROD.mkdir(parents=True, exist_ok=True)
    PREVIEW.mkdir(parents=True, exist_ok=True)

    src = Image.open(SOURCE).convert("RGBA")
    w, h = src.size
    if (w, h) != (1024, 1536):
        raise SystemExit(f"Unexpected Elenya sprite size: {w}x{h}")

    # Les zones suivent les formes réelles visibles du sprite au lieu de couper
    # horizontalement le torse. Le flou crée une couture alpha très douce.
    specs = {
        "head": {
            "points": [(420,15),(610,15),(645,185),(620,335),(550,410),(455,385),(385,315),(390,140)],
            "blur": 20, "z": 30, "className": "rig-head", "origin": "50% 78%"
        },
        "left_arm": {
            "points": [(330,340),(435,360),(490,500),(440,665),(325,640),(215,575),(185,475),(260,410)],
            "blur": 22, "z": 20, "className": "rig-arm-left", "origin": "41% 31%"
        },
        "right_arm": {
            "points": [(590,360),(700,395),(775,530),(800,690),(735,780),(665,705),(620,570)],
            "blur": 22, "z": 21, "className": "rig-arm-right", "origin": "63% 32%"
        },
    }

    raw_masks = []
    names = list(specs)
    for name in names:
        spec = specs[name]
        raw_masks.append(np.asarray(
            polygon_mask((w, h), spec["points"], spec["blur"]),
            dtype=np.float32
        ) / 255.0)

    masks = np.stack(raw_masks)
    # Empêche les zones adoucies de dépasser une couverture totale de 100 %.
    total = masks.sum(axis=0)
    masks = masks / np.maximum(1.0, total)

    src_alpha = np.asarray(src.getchannel("A"), dtype=np.float32) / 255.0
    overlay_alphas = [src_alpha * mask for mask in masks]

    # Alpha cumulé des overlays ; le base_alpha est résolu pour que
    # base + overlays reconstruisent le sprite d'origine à 1/255 près.
    overlay_union = np.zeros_like(src_alpha)
    for alpha in overlay_alphas:
        overlay_union = alpha + overlay_union * (1.0 - alpha)
    denom = 1.0 - overlay_union
    base_alpha = np.where(denom > 1e-6, (src_alpha - overlay_union) / denom, 0.0)
    base_alpha = np.clip(base_alpha, 0.0, 1.0)

    base = rgba_with_alpha(src, base_alpha)
    base.save(PROD / "base.webp", "WEBP", lossless=True, method=6)

    parts = {}
    for name, alpha in zip(names, overlay_alphas):
        part = rgba_with_alpha(src, alpha)
        part.save(PROD / f"{name}.webp", "WEBP", lossless=True, method=6)
        parts[name] = part

    rebuilt = base.copy()
    for name in ["left_arm", "right_arm", "head"]:
        rebuilt.alpha_composite(parts[name])

    src_np = np.asarray(src, dtype=np.int16)
    rebuilt_np = np.asarray(rebuilt, dtype=np.int16)
    max_error = int(np.abs(src_np - rebuilt_np).max())
    if max_error > 1:
        raise SystemExit(f"Rest reconstruction error too large: {max_error}")

    # Aperçu volontairement un peu amplifié pour révéler immédiatement les coutures.
    animated = base.copy()
    animated.alpha_composite(parts["left_arm"].rotate(
        1.2, resample=Image.Resampling.BICUBIC, center=(390,430), translate=(0,-1)
    ))
    animated.alpha_composite(parts["right_arm"].rotate(
        -1.0, resample=Image.Resampling.BICUBIC, center=(650,430), translate=(0,-1)
    ))
    animated.alpha_composite(parts["head"].rotate(
        -0.35, resample=Image.Resampling.BICUBIC, center=(512,300), translate=(0,-3)
    ))

    rebuilt.save(PREVIEW / "reconstructed.webp", "WEBP", lossless=True, method=6)
    sheet = Image.new("RGBA", (1620, 820), (10,11,16,255))
    for i, (image, label) in enumerate([
        (src, "SOURCE"),
        (rebuilt, "REBUILT SOFT"),
        (animated, "SOFT RIG TEST")
    ]):
        sheet.alpha_composite(make_card(image, label), (540*i, 0))
    sheet.save(PREVIEW / "preview.png", "PNG", optimize=True)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    elenya = manifest["characters"]["elenya"]
    layer_defs = {
        "base": {
            "src": "game-v56/modular/elenya/base.webp",
            "z": 0,
            "className": "rig-base",
            "origin": "50% 100%"
        }
    }
    for name in names:
        spec = specs[name]
        layer_defs[name] = {
            "src": f"game-v56/modular/elenya/{name}.webp",
            "z": spec["z"],
            "className": spec["className"],
            "origin": spec["origin"]
        }
    for outfit in ("travel", "combat", "injured"):
        elenya["outfits"][outfit]["layers"] = layer_defs
    elenya["dedicatedRig"] = {
        "version": 1,
        "source": "game-v54/sprites/elenya.webp",
        "restReconstructionMaxError": max_error,
        "parts": ["base", "head", "left_arm", "right_arm"]
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    report = {
        "character": "elenya",
        "source": str(SOURCE.relative_to(ROOT)),
        "size": [w, h],
        "production": [str((PROD/f"{name}.webp").relative_to(ROOT)) for name in ["base","head","left_arm","right_arm"]],
        "rest_reconstruction_max_channel_error": max_error
    }
    (PREVIEW / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
