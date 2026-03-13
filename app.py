from flask import Flask, redirect, request, session, url_for
import requests
import os
from pymongo import MongoClient


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change_this_secret")

# MongoDB setup
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://mongo:ToflcolbjYxOCwRJyIsyoqvIDBISAXgP@interchange.proxy.rlwy.net:32018")
# Extract database name from URI or set a default
from urllib.parse import urlparse
parsed = urlparse(MONGO_URI)
db_name = (parsed.path[1:] if parsed.path and len(parsed.path) > 1 else "appdb")
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[db_name] if mongo_client is not None else None
mongo_collection = mongo_db["verifications"] if mongo_db is not None else None

# Discord OAuth2 setup
DISCORD_CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = "https://flaskwebappsierra7-production-6f7b.up.railway.app/discord/oauth/callback"
DISCORD_SCOPE = "identify"

@app.route("/discord/oauth/start")
def discord_oauth_start():
    authorize_url = (
        "https://discord.com/api/oauth2/authorize"
        f"?client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={DISCORD_SCOPE}"
        "&prompt=consent"
    )
    return redirect(authorize_url)

@app.route("/discord/oauth/callback")
def discord_oauth_callback():
    code = request.args.get("code")
    if not code:
        return "Missing Discord code", 400
    # Exchange code for token
    token_url = "https://discord.com/api/oauth2/token"
    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "scope": DISCORD_SCOPE,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    resp = requests.post(token_url, data=data, headers=headers)
    if resp.status_code != 200:
        return f"Discord token error: {resp.text}", 400
    token_info = resp.json()
    access_token = token_info.get("access_token")
    # Fetch Discord user info
    user_info_url = "https://discord.com/api/users/@me"
    headers = {"Authorization": f"Bearer {access_token}"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
