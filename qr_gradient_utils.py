from PIL import Image, ImageColor


def apply_linear_gradient(img, color1, color2):
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    w, h = img.size
    r1, g1, b1 = ImageColor.getrgb(color1)
    r2, g2, b2 = ImageColor.getrgb(color2)
    grad = Image.new('RGBA', img.size)
    for y in range(h):
        ratio = y / max(h - 1, 1)
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        row = Image.new('RGBA', (w, 1), (r, g, b, 255))
        grad.paste(row, (0, y))
    mask = img.split()[3]
    return Image.composite(grad, img, mask)
