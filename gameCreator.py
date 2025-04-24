from google import genai
import json
import logging
from typing import List, Dict, Any
import os 
from pydantic import BaseModel
import re
from urllib.parse import urlparse
import requests
import zipfile

API="YOUR_API_KEY_HERE"
client = genai.Client(API)


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



MODEL = "gemini-2.0-flash"
class responseBase(BaseModel):
    title: str
    description: str
    genre: str
    required_assets: list[str]
    game_logic: str
    instructions: str

class plan(BaseModel):
    sprite_textures: list[str]
    logic_functions: list[str]

class bootscene(BaseModel):
    code : str
    textures: list[str]

class scene(BaseModel):
    code : str

class GameAssetSuggestion(BaseModel):
    alternatives: List[str]

class AssetList(BaseModel):
    audio : List[str]
    maps : List[str]
    particles : List[str]
    sprites : List[str]
    tilesets : List[str]
    ui : List[str]

class GameParameters(BaseModel):
    assets: str
    functions: str

class FunctionDescription(BaseModel):
    code: str

class TextureCode(BaseModel):
    asset : List[str]
    code : List[str]


class Downloader:
    def __init__(self, api_key: str, base_dir: str = "assets"):
        """Initialize the downloader with API key and base directory."""
        self.client = genai.Client(api_key=api_key)
        self.base_dir = "game_output/downloaded/assets"  # Fixed directory name
        os.makedirs(self.base_dir, exist_ok=True)
        self.downloaded = []
        self.not_downloaded = []

    def set_config(self, config: Dict[str, Any]):
        """Set the game configuration."""
        self.config = config
        print(f"Game config set: {config['title']}")


    def find_alternative_asset(self,original_name):
        try:
            query = f"""
            Suggest 3 alternate links of the asset that are similar to "{original_name}" from labs.phaser.io.
            You must return the complete link to the asset including its extensions.

            Return only JSON in this format: {{"alternatives": ["alt1", "alt2", "alt3"]}} 
            """

            response = self.client.models.generate_content(
                model=MODEL,
                contents=query,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': GameAssetSuggestion,
                },
            )

            parsed = json.loads(response.text)
            return parsed["alternatives"]

        except Exception as e:
            print(f"⚠️ Gemini error: {str(e)}")
            return []
            
    def download_asset(self, url, retry_alternatives=True):
        try:
            # Ensure URL has a scheme
            if not urlparse(url).scheme:
                url = 'https://' + url

            try:
                filename = os.path.basename(urlparse(url).path)
                if not filename:  # Handle URLs without a path
                    filename = 'asset_' + str(hash(url))[:8] + '.bin'
            except Exception:
                filename = 'asset_' + str(hash(url))[:8] + '.bin'
                
            # Replace whitespaces with underscores
            filename = filename.replace(' ', '_')
                
            filepath = os.path.join(self.base_dir, filename)  # Removed category from path
            print(f"\n Downloading {url} ")

            if os.path.exists(filepath):
                print(f"⏩ Already exists: {filename}")
                self.downloaded.append(url)
                return True

            try:
                response = requests.get(url, stream=True, timeout=10, allow_redirects=True)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise requests.exceptions.HTTPError(f"Failed to download {url}: {str(e)}")

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Check if downloaded file is a zip
            if filename.endswith('.zip'):
                print(f"📦 Extracting zip: {filename}")
                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                    # Extract files ensuring no whitespaces in names
                    for zip_info in zip_ref.filelist:
                        zip_info.filename = zip_info.filename.replace(' ', '_')
                        zip_ref.extract(zip_info, self.base_dir)
                # Remove the zip file after extraction
                os.remove(filepath)
                print(f"✅ Extracted and removed: {filename}")
            else:
                print(f"✅ Downloaded: {filename}")

            self.downloaded.append(url)
            return True


        except requests.exceptions.HTTPError as e:
            if retry_alternatives:
                original_name = os.path.splitext(filename)[0]
                alternatives = self.find_alternative_asset(original_name)
                print(f"〽️ Alternatives found : " + str(alternatives))

                for alt in alternatives:
                    if self.download_asset(alt, retry_alternatives=False):
                        self.downloaded.append(alt)
                        return True
                    
            self.not_downloaded.append(url)
            print(f"❌ Failed {url}: {str(e)}")
            return False
        
    def download_all_assets(self,ASSETS):

        for category, urls in ASSETS.items():
            print(f"\n📁 Downloading {category} assets...")
            for url in urls:
                self.download_asset(url, category)
        print(f"\n✨ Asset download complete!")
        print(f"Downloaded assets: {self.downloaded}")  
        print(f"Not Downloaded assets: {self.not_downloaded}")  

        return self.downloaded, self.not_downloaded
 

