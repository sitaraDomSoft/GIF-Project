from flask import Flask, request, jsonify
import requests
import random
import torch
from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)

# Load sentence transformer model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Define response labels
response_tags = [
    "comforting", "relax", "calm", "celebrate", "support",
    "rest", "success", "happy", "joy", "inspire", "sad", "angry"
]

# Embed once at startup
tag_embeddings = model.encode(response_tags, convert_to_tensor=True)

# Map tags to better search phrases
response_to_keywords = {
    "comforting": [
        "hug", "snuggle", "it's okay", "you'll be okay", "comforting hug", "pat on back", 
        "warm blanket", "you are not alone", "kind words"
    ],
    "relax": [
        "peaceful", "relaxing nature", "ocean waves", "chill vibes", "meditation", "deep breath", 
        "zen", "calming animation", "spa"
    ],
    "calm": [
        "serenity", "stay calm", "keep breathing", "calming", "soothing animation", 
        "peaceful cartoon", "gentle music", "floating"
    ],
    "celebrate": [
        "confetti", "party", "celebration", "yay", "victory dance", "happy dance", 
        "fist bump", "cheers", "high five"
    ],
    "support": [
        "i'm here for you", "you got this", "supportive friend", "virtual hug", "lean on me", 
        "we got this", "teamwork", "i believe in you", "you matter"
    ],
    "rest": [
        "sleepy", "nap", "bedtime", "cozy blanket", "good night", "pajamas", 
        "resting", "relaxing sleep", "sleepy cartoon"
    ],
    "success": [
        "you did it", "achievement", "success", "trophy", "winning", 
        "level up", "gold star", "clap", "well done"
    ],
    "happy": [
        "happy dance", "smiling", "pure joy", "so happy", "joyful", 
        "laughing", "happy cartoon", "sunshine", "grinning"
    ],
    "joy": [
        "bursting with joy", "ecstatic", "jumping for joy", "yay", "excited smile", 
        "sparkle", "joyful celebration", "cartoon joy", "excited animation"
    ],
    "inspire": [
        "you can do it", "believe in yourself", "motivational", "you are amazing", 
        "keep going", "never give up", "dream big", "push forward", "encouragement"
    ],
    "sad": [
        "it's okay to cry", "gentle hug", "empathy", "supportive", 
        "i'm listening", "sad but hopeful", "soft music", "shoulder to cry on", "crying animation"
    ],
    "angry": [
        "deep breath", "calm down", "relax", "let it out", "cool off", 
        "breathe", "release anger", "walk it off", "stress relief"
    ]
}

# Giphy API key
GIPHY_API_KEY = "EhPDCGyb3CrQQRr8bd1aFtCiDw6d2P6a"

def map_user_input_to_tag(user_input):
    input_embedding = model.encode(user_input, convert_to_tensor=True)
    cosine_scores = util.pytorch_cos_sim(input_embedding, tag_embeddings)
    best_idx = torch.argmax(cosine_scores).item()
    return response_tags[best_idx]

@app.route("/get_gif", methods=["GET"])
def get_gif():
    user_input = request.args.get("emotion", "").lower().strip()
    if not user_input:
        return jsonify({"error": "No input provided."}), 400

    tag = map_user_input_to_tag(user_input)
    search_terms = response_to_keywords.get(tag, [tag])
    query_term = random.choice(search_terms)

    # Query Giphy
    params = {
        "api_key": GIPHY_API_KEY,
        "q": query_term + " cartoon",
        "limit": 25,
        "offset": random.randint(0, 50),
        "rating": "pg",
        "lang": "en"
    }
    response = requests.get("https://api.giphy.com/v1/gifs/search", params=params)

    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch from Giphy"}), 500

    gifs = response.json().get("data", [])
    if not gifs:
        return jsonify({"error": f"No GIFs found for '{user_input}'"}), 404

    preferred = [
        gif for gif in gifs 
        if gif.get("type") == "sticker" 
        or "cartoon" in gif.get("slug", "").lower()
        or "cartoon" in gif.get("title", "").lower()
    ]
    candidates = preferred if preferred else gifs
    selected_gif = random.choice(candidates)
    gif_url = selected_gif["images"]["original"]["url"]

    return f"""
    <html>
        <body style="text-align: center; font-family: sans-serif;">
            <h2>You said: <i>{user_input}</i></h2>
            <img src="{gif_url}" alt="GIF response" />
            <p>Responding with: <b>{tag}</b> ({query_term})</p>
        </body>
    </html>
    """

@app.route("/moods", methods=["GET"])
def get_supported_tags():
    return jsonify({"response_tags": sorted(response_tags)})

if __name__ == "__main__":
    app.run(debug=True)
