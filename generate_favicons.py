import os
from PIL import Image, ImageDraw

def generate_favicons():
    # Generate on a high-resolution canvas (512x512) for clean anti-aliasing on resize
    size = 512
    img = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # 1. Deep forest green background circle (cx=256, cy=256, r=240)
    draw.ellipse([16, 16, 496, 496], fill=(13, 59, 17, 255))
    
    # 2. Outer bright green ring (cx=256, cy=256, r=220) with transparency
    draw.ellipse([36, 36, 476, 476], outline=(46, 204, 64, 76), width=4)
    
    # Helper to calculate cubic bezier points
    def bezier_curve(p0, p1, p2, p3, num_pts=30):
        pts = []
        for i in range(num_pts + 1):
            t = i / num_pts
            x = (1-t)**3 * p0[0] + 3*(1-t)**2 * t * p1[0] + 3*(1-t) * t**2 * p2[0] + t**3 * p3[0]
            y = (1-t)**3 * p0[1] + 3*(1-t)**2 * t * p1[1] + 3*(1-t) * t**2 * p2[1] + t**3 * p3[1]
            pts.append((x, y))
        return pts

    # 3. Draw Tracing Paths / Network Nodes
    # Left tracer curve
    left_trace = bezier_curve((180, 200), (120, 280), (200, 320), (256, 360))
    draw.line(left_trace, fill=(46, 204, 64, 50), width=3)
    
    # Right tracer curve
    right_trace = bezier_curve((332, 200), (392, 280), (312, 320), (256, 360))
    draw.line(right_trace, fill=(46, 204, 64, 50), width=3)
    
    # Node circles
    draw.ellipse([175, 195, 185, 205], fill=(46, 204, 64, 200))
    draw.ellipse([327, 195, 337, 205], fill=(46, 204, 64, 200))

    # 4. Draw Sprout Stem
    # Thick main stem path
    draw.line([(256, 190), (256, 400)], fill=(46, 204, 64, 255), width=20)
    draw.line([(256, 190), (256, 400)], fill=(27, 122, 37, 255), width=10)
    # Rounded stem caps
    draw.ellipse([246, 180, 266, 200], fill=(46, 204, 64, 255))
    draw.ellipse([246, 390, 266, 410], fill=(46, 204, 64, 255))
    
    # 5. Draw Left Leaf (light green and shaded half)
    left_leaf_pts = (
        bezier_curve((256, 260), (210, 240), (130, 200), (130, 140)) +
        bezier_curve((130, 140), (130, 90), (200, 120), (256, 180)) +
        [(256, 260)]
    )
    draw.polygon(left_leaf_pts, fill=(46, 204, 64, 255))
    
    left_inner_pts = (
        bezier_curve((256, 260), (220, 245), (160, 215), (150, 170)) +
        bezier_curve((150, 170), (190, 150), (230, 170), (256, 180)) +
        [(256, 260)]
    )
    draw.polygon(left_inner_pts, fill=(27, 122, 37, 200))

    # 6. Draw Right Leaf (bright green and shaded half)
    right_leaf_pts = (
        bezier_curve((256, 230), (290, 210), (370, 170), (370, 120)) +
        bezier_curve((370, 120), (370, 70), (310, 100), (256, 150)) +
        [(256, 230)]
    )
    draw.polygon(right_leaf_pts, fill=(61, 219, 82, 255))

    right_inner_pts = (
        bezier_curve((256, 230), (280, 215), (330, 185), (340, 145)) +
        bezier_curve((340, 145), (310, 130), (280, 145), (256, 150)) +
        [(256, 230)]
    )
    draw.polygon(right_inner_pts, fill=(34, 149, 46, 200))

    # Ensure output static directory exists
    os.makedirs("app/static", exist_ok=True)

    # Save apple-touch-icon.png (180x180)
    apple_icon = img.resize((180, 180), Image.Resampling.LANCZOS)
    apple_icon.save("app/static/apple-touch-icon.png", "PNG")
    print("Successfully saved app/static/apple-touch-icon.png")

    # Save favicon.png (192x192)
    favicon_png = img.resize((192, 192), Image.Resampling.LANCZOS)
    favicon_png.save("app/static/favicon.png", "PNG")
    print("Successfully saved app/static/favicon.png")

    # Save favicon.ico (multi-resolution 16x16, 32x32, 48x48)
    ico_img = img.resize((48, 48), Image.Resampling.LANCZOS)
    ico_img.save("app/static/favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    print("Successfully saved app/static/favicon.ico")

if __name__ == "__main__":
    generate_favicons()
