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
        "TOUR_API_KEY": os.environ.get("TOUR_API_KEY", ""),
        "GITHUB_REPO_PATH": ".",
        "NAVER_OUTPUT_DIR": "./naver_posts",
        "HN_API_URL": "https://hacker-news.firebaseio.com/v0/topstories.json",
        "HN_ITEM_URL": "https://hacker-news.firebaseio.com/v0/item/{}.json",
        "TOUR_API_URL": "https://apis.data.go.kr/B551011/EngService2/areaBasedList2",
        "TOUR_DETAIL_URL": "https://apis.data.go.kr/B551011/EngService2/detailCommon2",
        "SCHEDULE_INTERVAL_MINUTES": 240
    }

    if os.path.exists("config.json"):
        with open("config.json", "r", encoding="utf-8") as f:
            file_config = json.load(f)
            config.update(file_config)

    # STRICTLY enforce Env vars over Config file if Env vars exist (even if Config has value)
    if os.environ.get("GEMINI_API_KEY"):
        config["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY")
    if os.environ.get("TOUR_API_KEY"):
        config["TOUR_API_KEY"] = os.environ.get("TOUR_API_KEY")

    return config

CONFIG = load_config()

# Ensure Naver output dir exists
os.makedirs(CONFIG["NAVER_OUTPUT_DIR"], exist_ok=True)
os.makedirs("assets/images", exist_ok=True) # For local thumbnails

# Initialize DB
db_manager.init_db()

# Configure Gemini
gemini_key = CONFIG.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
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

        if prompt_type == "tech":
            prompt = f"""
            Analyze the following technical content:
            {text[:8000]}

            Provide a summary in {lang_instruction} (Markdown format).
            Structure:
            1. **Title**: Catchy {lang_instruction} title (Keep it relevant to the original).
            2. **Summary**: 3 concise bullet points.
            3. **Key Takeaway**: 1 sentence insight.
            """
        else: # travel
            prompt = f"""
            Analyze the following travel destination info:
            {text[:4000]}

            Provide a blog post in {lang_instruction} (Markdown format).
            Structure:
            1. **Title**: Attractive travel title.
            2. **Intro**: Why visit here?
            3. **Highlights**: What to see?
            4. **Tips**: Practical info.
            """

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "Summary generation failed."

def create_text_thumbnail(text, filename_prefix):
    """
    Creates a simple text thumbnail using Pillow if AI image generation fails.
    """
    try:
        width, height = 800, 400
        color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
        img = Image.new('RGB', (width, height), color=color)
        d = ImageDraw.Draw(img)

        # Simple text wrapping
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            if len(" ".join(current_line + [word])) * 15 < width - 40: # Rough estimation
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
        lines.append(" ".join(current_line))

        y_text = 100
        for line in lines[:3]: # Limit to 3 lines
            d.text((50, y_text), line, fill=(255, 255, 255))
            y_text += 50

        timestamp = int(datetime.now().timestamp())
        filename = f"assets/images/{filename_prefix}_{timestamp}.png"
        img.save(filename)
        return f"/{filename}"
    except Exception as e:
        print(f"Thumbnail generation failed: {e}")
        return None

