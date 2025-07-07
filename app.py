import streamlit as st
import instaloader
import openai
import pandas as pd
import os
from dotenv import load_dotenv
import anthropic


load_dotenv()

# Set your OpenAI API key
anthropic_api_key = st.secrets.get("ANTHROPIC_API_KEY") # Replace with your actual key

client = anthropic.Anthropic(api_key=anthropic_api_key)

def load_instaloader_session(username, session_path):
    L = instaloader.Instaloader()

    try:
        # Try loading saved session
        L.load_session_from_file(username, filename=session_path)

        # Validate session (lightweight call)
        instaloader.Profile.from_username(L.context, username)

        st.success("✅ Instagram session loaded and valid.")
        return L

    except Exception as e:
        st.error("❌ Instagram session is expired or invalid.")
        st.info("🔁 Please re-export cookies and rerun the cookie-to-session script.")
        st.stop()
        return None

# --- Function to fetch recent posts from username using Instaloader ---
def get_latest_posts(target_username, max_posts=1):
    try:
        ig_username = "gist.grid9ja"
        session_path = "sesion-gist.grid9ja"

        # Load and validate session
        L = load_instaloader_session(ig_username, session_path)
       

        profile = instaloader.Profile.from_username(L.context, target_username)
        posts = profile.get_posts()

        results = []
        for i, post in enumerate(posts):
            if i >= max_posts:
                break
            caption = post.caption or "No caption available."
            mentions = [f"@{mention}" for mention in post.caption_mentions]
            credited = ", ".join(mentions) if mentions else target_username
            post_url = f"https://www.instagram.com/p/{post.shortcode}/"
            results.append({
                "original": caption,
                "credited": credited,
                "url": post_url
            })
        return results

    except Exception as e:
        st.error(f"❌ Failed to fetch posts: {str(e)}")
        return []
# --- Rewrite function using GPT ---
def rewrite_caption(caption):
    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",  # Fast, lightweight model
            max_tokens=500,
            temperature=0.7,
            messages=[
                {
                    "role": "user",
                    "content": f"Rewrite the following Instagram caption in a blog-style, engaging tone:\n\n{caption}"
                }
            ]
        )
        return response.content[0].text.strip()
    except Exception as e:
        return f"❌ Error rewriting caption: {str(e)}"

# --- Streamlit App UI ---
st.set_page_config(page_title="Instagram Rewriter", layout="centered")
st.title("📸 Instagram Caption Rewriter (Username-based)")
st.markdown("Enter a public Instagram username. It will fetch their latest post(s), rewrite the captions, and export to CSV.")

username = st.text_input("Instagram Username")
num_posts = st.slider("Number of recent posts to fetch", 1, 5, 1)

if "records" not in st.session_state:
    st.session_state.records = []

if st.button("Scrape & Rewrite"):
    if username:
        with st.spinner("Fetching and rewriting..."):
            posts = get_latest_posts(username.strip(), num_posts)

            for post in posts:
                original = post["original"]
                credited = post["credited"]
                url = post["url"]

                rewritten = rewrite_caption(original)

                st.markdown(f"### 🔗 [View Post]({url})")
                st.subheader("✍️ Original Caption")
                st.code(original)

                st.subheader("🔁 Rewritten Caption")
                st.code(rewritten)

                st.session_state.records.append({
                    "Original Text": original,
                    "Rewritten Text": rewritten,
                    "Credited Account": credited,
                    "URL": url
                })
    else:
        st.warning("Please enter a valid username.")

# --- CSV Download Button ---
if st.session_state.records:
    df = pd.DataFrame(st.session_state.records)
    st.download_button(
        label="📥 Download CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="rewritten_instagram_captions.csv",
        mime="text/csv"
    )
