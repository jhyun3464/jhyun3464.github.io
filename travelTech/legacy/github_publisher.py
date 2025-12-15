import os
from github import Github
from datetime import datetime
import yaml
import shutil

def upload_file(repo, file_path, content, message, branch="main", force=False):
    """
    Helper to create or update a file in the repo.
    """
    try:
        contents = repo.get_contents(file_path, ref=branch)
        # Check if content changed to avoid unnecessary commits
        if force or contents.decoded_content.decode('utf-8') != content:
            repo.update_file(contents.path, message, content, contents.sha, branch=branch)
            print(f"Updated {file_path}")
        else:
            print(f"No changes for {file_path}")
    except Exception:
        repo.create_file(file_path, message, content, branch=branch)
        print(f"Created {file_path}")

def ensure_theme_config(repo, branch="main"):
    """
    Ensures that the remote theme is set to 'mmistakes/minimal-mistakes'
    and applies customizations.
    """
    TARGET_THEME = "mmistakes/minimal-mistakes"

    try:
        try:
            contents = repo.get_contents("_config.yml", ref=branch)
            config_content = contents.decoded_content.decode("utf-8")
            config = yaml.safe_load(config_content) or {}
        except Exception:
            config = {}

        # Minimal Mistakes Configuration
        config["remote_theme"] = TARGET_THEME
        config["minimal_mistakes_skin"] = "dark"
        config["locale"] = "ko-KR"

        # Site Settings
        config["title"] = "jhinux's github pages"
        config["description"] = "jhinux 의 정리글"
        config["url"] = ""

        # Explicitly disable GitHub repo links
        config["repository"] = None
        config["github_username"] = None

        # Author & Social
        config["author"] = {
            "name": "jhinux",
            "bio": "jhinux 의 정리글",
            "location": "Seoul, Korea",
            "url": "https://jhinux.tistory.com/", # Follow button links here
            "avatar": "/assets/images/logo.png"
        }

        # Logo
        config["logo"] = "/assets/images/logo.png"

        # Plugins
        config["plugins"] = ["jekyll-remote-theme", "jekyll-paginate", "jekyll-include-cache", "jekyll-seo-tag", "jekyll-feed", "jekyll-sitemap"]

        # Layout Defaults
        config["defaults"] = [
            {
                "scope": {
                    "path": "",
                    "type": "posts"
                },
                "values": {
                    "layout": "single",
                    "author_profile": True,
                    "read_time": True,
                    "comments": False,
                    "share": False,
                    "related": True
                }
            }
        ]

        if "paginate" not in config:
            config["paginate"] = 5

        new_content = yaml.dump(config, default_flow_style=False, allow_unicode=True)
        upload_file(repo, "_config.yml", new_content, f"Setup Minimal Mistakes (Dark)", branch)

        # Upload Logo if exists locally
        local_logo_path = "assets/images/logo.png"
        if os.path.exists(local_logo_path):
            with open(local_logo_path, "rb") as f:
                logo_content = f.read() # Read as binary

            # Since upload_file helper expects string content for text files usually,
            # we need to handle binary. But wait, `upload_file` in this script:
            # contents.decoded_content.decode('utf-8') -> It assumes text.
            # We need to use repo.update_file directly for binary or modify upload_file.
            # Let's handle it directly here to avoid breaking the helper for now or just try-except.

            remote_logo_path = "assets/images/logo.png"
            try:
                contents = repo.get_contents(remote_logo_path, ref=branch)
                # Comparing binary might be heavy, let's just force update if needed or skip.
                # Simplest: Just try create, if fail (exists), update.
                repo.update_file(remote_logo_path, "Upload Logo", logo_content, contents.sha, branch=branch)
                print(f"Updated {remote_logo_path}")
            except Exception:
                # File likely doesn't exist
                repo.create_file(remote_logo_path, "Upload Logo", logo_content, branch=branch)
                print(f"Created {remote_logo_path}")

    except Exception as e:
        print(f"Warning: Could not check/update _config.yml or logo: {e}")

def create_index(repo, branch="main"):
    """
    Creates index.html for the homepage.
    """
    content = """---
layout: home
author_profile: true
title: "jhinux's github pages"
---

최신 기술 뉴스와 개발 트렌드를 정리하는 블로그입니다.
"""
    upload_file(repo, "index.html", content, "Create Homepage (index.html)", branch)

