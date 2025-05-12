from flask import Flask, request, jsonify
import json

app = Flask(__name__)

# Load tagged GIF data
with open("gifs.json", "r") as f:
    gif_data = json.load(f)

@app.route("/get_gif", methods=["GET"])
def get_gif():
    emotion = request.args.get("emotion", "").lower()
    
    # Try to find a GIF that matches the emotion tag
    matches = [gif for gif in gif_data if emotion in gif["tags"]]
    
    if matches:
        return jsonify({"gif_url": matches[0]["url"]})
    else:
        return jsonify({"error": "No matching GIF found"}), 404

if __name__ == "__main__":
    app.run(debug=True)