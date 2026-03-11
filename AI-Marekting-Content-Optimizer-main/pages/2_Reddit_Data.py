import streamlit as st
import os
import json
import requests
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timezone

# ---------------- GOOGLE SHEETS CONNECTION ----------------

def connect_sheets():

    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    if os.path.exists("credentials.json"):

        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "credentials.json", scope
        )

        client = gspread.authorize(creds)

        return client.open("Content Performance Tracker")

    else:
        st.error("❌ credentials.json file not found")
        st.stop()


# ---------------- CONFIG ----------------

GOOGLE_SHEET_NAME = "Content Performance Tracker"
POSTS_TAB = "Reddit Posts"
COMMENTS_TAB = "Reddit Comments"

SUBREDDITS = [
    "marketing",
    "content_marketing",
    "socialmedia",
    "DigitalMarketing",
    "SEO",
    "EmailMarketing",
    "PPC"
]

POST_LIMIT = 50
MIN_UPVOTES = 15
MIN_COMMENTS = 3


# ---------------- FETCH REDDIT DATA ----------------

@st.cache_data(show_spinner=False)
def fetch_reddit_data():

    all_posts = []
    all_comments = []

    status = st.empty()
    progress = st.progress(0)

    for index, sub in enumerate(SUBREDDITS):

        status.write(f"🔎 Scraping r/{sub}...")

        try:

            url = f"https://www.reddit.com/r/{sub}/hot.json?limit={POST_LIMIT}"

            headers = {"User-Agent": "streamlit-app"}

            response = requests.get(url, headers=headers)

            data = response.json()

            posts = data["data"]["children"]

            for post in posts:

                p = post["data"]

                if p["score"] < MIN_UPVOTES or p["num_comments"] < MIN_COMMENTS:
                    continue

                all_posts.append({

                    "Subreddit": sub,
                    "Title": p["title"],
                    "Upvotes": p["score"],
                    "Comments": p["num_comments"],
                    "URL": "https://reddit.com" + p["permalink"],
                    "Created Date": datetime.fromtimestamp(
                        p["created_utc"], timezone.utc
                    ).strftime("%Y-%m-%d"),
                    "Post Text": p["selftext"][:400] if p["selftext"] else "N/A",
                    "Post ID": p["id"]

                })

        except Exception as e:

            st.warning(f"Error reading r/{sub}: {e}")

        progress.progress((index + 1) / len(SUBREDDITS))

    status.success("✅ Reddit Scraping Complete")

    posts_df = pd.DataFrame(all_posts)
    comments_df = pd.DataFrame(all_comments)

    return posts_df, comments_df


# ---------------- UPLOAD TO GOOGLE SHEETS ----------------

def upload_to_sheets(posts_df, comments_df):

    sheet = connect_sheets()

    try:
        ws_posts = sheet.worksheet(POSTS_TAB)
    except:
        ws_posts = sheet.add_worksheet(title=POSTS_TAB, rows="2000", cols="20")

    if not posts_df.empty:

        ws_posts.clear()

        ws_posts.update(
            "A1",
            [posts_df.columns.tolist()] +
            posts_df.astype(str).values.tolist()
        )

    try:
        ws_comments = sheet.worksheet(COMMENTS_TAB)
    except:
        ws_comments = sheet.add_worksheet(title=COMMENTS_TAB, rows="2000", cols="20")

    if not comments_df.empty:

        ws_comments.clear()

        ws_comments.update(
            "A1",
            [comments_df.columns.tolist()] +
            comments_df.astype(str).values.tolist()
        )

    st.success("🚀 Uploaded to Google Sheets")


# ---------------- STREAMLIT UI ----------------

st.title("💬 Reddit Trend Monitor")

st.markdown(
    "Monitor discussions from marketing communities to discover trending topics."
)

col1, col2 = st.columns(2)

with col1:
    st.info("Subreddits:\n\n" + ", ".join(SUBREDDITS))

with col2:

    if st.button("🚀 Start Scraping Reddit", type="primary"):

        with st.spinner("Fetching Reddit data..."):

            posts_df, comments_df = fetch_reddit_data()

            if not posts_df.empty:

                st.subheader(f"📝 Found {len(posts_df)} Posts")
                st.dataframe(posts_df.head(10))

                upload_to_sheets(posts_df, comments_df)

            else:

                st.warning("No posts found.")