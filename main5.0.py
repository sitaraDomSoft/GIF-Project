from flask import Flask, request, jsonify
import requests
import random
import torch
from sentence_transformers import SentenceTransformer, util
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
from io import BytesIO

app = Flask(__name__)
GIPHY_API_KEY = "EhPDCGyb3CrQQRr8bd1aFtCiDw6d2P6a"

# Load models
semantic_model = SentenceTransformer("all-MiniLM-L6-v2")
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# Example-based intent detection
tag_to_examples = {
    "comforting": [
        "I'm feeling really down", "I'm sad", "I feel so empty", "I'm heartbroken", "I'm not okay"
    ],
    "support": [
        "I'm feeling alone", "No one gets it", "I'm going through a tough time", "Can someone check on me?"
    ],
    "calm": [
        "I'm angry", "I'm furious", "I'm so mad right now", "I'm irritated", "I want to scream"
    ],
    "rest": [
        "I'm exhausted", "I'm burnt out", "I can't keep going", "Running on empty"
    ],
    "relax": [
        "I'm overwhelmed", "There's too much going on", "Everything feels chaotic", "Too much noise"
    ],
    "inspire": [
        "I'm stuck in a rut", "I need a push", "I need to believe in myself", "Help me find hope"
    ],
    "celebrate": [
        "I did it!", "I achieved something", "That went well!", "I'm so proud of myself"
    ],
    "happy": [
        "I'm feeling good", "I'm in a good mood", "Today is great", "I'm content"
    ],
    "joy": [
        "I'm laughing so hard", "I'm full of joy", "Feeling giddy and silly"
    ],
    "success": [
        "I nailed it", "That was a win", "Finished a big task"
    ]
}

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
        "peaceful cartoon", "gentle music", "slow motion", "floating"
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

# Embed examples
example_sentences = []
example_labels = []
for tag, phrases in tag_to_examples.items():
    for phrase in phrases:
        example_sentences.append(phrase)
        example_labels.append(tag)
example_embeddings = semantic_model.encode(example_sentences, convert_to_tensor=True)

def map_user_input_to_response_tag(user_input):
    input_embedding = semantic_model.encode(user_input, convert_to_tensor=True)
    cosine_scores = util.pytorch_cos_sim(input_embedding, example_embeddings)
    best_idx = torch.argmax(cosine_scores).item()
    return example_labels[best_idx]

def rank_gifs_by_clip(gif_urls, response_tag):
    images = []
    valid_urls = []
    for url in gif_urls:
        preview_url = url.replace("/giphy.gif", "/200_s.gif")
        try:
            img_data = requests.get(preview_url, timeout=5).content
            img = Image.open(BytesIO(img_data)).convert("RGB")
            images.append(img)
            valid_urls.append(url)
        except Exception:
            continue
    if not images:
        return random.choice(gif_urls)
    inputs = clip_processor(
        text=[response_tag] * len(images),
        images=images,
        return_tensors="pt",
        padding=True
    )
    with torch.no_grad():
        outputs = clip_model(**inputs)
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=0)
    best_idx = torch.argmax(probs).item()
    return valid_urls[best_idx]

@app.route("/get_gif", methods=["GET"])
def get_gif():
    user_input = request.args.get("emotion", "").strip()
    if not user_input:
        return jsonify({"error": "Missing 'emotion' query parameter"}), 400

    tag = map_user_input_to_response_tag(user_input)
    search_term = random.choice(response_to_keywords.get(tag, [tag])) + " cartoon"
    
    # Query Giphy
    params = {
        "api_key": GIPHY_API_KEY,
        "q": search_term,
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
        return jsonify({"error": f"No GIFs found for response emotion '{tag}'"}), 404

    gif_urls = [gif["images"]["original"]["url"] for gif in gifs]
    selected_gif = rank_gifs_by_clip(gif_urls, tag)

    return f"""
    <html>
        <body style="text-align: center; font-family: sans-serif;">
            <h2>You said: {user_input}</h2>
            <img src="{selected_gif}" alt="GIF response" />
            <p>Responding with: <b>{tag}</b></p>
        </body>
    </html>
    """

@app.route("/response_tags", methods=["GET"])
def get_response_tags():
    return jsonify(sorted(set(tag_to_examples.keys())))

if __name__ == "__main__":
    app.run(debug=True)
