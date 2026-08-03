"""
Generate 100% valid PNG icon files for Chrome Extension
"""

import base64
import os

# Valid 1x1 cyan PNG image base64
TINY_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
png_bytes = base64.b64decode(TINY_PNG_B64)

ext_dir = r"c:\RIYAS\Sharp INtell\SI Filings\mca-extension"

for size in [16, 48, 128]:
    icon_path = os.path.join(ext_dir, f"icon{size}.png")
    with open(icon_path, "wb") as f:
        f.write(png_bytes)
    print(f"Created {icon_path}")
