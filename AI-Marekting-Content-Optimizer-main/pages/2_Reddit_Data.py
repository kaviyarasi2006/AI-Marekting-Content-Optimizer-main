import streamlit as st
import pandas as pd
import gspread
import feedparser
from oauth2client.service_account import ServiceAccountCredentials


# ---------------- GOOGLE SHEETS CONNECTION ----------------

def connect_sheets():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    try:
        creds_dict = dict(st.secrets["gcp_service_account"])

        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            creds_dict,
            scope
        )

        client = gspread.authorize(creds)

        return client.open("Content Performance Tracker")

    except Exception as e:
        st.error(f"❌ Google Sheets Error: {e}")
        st.stop()


# ---------------- CONFIG ----------------

POSTS_TAB = "Reddit Posts"

SUBREDDITS = [
    "marketing",
    "content_marketing",
    "socialmedia",
    "DigitalMarketing",
    "SEO",
    "EmailMarketing",
    "PPC"
]

POST_LIMIT = 20


# ---------------- FETCH REDDIT DATA ----------------

@st.cache_data(show_spinner=False)
def fetch_reddit_data():

    all_posts = []

    status = st.empty()
    progress = st.progress(0)

    for index, sub in enumerate(SUBREDDITS):

        status.write(f"🔎 Scraping r/{sub}...")

        try:
            urls = [
                f"https://www.reddit.com/r/{sub}/hot/.rss",
                f"https://www.reddit.com/r/{sub}/new/.rss"
            ]

            feed = None

            for url in urls:
                feed = feedparser.parse(url)

                if feed.entries:
                    break

            if not feed.entries:
                continue

            for entry in feed.entries[:POST_LIMIT]:
                all_posts.append({
                    "Subreddit": sub,
                    "Title": entry.title,
                    "URL": entry.link,
                    "Created Date": entry.published
                })

        except Exception:
            continue

        progress.progress((index + 1) / len(SUBREDDITS))

    status.success("✅ Reddit Scraping Complete")

    posts_df = pd.DataFrame(all_posts)

    return posts_df


# ---------------- UPLOAD TO GOOGLE SHEETS ----------------

def upload_to_sheets(posts_df):

    sheet = connect_sheets()

    try:
        ws_posts = sheet.worksheet(POSTS_TAB)
    except:
        ws_posts = sheet.add_worksheet(
            title=POSTS_TAB,
            rows="2000",
            cols="20"
        )

    if not posts_df.empty:
        ws_posts.clear()

        ws_posts.update(
            "A1",
            [posts_df.columns.tolist()] +
            posts_df.astype(str).values.tolist()
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

            posts_df = fetch_reddit_data()

            if not posts_df.empty:

                st.subheader(f"📝 Found {len(posts_df)} Posts")
                st.dataframe(posts_df.head(10))

                upload_to_sheets(posts_df)

            else:
                st.warning("⚠ No posts found.")
