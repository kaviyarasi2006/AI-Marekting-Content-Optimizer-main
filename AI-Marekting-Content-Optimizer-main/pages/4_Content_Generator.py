def connect_sheets():
    """Connect to Google Sheets using Cloud Secrets OR Local JSON"""
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    # First try Streamlit Cloud secrets
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])

            # Fix private key new line issue
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                creds_dict,
                scope
            )

            client = gspread.authorize(creds)

            # Open your Google Sheet
            return client.open("Content Performance Tracker")

    except Exception as e:
        st.error(f"❌ Cloud Secret Error: {e}")
        st.stop()

    # Local fallback
    if os.path.exists("credentials.json"):
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "credentials.json",
            scope
        )

    elif os.path.exists("../credentials.json"):
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "../credentials.json",
            scope
        )

    else:
        st.error("❌ Critical Error: No Google Credentials found!")
        st.stop()

    client = gspread.authorize(creds)
    return client.open("Content Performance Tracker")
