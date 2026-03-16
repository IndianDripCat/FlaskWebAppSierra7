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


# Discord OAuth2 setup
DISCORD_CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.environ.get("DISCORD_REDIRECT_URI", "https://flaskwebappsierra7-production-6f7b.up.railway.app/discord/oauth/callback")
DISCORD_SCOPE = "identify"

# Roblox OAuth2 setup
ROBLOX_CLIENT_ID = os.environ.get("ROBLOX_CLIENT_ID")
ROBLOX_CLIENT_SECRET = os.environ.get("ROBLOX_CLIENT_SECRET")
ROBLOX_REDIRECT_URI = "https://flaskwebappsierra7-production-6f7b.up.railway.app/roblox/oauth/callback"
ROBLOX_SCOPE = "openid profile"

@app.route("/")
def index():
    from flask import render_template
    return render_template("index.html")

@app.route("/terms")
def terms():
    from flask import render_template
    return render_template("terms.html")

@app.route("/privacy")
def privacy():
    from flask import render_template
    return render_template("privacy.html")

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
    user_resp = requests.get(user_info_url, headers=headers)
    if user_resp.status_code != 200:
        return f"Discord user error: {user_resp.text}", 400
    discord_user = user_resp.json()
    # Store Discord info in session
    session["discord_user"] = discord_user
    # Redirect to Roblox OAuth
    return redirect(url_for("roblox_oauth_start"))

# Roblox OAuth2 endpoints
@app.route("/roblox/oauth/start")
def roblox_oauth_start():
    authorize_url = (
        "https://authorize.roblox.com/"
        f"?client_id={ROBLOX_CLIENT_ID}"
        f"&redirect_uri={ROBLOX_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid+profile"
        f"&state=discord"
        f"&step=account"
    )
    return redirect(authorize_url)

@app.route("/roblox/oauth/callback")
def roblox_oauth_callback():
    code = request.args.get("code")
    if not code:
        return "Missing Roblox code", 400
    # Exchange code for token
    token_url = "https://apis.roblox.com/oauth/v1/token"
    data = {
        "client_id": ROBLOX_CLIENT_ID,
        "client_secret": ROBLOX_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": ROBLOX_REDIRECT_URI,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    resp = requests.post(token_url, data=data, headers=headers)
    if resp.status_code != 200:
        return f"Roblox token error: {resp.text}", 400
    token_info = resp.json()
    access_token = token_info.get("access_token")
    # Fetch Roblox user info
    user_info_url = "https://apis.roblox.com/oauth/v1/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    user_resp = requests.get(user_info_url, headers=headers)
    if user_resp.status_code != 200:
        return f"Roblox user error: {user_resp.text}", 400
    roblox_user = user_resp.json()
    # Store Roblox info in session
    session["roblox_user"] = roblox_user
    # Store both Discord and Roblox info in DB
    if mongo_collection is not None:
        mongo_collection.insert_one({
            "discord": session.get("discord_user"),
            "roblox": roblox_user
        })
    return "Verification complete! You may close this page."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
