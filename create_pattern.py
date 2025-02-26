from PIL import Image, ImageDraw
import os

# Create a dark pattern for the background
def create_background_pattern():
    # Create a dark background image
    img = Image.new('RGB', (200, 200), (245, 245, 245))
    draw = ImageDraw.Draw(img)
    
    # Draw subtle grid lines
    for x in range(0, 200, 10):
        draw.line([(x, 0), (x, 200)], fill=(235, 235, 235), width=1)
    for y in range(0, 200, 10):
        draw.line([(0, y), (200, y)], fill=(235, 235, 235), width=1)
    
    # Add some dots at intersections
    for x in range(0, 200, 10):
        for y in range(0, 200, 10):
            if (x + y) % 20 == 0:  # Create a pattern
                draw.point((x, y), fill=(220, 220, 220))
    
    # Save the image
    img.save('static/images/background-pattern.png')
    print("Created background pattern image")

# Create a dark web themed background
def create_dark_web_bg():
    # Create a dark blue/black background
    img = Image.new('RGB', (500, 800), (20, 30, 40))
    draw = ImageDraw.Draw(img)
    
    # Add some network-like lines
    for i in range(20):
        x1 = i * 25
        y1 = 0
        x2 = 500 - (i * 25)
        y2 = 800
        draw.line([(x1, y1), (x2, y2)], fill=(30, 40, 55), width=2)
    
    # Add some dots (representing network nodes)
    for i in range(30):
        x = (i * 17) % 500
        y = (i * 29) % 800
        size = (i % 4) + 2
        draw.ellipse((x-size, y-size, x+size, y+size), fill=(40, 60, 90))
    
    # Save the image
    img.save('static/images/dark-web-bg.jpg')
    print("Created dark web background image")

# Create a world map outline
def create_world_map():
    # Create a white background
    img = Image.new('RGB', (500, 300), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Very simplified world map outline
    # (This is a super simplified representation - for a real app you'd use a proper image)
    draw.rectangle((100, 80, 400, 220), outline=(200, 200, 200), width=2)
    draw.ellipse((150, 100, 250, 200), outline=(200, 200, 200), width=2)
    draw.ellipse((300, 100, 380, 180), outline=(200, 200, 200), width=2)
    
    # Save the image
    img.save('static/images/world-map.png')
    print("Created world map image")

# Create a security badge icon
def create_security_badge():
    # Create a transparent background
    img = Image.new('RGBA', (200, 200), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a shield
    shield_points = [
        (100, 20),  # Top
        (180, 50),  # Right top
        (160, 170), # Right bottom
        (100, 190), # Bottom
        (40, 170),  # Left bottom
        (20, 50),   # Left top
    ]
    draw.polygon(shield_points, fill=(52, 152, 219, 50), outline=(52, 152, 219, 100), width=3)
    
    # Draw a checkmark
    check_points = [
        (70, 100),
        (90, 130),
        (130, 70)
    ]
    draw.line(check_points, fill=(52, 152, 219, 100), width=5)
    
    # Save the image
    img.save('static/images/security-badge.png')
    print("Created security badge image")

# Create a cyber pattern
def create_cyber_pattern():
    # Create a transparent background
    img = Image.new('RGBA', (300, 300), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw circuit-like lines
    for i in range(30):
        start_x = i * 10
        start_y = 0
        
        # Create zigzag pattern
        points = [(start_x, start_y)]
        for j in range(1, 10):
            if j % 2 == 0:
                points.append((start_x + 15, j * 30))
            else:
                points.append((start_x - 15, j * 30))
        
        draw.line(points, fill=(52, 152, 219, 30), width=2)
    
    # Add some circuit nodes
    for i in range(20):
        x = (i * 17) % 300
        y = (i * 19) % 300
        size = (i % 3) + 2
        draw.ellipse((x-size, y-size, x+size, y+size), fill=(52, 152, 219, 40))
        
        # Add connecting lines to some nodes
        if i % 3 == 0:
            draw.line([(x, y), (x + 30, y + 20)], fill=(52, 152, 219, 30), width=1)
    
    # Save the image
    img.save('static/images/cyber-pattern.png')
    print("Created cyber pattern image")

if __name__ == "__main__":
    # Ensure directory exists
    os.makedirs('static/images', exist_ok=True)
    
    create_background_pattern()
    create_dark_web_bg()
    create_world_map()
    create_security_badge()
    create_cyber_pattern()
    
    print("All images created successfully!")
