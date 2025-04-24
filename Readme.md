# 🎮 SUI Playground Backend

This is a Flask-based backend service for generating, updating, and managing HTML5 games using natural language prompts and AI-powered content generation. It uses Google's Gemini model for game design, supports storage/retrieval via a blockchain blob store, and can generate game screenshots.

---

## 🚀 Features

- 🎨 Generate game designs in structured JSON using Gemini AI (`/json`)
- 🕹️ Generate playable HTML games from JSON configs (`/create_game`)
- ♻️ Update games using feedback (`/update_game`)
- 💾 Store games and images on decentralized blob storage (`/store_blob`)
- 📥 Retrieve game HTML or image from blob storage (`/get_blob`, `/get_image`)
- 🔍 Fetch game file by ID (`/get_game/<gameid>`)
- 📸 Automatically generate and store a screenshot of the game

---

## 🛠️ Tech Stack

- **Flask** (Python web framework)
- **Pydantic** (for request/response schema validation)
- **Google Gemini API** (natural language to structured JSON )
- **Claude API**(json to game code) 
- **Blockchain Blob Storage** (for decentralized storage)
- **OpenCV + HTML rendering** (for game screenshots)

---

## 📦 Installation

```bash
git clone https://github.com/yourusername/game-ai-backend.git
cd game-ai-backend
pip install -r requirements.txt
python app.py
```

---

## 🔐 Environment Variables

Replace the Gemini API key in `app.py` with an environment variable for security:

```python
import os
api_key = os.environ.get("GEMINI_API_KEY")
```

And set the variable:

```bash
export GEMINI_API_KEY="your_api_key_here"
```

---

## 📡 API Endpoints

### POST `/json`

Generates a game idea in JSON format from a natural language prompt.

**Request Body:**
```json
{
  "prompt": "A platformer game where a cat avoids water drops"
}
```

**Response:**
```json
{
  "title": "Rainy Cat Adventure",
  "description": "...",
  "genre": "...",
  "required_assets": ["cat sprite", "rain animation", "tileset"],
  "instructions": "Use arrow keys to move..."
}
```

---

### POST `/create_game`

Generates HTML code for a game from a JSON config.

**Request Body:**
```json
{
  "gameConfig": { /* game JSON as returned from /json */ }
}
```

**Response:**
```json
{ "html": "<!DOCTYPE html>..." }
```

---

### POST `/update_game`

Updates an existing game with new feedback.

**Request Body:**
```json
{
  "feedbackPrompt": "Add more enemies",
  "gameHtml": "<!DOCTYPE html>..."
}
```

**Response:**
```json
{ "html": "<!DOCTYPE html>..." }
```

---

### GET `/get_game/<gameid>`

Fetch the HTML content of a previously generated game.

---

### POST `/store_blob`

Stores the game HTML and its screenshot to blob storage.

**Request Body:**
```json
{ "gameHtml": "<!DOCTYPE html>..." }
```

**Response:**
```json
{
  "blob_id": "abc123...",
  "image_blob_id": "img456..."
}
```

---

### GET `/get_blob/<blob_id>`

Returns the raw blob content stored earlier (game HTML).

---

### GET `/get_image/<blob_id>`

Returns the stored game screenshot as a PNG image.

---

## 📂 Project Structure

```
├── app.py                  # Main Flask app
├── gameCreator.py          # Game generation logic
├── gamemaker.py            # AI code generation + update logic
├── blockchain.py           # Blob store interface
├── screenshot.py           # Game screenshot generation
├── requirements.txt
```

---

## 🧪 Example Usage

```bash
curl -X POST http://localhost:5000/json \
     -H "Content-Type: application/json" \
     -d '{"prompt": "a puzzle game where robots push boxes"}'
```

---

## 📄 License

MIT License. See `LICENSE` file for more details.

