from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    # Create a 256x256 image with a transparent background
    img = Image.new('RGBA', (256, 256), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a hand icon
    # Draw a circle for the palm
    draw.ellipse((78, 78, 178, 178), fill=(52, 152, 219, 255))
    
    # Draw fingers (simplified)
    # Thumb
    draw.rectangle((60, 110, 90, 160), fill=(41, 128, 185, 255))
    # Index finger
    draw.rectangle((110, 40, 140, 110), fill=(41, 128, 185, 255))
    # Middle finger
    draw.rectangle((150, 30, 180, 110), fill=(41, 128, 185, 255))
    # Ring finger
    draw.rectangle((190, 40, 220, 110), fill=(41, 128, 185, 255))
    # Pinky
    draw.rectangle((230, 60, 250, 110), fill=(41, 128, 185, 255))
    
    # Add text "NoMouse"
    # try:
    #     font = ImageFont.truetype("arial.ttf", 32)
    # except IOError:
    #     font = ImageFont.load_default()
    
    # draw.text((70, 190), "NoMouse", fill=(52, 152, 219, 255), font=font)
    
    # Save the image
    os.makedirs('assets', exist_ok=True)
    img.save('assets/icon.png')
    
    # Create ICO version for Windows
    img.save('assets/icon.ico')
    
    print("Icon created successfully!")

if __name__ == "__main__":
    create_icon()
