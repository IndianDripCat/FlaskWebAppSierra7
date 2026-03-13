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
db_name = (parsed.path[1:] if parsed.path and len(parsed.path) > 1 else "sierra_applications")
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[db_name] if mongo_client is not None else None
mongo_collection = mongo_db["verifications"] if mongo_db is not None else None

ROBLOX_CLIENT_ID = os.environ.get("ROBLOX_CLIENT_ID")
ROBLOX_CLIENT_SECRET = os.environ.get("ROBLOX_CLIENT_SECRET")
REDIRECT_URI = "https://flaskwebappsierra7-production-6f7b.up.railway.app/roblox/oauth/callback"

@app.route("/roblox/oauth/start")
def roblox_oauth_start():
    authorize_url = (
        "https://apis.roblox.com/oauth/v1/authorize"
        "?response_type=code"
        f"&client_id={ROBLOX_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&scope=openid profile"
        "&state=discord"
    )
    return redirect(authorize_url)

@app.route("/roblox/oauth/callback")
def roblox_oauth_callback():
    code = request.args.get("code")
    if not code:
        return "Missing code", 400

    # Exchange code for token
    token_url = "https://apis.roblox.com/oauth/v1/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": ROBLOX_CLIENT_ID,
        "client_secret": ROBLOX_CLIENT_SECRET,
    }
    resp = requests.post(token_url, data=data)
    if resp.status_code != 200:
        return f"Token error: {resp.text}", 400

    token_info = resp.json()
    access_token = token_info.get("access_token")

    # Fetch user info
    user_info_url = "https://apis.roblox.com/oauth/v1/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    user_resp = requests.get(user_info_url, headers=headers)
    if user_resp.status_code != 200:
        return f"User info error: {user_resp.text}", 400

    user_data = user_resp.json()

    # Log user_data to MongoDB
    if mongo_collection is not None:
        try:
            log_entry = {
                "user_data": user_data,
                "ip": request.remote_addr,
                "user_agent": request.headers.get("User-Agent"),
                "event": "roblox_verification",
            }
            mongo_collection.insert_one(log_entry)
        except Exception as e:
            print(f"MongoDB logging error: {e}")

    return f"Roblox account linked: {user_data}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
