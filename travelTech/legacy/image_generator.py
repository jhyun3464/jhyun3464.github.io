import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import os
import urllib.parse
import random
import time

def download_font():
    """Downloads NotoSansKR-Bold for text thumbnails if not exists."""
    font_path = "assets/fonts/NotoSansKR-Bold.otf"
    if not os.path.exists(font_path):
        os.makedirs(os.path.dirname(font_path), exist_ok=True)
        url = "https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR-Bold.otf"
        try:
            print("Downloading font for text thumbnails...")
            r = requests.get(url)
            with open(font_path, "wb") as f:
                f.write(r.content)
        except Exception as e:
            print(f"Font download failed: {e}")
    return font_path

def generate_ai_image(keywords, save_path):
    """
    Priority 1: Pollinations.ai (Single attempt).
    """
    try:
        if not keywords:
            return False

        print(f"[Image] 1. Trying Pollinations with keywords: {keywords}")
        # Add 'minimalist, abstract' to avoid photorealistic copyright issues
        encoded = urllib.parse.quote(f"{keywords}, abstract tech, isometric 3d, minimalist, high quality, no text")
        seed = random.randint(0, 9999)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=800&height=450&seed={seed}&nologo=true"

        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"[Image] AI Gen failed: {e}")

    return False

def create_text_thumbnail(title, save_path):
    """
    Priority 2: Local Text Thumbnail (Guaranteed Success).
    """
    try:
        print(f"[Image] 2. Creating Text Thumbnail...")
        width, height = 800, 450
        # Dark Background
        img = Image.new('RGB', (width, height), color=(20, 24, 35)) # Dark Navy
        draw = ImageDraw.Draw(img)

        # Load Font
        font_path = download_font()
        try:
            font = ImageFont.truetype(font_path, 40)
        except:
            font = ImageFont.load_default()

        # Wrap Text
        import textwrap
        lines = textwrap.wrap(title, width=20) # Approx chars

        # Draw Text Centered
        text_color = (255, 255, 255)
        line_height = 50
        y_text = (height - (len(lines) * line_height)) / 2

        for line in lines:
            # Calculate text width (bbox)
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x_text = (width - text_width) / 2
            draw.text((x_text, y_text), line, font=font, fill=text_color)
            y_text += line_height

        img.save(save_path, "WEBP")
        return True

    except Exception as e:
        print(f"[Image] Text Gen failed: {e}")
        # Absolute last resort: Solid color
        img = Image.new('RGB', (800, 400), color=(50, 50, 50))
        img.save(save_path, "WEBP")
        return True

def get_best_image(article_url, keywords, title, save_path):
    """
    Main entry point. Tries AI -> Text.
    (OG Scraping removed due to copyright concerns)
    """
    # Ensure dir
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # 1. AI Image
    if generate_ai_image(keywords, save_path):
        return True

    # 2. Text Thumbnail
    if create_text_thumbnail(title, save_path):
        return True

    return False
