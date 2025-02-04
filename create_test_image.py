from PIL import Image, ImageDraw, ImageFont
import os

def create_test_image():
    # Create a new image with a white background
    width = 400
    height = 300
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Draw some shapes
    draw.rectangle((50, 50, 350, 250), outline='blue', width=2)
    draw.ellipse((100, 100, 300, 200), fill='red')
    
    # Add some text
    draw.text((150, 260), "Test Pattern", fill='black')
    
    # Save the image
    image.save('test_pattern.png')

if __name__ == "__main__":
    create_test_image()