def generate_image_url(prompt, style="realistic", fallback_text="Tech"):
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
    os.makedirs("_posts", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Saved GH Page post: {filename}")
    return filename

def save_naver_post(title, content, image_url=None):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{CONFIG['NAVER_OUTPUT_DIR']}/naver_{timestamp}.md"

    image_tag = f"![Main Image]({image_url})\n\n" if image_url else ""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n{image_tag}{content}")
    print(f"Saved Naver MD draft: {filename}")

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

        # 1. English Content
        summary_en = get_gemini_summary(content_for_ai, prompt_type="tech", language="en")

        # Image Strategy: Webtoon -> Fallback Text
        image_url = generate_image_url(f"Technology concept: {story['title']}", style="webtoon")

        # Verify if Pollinations URL is valid/reachable (simple check), otherwise use text thumbnail
        # Since Pollinations usually returns a valid URL string even if it fails later,
        # we will assume it works unless we want to do a strict requests.head check.
        # However, to honor the "fallback" request, let's try to verify.
        try:
            check_response = requests.head(image_url, timeout=5)
            if check_response.status_code != 200:
                raise Exception("Image URL unreachable")
        except Exception:
            print("Webtoon image generation failed or unreachable. Falling back to text thumbnail.")
            local_thumb = create_text_thumbnail(story['title'], "tech_thumb")
            if local_thumb:
                image_url = local_thumb

        final_content_en = f"![Tech Image]({image_url})\n\n{summary_en}\n\n[Original Source]({story.get('url', '#')})"
        save_markdown_post(f"Tech Trend: {story['title']}", final_content_en, category="tech")

        # 2. Korean Content (Naver Blog - Disabled for Server Automation)
        # summary_kr = get_gemini_summary(content_for_ai, prompt_type="tech", language="ko")
        # save_naver_post(f"IT 트렌드: {story['title']}", summary_kr, image_url)

        db_manager.log_tech_post(story_id, story['title'])

    except Exception as e:
        print(f"TechBot Error: {e}")

def run_travel_bot():
    print("Running TravelBot...")
    try:
        target_content_type = random.choice([76, 82, 85])

        params = {
            "serviceKey": CONFIG["TOUR_API_KEY"],
            "numOfRows": 20,
            "pageNo": random.randint(1, 5),
            "MobileOS": "ETC",
            "MobileApp": "AutoBlog",
            "_type": "json",
            "arrange": "P",
            "contentTypeId": target_content_type
        }

        response = requests.get(CONFIG["TOUR_API_URL"], params=params)
        data = response.json()

        items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
        if not items:
            print(f"No travel items found for type {target_content_type}.")
            return

        random.shuffle(items)

        item = None
        for cand in items:
            if not db_manager.is_travel_posted(cand.get("contentid")):
                # STRICT RULE: Official Images Only
                if cand.get("firstimage") or cand.get("firstimage2"):
                    item = cand
                    break

        if not item:
            print("No new Travel items with IMAGES found in this batch.")
            return

        title = item.get("title", "Unknown Spot")
        addr = item.get("addr1", "")
        content_id = item.get("contentid")
        # We already confirmed it has an image in the loop above
        image_url = item.get("firstimage") or item.get("firstimage2")

        print(f"Selected Travel Spot: {title} (Type {target_content_type})")

        detail_params = {
            "serviceKey": CONFIG["TOUR_API_KEY"],
            "numOfRows": 1,
            "pageNo": 1,
            "MobileOS": "ETC",
            "MobileApp": "AutoBlog",
            "_type": "json",
            "contentId": content_id,
            "defaultYN": "Y",
            "firstImageYN": "Y",
            "addrinfoYN": "Y",
            "mapinfoYN": "Y",
            "overviewYN": "Y"
        }

        detail_resp = requests.get(CONFIG["TOUR_DETAIL_URL"], params=detail_params)
        detail_data = detail_resp.json()
        detail_item = detail_data.get('response', {}).get('body', {}).get('items', {}).get('item', [{}])[0]

        overview = detail_item.get("overview", "No details available.")

        # Double check detail image, though list image was present
        final_image_url = detail_item.get("firstimage") or detail_item.get("firstimage2") or image_url

        # 1. English Content
        blog_post_en = get_gemini_summary(f"Spot: {title}\nAddress: {addr}\nOverview: {overview}", prompt_type="travel", language="en")
        final_content_en = f"![{title}]({final_image_url})\n\n{blog_post_en}\n\n**Address**: {addr}"
        save_markdown_post(f"Travel: {title}", final_content_en, category="travel")

        # 2. Korean Content (Naver Blog - Disabled for Server Automation)
        # blog_post_kr = get_gemini_summary(f"Spot: {title}\nAddress: {addr}\nOverview: {overview}", prompt_type="travel", language="ko")
        # final_content_kr = f"{blog_post_kr}\n\n**주소**: {addr}"
        # save_naver_post(f"한국 여행 추천: {title}", final_content_kr, final_image_url)

        db_manager.log_travel_post(content_id, title)

    except Exception as e:
        print(f"TravelBot Error: {e}")


def job():
    print(f"--- Job Started: {datetime.now()} ---")
    run_tech_bot()
    run_travel_bot()
    git_push()
    print("--- Job Finished ---")

if __name__ == "__main__":
    # Server/GitHub Actions mode: Run once and exit
    job()