class GameGenerator:
    def __init__(self, api_key: str, output_dir: str = "."):
        """Initialize the game generator with API key and output directory"""
        self.client = genai.Client(api_key=api_key)
        self.output_dir = output_dir
        self.ensure_output_dir()
        self.config = {}
        self.game_parameters = None
        self.html_template = self.load_html_template()
        self.downloader = Downloader(api_key)
        self.downloaded_assets = []
        self.not_downloaded_assets = []

        
    def ensure_output_dir(self):
        """Make sure the output directory exists"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"Created output directory: {self.output_dir}")
    
    def load_html_template(self) -> str:
        """Load the HTML template for the game"""
        template = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{{TITLE}}</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/phaser/3.55.2/phaser.min.js"></script>
    <style>
      body {
        margin: 0;
        padding: 0;
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        background-color: #FFFFFF;
      }
      canvas {
        display: block;
      }
    </style>
  </head>
  <body>
    <script>
      // Create all required textures programmatically to ensure game works without network issues
      {{SCENES}}
      
      // Game configuration
      const config = {
        type: Phaser.AUTO,
        width: 800,
        height: 600,
        backgroundColor: "#000000",
        physics: {
          default: "arcade",
          arcade: {
            gravity: { y: 300 },
            debug: false,
          },
        },
        scene: [MainScene],
      };

      // Create game instance
      const game = new Phaser.Game(config);
    </script>
  </body>
</html>"""
        return template
    
    def set_config(self, config: Dict[str, Any]):
        """Set the game configuration"""
        self.config = config
        logger.info(f"Game config set: {config['title']}")
        self.downloader.config = config

    def create_main_scene_template(self) -> str:
        """Create the MainScene class template"""
        return """class MainScene extends Phaser.Scene {
        constructor() {
          super("MainScene");
        }
      
{{MAIN_FUNCTIONS}}
      }"""
    
    def generate_game_parameters(self) -> Dict[str, Any]:
        """Generate the game parameters using Gemini API"""
        query = f"""
We are creating a game. 
The game's description is given as {self.config}.


Return a list that includes:
1.) All the assets that is needed for the game such as some main character's sprite, Enemy Sprite, Backgound Image Sprite, and others mentioned in the description. Do not add sound assets or music to the game.
2.) The functions that will be used to create the game, consistent with function naming conventions in Phaser JS.
"""
        logger.info("Sending query to generate game parameters...")
        
        try:
            response = self.client.models.generate_content(
                model=MODEL,
                contents=query,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': GameParameters,
                },
            )
            
            parsed_data = json.loads(response.text)
            self.game_parameters = parsed_data
            
            # Save parameters to file
            self._save_to_file("game_parameters.json", json.dumps(parsed_data, indent=2))
            logger.info("Game parameters generated successfully")
            
            return parsed_data
        except Exception as e:
            logger.error(f"Error generating game parameters: {e}")
            raise
    
    def download_assets(self, assets):
        # First generate textures programmatically
        query = f"""
        Generate Phaser code to programmatically create textures for all the assets below using graphics and shapes:
        {assets}
        
        The textures should be basic representations using rectangles, circles, triangles etc.
        Only return valid Phaser graphics code in JavaScript that creates and saves the textures.
        Follow this format for each texture:
        
        generateTexture(graphics) {{
            graphics.clear();
            // Draw the texture
            graphics.fillStyle(0xcolor);
            graphics.fillRect/fillCircle etc
            graphics.generateTexture('name', width, height);
        }}
        {{
                // Display loading text
                this.add.text(
                    this.cameras.main.width / 2,
                    this.cameras.main.height / 2,
                    'Loading game...',
                    {{ font: '24px Arial', fill: '#ffffff' }}
                ).setOrigin(0.5);

                // Generate all textures programmatically
                this.generateTextures();
            }}

            generateTextures() {{
                // Background with stars
                this.generateStarfieldTexture();

                // Player ship
                this.generatePlayerTexture();
            }}

            generateStarfieldTexture() {{
                const graphics = this.make.graphics({{ x: 0, y: 0, add: false }});
                graphics.fillStyle(0x000000);
                graphics.fillRect(0, 0, 800, 600);

                // Add some stars
                graphics.fillStyle(0xFFFFFF);
                for (let i = 0; i < 200; i++) {{
                    const x = Phaser.Math.Between(0, 800);
                    const y = Phaser.Math.Between(0, 600);
                    const size = Phaser.Math.Between(1, 3);
                    graphics.fillRect(x, y, size, size);
                }}

                // Add some bigger stars with glow
                graphics.fillStyle(0x00AAFF);
                for (let i = 0; i < 40; i++) {{
                    const x = Phaser.Math.Between(0, 800);
                    const y = Phaser.Math.Between(0, 600);
                    const size = Phaser.Math.Between(2, 4);
                    graphics.fillRect(x, y, size, size);
                }}

                graphics.generateTexture('background', 800, 600);
            }}
            generatePlayerTexture(){{
                const graphics = this.make.graphics({{x: 0, y: 0, add: false }});
                
                // Ship body
                graphics.fillStyle(0x4444FF);
                graphics.fillRect(15, 0, 20, 40);
                
                // Wings
                graphics.fillStyle(0x2222AA);
                graphics.fillTriangle(0, 30, 15, 15, 15, 40);
                graphics.fillTriangle(50, 30, 35, 15, 35, 40);
                
                // Engine
                graphics.fillStyle(0xFF8800);
                graphics.fillRect(20, 40, 10, 5);
                
                graphics.generateTexture('player', 50, 45);
            }}

            Do not write import export statements. 

        """
        
        # Get the texture generation code
        texture_response = self.client.models.generate_content(
            model=MODEL,
            contents=query,
            config={
                    'response_mime_type': 'application/json',
                    'response_schema': TextureCode,
                },
        )
        
        # Save the texture generation code
        self.texture_code = json.loads(texture_response.text)
        print("🗨️ Texture Codes for assets are : " + str(self.texture_code))
        
            
        # Now try to find real asset URLs
        query = f"""
        Convert the following asset descriptions into a Python dictionary.
        Each key in the dictionary should be a Phaser category like "sprites", "tilesets", "audio", "maps", "ui", or "particles",
        and the value should be a list of public asset URLs from labs.phaser.io that relates to the assets.
        You can also add other assets that are not in the list but are relevant to the game.

        Descriptions:
        {assets}

        For example 
        The format should be:
        ASSETS = {{
            "sprites": [
                "https://labs.phaser.io/assets/sprites/phaser-dude.png",
                ...
            ],
            ...
        }}

        Only return valid URLs.
        """

        response = self.client.models.generate_content(
                model=MODEL,
                contents=query,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': AssetList,
                },
            )
        self.assets = json.loads(response.text)
        print("Looking for online assets:", self.assets)
        
        # Try downloading online assets
        self.downloaded_assets, self.not_downloaded_assets = self.downloader.download_all_assets(self.assets)

        

    def generate_function_code(self, function_name: str, all_functions: List[str], 
                                existing_code: str = "") -> Dict[str, Any]:
        

        print(f"📩 Downloaded assets are : " + str(self.downloaded_assets))
        print(f"❌ Not Downloaded Assets are : " + str(self.downloaded_assets))
        """Generate code for a specific function using Gemini API"""
        
        query = f"""Generate the {function_name} function code for a Phaser 3 game.

        Context:
        We are implementing a game with title {self.config.get('title')}
        - Description: {self.config.get('description')}
        - Functions we will be implementing: {", ".join(all_functions)}
        - Available Assets: {[os.path.basename(asset) for asset in self.downloaded_assets]}

        Asset Requirements:
        - If the asset required is available load the assets from "./downloaded/assets/" directory
        - All filenames use underscores instead of spaces
        - For missing assets, use the textures from {[code for code in self.texture_code['code']]}

        Technical Requirements:
        1. Use proper scene context (this)
        2. Use arrow functions or WASD for event handlers. Space to shoot if required. 
        3. Handle asset loading failures gracefully
        4. Include error handling
        5. Don't add code comments
        6. Follow Phaser 3 best practices
        7. Make sure cellWidth and cellHeight are defined and assigned before using them to generate textures. Avoid using undefined or zero width/height in generateTexture().
        8. Use workflow suitable for Phaser 3.
        9. Use Phaser optimized codes like graphics.generateTexture() instead of canvas + toDataURL + addBase64()
        {f'- Existing Code: {existing_code}' if existing_code else ''}

        Return only the function implementation in valid JavaScript.
        """

        logger.info(f"Generating code for function: {function_name}")
        
        try:
            response = self.client.models.generate_content(
                model=MODEL,
                contents=query,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': FunctionDescription,
                },
            )
            
            parsed_data = json.loads(response.text)
            
            # Add to functions log
            self._append_to_file("functions_log.txt", f"\n\n--- {function_name} ---\n{parsed_data['code']}")
            print(str(parsed_data['code']))
            return parsed_data
        except Exception as e:
            logger.error(f"Error generating function {function_name}: {e}")
            return {"code": f"// Error generating {function_name}: {e}"}
    



    def _save_to_file(self, filename: str, content: str):
        """Save content to a file in the output directory"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w") as file:
            file.write(content)
    
    def _append_to_file(self, filename: str, content: str):
        """Append content to a file in the output directory"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "a") as file:
            file.write(content)
    
    def _read_file(self, filename: str, default: str = "") -> str:
        """Read content from a file in the output directory"""
        filepath = os.path.join(self.output_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, "r") as file:
                return file.read()
        return default
    
    def clean_function_code(self, code: str) -> str:
        """Clean up function code by removing 'function' keyword if present"""
        code = re.sub(r'^function\s*', '', code)
        return re.sub(r'\s*,$', '', code)
    
    
    def generate_complete_game(self) -> str:
        """Generate the complete game HTML file"""
        if not self.game_parameters:
            self.generate_game_parameters()
        
        functions_required = self.game_parameters['functions'].split(", ")
        
        self.download_assets(self.game_parameters['assets'].split(", "))

        # Map functions to their classes
        main_functions = []
        
        all_code = ""
        for function in functions_required:
            
            # Generate function code
            function_description = self.generate_function_code(
                function, functions_required, all_code
            )
            
            clean_code = self.clean_function_code(function_description['code'])
            all_code += clean_code + "\n\n"
            
            main_functions.append(clean_code)
            
    
        # Create scene code
        main_scene = self.create_main_scene_template().replace(
            "{{MAIN_FUNCTIONS}}", "\n".join(main_functions)
        )
        
        scenes_code = main_scene
        
        # Create final HTML
        html = self.html_template.replace(
            "{{TITLE}}", self.config.get("title", "Phaser Game")
        ).replace(
            "{{SCENES}}", scenes_code
        )
        
        # Save the complete game
        self._save_to_file("game.html", html)
        logger.info("Complete game generated and saved to game.html")
        
        return html
    
    def get_assets_list(self) -> List[str]:
        """Get the list of assets required for the game"""
        if not self.game_parameters:
            self.generate_game_parameters()
        
        return self.game_parameters['assets'].split(", ")
    
    def get_functions_list(self) -> List[str]:
        """Get the list of functions required for the game"""
        if not self.game_parameters:
            self.generate_game_parameters()
        
        return self.game_parameters['functions'].split(", ")