def configure_navigation(repo, branch="main"):
    """
    Creates _data/navigation.yml for Korean menu.
    """
    nav_data = {
        "main": [
            {"title": "홈", "url": "/"},
            {"title": "소개", "url": "/about/"},
            {"title": "태그", "url": "/tags/"}
        ]
    }

    content = yaml.dump(nav_data, default_flow_style=False, allow_unicode=True)
    upload_file(repo, "_data/navigation.yml", content, "Configure Navigation (Korean)", branch)

def create_pages(repo, branch="main"):
    """
    Creates 'About' and 'Tags' pages compatible with Minimal Mistakes.
    """
    # 1. About Page (소개)
    about_content = """---
layout: single
title: "소개"
permalink: /about/
author_profile: true
---

기술 뉴스 트렌드를 정리하여 공유하는 블로그입니다.

최신 해커뉴스(Hacker News)의 인기 글을 분석하고 요약하여 제공합니다.
"""
    upload_file(repo, "about.md", about_content, "Create About page", branch)

    # 2. Tags Page (태그)
    tags_content = """---
layout: single
title: "태그"
permalink: /tags/
author_profile: true
---

<div class="tags-container">
  {% for tag in site.tags %}
    <a href="#{{ tag[0] | slugify }}" style="font-size: 1.2em; margin-right: 15px;">
      {{ tag[0] }} ({{ tag[1].size }})
    </a>
  {% endfor %}
</div>

<hr>

{% for tag in site.tags %}
  <h2 id="{{ tag[0] | slugify }}">{{ tag[0] }}</h2>
  <ul>
    {% for post in tag[1] %}
      <li><a href="{{ post.url | relative_url }}">{{ post.title }}</a> <small>({{ post.date | date_to_string }})</small></li>
    {% endfor %}
  </ul>
{% endfor %}
"""
    upload_file(repo, "tags.md", tags_content, "Create Tags page", branch)

def clean_default_posts(repo, branch="main"):
    try:
        contents = repo.get_contents("_posts", ref=branch)
        for content_file in contents:
            if "welcome-to-jekyll" in content_file.name:
                repo.delete_file(content_file.path, "Remove default Jekyll post", content_file.sha, branch=branch)
    except Exception:
        pass

def upload(github_token, repo_name, article_data):
    """
    Uploads the article to the specified GitHub repository.
    """
    try:
        g = Github(github_token)
        repo = g.get_repo(repo_name)
        branch = "main"

        # 1. Configuration (Run on every upload to ensure consistency)
        ensure_theme_config(repo, branch)
        clean_default_posts(repo, branch)
        create_index(repo, branch)
        configure_navigation(repo, branch)
        create_pages(repo, branch)

        # 2. Prepare Post Content
        date_str = datetime.now().strftime("%Y-%m-%d")
        file_path = f"_posts/{date_str}-{article_data['slug']}.md"

        tags_list = [tag.strip() for tag in article_data['tags'].split(',')] if article_data.get('tags') else []

        content = f"""---
layout: single
title: "{article_data['korean_title']}"
date: {datetime.now().astimezone().isoformat()}
categories: [Tech, Trends]
tags: {tags_list}
author_profile: true
---

{article_data['summary_md']}

---
[원문 보러가기]({article_data['url']})
"""

        # 3. Upload Generated Image (if exists)
        if 'local_image_path' in article_data and os.path.exists(article_data['local_image_path']):
            remote_img_path = f"assets/images/{article_data['image_filename']}"
            try:
                with open(article_data['local_image_path'], "rb") as img_f:
                    img_content = img_f.read()

                # Check/Update image
                try:
                    contents = repo.get_contents(remote_img_path, ref=branch)
                    repo.update_file(remote_img_path, f"Update image for {article_data['slug']}", img_content, contents.sha, branch=branch)
                    print(f"Updated image {remote_img_path}")
                except Exception:
                    repo.create_file(remote_img_path, f"Upload image for {article_data['slug']}", img_content, branch=branch)
                    print(f"Created image {remote_img_path}")
            except Exception as e:
                print(f"Failed to upload image {remote_img_path}: {e}")

        # 4. Create or Update Post
        upload_file(repo, file_path, content, f"Post: {article_data['korean_title']}", branch)

        return True, f"Published to {file_path}"

    except Exception as e:
        return False, f"GitHub Upload Error: {str(e)}"
