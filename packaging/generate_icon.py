"""Generate ikon aplikasi PDF Combine (placeholder yang mudah diganti).

Menghasilkan:
  assets/icon.png      -> 512x512
  assets/icon-256.png  -> 256x256 (untuk .deb / hicolor)
  assets/icon.ico      -> multi-size (untuk EXE Windows)
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

SIZE = 512
RADIUS = 96
TOP = (21, 101, 192)      # #1565C0
BOTTOM = (13, 71, 161)    # #0D47A1
ACCENT = (255, 193, 7)    # amber


def load_font(size):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def gradient(size):
    img = Image.new("RGBA", (size, size))
    top = Image.new("RGBA", (1, size), TOP)
    bottom = Image.new("RGBA", (1, size), BOTTOM)
    gradient_col = Image.new("RGBA", (1, size))
    for y in range(size):
        ratio = y / max(1, size - 1)
        gradient_col.putpixel((0, y), tuple(
            round(TOP[i] + (BOTTOM[i] - TOP[i]) * ratio) for i in range(3)
        ) + (255,))
    return gradient_col.resize((size, size))


def main():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, SIZE - 1, SIZE - 1), radius=RADIUS, fill=255
    )
    img.paste(gradient(SIZE), (0, 0), mask)

    draw = ImageDraw.Draw(img)

    # Lembaran kertas bertumpuk
    draw.rounded_rectangle((128, 118, 356, 368), radius=22,
                           fill=(255, 255, 255, 235))
    draw.rounded_rectangle((156, 146, 384, 396), radius=22,
                           fill=(255, 255, 255, 255))

    # Aksen lipatan / garis dokumen
    for y in (206, 244, 282):
        draw.rounded_rectangle((196, y, 344, y + 12), radius=6,
                               fill=(144, 202, 249, 255))
    draw.rounded_rectangle((196, 320, 286, 332), radius=6, fill=ACCENT + (255,))

    # Teks PDF
    font = load_font(118)
    text = "PDF"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (SIZE - tw) / 2 - bbox[0]
    ty = 404 - bbox[1]
    draw.text((tx + 3, ty + 3), text, font=font, fill=(0, 0, 0, 70))
    draw.text((tx, ty), text, font=font, fill=(255, 255, 255, 255))

    img.save(ASSETS / "icon.png")
    img.resize((256, 256), Image.LANCZOS).save(ASSETS / "icon-256.png")
    img.save(ASSETS / "icon.ico", sizes=[
        (16, 16), (24, 24), (32, 32), (48, 48),
        (64, 64), (128, 128), (256, 256),
    ])

    print("Ikon dibuat di", ASSETS)


if __name__ == "__main__":
    main()