def create_json(prompt):
    client = genai.Client(api_key=API)
    query = f"""You are a game design assistant. The user will give you a short description of a game idea in natural language.
            Your task is to generate a structured JSON object that represents this game concept. Donot add sound assets or music to the game.
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
    return parsed_data



def create_game(config):
    api_key = "API"
    
    # config = {
    #     "description": "A simple rogue like game where the main character kills enemies and progresses towards boss. The game ends once the boss is dead. If the main character dies then the game restarts.",
    #     "genre": "RogueLike",
    #     "instructions": "Use standard Keyboard controls for movement and attack. Use 'R' to restart the game.",
    #     "level_logic": "The game consists of multiple levels with increasing difficulty. The player must defeat enemies and collect power-ups to progress. The game ends when the boss is defeated.",
    #     "required_assets": [
    #         "Main Character Sprite",
    #         "Enemy Sprites",
    #         "Boss Sprite",
    #         "Background Image",
    #     ],
    #     "title": "RogueLike"
    # }

    # config = {
    #     "description": "A simple chess game.",
    #     "genre": "Puzzle",
    #     "instructions": "Use Mouse to move pieces",
    #     "level_logic": "Players take turns moving their pieces. The game ends when one player checkmates the other.",
    #     "required_assets": [
    #         "Chess Bishop Sprite",
    #         "Chess Knight Sprite",
    #         "Chess Rook Sprite",
    #         "Chess Queen Sprite",
    #         "Chess King Sprite",
    #         "Chess Pawn Sprite",
    #         "Chess Board Sprite",
    #     ],
    #     "title": "Chess"
    # }
    
    # config = {
    #     "description": "A simple tic tac toe game.",
    #     "genre": "Puzzle",
    #     "instructions": "Use Mouse as input",
    #     "level_logic": "Players take turns placing their marks in a 3x3 grid. The first player to get three marks in a row (horizontally, vertically, or diagonally) wins the game.",
    #     "required_assets": [
    #         "Cross Sprite",
    #         "Circle Sprite",
    #     ],
    #     "title": "Tic Tac Toe"
    # }
    
    # config = {
    #     "description": "A modern and stylish platformer game where a player navigates across a 2d environment, encounters enemies, and kills them by using projectiles.",
    #     "genre": "Platformer",
    #     "instructions": "Use arrow keys or W key to move up, S to move Down, A to move left and D to move right. Press 'R' to restart the level. Press SpaceBar to shoot a projectile towards enemies. There are 3 lives for player. Add proper animation for the projectile and proper collision detection.",
    #     "level_logic": "Levels consist of waves of enemies with increasing difficulty. The player must defeat all enemies to progress to the next level. The game ends when the player runs out of lives.",
    #     "required_assets": [
    #         "Player sprite",
    #         "Enemy sprites",
    #         "Background image",
    #     ],
    #     "title": "Platformer"
    # }
    
    # Create output directory
    output_dir = "game_output"

    
    # Create game generator
    generator = GameGenerator(api_key=api_key, output_dir=output_dir)
    generator.set_config(config)
    
    # Generate game parameters
    params = generator.generate_game_parameters()
    
    # Print assets and functions required
    assets = generator.get_assets_list()
    print("Assets required:")
    for asset in assets:
        print(f"- {asset}")

    print("Functions required:")
    functions = generator.get_functions_list()
    for function in functions:
        print(f"- {function}")

    # Generate complete game
    game = generator.generate_complete_game()
    print(f"\nGame generated successfully! Check {output_dir}/game.html")
    return game

if __name__ == "__main__":
    config = create_json("A simple game where a player controls a character that can jump and collect coins. The game should have a simple background and a few obstacles.")
    print(config)
    create_game(config)