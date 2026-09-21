#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "game-v56" / "modular" / "manifest.json"
PREVIEW_ROOT = ROOT / "build" / "modular-preview"

CHARACTERS = {
    "elenya": {
        "source": "game-v54/sprites/elenya.webp",
        "specs": {
            "head": {"points":[(420,15),(610,15),(645,185),(620,335),(550,410),(455,385),(385,315),(390,140)],"blur":20,"z":30,"className":"rig-head","origin":"50% 78%"},
            "left_arm": {"points":[(330,340),(435,360),(490,500),(440,665),(325,640),(215,575),(185,475),(260,410)],"blur":22,"z":20,"className":"rig-arm-left","origin":"41% 31%"},
            "right_arm": {"points":[(590,360),(700,395),(775,530),(800,690),(735,780),(665,705),(620,570)],"blur":22,"z":21,"className":"rig-arm-right","origin":"63% 32%"},
        },
        "preview": {
            "head":{"rotate":-0.35,"center":(512,300),"translate":(0,-3)},
            "left_arm":{"rotate":1.2,"center":(390,430),"translate":(0,-1)},
            "right_arm":{"rotate":-1.0,"center":(650,430),"translate":(0,-1)},
        }
    },
    "kaelen": {
        "source": "game-v54/sprites/kaelen.webp",
        "specs": {
            "head": {"points":[(385,25),(625,25),(675,175),(650,335),(555,420),(425,390),(345,250),(360,110)],"blur":20,"z":30,"className":"rig-head","origin":"49% 76%"},
            "left_arm": {"points":[(300,300),(420,330),(455,520),(370,710),(260,760),(190,680),(205,500),(260,390)],"blur":20,"z":20,"className":"rig-arm-left","origin":"34% 28%"},
            "right_arm": {"points":[(585,310),(710,350),(770,520),(745,700),(650,760),(600,650),(570,470)],"blur":20,"z":21,"className":"rig-arm-right","origin":"65% 29%"},
        },
        "preview": {
            "head":{"rotate":-0.25,"center":(500,280),"translate":(0,-2)},
            "left_arm":{"rotate":0.5,"center":(350,390),"translate":(0,-1)},
            "right_arm":{"rotate":-0.5,"center":(650,390),"translate":(0,-1)},
        }
    },
    "alistair": {
        "source": "game-v54/sprites/alistair.webp",
        "specs": {
            "head": {"points":[(390,15),(610,15),(640,170),(610,300),(530,350),(430,325),(360,210),(365,80)],"blur":18,"z":30,"className":"rig-head","origin":"50% 75%"},
            "left_arm": {"points":[(285,315),(400,330),(420,515),(365,710),(285,825),(210,785),(230,590)],"blur":20,"z":20,"className":"rig-arm-left","origin":"34% 27%"},
            "right_arm": {"points":[(600,310),(735,345),(785,525),(745,720),(650,780),(600,660),(570,470)],"blur":20,"z":21,"className":"rig-arm-right","origin":"66% 27%"},
        },
        "preview": {
            "head":{"rotate":0.25,"center":(500,240),"translate":(0,-2)},
            "left_arm":{"rotate":0.7,"center":(350,360),"translate":(0,-1)},
            "right_arm":{"rotate":-0.7,"center":(675,360),"translate":(0,-1)},
        }
    },
}

def polygon_mask(size, points, blur):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(blur)) if blur else mask

def rgba_with_alpha(src, alpha):
    rgb = np.asarray(src)[..., :3]
    out = np.dstack([rgb, np.clip(np.rint(alpha * 255), 0, 255).astype(np.uint8)])
    return Image.fromarray(out, "RGBA")

