import requests
import threading
import random
import time
from performance_logger import log_event, track_api_response_time, log_final_stats  # Import tracking functions

# ==============================
# API SETTINGS
# ==============================

SIGNUPCODE = "Carleton comps 2024-2025!"
NUM_USERS = 10  # Adjust to increase bot players
BASE_USERNAME = "bot_user_"
API_BASE_URL = "http://onemovechess-api.eastus2.cloudapp.azure.com"

HEADERS = {'Content-type': 'application/json', 'Accept': 'application/json'}
registered_users = []  # Stores users with credentials & tokens

# ==============================
# Step 1: Register Users
# ==============================

def register_user(bot_index):
    # Registers a new user
    random_number = random.randint(1000, 9999)  
    username = f"{BASE_USERNAME}{bot_index}_{random_number}"  
    
    response = requests.post(f"{API_BASE_URL}/Account/{username}", data=f'"{SIGNUPCODE}"', headers=HEADERS)
    
    if response.status_code == 200:
        password = response.json().get("password", "No password returned")
        print(f"Registered {username} | Password: {password}")
        registered_users.append({"username": username, "password": password})
    else:
        print(f"Error registering {username}: {response.status_code} {response.text}")

threads = [threading.Thread(target=register_user, args=(i,)) for i in range(NUM_USERS)]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()

print("All users registered. Moving to login...\n")

# ==============================
# Step 2: Log In Users & Get Tokens
# ==============================

def login_user(user):
    # Logs in a user and gets authentication token
    login_url = f"{API_BASE_URL}/Token?username={user['username']}"
    response = requests.post(login_url, headers={"Content-Type": "application/json"}, data=f'"{user["password"]}"')

    if response.status_code == 200:
        user["token"] = response.text.strip('"')
        print(f"{user['username']} logged in")
    else:
        print(f"Login failed for {user['username']}: {response.status_code} {response.text}")
        user["token"] = None

threads = [threading.Thread(target=login_user, args=(user,)) for user in registered_users]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()

registered_users = [user for user in registered_users if user.get("token")]

if len(registered_users) < 1:
    print("Not enough users successfully logged in. Exiting...")
    exit()

print("All users logged in. Matching players...\n")

# ==============================
# Step 3: Get or Create a Game
# ==============================

def fetch_game(user):
    # Fetches game state or creates a new game if none exists
    headers_auth = {"Authorization": f"Bearer {user['token']}", "Accept": "application/json"}
    
    response = requests.get(f"{API_BASE_URL}/Game", headers=headers_auth)
    
    if response.status_code == 200:
        game_data = response.json()
        user["gameId"] = game_data["gameId"]
        print(f"{user['username']} is playing Game ID: {user['gameId']}")
    else:
        print(f"Failed to fetch game for {user['username']}: {response.status_code}")

threads = [threading.Thread(target=fetch_game, args=(user,)) for user in registered_users]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()

print("All users matched with games. Starting moves...\n")

# ==============================
# Step 4: Automate Making Moves
# ==============================

def play_game(user):
    # Plays a series of random, independent moves and we track performance
    headers_auth = {"Authorization": f"Bearer {user['token']}", "Accept": "application/json"}

    session_start = time.time()
    successful_moves = 0
    failed_moves = 0
    total_response_time = 0

    for _ in range(1):  # Number of independent moves to make
        time.sleep(3)

        # Fetch a new game
        start_time = time.time()
        response = requests.get(f"{API_BASE_URL}/Game", headers=headers_auth)
        track_api_response_time(start_time, "Fetch Game", user)

        if response.status_code != 200:
            log_event(f"{user['username']} failed to fetch game state: {response.status_code}", "error")
            failed_moves += 1
            return

        game_data = response.json()
        game_id = game_data["gameId"]
        current_move_number = game_data["currentMoveNumber"]
        legal_moves = game_data.get("legalMovesBySquare", [])

        if not legal_moves:
            log_event(f"⚠️ {user['username']} has no legal moves in Game {game_id}.", "warning")
            return

        move_choice = random.choice(legal_moves)
        start_square = move_choice["startSquare"]
        end_square = random.choice(move_choice["endSquares"])
        move_payload = {
            "gameId": game_id,
            "move": f"{start_square}{end_square}",
            "moveNumber": current_move_number
        }

        # Make a move
        start_time = time.time()
        move_response = requests.post(f"{API_BASE_URL}/Game", params=move_payload, headers=headers_auth)
        track_api_response_time(start_time, "Make Move", user)

        if move_response.status_code == 200:
            successful_moves += 1
            log_event(f"{user['username']} moved {start_square} → {end_square} in Game {game_id} (Move #{current_move_number})")
        else:
            failed_moves += 1
            log_event(f"{user['username']} failed to move: {move_response.status_code} {move_response.text}", "error")

        time.sleep(5)  # Allow server time to process

    # Log final session stats
    log_final_stats(user, successful_moves, failed_moves, total_response_time, session_start)


# Start game play
threads = [threading.Thread(target=play_game, args=(user,)) for user in registered_users]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()

print("Load test complete.")
