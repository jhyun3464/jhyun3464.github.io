import os
import json
import time
import requests
import random
import trafilatura
from datetime import datetime
import google.generativeai as genai
from git import Repo
import db_manager
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# --- CONFIGURATION LOADER ---
def load_config():
    # Priority: Environment Variables
    config = {
        "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", ""),
        "GITHUB_REPO_PATH": ".",
        "HN_API_URL": "https://hacker-news.firebaseio.com/v0/topstories.json",
        "HN_ITEM_URL": "https://hacker-news.firebaseio.com/v0/item/{}.json",
    }
    return config

CONFIG = load_config()

# Ensure directories exist
os.makedirs("assets/images/posts", exist_ok=True)
os.makedirs("_posts", exist_ok=True)

# Initialize DB
db_manager.init_db()

# Configure Gemini
gemini_key = CONFIG.get("GEMINI_API_KEY")
if gemini_key:
    genai.configure(api_key=gemini_key)

# --- HELPERS ---

def get_gemini_summary(text, prompt_type="tech", language="en"):
    """
    Generates a summary using Gemini in specific language.
    """
    if not gemini_key:
        return "Gemini API Key missing. Placeholder summary."

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')

        lang_instruction = "ENGLISH" if language == "en" else "KOREAN"

        prompt = f"""
        Analyze the following technical content:
        {text[:8000]}

        Provide a summary in {lang_instruction} (Markdown format).
        Structure:
        1. **Title**: Catchy {lang_instruction} title (Keep it relevant to the original).
        2. **Summary**: 3 concise bullet points.
        3. **Key Takeaway**: 1 sentence insight.
        """

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "Summary generation failed."

def download_and_process_image(url, filename_prefix):
    """
    Downloads image from URL, resizes it, and saves it locally.
    Returns the relative path for the blog post.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        img = Image.open(BytesIO(response.content))

        # Convert to RGB if necessary (e.g. for RGBA/P pngs to JPG)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Resize: maintain aspect ratio, max width 500
        max_width = 500
        if img.width > max_width:
            ratio = max_width / float(img.width)
            new_height = int((float(img.height) * float(ratio)))
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

        timestamp = int(datetime.now().timestamp())
        filename = f"{filename_prefix}_{timestamp}.jpg"
        filepath = f"assets/images/posts/{filename}"

        # Save with optimization
        img.save(filepath, "JPEG", quality=80, optimize=True)
        print(f"Image saved locally: {filepath}")

        return f"/{filepath}"
    except Exception as e:
        print(f"Image processing failed: {e}")
        return None

def create_text_thumbnail(text, filename_prefix):
    """
    Creates a simple text thumbnail using Pillow if AI image generation fails.
    """
    try:
        width, height = 500, 250 # Smaller size
        color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
        img = Image.new('RGB', (width, height), color=color)
        d = ImageDraw.Draw(img)

        # Simple text wrapping
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            if len(" ".join(current_line + [word])) * 10 < width - 40: # Rough estimation
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
        lines.append(" ".join(current_line))

        y_text = 50
        for line in lines[:3]: # Limit to 3 lines
            d.text((30, y_text), line, fill=(255, 255, 255))
            y_text += 30

        timestamp = int(datetime.now().timestamp())
        filename = f"{filename_prefix}_{timestamp}.jpg"
        filepath = f"assets/images/posts/{filename}"
        img.save(filepath, "JPEG", quality=80)
        return f"/{filepath}"
    except Exception as e:
        print(f"Thumbnail generation failed: {e}")
        return None

def generate_image_url(prompt, style="webtoon"):
    """
    Generates an image URL using Pollinations.ai.
    """
    if style == "webtoon":
        full_prompt = f"{prompt}, vibrant K-Webtoon style, bold outlines, dynamic angles, bright colors, anime inspired, high quality, 2D art, no text"
    else:
        full_prompt = prompt

    encoded_prompt = requests.utils.quote(full_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
    return url

def save_markdown_post(title, content, category="tech", date=None):
    if date is None:
        date = datetime.now()

    date_str = date.strftime("%Y-%m-%d")
    filename = f"_posts/{date_str}-{category}-{int(date.timestamp())}.md"

    clean_title = title.replace('"', "'").replace(":", " -")

    md_content = f"""---
layout: post
title: "{clean_title}"
date: {date_str}
categories: [{category}]
tags: [{category}, update]
---

{content}
"""
    # ensure dir exists (redundant but safe)
    os.makedirs("_posts", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Saved GH Page post: {filename}")
    return filename

# --- BOTS ---

def run_tech_bot():
    print("Running TechBot...")
    try:
        top_ids = requests.get(CONFIG["HN_API_URL"]).json()[:20]

        story = None
        story_id = None

        for sid in top_ids:
            if not db_manager.is_tech_posted(sid):
                fetched = requests.get(CONFIG["HN_ITEM_URL"].format(sid)).json()
                if fetched and "title" in fetched:
                    story = fetched
                    story_id = sid
                    break

        if not story:
            print("No new Tech stories found.")
            return

        print(f"Analyzing HN: {story['title']}")

        # Scrape content
        url = story.get("url")
        article_text = ""
        if url:
            try:
                downloaded = trafilatura.fetch_url(url)
                article_text = trafilatura.extract(downloaded) or ""
            except Exception as e:
                print(f"Scraping failed: {e}")

        if not article_text:
            article_text = story.get("text", "No content available.")

        content_for_ai = f"Title: {story['title']}\n\nContent:\n{article_text}"

        # 1. English Content
        summary_en = get_gemini_summary(content_for_ai, prompt_type="tech", language="en")

        # Image Generation & Download
        image_url = generate_image_url(f"Technology concept: {story['title']}", style="webtoon")
        local_image_path = download_and_process_image(image_url, "tech_thumb")

        if not local_image_path:
             print("Webtoon image generation failed or unreachable. Falling back to text thumbnail.")
             local_image_path = create_text_thumbnail(story['title'], "tech_thumb")

        final_content_en = f"![Tech Image]({local_image_path})\n\n{summary_en}\n\n[Original Source]({story.get('url', '#')})"
        save_markdown_post(f"Tech Trend: {story['title']}", final_content_en, category="tech")

        db_manager.log_tech_post(story_id, story['title'])

    except Exception as e:
        print(f"TechBot Error: {e}")

def job():
    print(f"--- Job Started: {datetime.now()} ---")
    run_tech_bot()
    # git_push() # Disabled: Let GitHub Actions handle committing and pushing
    print("--- Job Finished ---")

if __name__ == "__main__":
    job()
