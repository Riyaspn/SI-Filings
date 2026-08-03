import os
from PIL import Image, ImageDraw, ImageFont

EXTENSION_DIR = r"c:\RIYAS\Sharp INtell\SI Filings\mca-extension"

sizes = [16, 48, 128]

for size in sizes:
    img = Image.new("RGBA", (size, size), color=(15, 23, 42, 255))
    draw = ImageDraw.Draw(img)

    margin = max(1, size // 16)
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=max(2, size // 6),
        fill=(56, 189, 248, 255),
        outline=(14, 165, 233, 255),
        width=max(1, size // 20)
    )

    icon_path = os.path.join(EXTENSION_DIR, f"icon{size}.png")
    img.save(icon_path)
    print(f"Generated icon: {icon_path}")
