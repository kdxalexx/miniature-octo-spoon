import json
import time
import requests
from datetime import datetime
from instagrapi import Client

# ==================================================
# CONFIG — EDIT THESE VALUES
# ==================================================

INSTAGRAM_USERNAME = "YOUR_INSTAGRAM_USERNAME"
INSTAGRAM_PASSWORD = "YOUR_INSTAGRAM_PASSWORD"

TARGET_USERNAME = "TARGET_ACCOUNT_USERNAME"

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/WEBHOOK_ID/WEBHOOK_TOKEN"

CHECK_INTERVAL = 120  # seconds (2 minutes recommended)

# ==================================================
# FILES
# ==================================================

FOLLOWERS_FILE = f"{TARGET_USERNAME}_followers.json"
FOLLOWING_FILE = f"{TARGET_USERNAME}_following.json"

SESSION_FILE = "ig_session.json"

# ==================================================
# DISCORD FUNCTION
# ==================================================

def send_discord(message):
    try:
        r = requests.post(
            DISCORD_WEBHOOK_URL,
            json={"content": message},
            timeout=10
        )
        if r.status_code not in (200, 204):
            print("Discord error:", r.text)
    except Exception as e:
        print("Discord exception:", e)

# ==================================================
# FILE HELPERS
# ==================================================

def load_set(filename):
    try:
        with open(filename, "r") as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_set(filename, data):
    with open(filename, "w") as f:
        json.dump(sorted(list(data)), f)

# ==================================================
# INSTAGRAM LOGIN
# ==================================================

cl = Client()

try:
    cl.load_settings(SESSION_FILE)
    cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
    print("✅ Logged in using saved session")
except Exception:
    print("🔐 Fresh login")
    cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
    cl.dump_settings(SESSION_FILE)

target_id = cl.user_id_from_username(TARGET_USERNAME)
print(f"👀 Monitoring @{TARGET_USERNAME}")

# ==================================================
# MONITOR FUNCTION
# ==================================================

def check_changes():
    old_followers = load_set(FOLLOWERS_FILE)
    old_following = load_set(FOLLOWING_FILE)

    followers = cl.user_followers(target_id, amount=0)
    following = cl.user_following(target_id, amount=0)

    current_followers = set(u.username for u in followers.values())
    current_following = set(u.username for u in following.values())

    gained = current_followers - old_followers
    lost = old_followers - current_followers
    followed = current_following - old_following
    unfollowed = old_following - current_following

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for u in gained:
        send_discord(f"[{ts}] ➕ **{u}** followed **{TARGET_USERNAME}**")

    for u in lost:
        send_discord(f"[{ts}] ➖ **{u}** unfollowed **{TARGET_USERNAME}**")

    for u in followed:
        send_discord(f"[{ts}] 👀 **{TARGET_USERNAME}** followed **{u}**")

    for u in unfollowed:
        send_discord(f"[{ts}] 🚪 **{TARGET_USERNAME}** unfollowed **{u}**")

    save_set(FOLLOWERS_FILE, current_followers)
    save_set(FOLLOWING_FILE, current_following)

    print(f"✔ Checked ({len(current_followers)} followers)")

# ==================================================
# MAIN LOOP
# ==================================================

if __name__ == "__main__":
    print("🚀 Instagram monitor started")
    while True:
        try:
            check_changes()
        except Exception as e:
            print("⚠️ Error:", e)
        time.sleep(CHECK_INTERVAL)
