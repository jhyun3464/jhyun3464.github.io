import requests
import trafilatura
import google.generativeai as genai
import json
import time
import image_generator
from datetime import datetime
import os

HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

def fetch_hn_item(item_id):
    try:
        resp = requests.get(HN_ITEM_URL.format(item_id))
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"Error fetching HN item {item_id}: {e}")
    return None

def fetch_comments(comment_ids, limit=10):
    if not comment_ids:
        return ""

    comments_text = []
    count = 0
    for cid in comment_ids:
        if count >= limit:
            break
        item = fetch_hn_item(cid)
        if item and 'text' in item:
            # HN comments are HTML, we can simple strip tags or just pass as is (Gemini handles HTML well)
            # But trafilatura might be overkill for short comments.
            # Let's just keep the raw text or simple clean.
            # Usually HN text has <p>.
            text = item['text']
            comments_text.append(f"- {text}")
            count += 1
    return "\n".join(comments_text)

def analyze_article(hn_id, api_key):
    """
    Analyzes an HN article.
    Returns a dict with the results or None if failure.
    """
    print(f"Analyzing HN ID: {hn_id}...")

    # 1. Fetch HN Story
    story = fetch_hn_item(hn_id)
    if not story:
        return None

    title = story.get('title', '')
    url = story.get('url', '')
    kids = story.get('kids', [])

    # 2. Fetch Comments (Top 5-10)
    comments_text = fetch_comments(kids, limit=10)

    # 3. Content Fetch (Fail-Safe)
    article_text = ""
    image_url = ""
    if url:
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                # Optimized Content Extraction
                extracted_text = trafilatura.extract(downloaded)
                if extracted_text:
                    article_text = extracted_text
        except Exception as e:
            print(f"Trafilatura error: {e}")
            article_text = ""

    # 4. Gemini Prompting
    if not api_key:
        return {"error": "API Key missing"}

    try:
        genai.configure(api_key=api_key)
        # Using gemini-2.5-flash as confirmed by available models list.
        model = genai.GenerativeModel('gemini-2.5-flash')

        # PROMPT
        prompt = f"""
        You are a Tech Trend Analyst. Analyze the following Hacker News story.

        Input Data:
        - Title: {title}
        - URL: {url}
        - Article Content: {article_text}
        - User Comments: {comments_text}

        Instructions:
        1. If 'Article Content' is empty, infer the content strictly from 'Title' and 'User Comments'.
        2. **Translate and Explain (Not just summarize):**
           - Translate the core technical content into natural, professional Korean.
           - Maintain the depth and structure of the original article.
           - Do not skip technical details or over-simplify.
           - If the text is long, provide a comprehensive technical review that covers all key points.
        3. Create a separate section titled "### 💬 개발자 반응 (Comments)" summarizing developer reactions based on 'User Comments'.
        4. Determine the Grade (S/A/B) based on importance and engagement.
        5. Generate a URL slug (English, lowercase, hyphens).
        6. Extract tags (comma separated list).
        7. **Image Keywords Extraction:**
           - Extract 3 key English keywords representing the core topic for image generation.
           - Example: "Rust, Compiler, Performance"

        Output Format (JSON only):
        {{
            "korean_title": "...",
            "summary_md": "...",
            "grade": "S/A/B",
            "slug": "...",
            "tags": "...",
            "image_keywords": "..."
        }}
        """

        response = model.generate_content(prompt)

        # Parse JSON
        text = response.text
        # Cleanup code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]

        data = json.loads(text)

        # Add metadata
        data['id'] = hn_id
        data['title'] = title
        data['url'] = url

        # Generate Image (Safe Strategy: AI -> Text Fallback)
        date_str = datetime.now().strftime("%Y-%m-%d")
        image_filename = f"{date_str}-{data['slug']}.webp"
        local_image_path = f"assets/images/{image_filename}"

        keywords = data.get('image_keywords', '')
        title_for_thumb = data.get('korean_title', data.get('title', 'Tech News'))

        print(f"Generating image for: {data['slug']}...")
        # Call get_best_image: tries AI first, then Text Thumbnail. No OG scraping.
        if image_generator.get_best_image(data['url'], keywords, title_for_thumb, local_image_path):
             data['local_image_path'] = local_image_path
             data['image_filename'] = image_filename
             data['summary_md'] = f"![Header Image](/assets/images/{image_filename})\n\n" + data['summary_md']

        return data

    except Exception as e:
        print(f"Gemini Analysis Error: {e}")
        return None

def get_top_stories(limit=5):
    """
    Fetches top stories IDs from HN.
    """
    try:
        resp = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json")
        if resp.status_code == 200:
            return resp.json()[:limit]
    except Exception:
        pass
    return []
