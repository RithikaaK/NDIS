"""
Run once to get your Gmail OAuth2 refresh token.
Usage:
    pip install google-auth-oauthlib --break-system-packages
    python gmail_auth_setup.py

A browser window opens — sign in with priyacds24@gmail.com and allow access.
Then copy the refresh token printed here into your .env file.
"""
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

flow = InstalledAppFlow.from_client_secrets_file("gmail_credentials.json", SCOPES)
creds = flow.run_local_server(port=0)

print("\n✅ Auth successful!")
print("\nAdd these to your .env file:")
print(f"GMAIL_CLIENT_ID={creds.client_id}")
print(f"GMAIL_CLIENT_SECRET={creds.client_secret}")
print(f"GMAIL_REFRESH_TOKEN={creds.refresh_token}")
