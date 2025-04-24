from sui import SuiClient, SuiConfig
from sui.transactions import SuiTransaction
from sui.move import MoveCall
from sui.keypair import KeyPair

# Setup
client = SuiClient()
keypair = KeyPair.from_mnemonic("gadget brand analyst omit away open gasp key doll dance buddy damage")  # 🔐 Insert your wallet's mnemonic securely
client.set_active_address(keypair.address)

PACKAGE_ID = "0xc7a4be7ec704950cfa57d1d8fba36dbdcb2f0eb273b96685b1de7da4dc8a6983"
MODULE = "ai_game_generator"

# 🔧 Function 1: create_game_book
def create_game_book():
    tx = SuiTransaction()
    tx.add(MoveCall(PACKAGE_ID, MODULE, "create_game_book", args=[]))
    result = client.execute(tx, keypair)
    return result

# 🔧 Function 2: create_game
def create_game(game_book_id: str, blob_id: bytes, parent: list = None):
    parent_option = ["Some", parent] if parent else ["None"]
    tx = SuiTransaction()
    tx.add(MoveCall(
        PACKAGE_ID,
        MODULE,
        "create_game",
        args=[
            game_book_id,      # mutable reference to GameBook object
            blob_id,           # blob_id as vector<u8>
            parent_option      # Option<u64>
        ]
    ))
    result = client.execute(tx, keypair)
    return result

# 🔧 Function 3: update_leaderboard
def update_leaderboard(game_id: str, player_address: str, score: int):
    tx = SuiTransaction()
    tx.add(MoveCall(
        PACKAGE_ID,
        MODULE,
        "update_leaderboard",
        args=[
            game_id,
            player_address,
            score
        ]
    ))
    result = client.execute(tx, keypair)
    return result

# Example usage:
# print(create_game_book())
# print(create_game("0xYourGameBookID", list(b"your_blob_id"), parent=[123]))
# print(update_leaderboard("0xYourGameID", "0xPlayerAddress", 420))
