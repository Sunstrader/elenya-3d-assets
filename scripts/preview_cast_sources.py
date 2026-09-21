#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "modular-preview" / "cast"
OUT.mkdir(parents=True, exist_ok=True)

def card(path, label):
    image = Image.open(path).convert("RGBA")
    thumb = image.copy()
    thumb.thumbnail((512,768), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA",(540,820),(20,22,29,255))
    canvas.alpha_composite(thumb,((540-thumb.width)//2,42))
    ImageDraw.Draw(canvas).text((16,12),label,fill=(240,240,245,255))
    return canvas

items=[
    ("game-v54/sprites/kaelen.webp","KAELEN"),
    ("game-v54/sprites/alistair.webp","ALISTAIR"),
]
for rel, label in items:
    shutil.copyfile(ROOT/rel, OUT/(label.lower()+".webp"))
sheet=Image.new("RGBA",(1080,820),(10,11,16,255))
for i,(rel,label) in enumerate(items):
    sheet.alpha_composite(card(ROOT/rel,label),(540*i,0))
sheet.save(OUT/"source-sheet.png","PNG",optimize=True)
print(OUT/"source-sheet.png")