def card(image, label):
    thumb = image.copy()
    thumb.thumbnail((512,768), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA",(540,820),(20,22,29,255))
    canvas.alpha_composite(thumb,((540-thumb.width)//2,42))
    ImageDraw.Draw(canvas).text((16,12),label,fill=(240,240,245,255))
    return canvas

def transformed(part, cfg):
    return part.rotate(
        cfg.get("rotate",0),
        resample=Image.Resampling.BICUBIC,
        center=cfg.get("center"),
        translate=cfg.get("translate",(0,0))
    )

def build_character(character_id, cfg, manifest):
    source = ROOT / cfg["source"]
    prod = ROOT / "game-v56" / "modular" / character_id
    preview = PREVIEW_ROOT / character_id
    prod.mkdir(parents=True, exist_ok=True)
    preview.mkdir(parents=True, exist_ok=True)

    src = Image.open(source).convert("RGBA")
    w,h = src.size
    if (w,h) != (1024,1536):
        raise SystemExit(f"{character_id}: unexpected sprite size {w}x{h}")

    specs = cfg["specs"]
    names = list(specs)
    masks = np.stack([
        np.asarray(polygon_mask((w,h), specs[name]["points"], specs[name]["blur"]), dtype=np.float32)/255.0
        for name in names
    ])
    masks = masks / np.maximum(1.0, masks.sum(axis=0))

    src_alpha = np.asarray(src.getchannel("A"), dtype=np.float32)/255.0
    overlay_alphas = [src_alpha * mask for mask in masks]
    overlay_union = np.zeros_like(src_alpha)
    for alpha in overlay_alphas:
        overlay_union = alpha + overlay_union * (1.0-alpha)
    denom = 1.0-overlay_union
    base_alpha = np.where(denom > 1e-6, (src_alpha-overlay_union)/denom, 0.0)
    base_alpha = np.clip(base_alpha,0.0,1.0)

    base = rgba_with_alpha(src, base_alpha)
    base.save(prod/"base.webp","WEBP",lossless=True,method=6)

    parts = {}
    for name, alpha in zip(names, overlay_alphas):
        part = rgba_with_alpha(src, alpha)
        part.save(prod/f"{name}.webp","WEBP",lossless=True,method=6)
        parts[name] = part

    rebuilt = base.copy()
    for name in names:
        rebuilt.alpha_composite(parts[name])
    max_error = int(np.abs(np.asarray(src,dtype=np.int16)-np.asarray(rebuilt,dtype=np.int16)).max())
    if max_error > 1:
        raise SystemExit(f"{character_id}: rest reconstruction error {max_error}")

    animated = base.copy()
    for name in names:
        animated.alpha_composite(transformed(parts[name], cfg["preview"].get(name,{})))

    rebuilt.save(preview/"reconstructed.webp","WEBP",lossless=True,method=6)
    sheet = Image.new("RGBA",(1620,820),(10,11,16,255))
    for i,(image,label) in enumerate([(src,"SOURCE"),(rebuilt,"REBUILT SOFT"),(animated,"SOFT RIG TEST")]):
        sheet.alpha_composite(card(image,label),(540*i,0))
    sheet.save(preview/"preview.png","PNG",optimize=True)

    layer_defs = {
        "base":{"src":f"game-v56/modular/{character_id}/base.webp","z":0,"className":"rig-base","origin":"50% 100%"}
    }
    for name in names:
        spec = specs[name]
        layer_defs[name] = {
            "src":f"game-v56/modular/{character_id}/{name}.webp",
            "z":spec["z"],
            "className":spec["className"],
            "origin":spec["origin"]
        }

    entry = manifest["characters"][character_id]
    for outfit in ("travel","combat","injured"):
        entry["outfits"][outfit]["layers"] = layer_defs
    entry["dedicatedRig"] = {
        "version":1,
        "source":cfg["source"],
        "restReconstructionMaxError":max_error,
        "parts":["base"]+names
    }

    report = {
        "character":character_id,
        "source":cfg["source"],
        "size":[w,h],
        "rest_reconstruction_max_channel_error":max_error,
        "parts":["base"]+names
    }
    (preview/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    return report

def main():
    PREVIEW_ROOT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    reports = [build_character(cid,cfg,manifest) for cid,cfg in CHARACTERS.items()]
    MANIFEST.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(reports,indent=2))

if __name__ == "__main__":
    main()
