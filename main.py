from flask import Flask, request, jsonify
import requests
import difflib
import random

app = Flask(__name__)

# Your Giphy API key here
GIPHY_API_KEY = "YOUR_GIPHY_API_KEY"

# Optional: map mood aliases to core emotional tags
mood_response_map = {
    "melancholy": "sad",
    "blue": "sad",
    "gloomy": "sad",
    "pumped": "excited",
    "overwhelmed": "anxious",
    "victorious": "celebrate",
    "chill": "calm",
    "peaceful": "relax",
    "stressed": "anxious",
    "lonely": "lonely",
    "tired": "support",
    "motivated": "success",
    "joyful": "happy",
    "grateful": "happy",
    "burnt out": "anxious",
    "upbeat": "excited",
    "hopeful": "calm"
}

@app.route("/get_gif", methods=["GET"])
def get_gif():
    user_input = request.args.get("emotion", "").lower().strip()
    tag = mood_response_map.get(user_input, user_input)  # fallback to direct use if not mapped

    # Fuzzy match if tag not a common emotion
    known_tags = set(mood_response_map.values())
    if tag not in known_tags:
        close_match = difflib.get_close_matches(tag, known_tags, n=1, cutoff=0.6)
        if close_match:
            tag = close_match[0]

    # Query Giphy API for a GIF
    params = {
        "api_key": GIPHY_API_KEY,
        "q": tag,
        "limit": 25,
        "rating": "pg",
        "lang": "en"
    }
    response = requests.get("https://api.giphy.com/v1/gifs/search", params=params)

    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch from Giphy"}), 500

    gifs = response.json().get("data", [])
    if not gifs:
        return jsonify({"error": f"No GIFs found for '{user_input}'"}), 404

    # Prefer cartoon or sticker-style gifs if available
    preferred = [gif for gif in gifs if 'cartoon' in gif['title'].lower() or 'sticker' in gif['title'].lower()]
    candidates = preferred if preferred else gifs

    selected_gif = random.choice(candidates)
    gif_url = selected_gif["images"]["original"]["url"]

    return f"""
    <html>
        <body style="text-align: center; font-family: sans-serif;">
            <h2>You're feeling: {user_input}</h2>
            <img src="{gif_url}" alt="GIF response" />
            <p>Matched mood: <b>{tag}</b></p>
        </body>
    </html>
    """

@app.route("/moods", methods=["GET"])
def get_supported_moods():
    return jsonify({"supported_moods": sorted(set(mood_response_map.keys()))})

if __name__ == "__main__":
    app.run(debug=True)
