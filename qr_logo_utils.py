from PIL import Image, ImageDraw

def add_logo_with_border(qr_img, logo_img, logo_size_pct=20, border=False, border_color='#ffffff', border_thickness=4):
    qr_width, qr_height = qr_img.size
    logo_size = int(min(qr_width, qr_height) * logo_size_pct / 100)
    logo = logo_img.convert('RGBA').copy()
    logo.thumbnail((logo_size, logo_size), Image.LANCZOS)
    xpos = (qr_width - logo.width) // 2
    ypos = (qr_height - logo.height) // 2
    # Always clear QR area under logo (ellipse, not rectangle)
    if border:
        ellipse_bbox = [
            xpos - border_thickness, ypos - border_thickness,
            xpos + logo.width + border_thickness - 1, ypos + logo.height + border_thickness - 1
        ]
    else:
        ellipse_bbox = [
            xpos, ypos,
            xpos + logo.width - 1, ypos + logo.height - 1
        ]
    mask = Image.new('L', qr_img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(ellipse_bbox, fill=255)
    qr_img = qr_img.copy()
    white_bg = Image.new('RGBA', qr_img.size, (255,255,255,255))
    qr_img = Image.composite(white_bg, qr_img, mask)
    if border:
        border_img = Image.new('RGBA', (logo.width + 2*border_thickness, logo.height + 2*border_thickness), (0,0,0,0))
        border_draw = ImageDraw.Draw(border_img)
        border_draw.ellipse([0, 0, border_img.width-1, border_img.height-1], fill=border_color)
        border_img.paste(logo, (border_thickness, border_thickness), logo)
        qr_img.paste(border_img, (xpos-border_thickness, ypos-border_thickness), border_img)
    else:
        qr_img.paste(logo, (xpos, ypos), logo)
    return qr_img
