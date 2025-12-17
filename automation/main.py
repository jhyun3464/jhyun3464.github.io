import os
import json
import time
import schedule
import requests
import random
import yaml
import trafilatura
from datetime import datetime
import google.generativeai as genai
from git import Repo
import db_manager
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURATION LOADER ---
def load_config():
    # Priority: Environment Variables > config.json > Defaults
    config = {
        "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", ""),
        "GITHUB_REPO_PATH": ".",
        "HN_API_URL": "https://hacker-news.firebaseio.com/v0/topstories.json",
        "HN_ITEM_URL": "https://hacker-news.firebaseio.com/v0/item/{}.json",
        "SCHEDULE_INTERVAL_MINUTES": 240
    }

    if os.path.exists("config.json"):
        with open("config.json", "r", encoding="utf-8") as f:
            file_config = json.load(f)
            config.update(file_config)

    # STRICTLY enforce Env vars over Config file if Env vars exist (even if Config has value)
    if os.environ.get("GEMINI_API_KEY"):
        config["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY")

    return config

CONFIG = load_config()

# Ensure local image output dir exists
os.makedirs("assets/images/posts", exist_ok=True)
os.makedirs("assets/images", exist_ok=True)

# Initialize DB
db_manager.init_db()

# Configure Gemini
gemini_key = CONFIG.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
if gemini_key:
    genai.configure(api_key=gemini_key)

# --- HELPERS ---

def get_gemini_summary(text, prompt_type="tech", language="en"):
    """
    Generates a deep, professional technical summary using Gemini.
    """
    if not gemini_key:
        return "Gemini API Key missing. Placeholder summary."

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')

        lang_instruction = "ENGLISH" if language == "en" else "KOREAN"

        # Refined prompt for professional technical summary
        prompt = f"""
        You are a Senior Technology Editor for a high-profile tech blog.
        Analyze the following technical content deeply:
        {text[:10000]}

        Provide a professional, technical summary in {lang_instruction} (Markdown format).

        Structure Requirements:
        1. **Title**: A professional, engaging title that captures the technical essence (No clickbait).
        2. **Executive Summary**: A high-level overview of the article's core message (2-3 sentences).
        3. **Key Technical Details**: Bullet points covering the specific technologies, algorithms, methodologies, or findings discussed. Be specific.
        4. **Industry Impact / Analysis**: A deeper insight into why this matters for the tech industry or software engineering field.

        Tone: Professional, Insightful, Technical.
        Do not use markdown code blocks (like ```markdown) in the output, just raw markdown text.
        """

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "Summary generation failed."

def get_image_prompt_from_gemini(text):
    """
    Asks Gemini to describe an image based on the article content, suitable for a Webtoon style.
    """
    if not gemini_key:
        return "Technology concept, abstract, futuristic"

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        Based on the following article content, describe a scene for a header image in 1-2 sentences.
        The style should be suitable for a high-quality Webtoon (Korean comic) illustration.
        Focus on visual elements, characters, or futuristic landscapes that represent the topic.

        Content:
        {text[:2000]}

        Output ONLY the visual description in English. Do not add 'Image of...' or 'Draw a...'.
        """
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini Image Prompt Error: {e}")
        return "Futuristic technology concept, webtoon style"

def download_image(prompt, filename_prefix):
    """
    Generates an image using Pollinations.ai with the given prompt and downloads it.
    Returns the local file path.
    """
    full_prompt = f"{prompt}, vibrant K-Webtoon style, bold outlines, dynamic angles, bright colors, anime inspired, high quality, 2D art, masterpiece, 8k resolution, no text"

    encoded_prompt = requests.utils.quote(full_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"

    timestamp = int(datetime.now().timestamp())
    filename = f"assets/images/posts/{filename_prefix}_{timestamp}.jpg"

    try:
        print(f"Downloading image from: {url}")
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"Image saved to {filename}")
            return f"/{filename}" # Return absolute path for Jekyll
        else:
            print(f"Image download failed. Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"Image download error: {e}")
        return None

def save_markdown_post(title, content, image_path=None, category="tech", date=None):
    if date is None:
        date = datetime.now()

    date_str = date.strftime("%Y-%m-%d")
    filename = f"_posts/{date_str}-{category}-{int(date.timestamp())}.md"

    clean_title = title.replace('"', "'").replace(":", " -")

    # Minimal Mistakes Header Image Config
    header_config = ""
    if image_path:
        header_config = f"""header:
  overlay_image: {image_path}
  teaser: {image_path}"""

    md_content = f"""---
layout: post
title: "{clean_title}"
date: {date_str}
categories: [{category}]
tags: [{category}, update]
{header_config}
---

{content}
"""
    os.makedirs("_posts", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Saved GH Page post: {filename}")
    return filename

def git_push():
    try:
        repo = Repo(CONFIG["GITHUB_REPO_PATH"])
        repo.git.add(A=True)
        repo.index.commit(f"Auto-update: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        origin = repo.remote(name='origin')
        origin.push()
        print("Git Push Successful.")
    except Exception as e:
        print(f"Git Error: {e}")

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

        # 1. English Content Summary (Professional)
        summary_en = get_gemini_summary(content_for_ai, prompt_type="tech", language="en")

        # 2. Image Generation Strategy
        # Ask Gemini for a prompt based on content
        image_prompt_text = get_image_prompt_from_gemini(content_for_ai)
        print(f"Generated Image Prompt: {image_prompt_text}")

        # Download the image
        safe_title = "".join(x for x in story['title'] if x.isalnum())[:20]
        local_image_path = download_image(image_prompt_text, f"tech_{safe_title}")

        # Clean summary to remove potential markdown code blocks
        summary_en = summary_en.replace("```markdown", "").replace("```", "").strip()

        # Pass local_image_path to save_markdown_post for Front Matter integration
        final_content_en = f"{summary_en}\n\n[Original Source]({story.get('url', '#')})"
        save_markdown_post(f"Tech Trend: {story['title']}", final_content_en, image_path=local_image_path, category="tech")

        db_manager.log_tech_post(story_id, story['title'])

    except Exception as e:
        print(f"TechBot Error: {e}")


def job():
    print(f"--- Job Started: {datetime.now()} ---")
    run_tech_bot()
    git_push()
    print("--- Job Finished ---")

if __name__ == "__main__":
    # Server/GitHub Actions mode: Run once and exit
    job()
