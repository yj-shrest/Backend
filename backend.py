from google import genai
import json
from pydantic import BaseModel
import flask, flask_cors
from flask import request, jsonify
from gameCreator import create_game
app = flask.Flask(__name__)
flask_cors.CORS(app)

class responseBase(BaseModel):
    title: str
    description: str
    genre: str
    required_assets: list[str]
    instructions: str

class GameBase(BaseModel):
    html: str
    description: str
@app.route('/json', methods=['POST'])
def create_json():
    data = request.get_json()
    prompt = data['prompt']
    client = genai.Client(api_key="AIzaSyAFSjqpFOK2aG1jilF5RciOpjNbQYNi4cE")
    query = f"""You are a game design assistant. The user will give you a short description of a game idea in natural language.
            Your task is to generate a structured JSON object that represents this game concept. Not a level based game until specified. 
            Do not add music or sound assets to the game.
            The idea is {prompt}."""
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=query,
    config={
        'response_mime_type': 'application/json',
        'response_schema': responseBase,
    },
    )
    parsed_data = json.loads(response.text)
    return jsonify(parsed_data)

@app.route('/create_game', methods=['POST'])
def create():
    data = request.get_json()
    config = data["gameConfig"]
    html = create_game(config)
    return jsonify({"html": html})

@app.route('/update_game', methods=['POST'])
def update_game():
    data = request.get_json()
    feedback = data["feedbackPrompt"]
    html = data["gameHtml"]
    client = genai.Client(api_key="AIzaSyAFSjqpFOK2aG1jilF5RciOpjNbQYNi4cE")
    query = f"""update the game code with the following feedback: {feedback}. The game code is {html}."""
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=query,
    config={
        'response_mime_type': 'application/json',
        'response_schema': GameBase,
    },
    )
    parsed_data = json.loads(response.text)
    # Save the HTML content to a file
    with open("game.html", "w") as file:
        file.write(parsed_data["html"])
    return jsonify(parsed_data)


@app.route("/get_game/<gameid>", methods=["GET"])
def get_game(gameid):
    filepath = f"Gamefiles/game{gameid}/index.html"
    try:
        with open(filepath, "r") as file:
            game_content = file.read()
        return jsonify({"game": game_content})
    except FileNotFoundError:
        return jsonify({"error": "Game not found"}), 404

# if __name__ == "__main__":
#     prompt = "A platformer game where the player controls a character that can jump and run through levels filled with obstacles and enemies."
#     json_response = create_json(prompt)
#     print(json_response)
app.run(debug=True) 
