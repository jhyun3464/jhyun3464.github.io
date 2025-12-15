import streamlit as st
import analyzer
import db_manager
import github_publisher
import naver_poster
import time
import markdown

# Page Config
st.set_page_config(page_title="HN Ops Center", layout="wide")

# Initialize DB
db_manager.init_db()

# Sidebar: Configuration
st.sidebar.title("Configuration")

# Default values from user prompt
DEFAULT_GEMINI_KEY = "AIzaSyDlASRGPC9bXlEGvvGKQseNJYjE-6PmtuE"
DEFAULT_GITHUB_TOKEN = "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"
DEFAULT_REPO_NAME = "jhyun3464/jhyun3464.github.io"

gemini_key = st.sidebar.text_input("Gemini API Key", value=DEFAULT_GEMINI_KEY, type="password")
github_token = st.sidebar.text_input("GitHub Token", value=DEFAULT_GITHUB_TOKEN, type="password")
repo_name = st.sidebar.text_input("GitHub Repo", value=DEFAULT_REPO_NAME)

st.sidebar.divider()

# Automation Section
st.sidebar.subheader("Automation")
auto_mode = st.sidebar.checkbox("Enable Auto Mode")
interval = st.sidebar.number_input("Interval (minutes)", min_value=1, value=30)

# Main Title
st.title("jhinux 의 정리글")

# Section 1: Fetch & Analyze
st.header("1. Fetch & Analyze Trends")
if st.button("Fetch Top Stories"):
    if not gemini_key:
        st.error("Please provide Gemini API Key")
    else:
        with st.spinner("Fetching and Analyzing..."):
            story_ids = analyzer.get_top_stories(limit=5)
            progress_bar = st.progress(0)

            for i, sid in enumerate(story_ids):
                # Check if already exists/published to avoid re-work?
                # Requirement says "DB를 만드는것은 중복으로 발행하기 않기 위함입니다."
                # But fetch might update "Reaction"?
                # Let's simple fetch and UPSERT.

                result = analyzer.analyze_article(sid, gemini_key)
                if result:
                    db_manager.save_article(result)
                progress_bar.progress((i + 1) / len(story_ids))

            st.success("Analysis Complete!")
            st.rerun()

# Section 2: View & Publish
st.header("2. Manage Articles")

articles = db_manager.get_articles()

if not articles:
    st.info("No articles found. Fetch some first!")

for article in articles:
    with st.expander(f"[{article['grade']}] {article['korean_title']} (ID: {article['id']})"):
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**Original:** [{article['title']}]({article['url']})")
            st.markdown("### Summary")
            st.markdown(article['summary_md'])
            st.markdown(f"**Tags:** {article['tags']}")
            st.markdown(f"**Slug:** {article['slug']}")

        with col2:
            st.metric("Grade", article['grade'])
            status = "Published" if article['is_published'] else "Draft"
            st.info(f"Status: {status}")

            if not article['is_published']:
                if st.button("통합 발행 (One Click)", key=f"pub_{article['id']}"):
                    # 1. GitHub
                    with st.spinner("Publishing to GitHub..."):
                        gh_success, gh_msg = github_publisher.upload(github_token, repo_name, article)
                        if gh_success:
                            st.toast(f"GitHub: {gh_msg}", icon="✅")
                        else:
                            st.toast(f"GitHub Failed: {gh_msg}", icon="❌")

                    # 2. Naver
                    with st.spinner("Publishing to Naver..."):
                        html_content = markdown.markdown(article['summary_md'])
                        nv_success, nv_msg = naver_poster.post_article(article['korean_title'], html_content)
                        if nv_success:
                            st.toast(f"Naver: {nv_msg}", icon="✅")
                        else:
                            st.toast(f"Naver Failed: {nv_msg}", icon="❌")

                    # 3. Update DB
                    if gh_success and nv_success:
                        db_manager.mark_published(article['id'])
                        st.success("All published successfully!")
                        time.sleep(1)
                        st.rerun()

# Automation Loop
if auto_mode:
    st.sidebar.success(f"Auto Mode Running (Every {interval} mins)")

    # Use a placeholder to countdown or status
    placeholder = st.sidebar.empty()

    # We can't block the main thread forever in Streamlit or UI freezes.
    # Typically we use st.rerun() with time check or simpler loop logic.
    # For a simple "periodic fetch", we can check last run time.

    if 'last_run' not in st.session_state:
        st.session_state.last_run = time.time()

    elapsed = time.time() - st.session_state.last_run
    next_run = interval * 60

    if elapsed > next_run:
        # Run Fetch
        with st.spinner("Auto-Fetch Running..."):
            story_ids = analyzer.get_top_stories(limit=10)
            for sid in story_ids:
                result = analyzer.analyze_article(sid, gemini_key)
                if result:
                    db_manager.save_article(result)

            # Auto Publish S-Grade? Requirement says "One Click Publish" in section 3,
            # but section 4 says "주기적으로 자동으로 포스팅합니다".
            # Assuming auto-publish logic for NEW high grade items?
            # Or just fetch? The prompt says "Fetch -> DB 저장" in Section 1, and "Action" in Section 3.
            # But Section 4 says "Automatically posts periodically".
            # Let's assume it automatically PUBLISHES pending items or fetches and publishes.
            # I'll implement auto-publish for unpublished items.

            pending_articles = db_manager.get_articles()
            for article in pending_articles:
                if not article['is_published']:
                    # Optional: Only publish S/A grade?
                    # For now, publish everything fetched in auto mode or just follow standard logic.
                    # I will publish everything to fulfill "Automatically posts".

                    # GitHub
                    gh_success, _ = github_publisher.upload(github_token, repo_name, article)
                    # Naver
                    html_content = markdown.markdown(article['summary_md'])
                    nv_success, _ = naver_poster.post_article(article['korean_title'], html_content)

                    if gh_success and nv_success:
                        db_manager.mark_published(article['id'])

        st.session_state.last_run = time.time()
        st.rerun()
    else:
        # Refresh to keep the app "alive" and checking time?
        # A simple sleep in a loop inside a script works, but in Streamlit
        # we usually rely on st.empty() and time.sleep() then rerun.
        time.sleep(1) # Check every second? Too heavy.
        # Just show countdown
        placeholder.text(f"Next run in {int(next_run - elapsed)}s")
        time.sleep(1)
        st.rerun()
